import os
import urllib.request
import time
from src.database import db
from src.ai_engine import ai_engine

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
REAL_ITEMS_DIR = os.path.join(DATA_DIR, "real_items")
os.makedirs(REAL_ITEMS_DIR, exist_ok=True)

# Curated catalog of authentic everyday items frequently reported in campus and public transport lost property offices
# Direct high-res photographs from Unsplash CDN
REAL_ITEMS_METADATA = [
    # 1. Electronics & Phones
    {
        "filename": "iphone_14_black.jpg",
        "url": "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=600&auto=format&fit=crop&q=80",
        "title": "Apple iPhone 14 in Matte Black Case",
        "category": "phone",
        "brand": "Apple",
        "color": "Black",
        "location": "Central Library, 2nd Floor Silent Study Area",
        "custody": "Library Front Circulation Desk (Locker 04)",
        "date_found": "2026-09-24",
        "question": "What is the lockscreen wallpaper and phone case color?",
    },
    {
        "filename": "samsung_galaxy_white.jpg",
        "url": "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=600&auto=format&fit=crop&q=80",
        "title": "Samsung Galaxy S22 with Clear Transparent Case",
        "category": "phone",
        "brand": "Samsung",
        "color": "White / Silver",
        "location": "Student Cafeteria, Booth 18",
        "custody": "Main Security Office, Safe Deposit Box 2",
        "date_found": "2026-09-25",
        "question": "Are there any student photocards or metro cards slipped behind the clear case?",
    },
    {
        "filename": "macbook_air_spacegray.jpg",
        "url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&auto=format&fit=crop&q=80",
        "title": "Apple MacBook Air 13-inch (Space Grey)",
        "category": "laptop",
        "brand": "Apple",
        "color": "Space Grey",
        "location": "Computer Science Lab 3, Desk 14",
        "custody": "Department IT Administrator Desk",
        "date_found": "2026-09-22",
        "question": "Describe any developer stickers or decals on the aluminum lid.",
    },
    {
        "filename": "dell_xps_laptop.jpg",
        "url": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=600&auto=format&fit=crop&q=80",
        "title": "Dell XPS 15 Silver Laptop in Black Neoprene Sleeve",
        "category": "laptop",
        "brand": "Dell",
        "color": "Silver / Black",
        "location": "Auditorium Hall A, Row 6 Seat 12",
        "custody": "Campus Security Office, Vault 1",
        "date_found": "2026-09-21",
        "question": "What brand of charging cable or mouse was inside the laptop sleeve?",
    },
    {
        "filename": "airpods_pro_white.jpg",
        "url": "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=600&auto=format&fit=crop&q=80",
        "title": "Apple AirPods Pro (2nd Gen) in White MagSafe Case",
        "category": "audio",
        "brand": "Apple",
        "color": "White",
        "location": "Engineering Workshop B, Bench 3",
        "custody": "Central Custody Office, Drawer 8",
        "date_found": "2026-09-26",
        "question": "Is there a silicone protective cover or carabiner clip attached?",
    },
    {
        "filename": "sony_wh1000xm4.jpg",
        "url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=600&auto=format&fit=crop&q=80",
        "title": "Sony WH-1000XM4 Wireless Over-Ear Headphones (Black)",
        "category": "audio",
        "brand": "Sony",
        "color": "Matte Black",
        "location": "Sports Complex, Bleachers near Court 1",
        "custody": "Recreation Desk Custody Box",
        "date_found": "2026-09-23",
        "question": "Were they inside the original grey fabric hardshell travel case?",
    },

    # 2. Backpacks & Bags
    {
        "filename": "herschel_classic_black.jpg",
        "url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80",
        "title": "Herschel Supply Co. Heritage Backpack (Black / Tan Leather)",
        "category": "backpack",
        "brand": "Herschel",
        "color": "Black / Brown Accent",
        "location": "Main Lecture Theatre, Lecture Room 101",
        "custody": "Main Security Dispatch, Locker 11",
        "date_found": "2026-09-25",
        "question": "What books or stationery folders were inside the main compartment?",
    },
    {
        "filename": "kanken_yellow_backpack.jpg",
        "url": "https://images.unsplash.com/photo-1622560480605-d83c853bc5c3?w=600&auto=format&fit=crop&q=80",
        "title": "Fjällräven Kånken Classic Daypack (Warm Ochre Yellow)",
        "category": "backpack",
        "brand": "Fjällräven",
        "color": "Ochre Yellow",
        "location": "Fine Arts Building, 1st Floor Gallery Hall",
        "custody": "Arts Department Front Office",
        "date_found": "2026-09-24",
        "question": "What enamel pin or keychain is fastened to the top canvas handle?",
    },
    {
        "filename": "leather_messenger_brown.jpg",
        "url": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=600&auto=format&fit=crop&q=80",
        "title": "Vintage Brown Leather Shoulder Messenger Bag",
        "category": "backpack",
        "brand": "Handcrafted Leather",
        "color": "Chestnut Brown",
        "location": "Faculty Staff Room & Visitor Lounge",
        "custody": "Administration Reception, Room 104",
        "date_found": "2026-09-20",
        "question": "What initials or company documents are inside the interior zippered pouch?",
    },
    {
        "filename": "nike_gym_duffel.jpg",
        "url": "https://images.unsplash.com/photo-1577733966973-d680bffd2e80?w=600&auto=format&fit=crop&q=80",
        "title": "Nike Brasilia Medium Sports Duffel Bag (Navy Blue)",
        "category": "backpack",
        "brand": "Nike",
        "color": "Navy Blue / White",
        "location": "Athletics Changing Room, Locker Row 5",
        "custody": "Gymnasium Facilities Manager Office",
        "date_found": "2026-09-26",
        "question": "What brand of sports shoes or swimming gear was inside?",
    },

    # 3. Wallets, Cards & Keys
    {
        "filename": "bellroy_leather_wallet.jpg",
        "url": "https://images.unsplash.com/photo-1627123424574-724758594e93?w=600&auto=format&fit=crop&q=80",
        "title": "Bellroy Slim Leather Bifold Wallet (Tan Brown)",
        "category": "wallet",
        "brand": "Bellroy",
        "color": "Tan Brown",
        "location": "Campus Central ATM Kiosk",
        "custody": "Campus Security Bank Liaison Vault",
        "date_found": "2026-09-26",
        "question": "What name is printed on the bank cards and university ID inside?",
    },
    {
        "filename": "ridge_black_wallet.jpg",
        "url": "https://images.unsplash.com/photo-1606760227091-3dd870d97f1d?w=600&auto=format&fit=crop&q=80",
        "title": "The Ridge Minimalist Aluminum Cardholder Wallet (Matte Black)",
        "category": "wallet",
        "brand": "Ridge",
        "color": "Matte Black",
        "location": "Student Union Dining Hall, Table 7",
        "custody": "Student Union Information Desk",
        "date_found": "2026-09-25",
        "question": "How many cards are inside and does it have the cash strap or money clip?",
    },
    {
        "filename": "car_key_fob.jpg",
        "url": "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?w=600&auto=format&fit=crop&q=80",
        "title": "Automotive Remote Key Fob with Braided Leather Keychain",
        "category": "keys",
        "brand": "Honda / Multi",
        "color": "Black / Silver",
        "location": "North Surface Parking Lot P2, Near Row D",
        "custody": "Main Gate Security Gatehouse #1",
        "date_found": "2026-09-27",
        "question": "What other house or gym keys are attached to the split ring?",
    },

    # 4. Watches & Wearables
    {
        "filename": "apple_watch_ultra.jpg",
        "url": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=600&auto=format&fit=crop&q=80",
        "title": "Apple Watch Series 8 (45mm Space Gray with Sport Band)",
        "category": "watch",
        "brand": "Apple",
        "color": "Space Gray / Black",
        "location": "Tennis Courts, Bench 2",
        "custody": "Athletic Office Secure Safe",
        "date_found": "2026-09-25",
        "question": "What color is the silicone sport band and what watch face complication is displayed?",
    },
    {
        "filename": "casio_vintage_gold.jpg",
        "url": "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=600&auto=format&fit=crop&q=80",
        "title": "Casio Vintage Digital Watch (Gold-Tone Stainless Steel)",
        "category": "watch",
        "brand": "Casio",
        "color": "Gold Tone",
        "location": "Humanities Building, Stairwell Landing Floor 3",
        "custody": "Humanities Faculty Office",
        "date_found": "2026-09-23",
        "question": "Is the clasp adjusted to a small wrist size and is the hourly chime enabled?",
    },
    {
        "filename": "fossil_leather_watch.jpg",
        "url": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=600&auto=format&fit=crop&q=80",
        "title": "Fossil Grant Chronograph Leather Watch (Blue Dial / Brown Strap)",
        "category": "watch",
        "brand": "Fossil",
        "color": "Dark Brown / Navy Blue",
        "location": "Chemistry Lecture Hall 2, Row D",
        "custody": "Central Custody Office, Locker 14",
        "date_found": "2026-09-22",
        "question": "Describe the roman numeral markers and sub-dial arrangement.",
    },

    # 5. Water Bottles & Daily Accessories
    {
        "filename": "hydroflask_black_32.jpg",
        "url": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=600&auto=format&fit=crop&q=80",
        "title": "Hydro Flask 32 oz Wide Mouth Insulated Bottle (Matte Black)",
        "category": "bottle",
        "brand": "Hydro Flask",
        "color": "Matte Black",
        "location": "Science Library, Ground Floor Newspaper Reading Section",
        "custody": "Library Information Desk",
        "date_found": "2026-09-27",
        "question": "Are there any university or coffee brand stickers on the body?",
    },
    {
        "filename": "stanley_tumbler_cream.jpg",
        "url": "https://images.unsplash.com/photo-1589365278144-c9e705f843ba?w=600&auto=format&fit=crop&q=80",
        "title": "Stanley Quencher H2.0 FlowState Tumbler (40 oz Cream)",
        "category": "bottle",
        "brand": "Stanley",
        "color": "Cream / Rose Quartz",
        "location": "Management Studies Seminar Room 3",
        "custody": "Department Secretary Desk",
        "date_found": "2026-09-26",
        "question": "What color is the silicone handle insert and the reusable straw?",
    },
    {
        "filename": "yeti_rambler_teal.jpg",
        "url": "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?w=600&auto=format&fit=crop&q=80",
        "title": "YETI Rambler 26 oz Bottle with Chug Cap (Seafoam Teal)",
        "category": "bottle",
        "brand": "YETI",
        "color": "Seafoam Teal",
        "location": "Cricket Pavilion Grounds, North Steps",
        "custody": "Grounds Maintenance Custody Desk",
        "date_found": "2026-09-24",
        "question": "Describe any small scratch or engraved name on the bottom stainless rim.",
    },
    {
        "filename": "rayban_sunglasses.jpg",
        "url": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=600&auto=format&fit=crop&q=80",
        "title": "Ray-Ban Classic Wayfarer Sunglasses in Black Leather Case",
        "category": "other",
        "brand": "Ray-Ban",
        "color": "Glossy Black",
        "location": "North Campus Shuttle Bus Bay #3",
        "custody": "Transit Liaison Dispatch Office",
        "date_found": "2026-09-25",
        "question": "What color cleaning cloth or receipt was inside the snap case?",
    },
    {
        "filename": "compact_umbrella_black.jpg",
        "url": "https://images.unsplash.com/photo-1534353436294-0dbd4bdac845?w=600&auto=format&fit=crop&q=80",
        "title": "Windproof Compact Automatic Umbrella (Classic Black)",
        "category": "other",
        "brand": "Davek",
        "color": "Black",
        "location": "University Health Centre, Waiting Lobby",
        "custody": "Health Centre Reception Desk",
        "date_found": "2026-09-27",
        "question": "What brand logo is embossed on the wooden or rubberized handle?",
    }
]


def download_and_ingest_real_dataset():
    """Download authentic items, compute multimodal embeddings, and register in database."""
    print("Beginning download of real-world lost property dataset...")
    added_count = 0

    existing_filenames = {it.get("filename") for it in db.found_items if it.get("filename")}

    for item in REAL_ITEMS_METADATA:
        fn = item["filename"]
        local_path = os.path.join(REAL_ITEMS_DIR, fn)
        rel_path = os.path.relpath(local_path, BASE_DIR).replace("\\", "/")

        # 1. Download image if missing
        if not os.path.exists(local_path):
            print(f"Downloading authentic photograph: {fn}...")
            try:
                req = urllib.request.Request(
                    item["url"],
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )
                with urllib.request.urlopen(req, timeout=15) as resp, open(local_path, "wb") as f:
                    f.write(resp.read())
                time.sleep(0.3)
            except Exception as e:
                print(f"Warning: Failed to download {fn}: {e}")
                continue

        # 2. Extract embedding and add to database
        if fn not in existing_filenames or not any(it.get("filename") == fn and it.get("embedding") for it in db.found_items):
            print(f"Generating normalized visual features for: {item['title']}...")
            try:
                emb = ai_engine.extract_image_embedding(local_path)
                record = {
                    "id": f"FND-26{len(db.found_items)+10:03d}",
                    "title": item["title"],
                    "description": f"{item['title']}. Brand: {item['brand']}. Color: {item['color']}. Found at {item['location']}.",
                    "category": item["category"],
                    "brand": item["brand"],
                    "color": item["color"],
                    "location": item["location"],
                    "date_found": item["date_found"],
                    "filename": fn,
                    "image_path": rel_path,
                    "status": "Available",
                    "custody_location": item["custody"],
                    "verification_prompt": item["question"],
                    "embedding": emb.tolist()
                }
                db.found_items.insert(0, record)
                added_count += 1
            except Exception as e:
                print(f"Error embedding {fn}: {e}")

    db.save()
    print(f"\nReal dataset ingestion complete! Added {added_count} genuine items. Total items in custody: {len(db.found_items)}.")


if __name__ == "__main__":
    download_and_ingest_real_dataset()
