import os
import io
import uuid
from datetime import datetime
from PIL import Image
import streamlit as st

from src.database import db
from src.ai_engine import ai_engine

# ============================================================
# PAGE CONFIGURATION & WEBLIUM DESIGN SYSTEM
# ============================================================
st.set_page_config(
    page_title="FindSphere — Campus & Transit Lost & Found Recovery Network",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Weblium-Inspired CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #0F172A;
    }
    
    /* Classic Top Header */
    .app-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: #FFFFFF;
        padding: 32px 36px;
        border-radius: 14px;
        margin-bottom: 28px;
        box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.15);
    }
    .app-header h1 {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin-bottom: 8px;
        color: #FFFFFF !important;
    }
    .app-header p {
        font-size: 1.05rem;
        color: #94A3B8;
        max-width: 800px;
        line-height: 1.5;
        margin: 0;
    }
    .badge-pill {
        display: inline-block;
        background-color: rgba(37, 99, 235, 0.2);
        color: #60A5FA;
        border: 1px solid rgba(96, 165, 250, 0.3);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 12px;
    }
    
    /* Metrics Row */
    .metric-container {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: #0F172A;
    }
    .metric-label {
        font-size: 0.8125rem;
        color: #64748B;
        font-weight: 600;
    }
    
    /* Item Cards */
    .item-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.04);
        transition: transform 0.2s ease;
    }
    .item-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 8px 16px -2px rgba(15, 23, 42, 0.08);
    }
    .score-badge {
        font-size: 0.8125rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 9999px;
        display: inline-block;
    }
    .score-high { background-color: #DCFCE7; color: #15803D; }
    .score-medium { background-color: #DBEAFE; color: #1D4ED8; }
    .score-low { background-color: #F1F5F9; color: #475569; }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        font-size: 0.95rem;
        color: #475569;
        border-radius: 6px;
        padding: 10px 18px;
    }
    .stTabs [aria-selected="true"] {
        color: #2563EB !important;
        background-color: #EFF6FF !important;
    }
    
    /* Buttons */
    div.stButton > button {
        background-color: #2563EB;
        color: #FFFFFF;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        background-color: #1D4ED8;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
    }
</style>
""", unsafe_allow_html=True)

# Header Banner
st.markdown("""
<div class="app-header">
    <span class="badge-pill">● Official Custody Protocol • Section 12-B</span>
    <h1>FindSphere Recovery Network</h1>
    <p>Intelligent community and campus lost & found management system. Utilizing OpenAI CLIP multimodal embeddings to visually cross-match and reunite belongings with verified owners.</p>
</div>
""", unsafe_allow_html=True)

# Metrics Ribbon
stats = db.get_statistics()
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="metric-container"><div class="metric-value">{stats['total_found']}</div><div class="metric-label">Items in Vault Custody</div></div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="metric-container"><div class="metric-value">{stats['success_rate_percent']}%</div><div class="metric-label">Verified Reconnection Rate</div></div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="metric-container"><div class="metric-value">{stats['avg_recovery_hours']} hrs</div><div class="metric-label">Avg. Resolution Window</div></div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="metric-container"><div class="metric-value">{stats['active_custody_zones']}</div><div class="metric-label">Campus Custody Desks</div></div>""", unsafe_allow_html=True)

st.write("")

# Navigation Tabs
tab_match, tab_catalog, tab_found, tab_lost, tab_claims = st.tabs([
    "🔎 Visual Match Studio",
    "📦 Custody Vault Catalog",
    "📥 Register Found Item",
    "📝 File Lost Inquiry",
    "🛡️ Verification & Claims Desk"
])


# ============================================================
# TAB 1: VISUAL MATCH STUDIO
# ============================================================
with tab_match:
    st.subheader("Locate Your Missing Valuable")
    st.caption("Upload a photograph or provide details. Our CLIP multimodal model compares visual features against all items currently in campus custody.")
    
    col_input, col_results = st.columns([1, 1.2], gap="large")
    
    with col_input:
        st.markdown("##### 1. Query Details")
        
        query_image = st.file_uploader("Upload Lost Item Photo", type=["jpg", "jpeg", "png", "webp"])
        
        # Sample quick pick
        sample_choice = st.selectbox(
            "Or select a test reference item from the campus dataset:",
            ["None", "Water Bottle (b2.jpg)", "Leather Wallet (wallet_test.jpg)", "Wristwatch (watchhh.jpg)", "Backpack (backpag.jpg)"]
        )
        
        sample_path = None
        if sample_choice == "Water Bottle (b2.jpg)":
            sample_path = "data/test_images/b2.jpg"
        elif sample_choice == "Leather Wallet (wallet_test.jpg)":
            sample_path = "data/test_images/wallet_test.jpg"
        elif sample_choice == "Wristwatch (watchhh.jpg)":
            sample_path = "data/test_images/watchhh.jpg"
        elif sample_choice == "Backpack (backpag.jpg)":
            sample_path = "data/test_images/backpag.jpg"
            
        if sample_path and os.path.exists(sample_path) and not query_image:
            st.image(sample_path, caption=f"Selected Sample: {sample_choice}", use_container_width=True)
            
        description = st.text_input("Item Description / Hallmarks", placeholder="e.g. Black Herschel backpack with red striped lining")
        
        c_cat, c_loc = st.columns(2)
        with c_cat:
            category = st.selectbox("Category Filter", ["all", "backpack", "bottle", "phone", "wallet", "watch", "other"])
        with c_loc:
            location = st.selectbox("Location Filter", ["all", "Library", "Cafeteria", "Engineering", "Science", "Sports", "Transit"])
            
        min_threshold = st.slider("Minimum Confidence Threshold", min_value=30, max_value=80, value=45, step=5)
        
        btn_match = st.button("🔎 Run Multimodal Search", use_container_width=True)

    with col_results:
        st.markdown("##### 2. Ranked Custody Matches")
        
        if btn_match:
            img_to_search = None
            if query_image:
                img_to_search = Image.open(query_image)
            elif sample_path and os.path.exists(sample_path):
                img_to_search = Image.open(sample_path)
                
            if not img_to_search and not description.strip():
                st.warning("Please upload an image, select a sample, or provide a description to begin searching.")
            else:
                with st.spinner("Analyzing visual embeddings and searching custody vaults..."):
                    candidates = db.get_all_found_items()
                    matches = ai_engine.search_matches(
                        candidate_items=candidates,
                        query_image=img_to_search,
                        query_text=description,
                        selected_category=category,
                        selected_location=location,
                        min_confidence=float(min_threshold),
                        top_k=5
                    )
                    
                if not matches:
                    st.info("No items in custody met the selected confidence threshold. Try lowering the threshold or file a Lost Inquiry in Tab 4.")
                else:
                    st.success(f"Discovered {len(matches)} matching candidate(s) in custody:")
                    for m in matches:
                        it = m["item"]
                        score = m["confidence"]
                        badge_style = "score-high" if score >= 80 else ("score-medium" if score >= 65 else "score-low")
                        
                        with st.container():
                            st.markdown(f"""
                            <div class="item-card">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                    <h4 style="margin:0; font-size:1.1rem; color:#0F172A;">{it.get('title')}</h4>
                                    <span class="score-badge {badge_style}">{score}% Match</span>
                                </div>
                                <p style="font-size:0.85rem; color:#475569; margin:4px 0;">📍 <strong>Location:</strong> {it.get('location')} • 🔒 <strong>Custody:</strong> {it.get('custody_location')}</p>
                                <p style="font-size:0.8rem; color:#2563EB; margin:4px 0;"><strong>Matched via:</strong> {', '.join(m.get('reasons', []))}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            c_img, c_claim = st.columns([1, 1.5])
                            with c_img:
                                if it.get("image_path") and os.path.exists(it["image_path"]):
                                    st.image(it["image_path"], use_container_width=True)
                            with c_claim:
                                st.caption(f"Verification Prompt: {it.get('verification_prompt', 'Describe unique marks.')}")
                                with st.expander(f"Claim Item #{it.get('id')}"):
                                    c_name = st.text_input("Your Full Name", key=f"cn_{it.get('id')}")
                                    c_phone = st.text_input("Phone Number", key=f"cp_{it.get('id')}")
                                    c_proof = st.text_area("Identifying Proof (Secret Answer)", key=f"cpr_{it.get('id')}", placeholder="Describe scratch, wallpaper, contents...")
                                    if st.button("Submit Ownership Claim", key=f"btn_c_{it.get('id')}"):
                                        if c_name and c_phone and c_proof:
                                            res = db.submit_claim({
                                                "item_id": it.get("id"),
                                                "claimant_name": c_name,
                                                "claimant_phone": c_phone,
                                                "claimant_email": "",
                                                "identifying_details": c_proof
                                            })
                                            st.success(f"Claim filed successfully! Reference: {res.get('claim_id')}. Please report to {it.get('custody_location')}.")
                                        else:
                                            st.error("Please fill all claim fields.")
        else:
            st.info("Upload an image or pick a test item on the left and click 'Run Multimodal Search' to view matched items.")


# ============================================================
# TAB 2: CUSTODY VAULT CATALOG
# ============================================================
with tab_catalog:
    st.subheader("Items Currently in Safe Custody")
    st.caption("All items logged by security personnel and campus staff awaiting verified owner reclamation.")
    
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        cat_filter = st.selectbox("Category Filter", ["all", "backpack", "bottle", "phone", "wallet", "watch", "other"], key="cat_catalog")
    with col_f2:
        search_filter = st.text_input("Search catalog by keyword or brand...", placeholder="e.g. Apple, Hydro Flask, Herschel, Casio...")
        
    items = db.get_all_found_items(category=cat_filter)
    if search_filter:
        q = search_filter.lower().strip()
        items = [it for it in items if q in it.get("title", "").lower() or q in it.get("location", "").lower() or q in it.get("brand", "").lower()]
        
    st.write(f"Displaying **{len(items)}** items:")
    
    # Render in 3-column grid
    cols = st.columns(3)
    for idx, it in enumerate(items):
        with cols[idx % 3]:
            st.markdown(f"""
            <div class="item-card">
                <span class="score-badge {'score-high' if it.get('status') == 'Available' else 'score-medium'}" style="margin-bottom:8px;">{it.get('status')}</span>
                <h4 style="margin:4px 0; font-size:1rem;">{it.get('title')}</h4>
                <p style="font-size:0.8rem; color:#64748B;">📍 {it.get('location')}</p>
                <p style="font-size:0.75rem; color:#94A3B8;">📅 Found: {it.get('date_found')} • 🔒 {it.get('custody_location')}</p>
            </div>
            """, unsafe_allow_html=True)
            if it.get("image_path") and os.path.exists(it["image_path"]):
                st.image(it["image_path"], use_container_width=True)
            st.divider()


# ============================================================
# TAB 3: REGISTER FOUND ITEM (INTAKE)
# ============================================================
with tab_found:
    st.subheader("Custody Intake Registration")
    st.caption("Register an item turned into security or lost & found dispatch. Generates multimodal vectors and alerts matching lost inquiries.")
    
    with st.form("form_intake"):
        f_title = st.text_input("Item Title *", placeholder="e.g. Apple Watch Series 8 (Midnight)")
        c1, c2, c3 = st.columns(3)
        with c1:
            f_cat = st.selectbox("Category *", ["backpack", "bottle", "phone", "wallet", "watch", "other"])
        with c2:
            f_brand = st.text_input("Brand", placeholder="e.g. Apple")
        with c3:
            f_color = st.text_input("Color", placeholder="e.g. Midnight Black")
            
        c4, c5 = st.columns(2)
        with c4:
            f_loc = st.text_input("Location Found *", placeholder="e.g. Central Library - 2nd Floor")
        with c5:
            f_locker = st.text_input("Custody Locker / Desk *", value="Locker A-04, Main Security Office")
            
        f_prompt = st.text_input("Anti-Theft Verification Prompt *", value="Describe any unique scratch, marks, or packaging details.")
        f_img = st.file_uploader("Item Photograph *", type=["jpg", "jpeg", "png"])
        
        submitted = st.form_submit_button("Register Item into Custody")
        
        if submitted:
            if f_title and f_loc and f_img:
                img_bytes = f_img.read()
                ext = os.path.splitext(f_img.name)[1] or ".jpg"
                fn = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}{ext}"
                save_dir = os.path.join("data", "registered_items")
                os.makedirs(save_dir, exist_ok=True)
                full_path = os.path.join(save_dir, fn)
                with open(full_path, "wb") as f:
                    f.write(img_bytes)
                    
                emb = ai_engine.extract_image_embedding(img_bytes)
                
                new_item = {
                    "title": f_title,
                    "description": f"{f_title}. Brand: {f_brand}. Color: {f_color}. Found at {f_loc}.",
                    "category": f_cat,
                    "brand": f_brand,
                    "color": f_color,
                    "location": f_loc,
                    "date_found": datetime.now().strftime("%Y-%m-%d"),
                    "filename": fn,
                    "image_path": full_path.replace("\\", "/"),
                    "status": "Available",
                    "custody_location": f_locker,
                    "verification_prompt": f_prompt,
                    "embedding": emb.tolist()
                }
                added = db.add_found_item(new_item)
                st.success(f"Item logged into custody! Custody ID: {added.get('id')}.")
            else:
                st.error("Please provide title, location, and a photograph.")


# ============================================================
# TAB 4: FILE LOST INQUIRY
# ============================================================
with tab_lost:
    st.subheader("Submit Lost Valuable Inquiry")
    st.caption("Can't find your item in the catalog? File a report and our continuous matcher will alert you as soon as matching items are registered.")
    
    with st.form("form_lost_inquiry"):
        l_name = st.text_input("What did you lose? *", placeholder="e.g. Grey Herschel Travel Laptop Backpack")
        l_cat = st.selectbox("Category *", ["backpack", "bottle", "phone", "wallet", "watch", "other"])
        l_desc = st.text_area("Detailed Description *", placeholder="Describe brand, markings, stickers, unique features...")
        l_loc = st.text_input("Last Seen Location *", placeholder="e.g. Cafeteria Table 14")
        
        c_n, c_e, c_p = st.columns(3)
        with c_n:
            owner_name = st.text_input("Your Full Name *")
        with c_e:
            owner_email = st.text_input("Email Address *")
        with c_p:
            owner_phone = st.text_input("Phone Number *")
            
        lost_sub = st.form_submit_button("Submit Lost Report")
        if lost_sub:
            if l_name and l_desc and owner_name and (owner_email or owner_phone):
                rep = db.add_lost_report({
                    "item_name": l_name,
                    "category": l_cat,
                    "description": l_desc,
                    "location_lost": l_loc,
                    "date_lost": datetime.now().strftime("%Y-%m-%d"),
                    "contact_name": owner_name,
                    "contact_email": owner_email,
                    "contact_phone": owner_phone
                })
                st.success(f"Lost report registered! Tracking ID: {rep.get('id')}. You will be alerted upon a positive match.")
            else:
                st.error("Please fill all required fields.")


# ============================================================
# TAB 5: CLAIMS VERIFICATION DESK
# ============================================================
with tab_claims:
    st.subheader("Custody Handover & Verification Desk")
    st.caption("Authorized campus security staff review claimant proofs and approve physical handovers.")
    
    claims = db.get_all_claims()
    if not claims:
        st.info("No active ownership claims currently pending review.")
    else:
        for c in claims:
            target_item = db.get_item_by_id(c.get("item_id", ""))
            with st.container():
                st.markdown(f"""
                <div class="item-card">
                    <div style="display:flex; justify-content:space-between;">
                        <strong>Claim #{c.get('claim_id')}</strong>
                        <span class="score-badge {'score-high' if c.get('status') == 'Approved' else 'score-medium'}">{c.get('status')}</span>
                    </div>
                    <p style="margin:4px 0;"><strong>Target Item:</strong> {target_item.get('title', 'Unknown') if target_item else 'Unknown'} (ID: {c.get('item_id')})</p>
                    <p style="margin:4px 0;"><strong>Claimant:</strong> {c.get('claimant_name')} • 📞 {c.get('claimant_phone')} • ✉️ {c.get('claimant_email')}</p>
                    <p style="margin:4px 0; background:#F8FAFC; padding:8px; border-radius:6px;"><strong>Submitted Proof / Secret Answer:</strong> <em>"{c.get('identifying_details')}"</em></p>
                </div>
                """, unsafe_allow_html=True)
                
                if c.get("status") == "Pending Review":
                    c_app, c_rej = st.columns([1, 1])
                    with c_app:
                        if st.button(f"Approve Handover", key=f"app_{c.get('claim_id')}"):
                            db.resolve_claim(c.get("claim_id"), "Approved", notes="Verified by officer")
                            st.success(f"Claim #{c.get('claim_id')} approved. Item marked as Reunited.")
                            st.rerun()
                    with c_rej:
                        if st.button(f"Reject Claim", key=f"rej_{c.get('claim_id')}"):
                            db.resolve_claim(c.get("claim_id"), "Rejected", notes="Proof did not match physical item")
                            st.warning(f"Claim #{c.get('claim_id')} rejected.")
                            st.rerun()
                st.divider()