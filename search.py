from dotenv import load_dotenv
import os
# Load environment variables from the .env file
from pymongo import MongoClient
from typing import List, Optional, Union
import certifi
import re

load_dotenv()
ca = certifi.where()

# MongoDB Setup
# MONGO_URI = os.environ["MONGO"]
MONGO_URI = "mongodb+srv://tripcredittracker:pOeTtv2PJCJyBqUz@tripcredittracker.0ymb8.mongodb.net/dev"
client = MongoClient(MONGO_URI, tlsCAFile=ca)
db = client["dev"]
collection = db["pages"]

# Ensure full-text search index is created [WTF IS THIS?]
# collection.create_index([("raw_text", "text")])

def extract_years(volume_title):
    """Extracts a list of all years in a volume title."""
    
    # Look for multiple year patterns in the title
    all_years = []
    
    # Pattern for range formats: 1640-42, 1640-1642, 1640/42
    range_patterns = [
        r"(\d{4})[-/](\d{2})",  # Like 1640-42
        r"(\d{4})[-/](\d{4})",  # Like 1640-1642
    ]
    
    # Try each pattern
    for pattern in range_patterns:
        for match in re.finditer(pattern, volume_title):
            start_year = int(match.group(1))
            end_suffix = match.group(2)
            
            if len(end_suffix) == 2:
                end_year = int(str(start_year)[:2] + end_suffix)
            else:
                end_year = int(end_suffix)
                
            # Add all years in the range
            all_years.extend(list(range(start_year, end_year + 1)))
    
    # Also look for standalone years
    for match in re.finditer(r"\b(\d{4})\b", volume_title):
        all_years.append(int(match.group(1)))
    
    # Return unique sorted years    
    return sorted(list(set(all_years)))

def search_journals(
    volume: List[str] = None,
    page_numbers: List[str] = None,
    dates: List[str] = None,
    topics: List[str] = None,
    keywords: List[str] = None,
    year: Optional[Union[str, int]] = None
) -> dict:
    """Search journals based on provided filters"""
    # Print filters for debugging
    print("=== Search Filters ===")
    print(f"Topics: {topics}")
    print(f"Keywords: {keywords}")
    print(f"Year: {year}")
    print("=====================")
    
    # Build the base query (non-year filters)
    query = {}  # Empty query will match all documents in MongoDB

    # Filter by volume
    if volume and volume[0]:  # Check if list is not empty
        query["volume_id"] = volume[0]  # Take first volume ID from the list

    # Filter by page numbers (convert strings to integers)
    if page_numbers and page_numbers[0]:
        try:
            page_nums = [int(p) for p in page_numbers]
            if len(page_nums) == 2:  # If exactly 2 numbers, treat as a range
                query["page_number"] = {"$gte": page_nums[0], "$lte": page_nums[1]}
            else:
                query["page_number"] = {"$in": page_nums}
        except ValueError:
            pass  # Handle invalid number formats gracefully

    # Filter by date
    if dates and dates[0]:
        if len(dates) == 2:  # If exactly 2 dates, treat as a range
            start_date, end_date = dates
            if start_date == end_date:  # Exact date match
                query["dates"] = start_date
            else:
                query["dates"] = {"$gte": start_date, "$lte": end_date}
        else:
            # Single date or multiple specific dates
            query["dates"] = {"$in": dates}

    # Filter by topics
    if topics and topics[0]:
        query["topics"] = {"$all": topics}  # Ensures all topics exist in the document

    # Full-text search for keywords
    if keywords and keywords[0]:
        query["$text"] = {"$search": " ".join(keywords)}
    
    try:
        results = []
        total_count = 0
        
        # If year filter is provided, search for it
        if year is not None:
            # Convert to string if an integer was passed
            year = str(year)
            print(f"Searching for year: {year}")
            
            base_query = query.copy()
            
            # APPROACH 1: EXACT MATCH SEARCH
            # This is the recommended approach for dropdown-selected values
            # When a year or range is selected from the dropdown, search for exact matches
            # in volume_title
            exact_query = base_query.copy()
            exact_query["volume_title"] = {"$regex": f"\\b{re.escape(year)}\\b", "$options": "i"}
            
            exact_cursor = collection.find(exact_query)
            exact_results = list(exact_cursor)
            
            if exact_results:
                print(f"Found {len(exact_results)} documents with exact match for '{year}'")
                for doc in exact_results:
                    doc["_id"] = str(doc["_id"])
                
                return {
                    "count": len(exact_results),
                    "results": exact_results
                }
            
            print(f"No exact matches found for '{year}', trying alternative search methods")
            
            # APPROACH 2: DECOMPOSE RANGE AND SEARCH BY INDIVIDUAL YEARS
            # Only used as a fallback if exact match fails
            year_range = []
            
            # Check for range patterns like 1640-42 or 1640-1642
            range_match = re.match(r"(\d{4})[-/](\d{2}|\d{4})", year)
            if range_match:
                start_year = int(range_match.group(1))
                end_suffix = range_match.group(2)
                
                if len(end_suffix) == 2:
                    # Handle shortened range format (1640-42)
                    # Use the century from the start year
                    century = start_year // 100
                    end_year = (century * 100) + int(end_suffix)
                    
                    # If this makes end_year less than start_year, assume we went to the next century
                    if end_year < start_year:
                        end_year += 100
                else:
                    # Handle full year range format (1640-1642)
                    end_year = int(end_suffix)
                
                # Make sure range is in chronological order
                if end_year < start_year:
                    print(f"Warning: Unusual year range {start_year}-{end_year}. Using as-is.")
                    # Don't swap - trust the database format
                
                # Create the range of years to search for
                year_range = list(range(start_year, end_year + 1))

            else:
                # Try to convert to a single year
                try:
                    year_range = [int(year)]

                except ValueError:
                    year_range = []
                    print(f"Warning: Could not parse '{year}' as a year.")
            
            # Now try to find documents that might contain any year in the range
            if year_range:
                broader_query = base_query.copy()
                # Use the first 2 digits of the year for a broader search
                year_prefix = year[:2] if len(year) >= 2 else year
                broader_query["volume_title"] = {"$regex": year_prefix, "$options": "i"}
                
                broader_cursor = collection.find(broader_query)
                
                for doc in broader_cursor:
                    volume_title = doc.get("volume_title", "")
                    extracted_years = extract_years(volume_title)
                    
                    # Check if any year in our range appears in the extracted years
                    if extracted_years and any(y in extracted_years for y in year_range):
                        doc["_id"] = str(doc["_id"])
                        results.append(doc)
            
            total_count = len(results)
            print(f"After broader search: {total_count} documents match")
            
        else:
            # If no year filter, use normal MongoDB query
            total_count = collection.count_documents(query)
            cursor = collection.find(query)
            
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                results.append(doc)

        return {
            "count": total_count,
            "results": results
        }
    except Exception as e:
        import traceback
        print(f"Database error: {e}")
        print(traceback.format_exc())
        return {
            "count": 0,
            "results": []
        }

def test_query(limit: int = 100) -> List[dict]:
    """Test function that searches for the keyword 'a' in text.
    
    This tests if the full-text search is working properly with a common keyword.
    
    Args:
        limit: Maximum number of documents to return (default: 100)
        
    Returns:
        List of journal documents containing the letter 'a'
    """
    print("Testing search with keyword 'a'")
    try:
        # Print all indexes to see what's available
        print("=== Text Indexes Available ===")
        for idx in collection.list_indexes():
            if 'textIndexVersion' in idx:
                print(f"Using text index: {idx}")
                # Extract the field being indexed from the weights
                if 'weights' in idx:
                    print(f"Fields being indexed: {list(idx['weights'].keys())}")
        print("=============================")
        
        # First, check if there are any documents at all
        total_docs = collection.count_documents({})
        print(f"Total documents in collection: {total_docs}")
        
        # Check the first document to see what fields it has
        if total_docs > 0:
            first_doc = collection.find_one({})
            print("Fields in first document:")
            for key in first_doc.keys():
                print(f"  - {key}")
            
            # Check if 'text' field exists and what it contains
            if 'text' in first_doc:
                text_sample = first_doc['text']
                if isinstance(text_sample, str):
                    print(f"Text field sample (first 100 chars): {text_sample[:100]}...")
                else:
                    print(f"Text field is not a string, it's: {type(text_sample)}")
            else:
                print("Warning: 'text' field not found in document!")
        
        # Hardcoded query to search for 'a' in the text
        query = {"$text": {"$search": "tax"}}
        print(f"Executing text search query: {query}")
        
        results = list(collection.find(query).limit(limit))
        
        # Convert ObjectId to string for JSON response
        for doc in results:
            doc["_id"] = str(doc["_id"])
        return results
    except Exception as e:
        print(f"Database error: {e}")
        return []

# Debug: Check all volume titles in the database
def debug_volume_titles():
    """Print all unique volume titles from the database"""
    titles = collection.distinct("volume_title")
    print(f"Found {len(titles)} unique volume titles:")
    for i, title in enumerate(titles):
        print(f"{i+1}. '{title}' => Years: {extract_years(title)}")
    return titles

# Add this line at the very end of your file to run it once
# debug_volume_titles()

# Debug: Find ALL volumes in the database and analyze them
def debug_all_volumes():
    """Print all unique volume titles and years in the database"""
    print("\n=== DEBUGGING ALL VOLUMES ===")
    titles = collection.distinct("volume_title")
    print(f"Found {len(titles)} unique volume titles:")
    
    # Index for all possible years mentioned in the database
    all_years = {}
    
    for title in titles:
        years = extract_years(title)
        print(f"Volume: '{title}' => Years: {years}")
        
        # Index years to volumes
        for year in years:
            if year not in all_years:
                all_years[year] = []
            all_years[year].append(title)
    
    # Print all years and which volumes contain them
    print("\n=== YEARS IN DATABASE ===")
    for year in sorted(all_years.keys()):
        volumes = all_years[year]
        print(f"Year {year} found in {len(volumes)} volumes: {volumes[:3]}")

def get_all_years():
    """
    Returns information about years available in the database
    including both individual years and the original ranges.
    """
    try:
        # Get all unique volume titles
        titles = collection.distinct("volume_title")
        
        # Extract both individual years and original ranges
        year_data = {
            "years": set(),        # Individual years
            "ranges": set()        # Original year ranges from volume titles
        }
        
        # Regular expressions to find year ranges
        range_patterns = [
            r"(\d{4})[-/](\d{2})",    # Like 1640-42
            r"(\d{4})[-/](\d{4})",    # Like 1640-1642
        ]
        
        for title in titles:
            # Add individual years
            years = extract_years(title)
            year_data["years"].update(years)
            
            # Extract original range formats
            for pattern in range_patterns:
                for match in re.finditer(pattern, title):
                    original_range = match.group(0)  # Get the original range text
                    year_data["ranges"].add(original_range)
            
            # Also add standalone years as ranges
            for match in re.finditer(r"\b(\d{4})\b", title):
                # Only add if it's not part of a range we already captured
                year = match.group(0)
                already_in_range = False
                
                for range_text in year_data["ranges"]:
                    if year in range_text:
                        already_in_range = True
                        break
                
                if not already_in_range:
                    year_data["ranges"].add(year)
        
        # Return sorted data
        return {
            "years": sorted(list(year_data["years"])),
            "ranges": sorted(list(year_data["ranges"]))
        }
    except Exception as e:
        print(f"Error retrieving years: {e}")
        return {"years": [], "ranges": []}
