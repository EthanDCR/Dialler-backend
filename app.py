
from flask import Flask, request, jsonify
import pandas as pd
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and file.filename.endswith('.csv'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Read CSV file
            df = pd.read_csv(filepath)
            
            # Convert DataFrame to list of contact dictionaries
            contacts = []
            for _, row in df.iterrows():
                contact = {
                    'name': row.get('name', ''),
                    'phone': row.get('phone', ''),
                    'company': row.get('company', ''),
                    'position': row.get('position', ''),
                    'address': row.get('address', ''),
                    'email': row.get('email', ''),
                    'notes': row.get('notes', '')
                }
                contacts.append(contact)
            
            # Clean up the uploaded file
            os.remove(filepath)
            
            return jsonify({
                'message': 'File processed successfully',
                'contacts': contacts
            })
        
        return jsonify({'error': 'Invalid file type'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
