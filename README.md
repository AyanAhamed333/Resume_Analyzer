# Smart Resume Analyzer

A complete full-stack web application designed to analyze resumes against specific job roles (Backend Developer or Data Analyst) and provide actionable feedback, a match score, and missing skills.

## Features
- **Paste or Upload**: Paste your raw resume text or upload a PDF file to extract text automatically.
- **Role-Based Analysis**: Compares the resume against the required skills for pre-defined roles using a weighted scoring algorithm.
- **Custom JD Extraction**: Paste any Job Description and the app will automatically extract the most critical keywords to compare against your resume.
- **Detailed Results**: Instantly view your match score, skills found, missing skills, and top suggestions for improvement.
- **Enhanced Feedback**: Get suggestions on resume length, action verbs, and quantifying metrics.
- **History Tracking**: The backend uses SQLite to save analysis history, including the score and timestamp.
- **Beautiful UI**: Modern, fast, and simple user interface built with HTML, clean CSS, and Vanilla JavaScript.

## Tech Stack
- **Backend**: Python, Flask, PyPDF2, SQLite
- **Frontend**: HTML5, Vanilla CSS, Vanilla JavaScript (Fetch API).

## How to Run

1. **Clone or download the repository**.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the Application**:
   ```bash
   python app.py
   ```
4. **Open in Browser**:
   Navigate to `http://127.0.0.1:5000/`

## API Endpoints
- `GET /`: Serves the UI.
- `POST /analyze`: Receives `resume_text` and `role` to perform the analysis. Returns JSON score and suggestions.
- `POST /upload`: Receives a PDF file, extracts text, and returns the raw string.
- `GET /history`: Returns JSON containing all historical analysis runs.

## Screenshots
*(Add screenshots here showing the home screen, upload process, and result visualization)*

## Example Output
When analyzing a resume containing "Python" and "Flask" for a backend role, the output looks like:
```json
{
  "score": 80,
  "skills_found": ["python", "flask"],
  "missing_skills": ["sql", "api"],
  "suggestions": [
    "Add 'sql' to your skill set or mention related experience.",
    "Add 'api' to your skill set or mention related experience."
  ]
}
```
