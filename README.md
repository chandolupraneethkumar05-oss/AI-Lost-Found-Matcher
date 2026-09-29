# 🔎 FindSphere — Campus & Transit AI Lost & Found Recovery Network

[![FastAPI](https://img.shields.io/badge/FastAPI-0.141.1-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.61.1-FF4B4B.svg?style=flat&logo=streamlit)](https://streamlit.io)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.13.0-EE4C2C.svg?style=flat&logo=pytorch)](https://pytorch.org)
[![CLIP](https://img.shields.io/badge/Model-OpenAI%20CLIP%20ViT--B%2F32-blue.svg)](https://github.com/openai/CLIP)

An intelligent, production-ready Lost & Found recovery platform designed for universities, transit authorities, airports, and corporate complexes. Utilizing **OpenAI CLIP multimodal vision embeddings** and **multi-criteria hybrid scoring**, FindSphere automatically connects lost valuables with verified owners while preventing fraudulent claims.

---

## 🏛️ Real-World Problem & Solution

In colleges, hospitals, transit terminals, and public venues, thousands of lost items are deposited into security lockers each month. Traditional recovery workflows fail because:
- **Manual logbooks** are difficult to search by physical appearance.
- **Text descriptions are subjective** (one person says *"dark grey pouch"*, another says *"black pencil case"*).
- **Public registries risk theft**: anyone can see lost items and fraudulently claim them without proof.

### The FindSphere Solution:
1. **Multimodal Visual Matching**: Upload an image or enter a natural language description. CLIP extracts a 512-dimensional semantic vector and ranks candidate items by visual and semantic similarity.
2. **Anti-Theft Verification Protocol**: High-value hallmarks (serial numbers, engravings, lockscreen images, interior pocket contents) are hidden from the public. Claimants must answer an encrypted verification prompt before custody release is authorized.
3. **Automated Reverse-Match Listener**: When a security officer registers a newly found item, the system automatically cross-references all open lost reports and dispatches alert notifications to potential owners.
4. **Dual Interface**:
   - **Weblium-Style Web Portal**: Clean, human-crafted responsive web interface with zero AI clichés.
   - **Streamlit Command Studio**: Interactive dashboard for custody desk staff and security administrators.

---

## 📊 System Architecture

```mermaid
flowchart TD
    subgraph Intake["1. Ingestion Layer"]
        A1[User Upload: Photo / Description]
        A2[Custody Officer: Found Item Intake]
    end

    subgraph AI["2. Multimodal AI Engine"]
        B1[Orientation & Contrast Normalizer]
        B2[CLIP Vision Encoder ViT-B/32]
        B3[CLIP Text Encoder]
        B4[Normalized 512-D Vector]
    end

    subgraph Search["3. Multi-Criteria Hybrid Scoring"]
        C1[Cosine Visual Similarity]
        C2[Calibrated Text Similarity]
        C3[Category Exactness Match]
        C4[Location & Zone Proximity]
        C5[Hybrid Confidence Score 0-100%]
    end

    subgraph Custody["4. Verification & Custody Protocol"]
        D1[Locker & Safe Box Tracking]
        D2[Anti-Theft Ownership Proof]
        D3[Officer Approval & Handover Receipt]
    end

    A1 --> B1 --> B2 --> B4
    A1 --> B3 --> B4
    A2 --> B1 --> B2 --> B4
    B4 --> C1 & C2
    C1 & C2 & C3 & C4 --> C5
    C5 --> D2 --> D3
```

---

## 🗄️ Curated Dataset & Scaling Strategy

The platform includes a pre-cataloged dataset of **28+ real-world items** stored in `data/` across five high-frequency lost categories:

| Category | Example Brands & Items | Typical Custody Locations |
| :--- | :--- | :--- |
| **Backpacks & Bags** | Herschel Classic, JanSport SuperBreak, SwissGear, Nike Brasilia | Library Quiet Rooms, Lecture Halls, Transit Hub |
| **Phones & Electronics** | iPhone 14 Pro, Samsung Galaxy S23, Google Pixel 8 | Cafeteria Register, Study Desks, Labs |
| **Wallets & Cards** | Bellroy Bi-Fold, Fossil RFID, Ridge Aluminum, Tommy Hilfiger | ATM Kiosks, Dining Halls, Parking Stands |
| **Watches & Wearables** | Apple Watch Series 8, Casio Vintage Illuminator, Fossil Grant | Gymnasiums, Sports Arenas, Music Rooms |
| **Bottles & Thermoses** | Hydro Flask 32oz, Stanley Quencher 40oz, YETI Rambler | Science Labs, Workshop Desks, Auditoriums |

### Recommended Real-World Open Datasets for Scaling:
- **Stanford Online Products (SOP)**: ~120k product images for fine-grained retrieval benchmarking.
- **Amazon Berkeley Objects (ABO)**: ~150k multi-angle product photographs with structured catalog metadata.
- **COCO (Common Objects in Context)**: 80 common object classes for bounding-box detection and auto-cropping.

---

## 🚀 Quickstart Guide

### 1. Installation
Clone the repository and install requirements:
```bash
git clone https://github.com/chandolupraneethkumar05-oss/AI-Lost-Found-Matcher.git
cd AI-Lost-Found-Matcher

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # On Windows
source venv/bin/activate  # On Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch the Weblium-Inspired Web Portal (Recommended)
```bash
python server.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

### 3. Or Launch the Streamlit Admin Studio
```bash
streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

---

## 🌐 REST API Endpoints

The FastAPI backend (`server.py`) provides full REST API capabilities:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/match` | Upload image and/or text to perform hybrid multimodal search |
| `GET` | `/api/items` | Retrieve filterable catalog items (`category`, `location`, `search`) |
| `GET` | `/api/items/{id}` | Retrieve specific item metadata |
| `POST` | `/api/report-found` | Intake found item, compute embedding, check reverse lost matches |
| `POST` | `/api/report-lost` | File lost inquiry and scan existing custody inventory |
| `POST` | `/api/claim` | Submit ownership claim with anti-theft verification proof |
| `GET` | `/api/claims` | List submitted claims for custody officer review |
| `POST` | `/api/claims/{id}/verify` | Approve or reject claim and issue handover status |
| `GET` | `/api/stats` | Live system statistics (recovery rate, custody count, avg time) |

---

## 🔒 Anti-Theft Verification Protocol

To prevent fraudulent claims:
1. Public listings display the item photograph and general location, but **omit specific unique identifiers** (serial number digits, internal pocket contents, lockscreen wallpaper).
2. When claiming an item, the user must answer a specific **Verification Prompt**.
3. A campus custody officer cross-checks the claimant's answer against the physical item or sealed note before handing over the valuable.

---

## 📁 Repository Structure

```
AI_Lost_Found/
├── app.py                      # Modernized Streamlit Command Studio
├── server.py                   # Production FastAPI server & REST API
├── requirements.txt            # Project dependencies
├── README.md                   # Comprehensive documentation
├── data/
│   ├── database.json           # Centralized database (items, reports, claims)
│   ├── found_items/            # Categorized catalog image directory
│   ├── registered_items/       # Newly registered custody uploads
│   └── test_images/            # Reference testing images
├── models/
│   └── image_embeddings.pkl    # Precomputed CLIP feature vectors
├── src/
│   ├── ai_engine.py            # Multimodal CLIP matching & hybrid scoring
│   ├── database.py             # Database persistence & claim management
│   ├── dataset_catalog.py      # Dataset ingestion & embedding precomputation
│   ├── embeddings.py           # Legacy embedding compatibility module
│   └── matcher.py              # Legacy matcher compatibility module
└── static/
    ├── index.html              # Weblium-style institutional web portal
    ├── style.css               # Classic slate/navy styling system
    └── app.js                  # Dynamic client-side controller
```

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).