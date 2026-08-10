import pickle
import os
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "openai/clip-vit-base-patch32"
EMBEDDINGS_PATH = "models/image_embeddings.pkl"

# Minimum similarity required to consider an item a match
MIN_SIMILARITY = 0.55


# ============================================================
# LOAD CLIP MODEL
# ============================================================

print("Loading CLIP model...")

model = CLIPModel.from_pretrained(MODEL_NAME)
processor = CLIPProcessor.from_pretrained(MODEL_NAME)

model.eval()

print("CLIP loaded successfully!")


# ============================================================
# LOAD STORED EMBEDDINGS
# ============================================================

with open(EMBEDDINGS_PATH, "rb") as file:
    database = pickle.load(file)

print(f"Loaded {len(database)} stored image embeddings.")


# ============================================================
# IMAGE EMBEDDING
# ============================================================

def get_image_embedding(image_path):

    image = Image.open(image_path).convert("RGB")

    inputs = processor(
        images=image,
        return_tensors="pt"
    )

    with torch.no_grad():

        vision_outputs = model.vision_model(
            pixel_values=inputs["pixel_values"]
        )

        image_features = vision_outputs.pooler_output

        image_features = model.visual_projection(
            image_features
        )

    # Normalize embedding
    image_features = image_features / image_features.norm(
        p=2,
        dim=-1,
        keepdim=True
    )

    return image_features.squeeze()


# ============================================================
# FIND MATCHES
# ============================================================

def resolve_image_path(image_path):
    """
    Resolve image paths so they work both locally and on Streamlit Cloud.
    """

    if not image_path:
        return None

    # Normalize Windows/Linux path separators
    image_path = str(image_path).replace("\\", "/")

    # 1. Direct path
    if os.path.exists(image_path):
        return image_path

    # 2. Try relative to project root
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )

    relative_path = os.path.join(
        project_root,
        image_path
    )

    if os.path.exists(relative_path):
        return relative_path

    # 3. Search common image folders by filename
    filename = os.path.basename(image_path)

    search_folders = [
        os.path.join(project_root, "data"),
        os.path.join(project_root, "data", "found_images"),
        os.path.join(project_root, "data", "images"),
        os.path.join(project_root, "data", "found_items"),
        os.path.join(project_root, "data", "test_images"),
    ]

    for folder in search_folders:

        if not os.path.exists(folder):
            continue

        for root, dirs, files in os.walk(folder):

            if filename in files:
                return os.path.join(root, filename)

    return None


def find_matches(
    image_path,
    description=None,
    selected_category=None,
    top_k=5,
    min_similarity=MIN_SIMILARITY
):

    query_embedding = get_image_embedding(image_path)

    results = []

    # Normalize selected category
    category = None

    if selected_category:
        category = selected_category.strip().lower()

    # --------------------------------------------------------
    # COMPARE WITH DATABASE
    # --------------------------------------------------------

    for item in database:

        item_category = str(
            item.get("category", "")
        ).strip().lower()

        # ----------------------------------------------------
        # CATEGORY FILTER
        # ----------------------------------------------------
        # If user selected a category, only compare with
        # images belonging to that category.
        # ----------------------------------------------------

        if category:

            if item_category != category:
                continue

        # ----------------------------------------------------
        # STORED EMBEDDING
        # ----------------------------------------------------

        stored_embedding = torch.tensor(
            item["embedding"],
            dtype=torch.float32
        )

        # ----------------------------------------------------
        # COSINE SIMILARITY
        # ----------------------------------------------------

        similarity = torch.dot(
            query_embedding,
            stored_embedding
        ).item()

        # ----------------------------------------------------
        # SIMILARITY THRESHOLD
        # ----------------------------------------------------

        if similarity < min_similarity:
            continue

        results.append({
            "filename": item["filename"],
            "category": item["category"],
            "image_path": resolve_image_path(
            item["image_path"]
            ),
            "similarity": similarity
        })

    # ========================================================
    # SORT BY HIGHEST SIMILARITY
    # ========================================================

    results.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    # ========================================================
    # REMOVE DUPLICATE FILES
    # ========================================================

    unique_results = []

    seen_files = set()

    for result in results:

        filename = result["filename"]

        if filename in seen_files:
            continue

        seen_files.add(filename)

        unique_results.append(result)

        if len(unique_results) >= top_k:
            break

    return unique_results


# ============================================================
# TEST FROM TERMINAL
# ============================================================

if __name__ == "__main__":

    print("\nAI Lost & Found Matcher")
    print("=" * 40)

    image_path = input(
        "Enter the path of a test image: "
    )

    category = input(
        "Enter category (or press Enter for all): "
    ).strip()

    if category == "":
        category = None

    matches = find_matches(
        image_path,
        category=category,
        top_k=5
    )

    print("\nTop Matches")
    print("=" * 40)

    if not matches:

        print(
            "No sufficiently similar matching item found."
        )

    else:

        for rank, match in enumerate(
            matches,
            start=1
        ):

            score = (
                match["similarity"] * 100
            )

            print(
                f"{rank}. "
                f"{match['filename']} | "
                f"{match['category']} | "
                f"{score:.2f}%"
            )