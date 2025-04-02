from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from search import search_journals, test_query, get_all_years
from results import get_pages_by_ids

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
    vary_header=True
)


@app.route("/api/test", methods=["GET"])
def test_route():
    return jsonify({"message": "APE TOGETHER STRONG"})


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
    

@app.route('/api/results', methods=['POST'])
def get_results():
    try:
        print("Results endpoint called")
        data = request.get_json()
        page_ids = data.get('page_ids', [])
        
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
