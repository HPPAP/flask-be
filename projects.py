from dotenv import load_dotenv

load_dotenv()

import os
from pymongo import MongoClient
import certifi
from bson.objectid import ObjectId

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
    update = {}

    attributes = ["title", "description", "pages"]
    for attribute in attributes:
        try:
            if data[attribute]:
                update[attribute] = data[attribute]
        except:
            pass

    result = projects_collection.update_one(
        {"_id": ObjectId(data["id"])},  # Filter
        {"$set": update},  # Update operation
        upsert=True,  # Insert if not found
    )
    print(result)


def get_project(data):
    p = projects_collection.find_one({"_id": ObjectId(data["id"])})
    p["_id"] = str(p["_id"])
    return p


# added create project
def create_project():
    doc = projects_collection.insert_one({"title": "", "description": "", "pages": []})
    return {"_id": str(doc.inserted_id), "title": "", "description": "", "pages": []}
