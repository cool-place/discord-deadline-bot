import os
import json
import fitz # PyMuPDF library
from google import genai
from google.genai import types
from pathlib import Path 
from docx import Document
from dotenv import load_dotenv
from pydantic import BaseModel

# Load API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Path.cwd() is an easier way to get current path
folder_path = Path.cwd()

# list makes an array based off of what is found in parenthesis. * ignores characters so we only care about .docx
pdf_files = list(folder_path.glob("*.pdf"))
docx_files = list(folder_path.glob("*.docx"))

if not docx_files and not pdf_files:
    print("No .docx or .pdf files found in the current directory")
    exit()

def extract_text_from_docx(file_path):
    doc = Document(file_path)

    clean_paragraphs = []

    for p in doc.paragraphs:
        if p.text.strip():
            clean_paragraphs.append(p.text)

    temp_memory = "\n".join(clean_paragraphs)

    return temp_memory

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)

    clean_paragraphs = []

    for page in doc:
        text = page.get_text()

        cleaned_strips = text.strip()

        if cleaned_strips:
            clean_paragraphs.append(cleaned_strips)
    doc.close()

    temp_memory = "\n\n--- Next Page ---\n\n".join(clean_paragraphs)

    return temp_memory

temp_memory = extract_text_from_docx

class SyllabusDeadline(BaseModel):
    task_or_event: str
    due_date_iso: str # forces usage of standard YYY-MM-DD

class SyllabusExtraction(BaseModel):
    deadlines: list[SyllabusDeadline]

# Gemini prompt
prompt = f"""
Analyze the following document text and extract all assignments, quizzes, tests, deadlines, and important event times. 
Format all dates into standard ISO format (YYYY-MM-DD, and include HH:MM if a specific time of day is mentioned).

Syllabus Text:
\"\"\"
{temp_memory}
\"\"\"
"""

print("Sending document content to Gemini...")

# 6. Make the API request using gemini-3.6
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=SyllabusExtraction,
    ),
)

# 7. Print out the final structured results to your terminal
print("\n--- Extracted Deadlines ---")

parsed_json = json.loads(response.text)
print(json.dumps(parsed_json, indent=4))
