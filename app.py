from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from search import search_journals, test_query, get_all_years
from results import get_pages_by_ids, get_adjacent_page
from projects import (
    get_all_projects,
    update_project,
    get_project,
    create_project,
    delete_project,
    get_page,
    update_page_metadata,
    update_project_page_metadata,
    get_project_data_for_export,
)
import csv
import io
import json

app = Flask(__name__)
# Configure CORS properly to allow all origins, methods, and headers
CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://react-fe-2xnv.onrender.com",
    ],
    methods=["GET", "POST", "OPTIONS", "DELETE", "PUT", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    expose_headers=["Content-Type", "X-Total-Count"],
    vary_header=True,
)

# Remove this custom CORS headers function as it conflicts with flask-cors
# @app.after_request
# def add_cors_headers(response):
#     response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
#     response.headers.add('Access-Control-Allow-Credentials', 'true')
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
#     response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
#     return response


@app.route("/api/page/get", methods=["POST"])
def api_get_page():
    try:
        data = request.get_json()  # This parses the incoming JSON body
        if not data:
            return {"error": "No JSON data found"}, 400

        return jsonify({"page": get_page(data)})

    except Exception as e:
        return {"error": str(e)}, 400


@app.route("/api/test", methods=["GET"])
def test_route():
    return jsonify({"message": "APE TOGETHER STRONG"})


# added create project
@app.route("/api/project/create", methods=["POST", "OPTIONS"])
def api_project_create():
    if request.method == "OPTIONS":
        return make_response(), 200

    proj = create_project()
    return jsonify({"project": proj}), 201


@app.route("/api/test-post", methods=["POST", "OPTIONS"])
def test_post():
    # Handle OPTIONS request (preflight)
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response

    # Handle POST request
    data = request.get_json()
    return jsonify({"received": data})


# @app.route('/api/search', methods=['OPTIONS'])
# def options_search():
#     response = make_response()
#     response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
#     response.headers.add('Access-Control-Allow-Origin', '*')
#     return response


@app.route("/api/search", methods=["POST"])
def search():
    try:
        # print("Request headers:", dict(request.headers))
        # Debugging: Log when the search method is called
        print("Search method called")
        # Debugging: Log the incoming request data
        data = request.get_json()
        print("Received data:", data)

        results = search_journals(
            volume=data.get("volume", []),
            page_numbers=data.get("pageNumber", []),
            dates=data.get("date", []),
            topics=data.get("topics", []),
            keywords=data.get("keywords", []),
            year=data.get("year"),
        )

        response = jsonify({"results": results})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    except Exception as e:
        # Debugging: Log any exceptions
        print("Error occurred:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/api/results", methods=["POST"])
def get_results():
    try:
        print("Results endpoint called")
        data = request.get_json()
        page_ids = data.get("page_ids", [])

        if not page_ids:
            return jsonify({"error": "No page IDs provided"}), 400

        results = get_pages_by_ids(page_ids)
        return jsonify({"results": results})
    except Exception as e:
        print("Error occurred:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/api/years", methods=["GET"])
def get_available_years():
    try:
        # Get all years and ranges from the database
        year_data = get_all_years()

        # Simply return the data - CORS is handled by the global CORS middleware
        return jsonify(year_data)
    except Exception as e:
        print("Error fetching years:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects", methods=["GET"])
def api_get_all_projects():
    all_projects = get_all_projects()
    return jsonify({"projects": all_projects})
    # return jsonify({"good": "god"})


@app.route("/api/project", methods=["POST"])
def api_get_project():
    try:
        data = request.get_json()  # This parses the incoming JSON body
        if not data:
            return {"error": "No JSON data found"}, 400
        project = get_project(data)
        if not project:
            return {"error": "No project found"}, 400
        return jsonify({"project": project})

    except Exception as e:
        return {"error": str(e)}, 400


@app.route("/api/project/update", methods=["post"])
def api_create_project():
    try:
        data = request.get_json()  # This parses the incoming JSON body
        if not data:
            return {"error": "No JSON data found"}, 400
        update_project(data)
        return jsonify({"good": "good"})

    except Exception as e:
        return {"error": str(e)}, 400


@app.route("/api/page/adjacent", methods=["POST", "OPTIONS"])
def get_adjacent_page_endpoint():
    # Handle OPTIONS request (preflight)
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response
        
    try:
        data = request.get_json()
        page_id = data.get("page_id")
        direction = data.get("direction", "next")  # "next" or "previous"
        
        if not page_id:
            return jsonify({"error": "No page ID provided"}), 400
            
        # Get the adjacent page from the database
        adjacent_page = get_adjacent_page(page_id, direction)
        
        if not adjacent_page:
            return jsonify({"error": f"No {direction} page found"}), 404
            
        return jsonify({"page": adjacent_page})
        
    except Exception as e:
        print(f"Error getting adjacent page: {str(e)}")
        return jsonify({"error": str(e)}), 500


# added delete project
@app.route("/api/project/delete", methods=["POST", "OPTIONS"])
def api_project_delete():
    if request.method == "OPTIONS":
        return make_response(), 200

    data = request.get_json() or {}
    proj_id = data.get("_id")
    if not proj_id:
        return jsonify({"error": "No project ID provided"}), 400

    success = delete_project(proj_id)
    if not success:
        return jsonify({"error": "Delete failed or project not found"}), 404

    return jsonify({"deleted": proj_id}), 200


# Add an endpoint to update universal page metadata
@app.route("/api/page/metadata/update", methods=["POST"])
def api_update_page_metadata():
    try:
        data = request.get_json()
        if not data or "page_id" not in data or "metadata" not in data:
            return {"error": "Invalid request data"}, 400
        
        page_id = data["page_id"]
        metadata = data["metadata"]
        
        success = update_page_metadata(page_id, metadata)
        if not success:
            return {"error": "Failed to update page metadata"}, 500
            
        return {"success": True, "message": "Page metadata updated successfully"}, 200
    except Exception as e:
        return {"error": str(e)}, 500


# Add an endpoint to update project-specific page metadata
@app.route("/api/project/page/metadata/update", methods=["POST"])
def api_update_project_page_metadata():
    try:
        data = request.get_json()
        if not data or "project_id" not in data or "page_id" not in data or "metadata" not in data:
            return {"error": "Invalid request data"}, 400
        
        project_id = data["project_id"]
        page_id = data["page_id"]
        metadata = data["metadata"]
        
        success = update_project_page_metadata(project_id, page_id, metadata)
        if not success:
            return {"error": "Failed to update project page metadata"}, 500
            
        return {"success": True, "message": "Project page metadata updated successfully"}, 200
    except Exception as e:
        return {"error": str(e)}, 500


# Add an endpoint to export project data to CSV
@app.route("/api/project/export/csv", methods=["POST", "OPTIONS"])
def api_export_project_to_csv():
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
        
    try:
        print("Export to CSV endpoint called")
        data = request.get_json()
        print(f"Request data: {data}")
        
        if not data or "project_id" not in data:
            print("Invalid request data - project_id missing")
            return {"error": "Invalid request data"}, 400
        
        project_id = data["project_id"]
        print(f"Exporting project: {project_id}")
        
        # Get project data including all metadata
        project_data = get_project_data_for_export(project_id)
        if not project_data:
            print(f"Project data not found for ID: {project_id}")
            return {"error": "Project not found or error retrieving data"}, 404
            
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write CSV header
        writer.writerow([
            "Volume", 
            "Page Number", 
            "Date", 
            "Topics", 
            "Text", 
            "Keywords",
            "Page Notes",
            "Passages"
        ])
        
        # Sort pages by page number (numerically)
        sorted_pages = sorted(project_data["pages"], 
                            key=lambda x: int(x["page_number"]) if x["page_number"].isdigit() else 0)
        
        # Write data for each page (one row per page)
        page_count = 0
        for page in sorted_pages:
            try:
                # Prepare the passages data
                passages_text = ""
                
                if page["passages"] and len(page["passages"]) > 0:
                    # Combine all passages into a single formatted text
                    passages_list = []
                    for passage in page["passages"]:
                        passage_id = passage.get("id", "")
                        passage_text = passage.get("text", "").replace("\n", " ").replace("\r", "")
                        passage_note = page["passage_notes"].get(passage_id, "").replace("\n", " ").replace("\r", "")
                        
                        # Format: "PASSAGE: {text} | NOTE: {note}"
                        formatted_passage = f"PASSAGE: {passage_text}"
                        if passage_note.strip():
                            formatted_passage += f" | NOTE: {passage_note}"
                        
                        passages_list.append(formatted_passage)
                    
                    # Join all passages with a clear separator
                    passages_text = "\n\n".join(passages_list)
                
                # Write a single row for the page with all its passages
                writer.writerow([
                    page.get("volume_title", ""),
                    page.get("page_number", ""),
                    page.get("date", ""),
                    "; ".join(page.get("topics", [])),
                    # Sanitize text fields to avoid CSV formatting issues
                    (page.get("text", "") or "").replace("\n", " ").replace("\r", ""),
                    page.get("keywords", ""),
                    (page.get("page_notes", "") or "").replace("\n", " ").replace("\r", ""),
                    passages_text
                ])
                page_count += 1
                
            except Exception as e:
                print(f"Error processing page: {e}")
                continue
        
        # Get the CSV string
        csv_data = output.getvalue()
        output.close()
        
        print(f"CSV export successful with {page_count} rows generated")
        
        return jsonify({
            "success": True,
            "csv_data": csv_data,
            "filename": f"{project_data['project_title'] or 'project'}_export.csv"
        })
        
    except Exception as e:
        print(f"Error exporting project data: {e}")
        # Print stack trace
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500


@app.route("/api/page/passages/all-projects", methods=["POST"])
def api_get_page_passages_all_projects():
    try:
        data = request.get_json()
        if not data or "page_id" not in data:
            return {"error": "Invalid request data"}, 400
        
        page_id = data["page_id"]
        current_project_id = data.get("current_project_id", None)
        
        # Get all projects that include this page
        all_projects = get_all_projects()
        projects_with_page = []
        
        for project in all_projects:
            # Skip the current project if specified
            if current_project_id and project["_id"] == current_project_id:
                continue
                
            # Check if the page is in this project
            if page_id in project.get("pages", []):
                # Get page metadata from this project
                if "page_metadata" in project and page_id in project["page_metadata"]:
                    metadata = project["page_metadata"][page_id]
                    
                    # Extract passage data only
                    if "passages" in metadata and metadata["passages"]:
                        projects_with_page.append({
                            "project_id": project["_id"],
                            "project_title": project.get("title", f"Project {project['_id'][-6:]}"),
                            "passages": metadata["passages"],
                            "passage_notes": metadata.get("passage_notes", {})
                        })
        
        return jsonify({
            "success": True,
            "projects": projects_with_page
        })
        
    except Exception as e:
        print(f"Error getting passage data: {e}")
        return {"error": str(e)}, 500


# This should be the last part of the file
if __name__ == "__main__":
    app.run(debug=True, port=5000)
