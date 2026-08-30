# seed.py
import json
import os

from google import genai
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector

# Connect to Firestore
db = firestore.Client(database="coffee-menu")

# Connect to Gemini
client = genai.Client(
    vertexai=True,
    project=os.environ.get("PROJECT_ID"),
    location=os.environ.get("REGION", "us-central1")
)

# Load the local menu
with open("menu.json", "r") as f:
    menu_items = json.load(f)

# Generate embeddings and upload each menu item
for item in menu_items:
    # Use the name as the document ID
    doc_id = item["name"].lower().replace(" ", "-")

    # Text that will be converted into a vector
    text_to_embed = f"{item['name']}: {item['description']}"

    response = client.models.embed_content(
        model="text-embedding-005",
        contents=text_to_embed,
    )

    embedding = response.embeddings[0].values

    # Add the vector to the Firestore document
    item["embedding"] = Vector(embedding)

    db.collection("menu").document(doc_id).set(item)

print("Firestore menu collection seeded with vector embeddings successfully!")