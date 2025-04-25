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
pages_collection = db["pages"]


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
            if data[attribute] is not None:
                update[attribute] = data[attribute]
        except:
            pass

    result = projects_collection.update_one(
        {"_id": ObjectId(data["_id"])},  # Filter
        {"$set": update},  # Update operation
        upsert=True,  # Insert if not found
    )


def get_project(data):
    p = projects_collection.find_one({"_id": ObjectId(data["_id"])})

    print(p["pages"])

    object_ids = [ObjectId(id_) for id_ in p["pages"]]

    print(object_ids)
    docs_cursor = pages_collection.find({"_id": {"$in": object_ids}})

    docs = list(docs_cursor)

    p["page_docs"] = list(
        map(
            lambda doc: {
                "_id": str(doc["_id"]),
                "page_number": str(doc["page_number"]),
                "volume_title": str(doc["volume_title"]),
                "text": doc["text"][:40],
            },
            docs,
        )
    )

    p["_id"] = str(p["_id"])

    return p


# added create project
def create_project():
    doc = projects_collection.insert_one({"title": "", "description": "", "pages": []})
    return {"_id": str(doc.inserted_id), "title": "", "description": "", "pages": []}


# added delete project
def delete_project(project_id: str) -> bool:
    result = projects_collection.delete_one({"_id": ObjectId(project_id)})
    return result.deleted_count == 1


def get_page(data):
    print(data)
    p = pages_collection.find_one({"_id": ObjectId(data["_id"])})
    p["_id"] = str(p["_id"])
    return p
