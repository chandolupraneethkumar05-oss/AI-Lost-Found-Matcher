import pickle
import os
import torch
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from src.database import db, LEGACY_EMBEDDINGS_PATH

# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "openai/clip-vit-base-patch32"
EMBEDDINGS_PATH = LEGACY_EMBEDDINGS_PATH
MIN_SIMILARITY = 0.50

# Lazy-loaded model & processor to prevent redundant overhead
_model = None
_processor = None

def get_model_and_processor():
    global _model, _processor
    if _model is None or _processor is None:
        print("Loading CLIP model in matcher...")
        _model = CLIPModel.from_pretrained(MODEL_NAME)
        _processor = CLIPProcessor.from_pretrained(MODEL_NAME)
        _model.eval()
    return _model, _processor


# ============================================================
# DATABASE LOADER
# ============================================================

def load_stored_database():
    """Load items from centralized database or legacy pickle."""
    items = db.get_all_found_items()
    if items:
        return items
    if os.path.exists(EMBEDDINGS_PATH):
        try:
            with open(EMBEDDINGS_PATH, "rb") as file:
                return pickle.load(file)
        except Exception:
            return []
    return []

database = load_stored_database()


# ============================================================
# IMAGE EMBEDDING
# ============================================================

def get_image_embedding(image_path):
    model, processor = get_model_and_processor()
    image = Image.open(image_path).convert("RGB")

    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        vision_outputs = model.vision_model(pixel_values=inputs["pixel_values"])
        image_features = vision_outputs.pooler_output
        image_features = model.visual_projection(image_features)

    # Normalize embedding
    image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
    return image_features.squeeze()


# ============================================================
# PATH RESOLVER
# ============================================================

def resolve_image_path(image_path):
    """
    Resolve image paths so they work reliably across platforms.
    """
    if not image_path:
        return None

    image_path = str(image_path).replace("\\", "/")

    if os.path.exists(image_path):
        return image_path

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    relative_path = os.path.join(project_root, image_path)

    if os.path.exists(relative_path):
        return relative_path

    filename = os.path.basename(image_path)
    search_folders = [
        os.path.join(project_root, "data"),
        os.path.join(project_root, "data", "found_items"),
        os.path.join(project_root, "data", "registered_items"),
        os.path.join(project_root, "data", "test_images"),
    ]

    for folder in search_folders:
        if not os.path.exists(folder):
            continue
        for root, dirs, files in os.walk(folder):
            if filename in files:
                return os.path.join(root, filename).replace("\\", "/")

    return None


# ============================================================
# FIND MATCHES
# ============================================================

def find_matches(
    image_path,
    description=None,
    selected_category=None,
    top_k=5,
    min_similarity=MIN_SIMILARITY
):
    """Find matching items against stored records."""
    query_embedding = get_image_embedding(image_path)
    results = []

    category = None
    if selected_category and selected_category.lower() != "all":
        category = selected_category.strip().lower()

    items = load_stored_database()

    for item in items:
        item_category = str(item.get("category", "")).strip().lower()

        if category and item_category != category:
            continue

        stored_emb = item.get("embedding")
        if stored_emb is None:
            continue

        stored_embedding = torch.tensor(stored_emb, dtype=torch.float32)
        # Normalize
        stored_norm = stored_embedding.norm(p=2, dim=-1, keepdim=True)
        if stored_norm.item() > 0:
            stored_embedding = stored_embedding / stored_norm

        similarity = torch.dot(query_embedding, stored_embedding).item()

        if similarity < min_similarity:
            continue

        raw_path = item.get("image_path", "")
        resolved = resolve_image_path(raw_path)

        results.append({
            "id": item.get("id", ""),
            "title": item.get("title", item.get("filename", "")),
            "filename": item.get("filename", os.path.basename(raw_path)),
            "category": item.get("category", ""),
            "location": item.get("location", "Campus Custody"),
            "image_path": resolved if resolved else raw_path.replace("\\", "/"),
            "similarity": round(similarity, 4),
            "confidence_percent": round(similarity * 100, 1)
        })

    results.sort(key=lambda x: x["similarity"], reverse=True)

    # De-duplicate
    unique_results = []
    seen = set()
    for res in results:
        fn = res["filename"]
        if fn in seen:
            continue
        seen.add(fn)
        unique_results.append(res)
        if len(unique_results) >= top_k:
            break

    return unique_results


if __name__ == "__main__":
    print("\nAI Lost & Found Matcher")
    print("=" * 40)
    test_img = input("Enter the path of a test image: ")
    if os.path.exists(test_img):
        matches = find_matches(test_img)
        print(f"\nFound {len(matches)} matches:")
        for m in matches:
            print(f"- {m['title']} ({m['category']}) | Confidence: {m['confidence_percent']}% | Path: {m['image_path']}")
    else:
        print("Image file not found.")