import os
import pickle

import torch
from PIL import Image
from transformers import AutoProcessor, AutoModel


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "openai/clip-vit-base-patch32"

DATASET_PATH = "data/found_items"

OUTPUT_PATH = "models/image_embeddings.pkl"


# ============================================================
# LOAD CLIP MODEL
# ============================================================

print("Loading CLIP model...")

model = AutoModel.from_pretrained(
    MODEL_NAME
)

processor = AutoProcessor.from_pretrained(
    MODEL_NAME
)

model.eval()

print("CLIP model loaded successfully!")


# ============================================================
# GENERATE IMAGE EMBEDDING
# ============================================================

def get_image_embedding(image_path):

    image = Image.open(
        image_path
    ).convert("RGB")

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
    image_features = (
        image_features /
        image_features.norm(
            p=2,
            dim=-1,
            keepdim=True
        )
    )

    return image_features.squeeze().numpy()


# ============================================================
# ADD SINGLE ITEM TO DATABASE
# ============================================================

def add_item_to_database(
    image_path,
    category,
    filename
):

    # Generate embedding
    embedding = get_image_embedding(
        image_path
    )

    # Create models directory
    os.makedirs(
        os.path.dirname(OUTPUT_PATH),
        exist_ok=True
    )

    # Load existing database
    if os.path.exists(OUTPUT_PATH):

        with open(
            OUTPUT_PATH,
            "rb"
        ) as file:

            embeddings = pickle.load(file)

    else:

        embeddings = []


    # Create new record
    new_item = {

        "image_path": os.path.abspath(image_path),

        "category": category,

        "filename": filename,

        "embedding": embedding

    }


    # Add item
    embeddings.append(
        new_item
    )


    # Save updated database
    with open(
        OUTPUT_PATH,
        "wb"
    ) as file:

        pickle.dump(
            embeddings,
            file
        )


    print(
        f"Added {filename} to embedding database."
    )


# ============================================================
# GENERATE DATASET EMBEDDINGS
# ============================================================

def generate_dataset_embeddings():

    embeddings = []

    print("\nScanning dataset...")


    for category in os.listdir(
        DATASET_PATH
    ):

        category_path = os.path.join(
            DATASET_PATH,
            category
        )


        if not os.path.isdir(
            category_path
        ):

            continue


        print(
            f"\nCategory: {category}"
        )


        for filename in os.listdir(
            category_path
        ):

            if not filename.lower().endswith(
                (
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp"
                )
            ):

                continue


            image_path = os.path.join(
                category_path,
                filename
            )


            try:

                embedding = get_image_embedding(
                    image_path
                )


                embeddings.append(
                    {

                        "image_path": image_path,

                        "category": category,

                        "filename": filename,

                        "embedding": embedding

                    }
                )


                print(
                    f"  ✓ {filename}"
                )


            except Exception as e:

                print(
                    f"  ✗ Error processing "
                    f"{filename}: {e}"
                )


    # Create models directory
    os.makedirs(
        os.path.dirname(OUTPUT_PATH),
        exist_ok=True
    )


    # Save embeddings
    with open(
        OUTPUT_PATH,
        "wb"
    ) as file:

        pickle.dump(
            embeddings,
            file
        )


    print("\n" + "=" * 50)

    print(
        "EMBEDDING GENERATION COMPLETE"
    )

    print("=" * 50)

    print(
        f"Total images processed: "
        f"{len(embeddings)}"
    )

    print(
        f"Saved to: {OUTPUT_PATH}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    generate_dataset_embeddings()

def add_item_to_database(
    image_path,
    category,
    filename
):

    # Generate embedding
    embedding = get_image_embedding(
        image_path
    )

    # Load existing database
    if os.path.exists(OUTPUT_PATH):

        with open(
            OUTPUT_PATH,
            "rb"
        ) as file:

            embeddings = pickle.load(file)

    else:

        embeddings = []

    # Add new item
    embeddings.append(
        {
            "image_path": image_path,
            "category": category,
            "filename": filename,
            "embedding": embedding
        }
    )

    # Save updated database
    with open(
        OUTPUT_PATH,
        "wb"
    ) as file:

        pickle.dump(
            embeddings,
            file
        )

    print(
        f"Added {filename} to embedding database."
    )