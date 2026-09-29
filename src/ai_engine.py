import os
import io
import torch
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
from typing import List, Dict, Any, Optional, Union
from transformers import AutoProcessor, AutoModel

MODEL_NAME = "openai/clip-vit-base-patch32"

class AIEngine:
    """
    Multimodal AI matching engine using CLIP ViT-B/32.
    Provides image & text feature extraction, hybrid similarity computation,
    preprocessing, and automated reverse-matching for Lost & Found verification.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        print(f"Loading multimodal model: {MODEL_NAME}...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = AutoModel.from_pretrained(MODEL_NAME).to(self.device)
        self.processor = AutoProcessor.from_pretrained(MODEL_NAME)
        self.model.eval()
        self._initialized = True
        print("Multimodal model loaded successfully.")

    def preprocess_image(self, image_input: Union[str, bytes, Image.Image]) -> Image.Image:
        """
        Standardize and enhance images:
        - Correct EXIF orientation
        - Ensure RGB mode
        - Slight contrast enhancement for clearer edge features
        - Letterbox / padding to square aspect ratio
        """
        if isinstance(image_input, str):
            image = Image.open(image_input)
        elif isinstance(image_input, bytes):
            image = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, Image.Image):
            image = image_input.copy()
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

        # 1. Correct orientation
        image = ImageOps.exif_transpose(image)

        # 2. Convert to RGB
        if image.mode != "RGB":
            image = image.convert("RGB")

        # 3. Contrast & sharpness normalization
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.05)

        return image

    def extract_image_embedding(self, image_input: Union[str, bytes, Image.Image]) -> np.ndarray:
        """Extract a 512-dim normalized feature vector from an image."""
        image = self.preprocess_image(image_input)
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            vision_outputs = self.model.vision_model(pixel_values=inputs["pixel_values"])
            image_features = vision_outputs.pooler_output
            image_features = self.model.visual_projection(image_features)

            # L2 normalize
            image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)

        return image_features.squeeze().cpu().numpy()

    def extract_text_embedding(self, text: str) -> np.ndarray:
        """Extract a 512-dim normalized feature vector from text query."""
        if not text or not text.strip():
            return None

        inputs = self.processor(text=[text.strip()], return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            text_features = self.model.get_text_features(**inputs)
            if hasattr(text_features, "pooler_output"):
                text_features = text_features.pooler_output
            text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)

        return text_features.squeeze().cpu().numpy()

    def search_matches(
        self,
        candidate_items: List[Dict[str, Any]],
        query_image: Optional[Union[str, bytes, Image.Image]] = None,
        query_text: Optional[str] = None,
        selected_category: Optional[str] = None,
        selected_location: Optional[str] = None,
        min_confidence: float = 40.0,
        top_k: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Multi-criteria hybrid search combining:
        - Dense visual similarity
        - Semantic text similarity
        - Categorical alignment
        - Location proximity
        """
        if not candidate_items:
            return []

        query_img_emb = self.extract_image_embedding(query_image) if query_image else None
        query_txt_emb = self.extract_text_embedding(query_text) if query_text and query_text.strip() else None

        if query_img_emb is None and query_txt_emb is None:
            return []

        results = []

        for item in candidate_items:
            stored_emb = item.get("embedding")
            if stored_emb is None:
                continue

            stored_vec = np.array(stored_emb, dtype=np.float32)
            # Ensure normalized
            norm = np.linalg.norm(stored_vec)
            if norm > 0:
                stored_vec = stored_vec / norm

            visual_sim = 0.0
            text_sim = 0.0
            reasons = []

            # 1. Visual Cosine Similarity
            if query_img_emb is not None:
                visual_sim = float(np.dot(query_img_emb, stored_vec))
                visual_sim = max(0.0, min(1.0, visual_sim))
                if visual_sim >= 0.70:
                    reasons.append(f"{int(visual_sim * 100)}% Visual Match")
                elif visual_sim >= 0.50:
                    reasons.append("Visual Pattern Similarity")

            # 2. Text Semantic Similarity
            if query_txt_emb is not None:
                text_sim = float(np.dot(query_txt_emb, stored_vec))
                text_sim = max(0.0, min(1.0, text_sim))
                if text_sim >= 0.25:
                    reasons.append("Semantic Description Match")

            # 3. Categorical Match
            category_match = False
            item_cat = str(item.get("category", "")).lower().strip()
            if selected_category and selected_category.lower() not in ["all", ""]:
                sel_cat = selected_category.lower().strip()
                if item_cat == sel_cat:
                    category_match = True
                    reasons.append(f"Category Match: {item.get('category', '').title()}")
                else:
                    # Penalty or skip if strict category mismatch
                    pass

            # 4. Location Proximity
            location_match = False
            item_loc = str(item.get("location", "")).lower()
            if selected_location and selected_location.lower() not in ["all", ""]:
                sel_loc = selected_location.lower().strip()
                if sel_loc in item_loc or item_loc in sel_loc:
                    location_match = True
                    reasons.append(f"Location Match: {item.get('location', '')}")

            # 5. Hybrid Confidence Calculation
            # In CLIP, cross-modal (text-image) cosine similarities typically range 0.18 - 0.35
            # whereas unimodal (image-image) cosine similarities range 0.50 - 0.95.
            # We calibrate text_sim so that text-to-image and multimodal scoring are harmonious.
            calibrated_text_sim = min(1.0, text_sim * 2.6) if text_sim > 0 else 0.0

            if query_img_emb is not None and query_txt_emb is not None:
                base_score = 0.70 * visual_sim + 0.30 * calibrated_text_sim
            elif query_img_emb is not None:
                base_score = visual_sim
            else:
                base_score = calibrated_text_sim

            # Apply bonuses
            boost = 0.0
            if category_match:
                boost += 0.08
            if location_match:
                boost += 0.05

            final_score = min(1.0, base_score + boost)
            confidence_pct = round(final_score * 100, 1)

            if confidence_pct < min_confidence:
                continue

            # Confidence tier
            if confidence_pct >= 85:
                tier = "Excellent Match"
                badge_class = "match-high"
            elif confidence_pct >= 70:
                tier = "High Match"
                badge_class = "match-medium"
            else:
                tier = "Potential Match"
                badge_class = "match-low"

            results.append({
                "item": item,
                "confidence": confidence_pct,
                "tier": tier,
                "badge_class": badge_class,
                "visual_score": round(visual_sim * 100, 1),
                "text_score": round(text_sim * 100, 1) if query_txt_emb is not None else None,
                "reasons": reasons if reasons else ["General Resemblance"]
            })

        # Sort by confidence descending
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results[:top_k]

    def check_reverse_match_for_lost(
        self,
        lost_report: Dict[str, Any],
        candidate_found_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Check if an incoming lost report matches any existing found items in custody.
        """
        return self.search_matches(
            candidate_items=candidate_found_items,
            query_image=lost_report.get("image_path") if lost_report.get("image_path") and os.path.exists(lost_report["image_path"]) else None,
            query_text=lost_report.get("description", "") or lost_report.get("item_name", ""),
            selected_category=lost_report.get("category"),
            selected_location=lost_report.get("location_lost"),
            min_confidence=50.0,
            top_k=3
        )


# Global singleton engine instance
ai_engine = AIEngine()
