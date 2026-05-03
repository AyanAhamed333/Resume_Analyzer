from flask import Flask, request, jsonify, render_template
import os
import PyPDF2
from database import init_db, insert_history, get_history
from analyzer import analyze_resume

app = Flask(__name__)

# Initialize Database on startup
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input, JSON expected"}), 400
        
    resume_text = data.get('resume_text', '').strip()
    role = data.get('role', '').strip()
    jd_text = data.get('jd_text', '').strip()
    
    if not resume_text:
        return jsonify({"error": "Resume text is empty"}), 400
        
    if not role and not jd_text:
        return jsonify({"error": "Please select a role or provide a Job Description"}), 400
        
    analysis_result = analyze_resume(resume_text, role, jd_text)
    
    if not analysis_result:
        return jsonify({"error": "Invalid role or unable to analyze"}), 400
        
    # Store history
    insert_history(role if role else "Custom JD", analysis_result["score"])
    
    return jsonify(analysis_result)

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file and file.filename.lower().endswith('.pdf'):
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            extracted_text = ""
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
            
            if not extracted_text.strip():
                return jsonify({"error": "Could not extract text from PDF, it might be an image-based PDF"}), 400
                
            return jsonify({"text": extracted_text})
        except Exception as e:
            return jsonify({"error": f"Error reading PDF file: {str(e)}"}), 500
    else:
        return jsonify({"error": "Invalid file type. Please upload a PDF file."}), 400

@app.route('/history', methods=['GET'])
def history():
    records = get_history()
    return jsonify(records)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
