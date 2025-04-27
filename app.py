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
)

app = Flask(__name__)
# test
# Configure CORS properly to allow all origins, methods, and headers
CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://react-fe-2xnv.onrender.com",
    ],
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type", "X-Total-Count"],
    vary_header=True,
)


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


# This should be the last part of the file
if __name__ == "__main__":
    app.run(debug=True, port=5000)
