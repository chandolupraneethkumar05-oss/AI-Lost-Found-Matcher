import os
import io
import uuid
from datetime import datetime
from PIL import Image
import streamlit as st

from src.database import db
from src.ai_engine import ai_engine

# ============================================================
# PAGE CONFIGURATION — CLASSIC INSTITUTIONAL DESIGN
# ============================================================
st.set_page_config(
    page_title="Central Lost Property Office — Campus & Community Network",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Classic Heritage Styling: Deep Oxford Navy, Warm Linen Cream, Heritage Gold
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Inter:wght@400;500;600&display=swap');
    
    /* Global Page Canvas */
    .stApp {
        background-color: #FAF8F5;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1F2937;
    }
    
    /* Clean Classic Institutional Header */
    .classic-header {
        background-color: #1B2A4A;
        color: #FFFFFF;
        padding: 40px 48px;
        border-radius: 8px;
        margin-bottom: 28px;
        border-bottom: 4px solid #C48208;
        box-shadow: 0 4px 12px rgba(27, 42, 74, 0.08);
    }
    .classic-dept {
        font-size: 0.8125rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #E2DDD5;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .classic-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 2.35rem;
        font-weight: 700;
        color: #FFFFFF !important;
        letter-spacing: -0.01em;
        margin-bottom: 12px;
        line-height: 1.2;
    }
    .classic-subtitle {
        font-size: 1rem;
        color: #CBD5E1;
        max-width: 760px;
        line-height: 1.6;
        margin: 0;
        font-weight: 400;
    }
    
    /* Statistics Ribbon */
    .stats-ribbon {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 32px;
    }
    .stat-box {
        background-color: #FFFFFF;
        border: 1px solid #E5E0D8;
        border-radius: 6px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }
    .stat-val {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 2rem;
        font-weight: 700;
        color: #1B2A4A;
        line-height: 1;
        margin-bottom: 6px;
    }
    .stat-desc {
        font-size: 0.8125rem;
        color: #6B7280;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    
    /* Clean Item Cards */
    .item-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E0D8;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .item-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.06);
    }
    .card-title {
        font-size: 1.0625rem;
        font-weight: 700;
        color: #1B2A4A;
        margin-bottom: 6px;
    }
    .card-detail {
        font-size: 0.85rem;
        color: #4B5563;
        margin: 3px 0;
        line-height: 1.5;
    }
    
    /* Badges */
    .badge-match {
        background-color: #FEF3C7;
        color: #92400E;
        border: 1px solid #FDE68A;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }
    .badge-high-match {
        background-color: #DCFCE7;
        color: #166534;
        border: 1px solid #BBF7D0;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-custody {
        background-color: #F3F4F6;
        color: #374151;
        border: 1px solid #E5E7EB;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    /* Clean Tab Navigation */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #E5E0D8;
        padding-bottom: 4px;
        margin-bottom: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        font-size: 0.9375rem;
        color: #4B5563;
        border-radius: 4px;
        padding: 10px 20px;
        background-color: transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #1B2A4A !important;
        background-color: #FFFFFF !important;
        border-bottom: 3px solid #1B2A4A !important;
    }
    
    /* Classic Buttons */
    div.stButton > button {
        background-color: #1B2A4A;
        color: #FFFFFF;
        font-weight: 600;
        font-size: 0.875rem;
        border-radius: 5px;
        border: 1px solid #1B2A4A;
        padding: 8px 20px;
        transition: all 0.15s ease;
    }
    div.stButton > button:hover {
        background-color: #0F172A;
        border-color: #0F172A;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.15);
    }
    
    /* Clean Callout */
    .notice-box {
        background-color: #F8F9FA;
        border-left: 3px solid #1B2A4A;
        padding: 14px 18px;
        margin-bottom: 20px;
        font-size: 0.875rem;
        color: #374151;
        border-radius: 0 4px 4px 0;
    }
</style>
""", unsafe_allow_html=True)

# Classic Header Banner
st.markdown("""
<div class="classic-header">
    <div class="classic-dept">
        <span>🏛️ Campus & Public Transit Services</span>
        <span>•</span>
        <span>Central Custody Desk</span>
    </div>
    <h1 class="classic-title">Lost Property Office</h1>
    <p class="classic-subtitle">
        The official repository for misplaced personal items across campus buildings, lecture halls, and transit hubs. Search recent hand-ins by photograph or description, register found property, and arrange verified collection.
    </p>
</div>
""", unsafe_allow_html=True)

# Live Statistics Ribbon
stats = db.get_statistics()
st.markdown(f"""
<div class="stats-ribbon">
    <div class="stat-box">
        <div class="stat-val">{stats['total_found']}</div>
        <div class="stat-desc">Items in Safe Custody</div>
    </div>
    <div class="stat-box">
        <div class="stat-val">{stats['success_rate_percent']}%</div>
        <div class="stat-desc">Successful Reconnection Rate</div>
    </div>
    <div class="stat-box">
        <div class="stat-val">{stats['avg_recovery_hours']} hrs</div>
        <div class="stat-desc">Average Claim Time</div>
    </div>
    <div class="stat-box">
        <div class="stat-val">6 Hubs</div>
        <div class="stat-desc">Security Collection Points</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Clear, human-readable tabs
tab_search, tab_catalog, tab_report_found, tab_report_lost, tab_desk = st.tabs([
    "🔍 Search Lost Property",
    "📋 Catalog of Handed-In Items",
    "📥 Report an Item You Found",
    "📝 Register a Missing Item",
    "🛡️ Verification & Collection Desk"
])

# ============================================================
# TAB 1: SEARCH LOST PROPERTY
# ============================================================
with tab_search:
    st.markdown("""
    <div class="notice-box">
        <strong>How to search:</strong> Upload a clear photograph of your missing belonging, or enter distinctive words (brand, model, color, or markings). Our system will compare it against all items held in campus custody lockers.
    </div>
    """, unsafe_allow_html=True)
    
    col_search_left, col_search_right = st.columns([1, 1.3], gap="large")
    
    with col_search_left:
        st.markdown("#### Search Details")
        uploaded_photo = st.file_uploader("Upload a photo of your lost item", type=["jpg", "jpeg", "png", "webp"])
        
        # Test reference samples from authentic dataset
        sample_pick = st.selectbox(
            "Or try searching with a real item photo from the repository:",
            [
                "None (Upload my own photo)",
                "Black Leather Wallet (data/test_images/wallet_test.jpg)",
                "Water Bottle (data/test_images/b2.jpg)",
                "Wristwatch (data/test_images/watchhh.jpg)",
                "Backpack (data/test_images/backpag.jpg)"
            ]
        )
        
        sample_file_path = None
        if "wallet_test.jpg" in sample_pick:
            sample_file_path = "data/test_images/wallet_test.jpg"
        elif "b2.jpg" in sample_pick:
            sample_file_path = "data/test_images/b2.jpg"
        elif "watchhh.jpg" in sample_pick:
            sample_file_path = "data/test_images/watchhh.jpg"
        elif "backpag.jpg" in sample_pick:
            sample_file_path = "data/test_images/backpag.jpg"
            
        if sample_file_path and os.path.exists(sample_file_path) and not uploaded_photo:
            st.image(sample_file_path, caption="Selected sample photograph for search", use_container_width=True)
            
        item_text = st.text_input("Keywords / Item Description", placeholder="e.g. Black Herschel backpack with red inner lining")
        
        c_filter1, c_filter2 = st.columns(2)
        with c_filter1:
            category_choice = st.selectbox("Category", [
                "all", "backpack", "phone", "laptop", "audio", "wallet", "watch", "bottle", "keys", "other"
            ])
        with c_filter2:
            location_choice = st.selectbox("Location Last Seen", [
                "all", "Library", "Cafeteria", "Engineering", "Science", "Sports", "Auditorium", "Transit"
            ])
            
        sensitivity = st.slider("Similarity Threshold", min_value=30, max_value=85, value=45, step=5, help="Lower value shows broader possibilities; higher value shows only close matches.")
        
        search_clicked = st.button("Search Found Property", use_container_width=True)

    with col_search_right:
        st.markdown("#### Potential Matches in Custody")
        
        if search_clicked:
            query_img = None
            if uploaded_photo:
                query_img = Image.open(uploaded_photo)
            elif sample_file_path and os.path.exists(sample_file_path):
                query_img = Image.open(sample_file_path)
                
            if not query_img and not item_text.strip():
                st.warning("Please upload a photograph or enter a description to search.")
            else:
                with st.spinner("Checking items currently held in custody lockers..."):
                    candidates = db.get_all_found_items()
                    matches = ai_engine.search_matches(
                        candidate_items=candidates,
                        query_image=query_img,
                        query_text=item_text,
                        selected_category=category_choice,
                        selected_location=location_choice,
                        min_confidence=float(sensitivity),
                        top_k=6
                    )
                    
                if not matches:
                    st.info("No items in our current inventory match these criteria. Please register a missing report in Tab 4, and we will contact you immediately if it is handed in.")
                else:
                    st.success(f"Found {len(matches)} potential match(es) held in custody:")
                    for m in matches:
                        it = m["item"]
                        score = m["confidence"]
                        badge_class = "badge-high-match" if score >= 80 else "badge-match"
                        
                        st.markdown(f"""
                        <div class="item-card">
                            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                                <div>
                                    <div class="card-title">{it.get('title')}</div>
                                    <span class="badge-custody">Ref: {it.get('id')}</span>
                                </div>
                                <span class="{badge_class}">{score}% Visual Match</span>
                            </div>
                            <div class="card-detail">📍 <strong>Found At:</strong> {it.get('location')}</div>
                            <div class="card-detail">📅 <strong>Handed In:</strong> {it.get('date_found')} • 🔒 <strong>Held At:</strong> {it.get('custody_location')}</div>
                            <div class="card-detail" style="color:#1E40AF; margin-top:6px;"><strong>Match Reasons:</strong> {', '.join(m.get('reasons', []))}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        c_card_img, c_card_action = st.columns([1, 1.6])
                        with c_card_img:
                            if it.get("image_path") and os.path.exists(it["image_path"]):
                                st.image(it["image_path"], use_container_width=True)
                        with c_card_action:
                            st.write(f"**Verification Question:** {it.get('verification_prompt', 'Describe unique marks or contents.')}")
                            with st.expander(f"Arrange Collection for #{it.get('id')}"):
                                cl_name = st.text_input("Your Full Name", key=f"n_{it.get('id')}")
                                cl_phone = st.text_input("Phone Number", key=f"p_{it.get('id')}")
                                cl_proof = st.text_area("Your Proof / Identifying Details", key=f"pr_{it.get('id')}", placeholder="Describe private details (lockscreen, scratches, inner pocket items, stickers)...")
                                if st.button("Submit Claim for Verification", key=f"b_{it.get('id')}"):
                                    if cl_name and cl_phone and cl_proof:
                                        res = db.submit_claim({
                                            "item_id": it.get("id"),
                                            "claimant_name": cl_name,
                                            "claimant_phone": cl_phone,
                                            "claimant_email": "",
                                            "identifying_details": cl_proof
                                        })
                                        st.success(f"Claim submitted successfully (Ref: {res.get('claim_id')}). Please present photo ID at {it.get('custody_location')} to collect.")
                                    else:
                                        st.error("Please provide your name, phone number, and proof.")
                        st.write("---")
        else:
            st.info("Select a sample item or upload a photograph on the left to begin searching.")

# ============================================================
# TAB 2: CATALOG OF HANDED-IN ITEMS
# ============================================================
with tab_catalog:
    st.markdown("#### Current Property in Safe Custody")
    st.caption("Browse all physical items deposited at campus security desks awaiting collection.")
    
    col_filter_a, col_filter_b = st.columns([1, 2])
    with col_filter_a:
        filter_cat = st.selectbox("Filter by Category", [
            "all", "backpack", "phone", "laptop", "audio", "wallet", "watch", "bottle", "keys", "other"
        ], key="cat_browser")
    with col_filter_b:
        filter_search = st.text_input("Search catalog by keyword or brand...", placeholder="e.g. Apple, Dell, Hydro Flask, Herschel, Casio...", key="search_browser")
        
    catalog_items = db.get_all_found_items(category=filter_cat)
    if filter_search:
        term = filter_search.lower().strip()
        catalog_items = [
            it for it in catalog_items
            if term in it.get("title", "").lower()
            or term in it.get("location", "").lower()
            or term in it.get("brand", "").lower()
            or term in it.get("color", "").lower()
        ]
        
    st.write(f"Showing **{len(catalog_items)}** items in custody:")
    
    grid_cols = st.columns(3)
    for idx, item in enumerate(catalog_items):
        with grid_cols[idx % 3]:
            st.markdown(f"""
            <div class="item-card">
                <span class="badge-custody">{item.get('status')}</span>
                <div class="card-title" style="margin-top:8px;">{item.get('title')}</div>
                <div class="card-detail">📍 {item.get('location')}</div>
                <div class="card-detail">🔒 {item.get('custody_location')}</div>
                <div class="card-detail" style="color:#6B7280; font-size:0.75rem;">Handed in: {item.get('date_found')}</div>
            </div>
            """, unsafe_allow_html=True)
            if item.get("image_path") and os.path.exists(item["image_path"]):
                st.image(item["image_path"], use_container_width=True)
            st.write("")

# ============================================================
# TAB 3: REPORT AN ITEM YOU FOUND
# ============================================================
with tab_report_found:
    st.markdown("#### Register a Found Belonging")
    st.caption("Please deposit the physical item at the nearest campus reception or security post after logging it.")
    
    with st.form("form_register_found"):
        title_in = st.text_input("Item Name / Title *", placeholder="e.g. Apple Watch Series 8 (Midnight)")
        
        row1_a, row1_b, row1_c = st.columns(3)
        with row1_a:
            cat_in = st.selectbox("Category *", ["backpack", "phone", "laptop", "audio", "wallet", "watch", "bottle", "keys", "other"])
        with row1_b:
            brand_in = st.text_input("Brand", placeholder="e.g. Apple, Hydro Flask")
        with row1_c:
            color_in = st.text_input("Primary Color", placeholder="e.g. Black, Silver")
            
        row2_a, row2_b = st.columns(2)
        with row2_a:
            loc_in = st.text_input("Exact Location Where Found *", placeholder="e.g. Central Library, 2nd Floor Study Room 204")
        with row2_b:
            locker_in = st.text_input("Physical Custody Location *", value="Main Security Office, Safe Box A")
            
        prompt_in = st.text_input("Ownership Verification Prompt *", value="Describe any unique scratch, marks, or packaging details.")
        photo_in = st.file_uploader("Item Photograph *", type=["jpg", "jpeg", "png"])
        
        submit_found = st.form_submit_button("Register Found Item")
        
        if submit_found:
            if title_in and loc_in and photo_in:
                img_data = photo_in.read()
                ext = os.path.splitext(photo_in.name)[1] or ".jpg"
                unique_fn = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}{ext}"
                save_dir = os.path.join("data", "registered_items")
                os.makedirs(save_dir, exist_ok=True)
                target_path = os.path.join(save_dir, unique_fn)
                
                with open(target_path, "wb") as f:
                    f.write(img_data)
                    
                emb = ai_engine.extract_image_embedding(img_data)
                
                new_record = {
                    "title": title_in,
                    "description": f"{title_in}. Brand: {brand_in}. Color: {color_in}. Found at {loc_in}.",
                    "category": cat_in,
                    "brand": brand_in,
                    "color": color_in,
                    "location": loc_in,
                    "date_found": datetime.now().strftime("%Y-%m-%d"),
                    "filename": unique_fn,
                    "image_path": target_path.replace("\\", "/"),
                    "status": "Available",
                    "custody_location": locker_in,
                    "verification_prompt": prompt_in,
                    "embedding": emb.tolist()
                }
                added_item = db.add_found_item(new_record)
                st.success(f"Item logged into custody catalog with Reference #{added_item.get('id')}.")
            else:
                st.error("Please provide the item title, location, and a photograph.")

# ============================================================
# TAB 4: REGISTER A MISSING ITEM
# ============================================================
with tab_report_lost:
    st.markdown("#### Submit a Missing Property Report")
    st.caption("If your item is not currently listed in our catalog, file this report. Our system monitors all new hand-ins and alerts you upon a match.")
    
    with st.form("form_register_lost"):
        lost_title = st.text_input("What item did you lose? *", placeholder="e.g. Navy Blue JanSport Backpack")
        lost_category = st.selectbox("Category *", ["backpack", "phone", "laptop", "audio", "wallet", "watch", "bottle", "keys", "other"])
        lost_desc = st.text_area("Detailed Description *", placeholder="Include any stickers, scratches, contents inside, or personal markings...")
        lost_loc = st.text_input("Location Last Seen *", placeholder="e.g. Cafeteria Table 14 or North Bus Bay")
        
        c_name, c_email, c_phone = st.columns(3)
        with c_name:
            contact_name = st.text_input("Your Full Name *")
        with c_email:
            contact_email = st.text_input("Email Address *")
        with c_phone:
            contact_phone = st.text_input("Contact Phone Number *")
            
        submit_lost = st.form_submit_button("Submit Missing Report")
        if submit_lost:
            if lost_title and lost_desc and contact_name and (contact_email or contact_phone):
                rep = db.add_lost_report({
                    "item_name": lost_title,
                    "category": lost_category,
                    "description": lost_desc,
                    "location_lost": lost_loc,
                    "date_lost": datetime.now().strftime("%Y-%m-%d"),
                    "contact_name": contact_name,
                    "contact_email": contact_email,
                    "contact_phone": contact_phone
                })
                st.success(f"Missing report registered! Reference ID: {rep.get('id')}. You will be contacted automatically upon an intake match.")
            else:
                st.error("Please fill all required fields.")

# ============================================================
# TAB 5: VERIFICATION & COLLECTION DESK
# ============================================================
with tab_desk:
    st.markdown("#### Claims Verification & Physical Handover Desk")
    st.caption("Authorized security officers review ownership proofs and authorize physical collection.")
    
    claims_list = db.get_all_claims()
    if not claims_list:
        st.info("There are currently no claims pending verification.")
    else:
        for c in claims_list:
            item_ref = db.get_item_by_id(c.get("item_id", ""))
            st.markdown(f"""
            <div class="item-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div><strong>Claim #{c.get('claim_id')}</strong></div>
                    <span class="badge-custody">{c.get('status')}</span>
                </div>
                <div class="card-detail" style="margin-top:6px;"><strong>Target Item:</strong> {item_ref.get('title', 'Unknown Item') if item_ref else 'Unknown'} (Ref: {c.get('item_id')})</div>
                <div class="card-detail"><strong>Claimant:</strong> {c.get('claimant_name')} • 📞 {c.get('claimant_phone')}</div>
                <div class="card-detail" style="background:#F9FAFB; padding:10px; border-radius:4px; margin-top:8px;">
                    <strong>Claimant Proof / Answer:</strong><br />
                    <em>"{c.get('identifying_details')}"</em>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if c.get("status") == "Pending Review":
                col_btn_app, col_btn_rej = st.columns(2)
                with col_btn_app:
                    if st.button("Approve & Hand Over", key=f"app_{c.get('claim_id')}"):
                        db.resolve_claim(c.get("claim_id"), "Approved", notes="Verified by desk officer")
                        st.success(f"Claim #{c.get('claim_id')} approved. Item marked as Reunited.")
                        st.rerun()
                with col_btn_rej:
                    if st.button("Reject Claim", key=f"rej_{c.get('claim_id')}"):
                        db.resolve_claim(c.get("claim_id"), "Rejected", notes="Proof did not match physical item")
                        st.warning(f"Claim #{c.get('claim_id')} rejected.")
                        st.rerun()
            st.write("---")