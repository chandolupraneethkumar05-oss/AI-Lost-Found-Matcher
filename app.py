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


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Lost & Found",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CATEGORY SYSTEM
# ============================================================

DEFAULT_CATEGORIES = [
    "backpack",
    "bottle",
    "phone",
    "wallet",
    "watch",
    "laptop",
    "other"
]


def get_categories():

    categories = set(DEFAULT_CATEGORIES)

    for item in database:

        category = item.get("category")

        if category:
            categories.add(category.lower())

    return sorted(categories)


def category_selector(label, key_prefix):

    categories = get_categories()

    display_categories = [
        category.title()
        for category in categories
        if category != "other"
    ]

    display_categories.append("Other / Custom")

    selected = st.selectbox(
        label,
        display_categories,
        key=f"{key_prefix}_category"
    )

    if selected == "Other / Custom":

        custom_category = st.text_input(
            "Enter your category",
            placeholder="Example: Earbuds, ID Card, Calculator...",
            key=f"{key_prefix}_custom"
        )

        if custom_category.strip():

            return custom_category.strip().lower()

        return "other"

    return selected.lower()


# ============================================================
# IMAGE DISPLAY
# ============================================================

def prepare_display_image(
    image_path,
    size=(320, 260)
):

    image = Image.open(
        image_path
    ).convert("RGB")

    image = ImageOps.contain(
        image,
        size,
        method=Image.Resampling.LANCZOS
    )

    canvas = Image.new(
        "RGB",
        size,
        "white"
    )

    x = (
        size[0] - image.width
    ) // 2

    y = (
        size[1] - image.height
    ) // 2

    canvas.paste(
        image,
        (x, y)
    )

    return canvas


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
# LOAD DATABASE
# ============================================================

@st.cache_data
def load_database():

    if not os.path.exists(
        EMBEDDINGS_PATH
    ):

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

    if not os.path.exists(
        METADATA_PATH
    ):

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
    date_found,
    category
):

    os.makedirs(
        REGISTERED_ITEMS_PATH,
        exist_ok=True
    )

    metadata = load_metadata()

    metadata[filename] = {

        "description": description,

        "location": location,

        "date_found": str(date_found),

        "category": category
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
# IMAGE EMBEDDING
# ============================================================

def get_image_embedding(image):

    inputs = processor(
        images=image,
        return_tensors="pt"
    )

    with torch.no_grad():

        vision_outputs = model.vision_model(
            pixel_values=inputs[
                "pixel_values"
            ]
        )

        image_features = (
            vision_outputs.pooler_output
        )

        image_features = (
            model.visual_projection(
                image_features
            )
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
    selected_category="all",
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

        image_similarity = max(
            min(
                image_similarity,
                1.0
            ),
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
                min(
                    text_similarity,
                    1.0
                ),
                -1.0
            )

        # ----------------------------------------------------
        # MULTIMODAL SCORE
        # ----------------------------------------------------

        if text_similarity is not None:

            final_score = (
                0.70 * image_similarity
                +
                0.30 * text_similarity
            )

        else:

            final_score = image_similarity

        # ----------------------------------------------------
        # CATEGORY BONUS
        # ----------------------------------------------------

        item_category = (
            item.get(
                "category",
                "other"
            ).lower()
        )

        category_match = False

        if (
            selected_category != "all"
            and selected_category != "other"
        ):

            if item_category == selected_category:

                category_match = True

                # Small category bonus
                final_score += 0.05

        elif selected_category == "other":

            if item_category == "other":

                category_match = True

                final_score += 0.05

        # Keep score valid
        final_score = max(
            min(
                final_score,
                1.0
            ),
            -1.0
        )

        results.append(
            {
                "filename": item["filename"],

                "category": item_category,

                "image_path": item["image_path"],

                "image_similarity":
                    image_similarity,

                "text_similarity":
                    text_similarity,

                "final_score":
                    final_score,

                "category_match":
                    category_match
            }
        )

    # ========================================================
    # SORT
    # ========================================================

    results.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    unique_results = []

    seen_files = set()

    for result in results:

        filename = result["filename"]

        if filename in seen_files:

            continue

        seen_files.add(filename)

        unique_results.append(
            result
        )

        if len(unique_results) >= top_k:

            break

    return unique_results


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
# PROJECT STATISTICS
# ============================================================

stat1, stat2, stat3 = st.columns(3)

with stat1:

    st.metric(
        "📦 Registered Items",
        len(database)
    )

with stat2:

    st.metric(
        "🏷️ Categories",
        len(
            set(
                item.get(
                    "category",
                    "other"
                )
                for item in database
            )
        )
    )

with stat3:

    st.metric(
        "🧠 AI Model",
        "CLIP"
    )


# ============================================================
# SIDEBAR - REGISTER FOUND ITEM
# ============================================================

st.sidebar.title(
    "📦 Register Found Item"
)

st.sidebar.caption(
    "Add a found item so other users can search for it."
)


found_image = st.sidebar.file_uploader(
    "Upload found item image",
    type=[
        "jpg",
        "jpeg",
        "png",
        "webp"
    ],
    key="found_image"
)


found_category = category_selector(
    "🏷️ Select item category",
    "found"
)


found_description = st.sidebar.text_area(
    "Found item description",
    placeholder=(
        "Example: Black backpack with red logo"
    ),
    key="found_description"
)


found_location = st.sidebar.text_input(
    "📍 Where was it found?",
    placeholder="Example: University Library",
    key="found_location"
)


found_date = st.sidebar.date_input(
    "📅 Date found",
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

    elif found_category == "other":

        st.sidebar.error(
            "❌ Please enter a custom category."
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
            # CREATE DIRECTORY
            # ------------------------------------------------

            os.makedirs(
                REGISTERED_ITEMS_PATH,
                exist_ok=True
            )

            # ------------------------------------------------
            # UNIQUE FILENAME
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
            # SAVE IMAGE
            # ------------------------------------------------

            with open(
                save_path,
                "wb"
            ) as file:

                file.write(
                    found_image.getbuffer()
                )

            # ------------------------------------------------
            # GENERATE EMBEDDING
            # ------------------------------------------------

            with st.spinner(
                "🤖 AI is analyzing the found item..."
            ):

                add_item_to_database(
                    save_path,
                    found_category,
                    unique_filename
                )

            # ------------------------------------------------
            # SAVE METADATA
            # ------------------------------------------------

            save_metadata(
                unique_filename,
                found_description,
                found_location,
                found_date,
                found_category
            )

            # ------------------------------------------------
            # CLEAR CACHE
            # ------------------------------------------------

            st.cache_data.clear()

            st.sidebar.success(
                "✅ Found item registered successfully!"
            )

            st.sidebar.info(
                f"🏷️ Category: "
                f"{found_category.title()}"
            )

            # Reload
            database = load_database()

        except Exception as e:

            st.sidebar.error(
                f"❌ Registration failed: {e}"
            )


# ============================================================
# SIDEBAR STATUS
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
        "png",
        "webp"
    ],
    key="lost_image"
)


lost_category = category_selector(
    "🏷️ Select lost item category",
    "lost"
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
    # UPLOADED IMAGE
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

        st.markdown(
            "### 📋 Item Information"
        )

        st.write(
            f"**Description:** "
            f"{description if description.strip() else 'Not provided'}"
        )

        st.write(
            f"**Location:** "
            f"{location if location.strip() else 'Not provided'}"
        )

        st.write(
            f"**Date lost:** {date}"
        )

        st.info(
            f"🏷️ Selected category: "
            f"**{lost_category.title()}**"
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
                    selected_category=lost_category,
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

            if not matches:

                st.warning(
                    "No matching items found."
                )

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
                # RESULT IMAGE
                # ------------------------------------------------

                with col1:

                    image_path = match[
                        "image_path"
                    ]

                    if not os.path.isabs(
                        image_path
                    ):

                        image_path = os.path.abspath(
                            image_path
                        )

                    if os.path.exists(
                        image_path
                    ):

                        try:

                            display_image = (
                                prepare_display_image(
                                    image_path,
                                    size=(320, 260)
                                )
                            )

                            st.image(
                                display_image,
                                width=320
                            )

                        except Exception:

                            st.warning(
                                "⚠️ Unable to display image."
                            )

                    else:

                        st.warning(
                            "⚠️ Image unavailable"
                        )


                # ------------------------------------------------
                # RESULT INFORMATION
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

                    # Category match indicator

                    if match[
                        "category_match"
                    ]:

                        st.success(
                            "🏷️ Category matched"
                        )

                    else:

                        st.info(
                            "🏷️ Visual/text candidate"
                        )

                    # Overall score

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

                    # Image score

                    st.write(
                        f"📷 **Image similarity:** "
                        f"{image_score:.2f}%"
                    )

                    # Text score

                    if text_score is not None:

                        st.write(
                            f"📝 **Description similarity:** "
                            f"{text_score:.2f}%"
                        )

                    # Confidence

                    if score >= 80:

                        st.success(
                            "🟢 Strong Match — "
                            "Highly similar item."
                        )

                    elif score >= 70:

                        st.warning(
                            "🟡 Good Candidate — "
                            "Please verify the item."
                        )

                    elif score >= 60:

                        st.warning(
                            "🟠 Possible Match — "
                            "Additional verification recommended."
                        )

                    else:

                        st.info(
                            "🔴 Low Match — "
                            "This may not be the same item."
                        )

                    # ------------------------------------------------
                    # FOUND ITEM DETAILS
                    # ------------------------------------------------

                    item_metadata = metadata.get(
                        match["filename"]
                    )

                    if item_metadata:

                        st.write("---")

                        st.write(
                            "📍 **Found at:** "
                            +
                            item_metadata.get(
                                "location",
                                "Unknown"
                            )
                        )

                        st.write(
                            "📅 **Date found:** "
                            +
                            item_metadata.get(
                                "date_found",
                                "Unknown"
                            )
                        )

                        st.write(
                            "📝 **Found description:** "
                            +
                            item_metadata.get(
                                "description",
                                "Not available"
                            )
                        )

                        st.write(
                            "🏷️ **Category:** "
                            +
                            item_metadata.get(
                                "category",
                                match["category"]
                            ).title()
                        )

                st.divider()


# ============================================================
# HOW IT WORKS
# ============================================================

with st.expander(
    "🤖 How does the AI work?"
):

    st.markdown(
        """
        ### 1️⃣ Upload

        Upload a photo of your lost item.

        ### 2️⃣ Select Category

        Choose the item category or enter
        your own custom category.

        ### 3️⃣ CLIP Vision

        CLIP converts the image into a
        numerical embedding representing
        its visual characteristics.

        ### 4️⃣ Text Understanding

        Your description is converted into
        a CLIP text embedding.

        ### 5️⃣ Multimodal Matching

        The system combines image similarity,
        description similarity and category
        information.

        ### 6️⃣ Ranking

        The most relevant found items are
        ranked and displayed with scores.
        """
    )


# ============================================================
# PROFESSIONAL PROJECT INFORMATION
# ============================================================

st.divider()

st.subheader(
    "🚀 AI Matching Technology"
)

info1, info2, info3 = st.columns(3)

with info1:

    st.info(
        "🖼️ **Computer Vision**\n\n"
        "CLIP understands visual features "
        "from uploaded item images."
    )

with info2:

    st.info(
        "📝 **Multimodal AI**\n\n"
        "Image and text descriptions are "
        "combined for better matching."
    )

with info3:

    st.info(
        "🏷️ **Dynamic Categories**\n\n"
        "Users can choose existing categories "
        "or create completely new ones."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🔎 AI Lost & Found • Powered by CLIP Computer Vision"
)

st.caption(
    "AI-assisted matching • Image + Text Similarity • Dynamic Categories"
)