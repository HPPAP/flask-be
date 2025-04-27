from pymongo import MongoClient
from typing import List, Dict, Any, Optional
from bson.objectid import ObjectId
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

def get_adjacent_page(page_id: str, direction: str = "next") -> Optional[Dict[str, Any]]:
    """
    Get the adjacent page (previous or next) based on the current page's volume and page number
    
    Args:
        page_id: The ID of the current page
        direction: Either "next" or "previous"
        
    Returns:
        The adjacent page document or None if not found
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(page_id)
        
        # Get the current page to find its volume and page number
        current_page = collection.find_one({"_id": object_id})
        if not current_page:
            print(f"Error: Page with ID {page_id} not found")
            return None
            
        # Get the volume and page number
        volume = current_page.get("volume_id")
        page_number = current_page.get("page_number")
        
        if volume is None or page_number is None:
            print(f"Error: Missing volume or page number for page {page_id}")
            return None
            
        # Build the query for the adjacent page
        if direction == "next":
            # Get the next page in the same volume
            query = {
                "volume_id": volume,
                "page_number": {"$gt": page_number}
            }
            sort_order = 1  # Ascending for next page
        else:
            # Get the previous page in the same volume
            query = {
                "volume_id": volume,
                "page_number": {"$lt": page_number}
            }
            sort_order = -1  # Descending for previous page
            
        # Find the adjacent page
        adjacent_page = collection.find_one(
            query,
            sort=[("page_number", sort_order)]
        )
        
        # If there's no next/previous page in the same volume
        if not adjacent_page:
            print(f"No {direction} page found in volume {volume}")
            
            # Try to find the adjacent volume
            if direction == "next":
                next_volume = collection.find_one(
                    {"volume_id": {"$gt": volume}},
                    sort=[("volume_id", 1)]
                )
                if next_volume:
                    # Get the first page of the next volume
                    adjacent_page = collection.find_one(
                        {"volume_id": next_volume["volume_id"]},
                        sort=[("page_number", 1)]
                    )
            else:
                prev_volume = collection.find_one(
                    {"volume_id": {"$lt": volume}},
                    sort=[("volume_id", -1)]
                )
                if prev_volume:
                    # Get the last page of the previous volume
                    adjacent_page = collection.find_one(
                        {"volume_id": prev_volume["volume_id"]},
                        sort=[("page_number", -1)]
                    )
        
        if adjacent_page:
            # Convert ObjectId to string for JSON response
            adjacent_page["_id"] = str(adjacent_page["_id"])
            return adjacent_page
            
        return None
        
    except Exception as e:
        print(f"Error getting adjacent page: {e}")
        return None 