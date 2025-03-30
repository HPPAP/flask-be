from dotenv import load_dotenv
import os

# Load environment variables from the .env file


from pymongo import MongoClient
from typing import List, Optional
import certifi

load_dotenv()
ca = certifi.where()

# MongoDB Setup
MONGO_URI = os.environ["MONGO"]
client = MongoClient(MONGO_URI, tlsCAFile=ca)
db = client["dev"]
collection = db["pages"]

# Ensure full-text search index is created [WTF IS THIS?]
# collection.create_index([("raw_text", "text")])


def search_journals(
    volume: List[str] = None,
    page_numbers: List[str] = None,
    dates: List[str] = None,
    topics: List[str] = None,
    keywords: List[str] = None,
    limit: int = 20,
) -> List[dict]:
    """Search journals based on provided filters"""

    query = {}

    # Filter by volume
    if volume and volume[0]:  # Check if list is not empty
        query["volume_id"] = {"$in": volume}

    # Filter by page numbers (convert strings to integers)
    if page_numbers and page_numbers[0]:
        try:
            page_nums = [int(p) for p in page_numbers]
            query["page_number"] = {"$in": page_nums}
        except ValueError:
            pass  # Handle invalid number formats gracefully

    # Filter by date
    if dates and dates[0]:
        # Assuming dates are provided in correct format
        query["dates"] = {"$in": dates}

    # Filter by topics
    if topics and topics[0]:
        query["topics"] = {"$all": topics}

    # Full-text search for keywords
    if keywords and keywords[0]:
        query["$text"] = {"$search": " ".join(keywords)}

    try:
        results = list(collection.find(query).limit(limit))
        # Convert ObjectId to string for JSON response
        for doc in results:
            doc["_id"] = str(doc["_id"])
        return results
    except Exception as e:
        print(f"Database error: {e}")
        return []
