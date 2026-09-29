import os
import io
import uuid
import shutil
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image

from src.database import db
from src.ai_engine import ai_engine

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "registered_items")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app = FastAPI(
    title="FindSphere AI - Lost & Found Recovery Network",
    description="Official institutional lost and found intelligent recovery system with multimodal visual matching.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve data directory for item images
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")


# ==========================================================
# PYDANTIC SCHEMAS
# ==========================================================

class LostReportRequest(BaseModel):
    item_name: str
    description: str
    category: str
    location_lost: str
    date_lost: Optional[str] = None
    contact_name: str
    contact_email: str
    contact_phone: str

class ClaimRequest(BaseModel):
    item_id: str
    claimant_name: str
    claimant_email: str
    claimant_phone: str
    identifying_details: str
    proof_description: Optional[str] = ""

class ClaimVerifyRequest(BaseModel):
    decision: str  # "Approved" or "Rejected"
    notes: Optional[str] = ""


# ==========================================================
# API ENDPOINTS
# ==========================================================

@app.get("/api/stats")
def get_stats():
    """Return live system operational metrics."""
    return db.get_statistics()


@app.get("/api/items")
def get_items(category: Optional[str] = None, location: Optional[str] = None, status: Optional[str] = None, search: Optional[str] = None):
    """Return all catalog items with flexible filtering."""
    items = db.get_all_found_items(category=category, status=status)
    if location and location.lower() != "all":
        items = [it for it in items if location.lower() in str(it.get("location", "")).lower()]
    if search and search.strip():
        q = search.lower().strip()
        items = [
            it for it in items
            if q in it.get("title", "").lower()
            or q in it.get("description", "").lower()
            or q in it.get("location", "").lower()
            or q in it.get("brand", "").lower()
            or q in it.get("color", "").lower()
        ]
    return items


@app.get("/api/items/{item_id}")
def get_item_detail(item_id: str):
    """Retrieve detailed information for a single item."""
    item = db.get_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    # Exclude secret verification answer for public safety
    safe_item = {k: v for k, v in item.items() if k not in ["embedding", "secret_verification_answer"]}
    return safe_item


@app.post("/api/match")
async def match_item(
    image: Optional[UploadFile] = File(None),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form("all"),
    location: Optional[str] = Form("all"),
    min_confidence: Optional[float] = Form(40.0),
    top_k: Optional[int] = Form(8)
):
    """
    Multimodal visual and semantic similarity search.
    Compares uploaded image / description against registered custody items.
    """
    image_bytes = None
    if image:
        image_bytes = await image.read()

    if not image_bytes and not (description and description.strip()):
        raise HTTPException(status_code=400, detail="Please provide either an image or a description to search.")

    candidates = db.get_all_found_items()
    # Filter candidates by category if selected
    if category and category.lower() != "all":
        candidates = [it for it in candidates if it.get("category", "").lower() == category.lower()]

    matches = ai_engine.search_matches(
        candidate_items=candidates,
        query_image=image_bytes,
        query_text=description,
        selected_category=category,
        selected_location=location,
        min_confidence=min_confidence or 40.0,
        top_k=top_k or 8
    )

    # Sanitize embeddings from output
    clean_results = []
    for m in matches:
        item = m["item"]
        safe_item = {k: v for k, v in item.items() if k not in ["embedding", "secret_verification_answer"]}
        clean_results.append({
            "confidence": m["confidence"],
            "tier": m["tier"],
            "badge_class": m["badge_class"],
            "visual_score": m["visual_score"],
            "text_score": m["text_score"],
            "reasons": m["reasons"],
            "item": safe_item
        })

    return {
        "status": "success",
        "query_has_image": bool(image_bytes),
        "query_has_text": bool(description and description.strip()),
        "total_matches": len(clean_results),
        "matches": clean_results
    }


@app.post("/api/report-found")
async def report_found_item(
    title: str = Form(...),
    category: str = Form(...),
    location: str = Form(...),
    date_found: Optional[str] = Form(None),
    brand: Optional[str] = Form(""),
    color: Optional[str] = Form(""),
    custody_location: Optional[str] = Form("Central Custody Office"),
    verification_prompt: Optional[str] = Form("Describe any unique identifying marks, scratches, or interior contents."),
    secret_answer: Optional[str] = Form(""),
    image: UploadFile = File(...)
):
    """
    Register a newly found item into safe custody.
    Generates AI vector embedding and automatically cross-checks against pending lost reports.
    """
    image_bytes = await image.read()
    ext = os.path.splitext(image.filename)[1].lower() or ".jpg"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_name = f"{timestamp}_{uuid.uuid4().hex[:6]}{ext}"
    saved_path = os.path.join(UPLOADS_DIR, unique_name)

    with open(saved_path, "wb") as f:
        f.write(image_bytes)

    rel_image_path = os.path.relpath(saved_path, BASE_DIR).replace("\\", "/")

    # Extract embedding
    embedding = ai_engine.extract_image_embedding(image_bytes)

    item_record = {
        "id": f"FND-{datetime.now().strftime('%y%m')}-{uuid.uuid4().hex[:4].upper()}",
        "title": title.strip(),
        "description": f"{title}. Brand: {brand}. Color: {color}. Found at {location}.",
        "category": category.strip().lower(),
        "brand": brand.strip(),
        "color": color.strip(),
        "location": location.strip(),
        "date_found": date_found or datetime.now().strftime("%Y-%m-%d"),
        "filename": unique_name,
        "image_path": rel_image_path,
        "status": "Available",
        "custody_location": custody_location,
        "verification_prompt": verification_prompt,
        "secret_verification_answer": secret_answer,
        "embedding": embedding.tolist()
    }

    created = db.add_found_item(item_record)

    # Automated reverse-match check against open lost reports
    reverse_matches = []
    for report in db.get_all_lost_reports():
        report_cat = report.get("category", "").lower()
        if report_cat == "all" or report_cat == category.strip().lower():
            # Check text similarity
            text_emb = ai_engine.extract_text_embedding(report.get("description", "") or report.get("item_name", ""))
            if text_emb is not None:
                sim = float(embedding @ text_emb)
                if sim >= 0.40:
                    reverse_matches.append({
                        "lost_report_id": report.get("id"),
                        "contact_name": report.get("contact_name"),
                        "contact_email": report.get("contact_email"),
                        "item_name": report.get("item_name"),
                        "similarity_percent": round(sim * 100, 1)
                    })

    return {
        "status": "success",
        "message": "Item registered successfully in custody catalog.",
        "item": {k: v for k, v in created.items() if k != "embedding"},
        "reverse_matches_found": len(reverse_matches),
        "potential_owners_alerted": reverse_matches
    }


@app.post("/api/report-lost")
async def report_lost_item(report: LostReportRequest):
    """
    File an inquiry for a lost item.
    Immediately searches the custody database for potential matches.
    """
    created_report = db.add_lost_report(report.dict())

    # Check for immediate matches in custody
    found_candidates = db.get_all_found_items()
    matches = ai_engine.search_matches(
        candidate_items=found_candidates,
        query_text=f"{report.item_name}. {report.description}",
        selected_category=report.category,
        selected_location=report.location_lost,
        min_confidence=45.0,
        top_k=4
    )

    clean_matches = []
    for m in matches:
        safe_item = {k: v for k, v in m["item"].items() if k not in ["embedding", "secret_verification_answer"]}
        clean_matches.append({
            "confidence": m["confidence"],
            "tier": m["tier"],
            "reasons": m["reasons"],
            "item": safe_item
        })

    return {
        "status": "success",
        "message": "Lost item report registered. Our continuous matching engine will monitor incoming intake.",
        "report_id": created_report.get("id"),
        "immediate_matches": clean_matches
    }


@app.post("/api/claim")
async def submit_ownership_claim(claim: ClaimRequest):
    """
    Submit a secure ownership claim with anti-theft verification answers.
    """
    target_item = db.get_item_by_id(claim.item_id)
    if not target_item:
        raise HTTPException(status_code=404, detail="Item not found")

    created_claim = db.submit_claim(claim.dict())

    return {
        "status": "success",
        "message": "Ownership claim filed successfully. Campus custody officers will verify your details.",
        "claim_id": created_claim.get("claim_id"),
        "item_title": target_item.get("title"),
        "custody_location": target_item.get("custody_location")
    }


@app.get("/api/claims")
def get_claims():
    """Retrieve all claims for the custody verification desk."""
    all_claims = db.get_all_claims()
    # Enrich claims with item title and image
    enriched = []
    for c in all_claims:
        item = db.get_item_by_id(c.get("item_id", ""))
        c_copy = dict(c)
        c_copy["item_title"] = item.get("title", "Unknown Item") if item else "Unknown Item"
        c_copy["item_image"] = item.get("image_path", "") if item else ""
        c_copy["item_category"] = item.get("category", "") if item else ""
        c_copy["custody_location"] = item.get("custody_location", "") if item else ""
        enriched.append(c_copy)
    return enriched


@app.post("/api/claims/{claim_id}/verify")
def verify_claim(claim_id: str, req: ClaimVerifyRequest):
    """Approve or reject a claim from the custody desk."""
    success = db.resolve_claim(claim_id, decision=req.decision, notes=req.notes or "")
    if not success:
        raise HTTPException(status_code=404, detail="Claim record not found")
    return {
        "status": "success",
        "message": f"Claim {claim_id} marked as {req.decision}."
    }


# ==========================================================
# STATIC ASSETS & SINGLE PAGE APPLICATION
# ==========================================================

@app.get("/")
def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": "FindSphere AI API active. static/index.html is being prepared."})

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    print("\nStarting FindSphere AI Lost & Found Recovery Server...")
    print("Web Portal: http://localhost:8000")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
