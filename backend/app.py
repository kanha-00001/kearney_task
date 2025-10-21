from flask import Flask, request, jsonify
from rag_tool import process_file_and_get_query_engine
import os

app = Flask(__name__)

# Initialize query engine with CSV file on startup
query_engine = None

def load_csv_and_build_engine():
    global query_engine
    # Construct absolute path to CSV file
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'Sugar_Spend_Data.csv'))
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return
    
    try:
        # Read file content as bytes
        with open(csv_path, 'rb') as file:
            file_content = file.read()
        file_name = 'Sugar_Spend_Data.csv'
        
        # Build RAG query engine
        query_engine = process_file_and_get_query_engine(file_content, file_name)
        print("RAG index built successfully")
    except Exception as e:
        print(f"Error processing CSV: {str(e)}")

# Load CSV and build engine on startup
load_csv_and_build_engine()

@app.route('/query', methods=['POST'])
def query_rag():
    global query_engine
    if query_engine is None:
        return jsonify({"error": "Failed to initialize RAG engine. Check server logs."}), 500
    
    data = request.json
    if 'query' not in data:
        return jsonify({"error": "No query provided"}), 400
    
    user_query = data['query']
    
    try:
        response = query_engine.query(user_query)
        return jsonify({"response": str(response)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)