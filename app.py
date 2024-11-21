
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import csv
import pandas as pd

app = Flask(__name__)

CORS(app, resources={
    r"/*": {
        "origins": "*",  # Be cautious in production
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    # Handle preflight OPTIONS request for CORS
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file part', 
                'status': 'failed'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'error': 'No selected file', 
                'status': 'failed'
            }), 400

        if not file.filename.lower().endswith('.csv'):
            return jsonify({
                'error': 'Invalid file type. Please upload a CSV file', 
                'status': 'failed'
            }), 400

        # Generate a unique filename
        filename = os.path.join(UPLOAD_FOLDER, f'contacts_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.csv')
        
        file.save(filename)

        # Validate CSV content
        try:
            df = pd.read_csv(filename)
            
            required_columns = ['name', 'phone']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                os.remove(filename)
                return jsonify({
                    'error': f'Missing required columns: {", ".join(missing_columns)}', 
                    'status': 'failed'
                }), 400

            def validate_phone(phone):
                # Basic phone number validation 
                return str(phone).replace('-','').replace(' ','').isdigit()

            invalid_phones = df[~df['phone'].apply(validate_phone)]
            
            if not invalid_phones.empty:
                os.remove(filename)
                return jsonify({
                    'error': 'Invalid phone numbers found', 
                    'invalid_rows': invalid_phones.to_dict(orient='records'),
                    'status': 'failed'
                }), 400

        except pd.errors.EmptyDataError:
            os.remove(filename)
            return jsonify({
                'error': 'The CSV file is empty', 
                'status': 'failed'
            }), 400
        except pd.errors.ParserError:
            os.remove(filename)
            return jsonify({
                'error': 'Unable to parse the CSV file', 
                'status': 'failed'
            }), 400

        # Successful upload response
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': os.path.basename(filename),
            'total_contacts': len(df),
            'status': 'success'
        }), 200

    except Exception as e:
        # Catch-all error handling
        app.logger.error(f"Unexpected error during file upload: {str(e)}")
        return jsonify({
            'error': 'An unexpected error occurred', 
            'details': str(e),
            'status': 'failed'
        }), 500

# Optional: Route to list uploaded files (for debugging)
@app.route('/uploaded-files', methods=['GET'])
def list_uploaded_files():
    try:
        files = os.listdir(UPLOAD_FOLDER)
        return jsonify({
            'files': files,
            'total_files': len(files)
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'Could not list files',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    app.run(
        debug=True,  # Set to False in production
        host='0.0.0.0',  # Listen on all available interfaces
        port=5000
    )
