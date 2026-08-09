import os
import pickle
import json
import uuid
from datetime import datetime

import streamlit as st
import torch
from PIL import Image, ImageOps
from transformers import AutoProcessor, AutoModel

from src.embeddings import add_item_to_database


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "openai/clip-vit-base-patch32"

EMBEDDINGS_PATH = "models/image_embeddings.pkl"

REGISTERED_ITEMS_PATH = "data/registered_items"

METADATA_PATH = "data/registered_items_metadata.json"


def prepare_display_image(image_path, width=280, height=200):

    image = Image.open(
        image_path
    ).convert("RGB")

    # Fit image inside fixed dimensions
    image.thumbnail(
        (width, height),
        Image.Resampling.LANCZOS
    )

    # Create fixed-size canvas
    canvas = Image.new(
        "RGB",
        (width, height),
        "white"
    )

    # Center image
    x = (width - image.width) // 2
    y = (height - image.height) // 2

    canvas.paste(
        image,
        (x, y)
    )

    return canvas


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Lost & Found",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded"
)

def prepare_display_image(image_path, size=(450, 450)):
    image = Image.open(image_path).convert("RGB")

    # Crop and resize to exactly fit the box
    image = ImageOps.fit(
        image,
        size,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5)
    )

    return image
# ============================================================
# LOAD CLIP MODEL
# ============================================================

@st.cache_resource
def load_model():

    model = AutoModel.from_pretrained(
        MODEL_NAME
    )

    processor = AutoProcessor.from_pretrained(
        MODEL_NAME
    )

    model.eval()

    return model, processor


# ============================================================
# LOAD EMBEDDING DATABASE
# ============================================================

@st.cache_data
def load_database():

    if not os.path.exists(EMBEDDINGS_PATH):

        return []

    with open(
        EMBEDDINGS_PATH,
        "rb"
    ) as file:

        return pickle.load(file)


# ============================================================
# LOAD METADATA
# ============================================================

def load_metadata():

    if not os.path.exists(METADATA_PATH):

        return {}

    try:

        with open(
            METADATA_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return {}


# ============================================================
# SAVE METADATA
# ============================================================

def save_metadata(
    filename,
    description,
    location,
    date_found
):

    os.makedirs(
        REGISTERED_ITEMS_PATH,
        exist_ok=True
    )

    metadata = load_metadata()

    metadata[filename] = {
        "description": description,
        "location": location,
        "date_found": str(date_found)
    }

    with open(
        METADATA_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metadata,
            file,
            indent=4
        )


# ============================================================
# LOAD MODEL + DATABASE
# ============================================================

model, processor = load_model()

database = load_database()

metadata = load_metadata()


# ============================================================
# PROJECT STATISTICS
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "📦 Found Items",
        len(database)
    )

with col2:

    st.metric(
        "🏷️ Categories",
        len(set(
            item["category"]
            for item in database
        ))
    )

with col3:

    st.metric(
        "🧠 AI Model",
        "CLIP"
    )


# ============================================================
# IMAGE EMBEDDING
# ============================================================

def get_image_embedding(image):

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

    image_features = (
        image_features
        / image_features.norm(
            p=2,
            dim=-1,
            keepdim=True
        )
    )

    return image_features.squeeze()


# ============================================================
# TEXT EMBEDDING
# ============================================================

def get_text_embedding(text):

    inputs = processor(
        text=[text],
        return_tensors="pt",
        padding=True
    )

    with torch.no_grad():

        text_features = model.get_text_features(
            **inputs
        )

    if hasattr(
        text_features,
        "pooler_output"
    ):

        text_features = (
            text_features.pooler_output
        )

    text_features = (
        text_features
        / text_features.norm(
            p=2,
            dim=-1,
            keepdim=True
        )
    )

    return text_features.squeeze()


# ============================================================
# FIND MATCHES
# ============================================================

def find_matches(
    image,
    description="",
    top_k=5
):

    if not database:

        return []

    image_embedding = get_image_embedding(
        image
    )

    text_embedding = None

    if description.strip():

        text_embedding = get_text_embedding(
            description
        )

    results = []

    for item in database:

        stored_embedding = torch.tensor(
            item["embedding"],
            dtype=torch.float32
        )

        # ----------------------------------------------------
        # IMAGE SIMILARITY
        # ----------------------------------------------------

        image_similarity = torch.dot(
            image_embedding,
            stored_embedding
        ).item()

        # Keep numerical value safe
        image_similarity = max(
            min(image_similarity, 1.0),
            -1.0
        )

        # ----------------------------------------------------
        # TEXT SIMILARITY
        # ----------------------------------------------------

        text_similarity = None

        if text_embedding is not None:

            text_similarity = torch.dot(
                text_embedding,
                stored_embedding
            ).item()

            text_similarity = max(
                min(text_similarity, 1.0),
                -1.0
            )

            # ------------------------------------------------
            # MULTIMODAL SCORE
            # ------------------------------------------------

            final_score = (
                0.70 * image_similarity
                +
                0.30 * text_similarity
            )

        else:

            final_score = image_similarity

        final_score = max(
            min(final_score, 1.0),
            -1.0
        )

        results.append(
            {
                "filename": item["filename"],
                "category": item["category"],
                "image_path": item["image_path"],
                "image_similarity": image_similarity,
                "text_similarity": text_similarity,
                "final_score": final_score
            }
        )

    # Sort highest first

    # Sort by highest score
    results.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

# Remove duplicate images
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
# CATEGORY DETECTION
# ============================================================

def detect_category(description):

    text = description.lower()

    categories = {
        "backpack": [
            "backpack",
            "bag",
            "school bag",
            "college bag",
            "rucksack"
        ],

        "bottle": [
            "bottle",
            "water bottle",
            "flask"
        ],

        "phone": [
            "phone",
            "mobile",
            "smartphone",
            "iphone",
            "android"
        ],

        "wallet": [
            "wallet",
            "purse"
        ],

        "watch": [
            "watch",
            "smartwatch"
        ]
    }

    for category, keywords in categories.items():

        for keyword in keywords:

            if keyword in text:

                return category

    return "other"


# ============================================================
# HEADER
# ============================================================

st.title(
    "🔎 AI Lost & Found"
)

st.subheader(
    "Find your lost belongings using AI-powered visual matching"
)

st.write(
    "Upload a photo of your lost item and our AI "
    "will search through registered found items."
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "📦 Register Found Item"
)

st.sidebar.caption(
    "Register an item so other users can find it."
)


found_image = st.sidebar.file_uploader(
    "Upload found item image",
    type=[
        "jpg",
        "jpeg",
        "png"
    ],
    key="found_image"
)


found_description = st.sidebar.text_area(
    "Found item description",
    placeholder=(
        "Example: Black backpack with red logo"
    ),
    key="found_description"
)


found_location = st.sidebar.text_input(
    "Where was it found?",
    placeholder="Example: University Library",
    key="found_location"
)


found_date = st.sidebar.date_input(
    "Date found",
    key="found_date"
)


# ============================================================
# REGISTER FOUND ITEM
# ============================================================

if st.sidebar.button(
    "➕ Register Found Item",
    use_container_width=True
):

    if found_image is None:

        st.sidebar.error(
            "❌ Please upload an image."
        )

    elif not found_description.strip():

        st.sidebar.error(
            "❌ Please enter a description."
        )

    elif not found_location.strip():

        st.sidebar.error(
            "❌ Please enter where the item was found."
        )

    else:

        try:

            # ------------------------------------------------
            # Create directory
            # ------------------------------------------------

            os.makedirs(
                REGISTERED_ITEMS_PATH,
                exist_ok=True
            )

            # ------------------------------------------------
            # Create unique filename
            # ------------------------------------------------

            extension = os.path.splitext(
                found_image.name
            )[1].lower()

            unique_filename = (
                datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )
                +
                "_"
                +
                uuid.uuid4().hex[:6]
                +
                extension
            )

            save_path = os.path.join(
                REGISTERED_ITEMS_PATH,
                unique_filename
            )

            # ------------------------------------------------
            # Save image
            # ------------------------------------------------

            with open(
                save_path,
                "wb"
            ) as file:

                file.write(
                    found_image.getbuffer()
                )

            # ------------------------------------------------
            # Detect category
            # ------------------------------------------------

            category = detect_category(
                found_description
            )

            # ------------------------------------------------
            # Generate CLIP embedding
            # ------------------------------------------------

            with st.spinner(
                "🤖 AI is analyzing the found item..."
            ):

                add_item_to_database(
                    save_path,
                    category,
                    unique_filename
                )

            # ------------------------------------------------
            # Save metadata
            # ------------------------------------------------

            save_metadata(
                unique_filename,
                found_description,
                found_location,
                found_date
            )

            # ------------------------------------------------
            # Clear cached database
            # ------------------------------------------------

            st.cache_data.clear()

            # Reload database
            database = load_database()

            st.sidebar.success(
                "✅ Found item registered successfully!"
            )

            st.sidebar.info(
                f"Category detected: {category.title()}"
            )

        except Exception as e:

            st.sidebar.error(
                f"❌ Registration failed: {e}"
            )


# ============================================================
# DATABASE STATUS
# ============================================================

st.sidebar.divider()

st.sidebar.metric(
    "🗃️ Registered AI Images",
    len(database)
)

st.sidebar.caption(
    "Powered by CLIP Computer Vision"
)


# ============================================================
# LOST ITEM SEARCH
# ============================================================

st.header(
    "🔍 Search for Your Lost Item"
)


uploaded_file = st.file_uploader(
    "📷 Upload an image of your lost item",
    type=[
        "jpg",
        "jpeg",
        "png"
    ],
    key="lost_image"
)


description = st.text_area(
    "📝 Describe your lost item",
    placeholder=(
        "Example: Black backpack with red logo"
    ),
    key="lost_description"
)


location = st.text_input(
    "📍 Where did you lose it?",
    placeholder="Example: University Library",
    key="lost_location"
)


date = st.date_input(
    "📅 Date you lost it",
    key="lost_date"
)


# ============================================================
# SEARCH
# ============================================================

if uploaded_file is not None:

    image = Image.open(
        uploaded_file
    ).convert("RGB")

    st.subheader(
        "📦 Uploaded Item"
    )

    col1, col2 = st.columns(
        [1, 2]
    )

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    with col1:

        st.image(
            image,
            caption="Your lost item",
            width=350
        )

    # --------------------------------------------------------
    # INFORMATION
    # --------------------------------------------------------

    with col2:

        st.write(
            "### 📋 Item Information"
        )

        if description.strip():

            st.write(
                f"**Description:** {description}"
            )

        if location.strip():

            st.write(
                f"**Location:** {location}"
            )

        st.write(
            f"**Date lost:** {date}"
        )

        if description.strip():

            detected_category = detect_category(
                description
            )

            st.info(
                f"🤖 AI detected category: "
                f"**{detected_category.title()}**"
            )

    st.divider()

    # ========================================================
    # SEARCH BUTTON
    # ========================================================

    if st.button(
        "🔍 Find My Item",
        type="primary",
        use_container_width=True
    ):

        if not database:

            st.error(
                "❌ No found items are registered yet."
            )

        else:

            with st.spinner(
                "🤖 AI is searching for matching items..."
            ):

                matches = find_matches(
                    image,
                    description=description,
                    top_k=5
                )

            st.success(
                "✅ AI search completed!"
            )

            st.subheader(
                "🏆 Top Matching Found Items"
            )

            # =================================================
            # DISPLAY RESULTS
            # =================================================

            for rank, match in enumerate(
                matches,
                start=1
            ):

                score = (
                    match["final_score"] * 100
                )

                image_score = (
                    match["image_similarity"] * 100
                )

                text_score = None

                if (
                    match["text_similarity"]
                    is not None
                ):

                    text_score = (
                        match["text_similarity"]
                        * 100
                    )

                col1, col2 = st.columns(
                    [1, 2]
                )

                # ------------------------------------------------
                # MATCH IMAGE
                # ------------------------------------------------

                with col1:

                    # Resolve image path safely
                    image_path = match["image_path"]

                    if not os.path.isabs(image_path):

                        image_path = os.path.abspath(
                            image_path
                        )

                    if os.path.exists(image_path):

                        display_image = prepare_display_image(
                        image_path,
                        size = (500,400)
                    )

                        st.image(
                        display_image,
                        width=500
                        )

                    else:

                        st.warning(
                        "⚠️ Image unavailable"
                    )
                # ------------------------------------------------
                # MATCH INFORMATION
                # ------------------------------------------------

                with col2:

                    st.markdown(
                        f"### #{rank} — "
                        f"{match['category'].title()}"
                    )

                    st.write(
                        f"**File:** "
                        f"{match['filename']}"
                    )

                    # ------------------------------------------------
                    # SCORE
                    # ------------------------------------------------

                    st.metric(
                        "🏆 Overall Match Score",
                        f"{score:.2f}%"
                    )

                    st.progress(
                        max(
                            min(
                                score / 100,
                                1.0
                            ),
                            0.0
                        )
                    )

                    # ------------------------------------------------
                    # IMAGE SCORE
                    # ------------------------------------------------

                    st.write(
                        f"📷 **Image similarity:** "
                        f"{image_score:.2f}%"
                    )

                    # ------------------------------------------------
                    # TEXT SCORE
                    # ------------------------------------------------

                    if text_score is not None:

                        st.write(
                            f"📝 **Description similarity:** "
                            f"{text_score:.2f}%"
                        )

                    # ------------------------------------------------
                    # MATCH CONFIDENCE
                    # ------------------------------------------------

                    if score >= 80:
                        st.success(
                            "🟢 Strong Match — This item is highly similar."
                        )

                    elif score >= 70:
                        st.warning(
                             "🟡 Good Candidate — Please verify the item."
                            )

                    elif score >= 60:
                        st.warning(
                            "🟠 Possible Match — Additional verification recommended."
                        )

                    else:
                        st.info(
                            "🔴 Low Match — This item may not be the same."
                        )

                    # ------------------------------------------------
                    # REGISTERED ITEM DETAILS
                    # ------------------------------------------------

                    item_metadata = metadata.get(
                        match["filename"]
                    )

                    if item_metadata:

                        st.write(
                            "---"
                        )

                        st.write(
                            "📍 **Found at:** "
                            + item_metadata.get(
                                "location",
                                "Unknown"
                            )
                        )

                        st.write(
                            "📅 **Date found:** "
                            + item_metadata.get(
                                "date_found",
                                "Unknown"
                            )
                        )

                        st.write(
                            "📝 **Found item description:** "
                            + item_metadata.get(
                                "description",
                                "Not available"
                            )
                        )

                st.divider()


# ============================================================
# HOW IT WORKS
# ============================================================

with st.expander(
    "🤖 How does the AI work?"
):

    st.write(
        """
        **1️⃣ Upload**

        Upload a photo of your lost item.

        **2️⃣ CLIP Vision**

        The CLIP model converts the image into
        a numerical embedding representing its
        visual characteristics.

        **3️⃣ Text Understanding**

        Your description is also converted into
        a CLIP text embedding.

        **4️⃣ Multimodal Matching**

        The system combines image and text
        similarity to rank registered found items.

        **5️⃣ Top Matches**

        The five most similar found items are
        displayed with similarity scores.
        """
    )




st.markdown("---")

st.subheader("🤖 How AI Matching Works")

st.markdown("""
### 1️⃣ Image Understanding
The uploaded image is processed using **OpenAI CLIP**.

### 2️⃣ Feature Extraction
CLIP converts the image into a numerical **embedding vector**.

### 3️⃣ Similarity Search
The AI compares the uploaded image embedding with embeddings
of registered found items using **cosine similarity**.

### 4️⃣ Ranking
The system ranks the found items from highest to lowest similarity.

### 5️⃣ Smart Match
The highest-scoring items are presented as potential matches.
""")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🔎 AI Lost & Found • Powered by CLIP Computer Vision"
)

st.caption(
    "AI-assisted matching • Image + Text Similarity"
)