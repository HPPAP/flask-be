from dotenv import load_dotenv

load_dotenv()

import os
from pymongo import MongoClient
import certifi

ca = certifi.where()

# MongoDB Setup
MONGO_URI = os.environ["MONGO"]
client = MongoClient(MONGO_URI, tlsCAFile=ca)
db = client["dev"]

projects_collection = db["projects"]


def get_all_projects():
    projects = list(projects_collection.find())
    for p in projects:
        p["_id"] = str(p["_id"])
    return projects


def update_project(data):
    projects_collection.update_one(
        {"title": data["title"]},  # Filter
        {
            "$set": {
                "description": data["description"],
                "volumes": data["volumes"],
                "pages": data["pages"],
            }
        },  # Update operation
        upsert=True,  # Insert if not found
    )
    pass
