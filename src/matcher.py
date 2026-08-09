import pickle

import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel


MODEL_NAME = "openai/clip-vit-base-patch32"
EMBEDDINGS_PATH = "models/image_embeddings.pkl"


print("Loading CLIP model...")

model = CLIPModel.from_pretrained(MODEL_NAME)
processor = CLIPProcessor.from_pretrained(MODEL_NAME)

model.eval()

print("CLIP loaded successfully!")


# Load stored embeddings
with open(EMBEDDINGS_PATH, "rb") as file:
    database = pickle.load(file)

print(f"Loaded {len(database)} stored image embeddings.")


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

    image_features = image_features / image_features.norm(
        p=2,
        dim=-1,
        keepdim=True
    )

    return image_features.squeeze()


def find_matches(image_path, top_k=5):

    query_embedding = get_image_embedding(image_path)

    results = []

    for item in database:

        stored_embedding = torch.tensor(
            item["embedding"],
            dtype=torch.float32
        )

        similarity = torch.dot(
            query_embedding,
            stored_embedding
        ).item()

        results.append({
            "filename": item["filename"],
            "category": item["category"],
            "image_path": item["image_path"],
            "similarity": similarity
        })

    results.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return results[:top_k]


if __name__ == "__main__":

    print("\nAI Lost & Found Matcher")
    print("=" * 40)

    image_path = input(
        "Enter the path of a test image: "
    )

    matches = find_matches(image_path)

    print("\nTop Matches")
    print("=" * 40)

    for rank, match in enumerate(matches, 1):

        score = match["similarity"] * 100

        print(
            f"{rank}. "
            f"{match['filename']} | "
            f"{match['category']} | "
            f"{score:.2f}%"
        )