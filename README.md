# 🔎 AI Lost & Found Matcher

An AI-powered Lost & Found system that uses computer vision and semantic similarity to identify potentially matching lost and found items.

## 🎯 Problem Statement

In colleges, universities, offices, airports, and public places, many lost items are collected but matching them with their owners is difficult.

Traditional Lost & Found systems mainly depend on manual searching, item descriptions, and category-based filtering.

This project uses Artificial Intelligence to automatically compare a user's lost-item image with registered found items and rank the most visually similar results.

---

## 💡 Proposed Solution

The system allows a user to:

1. Upload an image of a lost item.
2. Enter a description of the item.
3. Provide location information.
4. Search the registered found-item database.
5. Receive the most visually similar items ranked by AI.

The system uses **CLIP (Contrastive Language–Image Pre-training)** to generate image embeddings and calculate similarity between the uploaded item and registered items.

---

## 🤖 AI Technology

### CLIP

The project uses:

**OpenAI CLIP — ViT-B/32**

CLIP converts images into numerical embedding vectors.

The system compares these embeddings using cosine similarity.

### Matching Pipeline

```text
Lost Item Image
       ↓
Image Preprocessing
       ↓
CLIP Vision Encoder
       ↓
Image Embedding
       ↓
Cosine Similarity
       ↓
Compare with Found Items
       ↓
Rank Results
       ↓
Top Matching Items