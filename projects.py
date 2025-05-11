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
# db = client["dev"]
db = client["test"]

projects_collection = db["projects"]
pages_collection = db["pages"]


def get_all_projects():
    projects = list(projects_collection.find())
    for p in projects:
        p["_id"] = str(p["_id"])
    return projects


def update_project(data):
    update = {}
    attributes = [
        "title", 
        "description", 
        "pages", 
        "page_keywords",
        "page_metadata"  # Add project-specific page metadata
    ]

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

    # Add keywords to the page docs if available
    page_keywords = p.get("page_keywords", {})
    
    # Add project-specific page metadata if available
    page_metadata = p.get("page_metadata", {})

    p["page_docs"] = list(
        map(
            lambda doc: {
                "_id": str(doc["_id"]),
                "page_number": str(doc["page_number"]),
                "volume_title": str(doc["volume_title"]),
                "text": doc["text"][:40],
                "keywords": page_keywords.get(str(doc["_id"]), ""),
                # Include universal metadata from the page document
                "date": doc.get("date", None),
                "topics": doc.get("topics", []),
                # Include project-specific metadata for this page
                "project_metadata": page_metadata.get(str(doc["_id"]), {})
            },
            docs,
        )
    )

    p["_id"] = str(p["_id"])

    return p


# added create project
def create_project():
    doc = projects_collection.insert_one({
        "title": "", 
        "description": "", 
        "pages": [], 
        "page_keywords": {},
        "page_metadata": {}  # Add project-specific page metadata
    })
    return {
        "_id": str(doc.inserted_id), 
        "title": "", 
        "description": "", 
        "pages": [], 
        "page_keywords": {},
        "page_metadata": {}
    }


# added delete project
def delete_project(project_id: str) -> bool:
    result = projects_collection.delete_one({"_id": ObjectId(project_id)})
    return result.deleted_count == 1


def get_page(data):
    print(data)
    p = pages_collection.find_one({"_id": ObjectId(data["_id"])})
    p["_id"] = str(p["_id"])
    return p


# Add function to update universal page metadata
def update_page_metadata(page_id, metadata):
    """
    Update universal metadata for a page (date, topics)
    
    Args:
        page_id: ID of the page to update
        metadata: Dictionary containing date and/or topics
    
    Returns:
        True if successful, False otherwise
    """
    try:
        update = {}
        
        if "date" in metadata:
            update["date"] = metadata["date"]
            
        if "topics" in metadata:
            update["topics"] = metadata["topics"]
        
        if not update:
            return False
            
        result = pages_collection.update_one(
            {"_id": ObjectId(page_id)},
            {"$set": update}
        )
        
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating page metadata: {e}")
        return False


# Add function to update project-specific page metadata
def update_project_page_metadata(project_id, page_id, metadata):
    """
    Update project-specific metadata for a page (passages, notes)
    
    Args:
        project_id: ID of the project
        page_id: ID of the page
        metadata: Dictionary containing passages, page_notes, and/or passage_notes
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Validate inputs
        if not project_id or not page_id or not metadata:
            print(f"Invalid input: project_id={project_id}, page_id={page_id}, has_metadata={metadata is not None}")
            return False
            
        # Convert IDs to strings if they're not already
        project_id = str(project_id)
        page_id = str(page_id)
        
        print(f"Updating metadata for project {project_id}, page {page_id}")
        
        # First get the current project
        project = projects_collection.find_one({"_id": ObjectId(project_id)})
        if not project:
            print(f"Project not found with ID: {project_id}")
            return False
            
        # Get or initialize page_metadata (ensure it's a dictionary)
        page_metadata = project.get("page_metadata", {})
        if not isinstance(page_metadata, dict):
            page_metadata = {}
            
        # Get or initialize metadata for this specific page (ensure it's a dictionary)
        page_specific_metadata = page_metadata.get(page_id, {})
        if not isinstance(page_specific_metadata, dict):
            page_specific_metadata = {}
        
        # Update with new metadata, preserving existing metadata
        if "passages" in metadata:
            try:
                # Ensure passages is a list
                if not isinstance(metadata["passages"], list):
                    print(f"Warning: passages is not a list, it's a {type(metadata['passages'])}")
                    passages_list = []
                else:
                    passages_list = metadata["passages"]
                
                # Ensure each passage has properly formatted data
                cleaned_passages = []
                for passage in passages_list:
                    try:
                        if not isinstance(passage, dict):
                            print(f"Warning: passage is not a dict, it's a {type(passage)}")
                            continue
                            
                        if "text" not in passage:
                            print(f"Warning: passage missing text field: {passage}")
                            continue
                            
                        # Ensure each passage has the required fields with correct types
                        cleaned_passage = {
                            "id": str(passage.get("id", "")),
                            "text": str(passage.get("text", "")),
                            "start": int(passage.get("start", 0)) if passage.get("start") is not None else 0,
                            "end": int(passage.get("end", 0)) if passage.get("end") is not None else 0
                        }
                        cleaned_passages.append(cleaned_passage)
                    except Exception as e:
                        print(f"Error processing passage: {e}")
                        continue
                
                page_specific_metadata["passages"] = cleaned_passages
                print(f"Processed {len(cleaned_passages)} passages")
            except Exception as e:
                print(f"Error processing passages: {e}")
                import traceback
                traceback.print_exc()
            
        if "page_notes" in metadata:
            try:
                page_specific_metadata["page_notes"] = str(metadata["page_notes"] or "")
            except Exception as e:
                print(f"Error processing page_notes: {e}")
                page_specific_metadata["page_notes"] = ""
            
        if "passage_notes" in metadata:
            try:
                # Ensure passage_notes has string keys and values
                if not isinstance(metadata["passage_notes"], dict):
                    print(f"Warning: passage_notes is not a dict, it's a {type(metadata['passage_notes'])}")
                    cleaned_notes = {}
                else:
                    cleaned_notes = {}
                    for key, value in metadata["passage_notes"].items():
                        try:
                            str_key = str(key)
                            str_value = str(value or "")
                            cleaned_notes[str_key] = str_value
                        except Exception as e:
                            print(f"Error processing passage note with key {key}: {e}")
                
                page_specific_metadata["passage_notes"] = cleaned_notes
                print(f"Processed {len(cleaned_notes)} passage notes")
            except Exception as e:
                print(f"Error processing passage_notes: {e}")
                import traceback
                traceback.print_exc()
                page_specific_metadata["passage_notes"] = {}
        
        # Update the metadata for this page
        page_metadata[page_id] = page_specific_metadata
        
        # Update the project with the new metadata
        try:
            result = projects_collection.update_one(
                {"_id": ObjectId(project_id)},
                {"$set": {"page_metadata": page_metadata}}
            )
            success = result.modified_count > 0 or result.matched_count > 0
            print(f"Update result: modified={result.modified_count}, matched={result.matched_count}, success={success}")
            return success
        except Exception as e:
            print(f"Error updating project document: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"Error updating project page metadata: {e}")
        # Print more detailed error info for debugging
        import traceback
        traceback.print_exc()
        return False


def get_project_data_for_export(project_id):
    """
    Get all project data including page metadata for CSV export
    
    Args:
        project_id: ID of the project
    
    Returns:
        Dictionary with project and page data including all metadata
    """
    try:
        print(f"Retrieving project data for export, project_id: {project_id}")
        
        # Get the project document
        project = projects_collection.find_one({"_id": ObjectId(project_id)})
        if not project:
            print(f"Project not found with ID: {project_id}")
            return None
            
        # Get the page IDs from the project
        page_ids = project.get("pages", [])
        if not page_ids:
            print(f"No pages found in project: {project_id}")
            return {"project_title": project.get("title", ""), "project_description": project.get("description", ""), "pages": []}
            
        # Convert page IDs to ObjectIds
        print(f"Found {len(page_ids)} pages in project")
        object_ids = [ObjectId(id_) for id_ in page_ids]
        
        # Get all page documents
        pages = list(pages_collection.find({"_id": {"$in": object_ids}}))
        
        # Verify we found all pages
        if len(pages) != len(page_ids):
            print(f"Warning: Found {len(pages)} pages out of {len(page_ids)} requested")
        
        # Get project's page_keywords and page_metadata
        page_keywords = project.get("page_keywords", {})
        page_metadata = project.get("page_metadata", {})
        
        # Prepare data structure for export
        export_data = []
        for page in pages:
            page_id = str(page["_id"])
            
            # Get page metadata (both universal and project-specific)
            metadata = {
                "page_id": page_id,
                "volume_title": page.get("volume_title", ""),
                "page_number": str(page.get("page_number", "")),
                "date": page.get("date", ""),
                "topics": page.get("topics", []),
                "text": page.get("text", ""),
                "keywords": page_keywords.get(page_id, ""),
            }
            
            # Add project-specific metadata if available
            if page_id in page_metadata:
                project_meta = page_metadata[page_id]
                metadata["page_notes"] = project_meta.get("page_notes", "")
                metadata["passages"] = project_meta.get("passages", [])
                metadata["passage_notes"] = project_meta.get("passage_notes", {})
            else:
                metadata["page_notes"] = ""
                metadata["passages"] = []
                metadata["passage_notes"] = {}
            
            export_data.append(metadata)
            
        # Sort by volume_title and page_number
        export_data.sort(key=lambda x: (x["volume_title"], int(x["page_number"]) if x["page_number"].isdigit() else 0))
        
        print(f"Successfully prepared export data with {len(export_data)} pages")
        
        return {
            "project_title": project.get("title", ""),
            "project_description": project.get("description", ""),
            "pages": export_data
        }
        
    except Exception as e:
        print(f"Error getting project data for export: {e}")
        # Print stack trace
        import traceback
        traceback.print_exc()
        return None
