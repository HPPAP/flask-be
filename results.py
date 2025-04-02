from pymongo import MongoClient
from typing import List, Dict, Any
import certifi

ca = certifi.where()

# MongoDB Setup - using the same connection as search.py
MONGO_URI = "mongodb+srv://tripcredittracker:pOeTtv2PJCJyBqUz@tripcredittracker.0ymb8.mongodb.net/dev"

client = MongoClient(MONGO_URI, tlsCAFile=ca)
db = client["dev"]
collection = db["pages"]

def get_pages_by_ids(page_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch page data from MongoDB by page IDs
    
    Args:
        page_ids: List of page ID strings
        
    Returns:
        List of page documents
    """
    print(f"Fetching pages with IDs: {page_ids}")
    
    try:
        # Convert string IDs to ObjectId if necessary
        from bson.objectid import ObjectId
        object_ids = [ObjectId(page_id) for page_id in page_ids]
        
        # Query the database for pages with matching IDs
        results = list(collection.find({"_id": {"$in": object_ids}}))
        
        # Convert ObjectId to string for JSON response
        for doc in results:
            doc["_id"] = str(doc["_id"])
            
        print(f"Found {len(results)} pages")
        return results
    except Exception as e:
        print(f"Error fetching pages by IDs: {e}")
        return [] 