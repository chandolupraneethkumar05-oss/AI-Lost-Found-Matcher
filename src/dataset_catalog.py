import os
import glob
from datetime import datetime, timedelta
import random
from src.database import db
from src.ai_engine import ai_engine

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
FOUND_ITEMS_DIR = os.path.join(DATA_DIR, "found_items")
REGISTERED_ITEMS_DIR = os.path.join(DATA_DIR, "registered_items")

# Catalog definitions for existing sample items
METADATA_PRESETS = {
    # Backpacks
    "backpack1.jpg": {
        "title": "Herschel Supply Co. Classic Backpack (Black)",
        "brand": "Herschel",
        "category": "backpack",
        "color": "Black",
        "location": "Main Library - 2nd Floor Study Room 204",
        "custody": "Desk A - Campus Security Main Office",
        "question": "What is the color of the inner striped lining and what is in the front zip pocket?"
    },
    "backpack2.jpg": {
        "title": "JanSport SuperBreak Daypack (Navy Blue)",
        "brand": "JanSport",
        "category": "backpack",
        "color": "Navy Blue",
        "location": "Engineering Block B - 1st Floor Corridor",
        "custody": "Locker 14 - Department Office",
        "question": "Are there any keychains attached to the zipper pulls?"
    },
    "backpack3.jpg": {
        "title": "SwissGear ScanSmart Travel Laptop Backpack",
        "brand": "SwissGear",
        "category": "backpack",
        "color": "Charcoal / Red Accent",
        "location": "Central Cafeteria - Booth 12",
        "custody": "Desk B - Student Center Desk",
        "question": "What size laptop compartment is inside and are there water bottles in the mesh?"
    },
    "backpack4.jpg": {
        "title": "Nike Brasilia Training Backpack (Midnight Black)",
        "brand": "Nike",
        "category": "backpack",
        "color": "Black / White Swoosh",
        "location": "Sports Arena Gymnasium - Court 2 Bleachers",
        "custody": "Athletic Office - Safe Box 3",
        "question": "What gym shoes or towel were inside the main compartment?"
    },
    "backpack5.jpg": {
        "title": "The North Face Borealis Commuter Backpack",
        "brand": "The North Face",
        "category": "backpack",
        "color": "Heather Gray",
        "location": "Campus Transit Hub - North Bus Shelter",
        "custody": "Transit Security Post #2",
        "question": "What color is the front bungee cord and what brand water bottle is in the side pocket?"
    },

    # Bottles
    "b1.jpg": {
        "title": "Hydro Flask 32 oz Wide Mouth Bottle",
        "brand": "Hydro Flask",
        "category": "bottle",
        "color": "Matte Black",
        "location": "Science Complex - Physics Lab 301",
        "custody": "Lab Coordinator Custody Shelf",
        "question": "Are there any laptop or anime stickers on the exterior cylinder?"
    },
    "b2.jpg": {
        "title": "Stanley Quencher H2.0 FlowState Tumbler (40 oz)",
        "brand": "Stanley",
        "category": "bottle",
        "color": "Cream / Rose Gold",
        "location": "Central Library - Ground Floor Cafe Area",
        "custody": "Library Circulation Desk Locker 8",
        "question": "What color is the reusable straw and is there an engraved monogram?"
    },
    "b3.jpg": {
        "title": "YETI Rambler 26 oz Bottle with Chug Cap",
        "brand": "YETI",
        "category": "bottle",
        "color": "Seafoam Teal",
        "location": "Auditorium - Row G Seat 18",
        "custody": "Auditorium Event Operations Desk",
        "question": "Is there a small dent on the bottom rim or a name written on the base?"
    },
    "b4.jpg": {
        "title": "Milton Thermosteel Classic Flask (500ml)",
        "brand": "Milton",
        "category": "bottle",
        "color": "Brushed Silver",
        "location": "Mechanical Workshop - Bench 4",
        "custody": "Workshop Supervisor Room 101",
        "question": "Describe the thermal sleeve or carry pouch it was kept in."
    },
    "b5.jpg": {
        "title": "CamelBak Chute Mag Insulated Stainless Steel Bottle",
        "brand": "CamelBak",
        "category": "bottle",
        "color": "Olive Green",
        "location": "Student Activity Center - Table Tennis Area",
        "custody": "Recreation Desk Custody Drawer",
        "question": "What is the magnetic cap retention color?"
    },

    # Phones
    "phone1.jpg": {
        "title": "Apple iPhone 14 Pro (Space Black)",
        "brand": "Apple",
        "category": "phone",
        "color": "Space Black",
        "location": "Campus Library - 3rd Floor Silent Reading Area",
        "custody": "Security Safe #1 - Main Gate",
        "question": "What is the lock screen photo and the phone case design?"
    },
    "phone2.jpg": {
        "title": "Samsung Galaxy S23 Ultra (Phantom Black)",
        "brand": "Samsung",
        "category": "phone",
        "color": "Phantom Black",
        "location": "Cafeteria - Food Court Register 3",
        "custody": "Security Safe #2 - Cafeteria Office",
        "question": "What color is the S-Pen tip and what protective case is on it?"
    },
    "phone3.jpg": {
        "title": "Google Pixel 8 (Hazel)",
        "brand": "Google",
        "category": "phone",
        "color": "Hazel Gray/Green",
        "location": "Computer Center - Lab 4 Desk 28",
        "custody": "IT Admin Front Desk",
        "question": "What network SIM provider is displayed on the lockscreen?"
    },
    "phone4.jpg": {
        "title": "OnePlus 11 5G (Titan Black)",
        "brand": "OnePlus",
        "category": "phone",
        "color": "Titan Black",
        "location": "Administrative Building - Conference Room 2",
        "custody": "Admin Reception Locker 3",
        "question": "What wallpaper image is visible on the standby display?"
    },
    "phone5.jpg": {
        "title": "Apple iPhone 13 (Midnight Blue)",
        "brand": "Apple",
        "category": "phone",
        "color": "Midnight Blue",
        "location": "Mathematics Block - Classroom 201",
        "custody": "Department Secretary Locker",
        "question": "Describe the pattern or credit card holder on the back of the case."
    },

    # Wallets
    "w1.jpg": {
        "title": "Bellroy Hide & Seek Leather Bi-Fold Wallet",
        "brand": "Bellroy",
        "category": "wallet",
        "color": "Caramel Brown",
        "location": "Vignan University Cafeteria - Billing Counter",
        "custody": "Accounts & Custody Vault 5",
        "question": "What bank cards and ID card name are inside the hidden flap?"
    },
    "w2.jpg": {
        "title": "Fossil Derrick RFID Leather Bifold Wallet",
        "brand": "Fossil",
        "category": "wallet",
        "color": "Dark Brown",
        "location": "ATM Kiosk - Campus Commercial Center",
        "custody": "Campus Security Bank Liaison Desk",
        "question": "What university registration ID number is in the transparent window?"
    },
    "w3.jpg": {
        "title": "The Ridge Minimalist RFID Aluminum Wallet",
        "brand": "Ridge",
        "category": "wallet",
        "color": "Gunmetal Gray",
        "location": "Main Auditorium - Foyer Staircase",
        "custody": "Main Security Station Box 7",
        "question": "Is it fitted with the cash strap or money clip and how many cards are inside?"
    },
    "w4.jpg": {
        "title": "Tommy Hilfiger Men's Leather Passcase Wallet",
        "brand": "Tommy Hilfiger",
        "category": "wallet",
        "color": "Black",
        "location": "Parking Lot P3 - Near Bike Stand 4",
        "custody": "Parking Control Gate 2",
        "question": "What name is printed on the metro card inside?"
    },
    "w5.jpg": {
        "title": "Coach Slim Card Case in Signature Canvas",
        "brand": "Coach",
        "category": "wallet",
        "color": "Charcoal / Black Monogram",
        "location": "Executive Seminar Hall - Row B",
        "custody": "Dean's Office Reception",
        "question": "What student badge or driver's license initials are inside?"
    },

    # Watches
    "watch1.jpg": {
        "title": "Apple Watch Series 8 (45mm Midnight Aluminum)",
        "brand": "Apple",
        "category": "watch",
        "color": "Midnight",
        "location": "Indoor Badminton Court - Bench 1",
        "custody": "Athletics Custody Safe #4",
        "question": "What band is attached (Sport Loop, Solo Loop, or Milanese)?"
    },
    "watch2.jpg": {
        "title": "Casio Vintage Illuminator Digital Watch (A168WA)",
        "brand": "Casio",
        "category": "watch",
        "color": "Silver Metallic",
        "location": "Chemistry Building - Staircase Landing 2nd Floor",
        "custody": "Central Custody Office Drawer 9",
        "question": "Is the clasp adjusted to a small or large wrist size and is the chime active?"
    },
    "watch3.jpg": {
        "title": "Fossil Grant Chronograph Leather Watch",
        "brand": "Fossil",
        "category": "watch",
        "color": "Blue Dial / Brown Leather",
        "location": "Student Activity Center - Music Room",
        "custody": "Student Center Administration Desk",
        "question": "What roman numeral color and strap stitching color are visible?"
    },
    "watch4.jpg": {
        "title": "Samsung Galaxy Watch 5 (44mm Graphite)",
        "brand": "Samsung",
        "category": "watch",
        "color": "Graphite",
        "location": "Central Library - Digital Media Lab",
        "custody": "Library Safe Box 11",
        "question": "What watch face is displayed on wakeup?"
    },
    "watch5.jpg": {
        "title": "Timex Weekender 38mm Slip-Thru Strap Watch",
        "brand": "Timex",
        "category": "watch",
        "color": "Cream Dial / Olive Strap",
        "location": "Campus Green Lawn - Near Banyan Tree",
        "custody": "Grounds Maintenance Custody Box",
        "question": "What color is the second hand and does the Indiglo backlight work?"
    }
}


def build_and_enrich_catalog():
    """
    Scan all image directories, generate CLIP embeddings for items,
    and populate the structured database.
    """
    print("Beginning catalog enrichment...")
    existing_items = {it.get("filename"): it for it in db.found_items if it.get("filename")}

    all_images = []
    # 1. Category folders
    for cat_dir in glob.glob(os.path.join(FOUND_ITEMS_DIR, "*")):
        if os.path.isdir(cat_dir):
            cat_name = os.path.basename(cat_dir)
            for img_file in glob.glob(os.path.join(cat_dir, "*.*")):
                all_images.append((img_file, cat_name))

    # 2. Registered items folder
    for img_file in glob.glob(os.path.join(REGISTERED_ITEMS_DIR, "*.*")):
        all_images.append((img_file, "registered"))

    print(f"Discovered {len(all_images)} item images across local repositories.")

    added_count = 0
    updated_count = 0

    base_date = datetime.now() - timedelta(days=14)

    for idx, (img_path, folder_cat) in enumerate(all_images):
        filename = os.path.basename(img_path)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            continue

        rel_path = os.path.relpath(img_path, BASE_DIR).replace("\\", "/")

        preset = METADATA_PRESETS.get(filename, {})
        category = preset.get("category", folder_cat if folder_cat != "registered" else "other")
        title = preset.get("title", f"{category.title()} Item ({filename})")
        location = preset.get("location", "Campus Main Premises")
        brand = preset.get("brand", "Standard")
        color = preset.get("color", "Standard")
        custody = preset.get("custody", "Central Security Desk - Vault Locker")
        question = preset.get("question", "Describe any unique scratch, marks, or packaging details.")

        item_date = (base_date + timedelta(days=idx % 14)).strftime("%Y-%m-%d")

        # Check if already in database with embedding
        if filename in existing_items and existing_items[filename].get("embedding"):
            # Update metadata if needed
            it = existing_items[filename]
            it["title"] = title
            it["category"] = category
            it["location"] = location
            it["brand"] = brand
            it["color"] = color
            it["custody_location"] = custody
            it["verification_prompt"] = question
            it["image_path"] = rel_path
            updated_count += 1
            continue

        print(f"Generating CLIP embedding for: {filename}...")
        try:
            emb = ai_engine.extract_image_embedding(img_path)
            item_record = {
                "id": f"FND-26{idx+10:03d}",
                "title": title,
                "description": f"{title}. Brand: {brand}. Color: {color}. Found at {location}.",
                "category": category,
                "brand": brand,
                "color": color,
                "location": location,
                "date_found": item_date,
                "filename": filename,
                "image_path": rel_path,
                "status": "Available",
                "custody_location": custody,
                "verification_prompt": question,
                "embedding": emb.tolist()
            }
            db.found_items.append(item_record)
            added_count += 1
        except Exception as e:
            print(f"Failed to embed {img_path}: {e}")

    # Seed sample realistic lost inquiries for automated matching verification
    if len(db.lost_reports) == 0:
        db.add_lost_report({
            "id": "LST-2601",
            "item_name": "Hydro Flask 32oz Black Water Bottle",
            "description": "Black insulated Hydro Flask water bottle, lost somewhere near the Physics lab on 3rd floor.",
            "category": "bottle",
            "location_lost": "Science Complex - Physics Lab",
            "date_lost": (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d"),
            "contact_name": "Aarav Sharma",
            "contact_email": "aarav.s@campus.edu",
            "contact_phone": "+91 98765 43210",
            "status": "Potential Match Found"
        })
        db.add_lost_report({
            "id": "LST-2602",
            "item_name": "Brown Leather Bellroy Bifold Wallet",
            "description": "Tan brown leather wallet with college student ID card and bus pass. Lost during lunch at cafeteria.",
            "category": "wallet",
            "location_lost": "Cafeteria - Food Court",
            "date_lost": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "contact_name": "Priya Patel",
            "contact_email": "priya.p@campus.edu",
            "contact_phone": "+91 98111 22334",
            "status": "Pending Search"
        })

    db.save()
    print(f"Catalog sync completed! Added {added_count} items, updated {updated_count} items. Total: {len(db.found_items)} items.")


if __name__ == "__main__":
    build_and_enrich_catalog()
