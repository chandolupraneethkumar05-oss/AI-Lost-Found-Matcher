import os
import pickle
import torch
import numpy as np
from PIL import Image
from transformers import AutoProcessor, AutoModel
from src.database import db

MODEL_NAME = "openai/clip-vit-base-patch32"
DATASET_PATH = "data/found_items"
OUTPUT_PATH = "models/image_embeddings.pkl"

_model = None
_processor = None

def get_model():
    global _model, _processor
    if _model is None or _processor is None:
        _model = AutoModel.from_pretrained(MODEL_NAME)
        _processor = AutoProcessor.from_pretrained(MODEL_NAME)
        _model.eval()
    return _model, _processor

def get_image_embedding(image_path):
    model, processor = get_model()
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        vision_outputs = model.vision_model(pixel_values=inputs["pixel_values"])
        image_features = vision_outputs.pooler_output
        image_features = model.visual_projection(image_features)

    # Normalize embedding
    image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
    return image_features.squeeze().numpy()

def add_item_to_database(image_path, category, filename, title=None, location=None):
    embedding = get_image_embedding(image_path)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    rel_path = os.path.relpath(image_path).replace("\\", "/") if os.path.exists(image_path) else image_path

    # Save to unified database
    item_record = {
        "title": title or f"{category.title()} ({filename})",
        "category": category,
        "filename": filename,
        "image_path": rel_path,
        "location": location or "Campus Custody Desk",
        "date_found": os.path.basename(filename).split("_")[0] if "_" in filename else "2026-09-29",
        "status": "Available",
        "custody_location": "Central Security Custody Vault",
        "verification_prompt": "Describe any unique scratch, marks, or packaging details.",
        "embedding": embedding.tolist()
    }
    db.add_found_item(item_record)
    print(f"Added {filename} to centralized database and legacy pickle.")