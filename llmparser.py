from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel
from docx import Document
from google import genai
from google.genai import types
from docx2python import docx2python
import os
import json
import fitz # *PyMuPDF

# Load API key
load_dotenv()
api_key = os.getenv("Gemini_API_KEY")
client = genai.Client(api_key=api_key)

def extract_text_from_docx(file_path):

    with docx2python(file_path) as doc:
        all_docx_text = doc.text

    return all_docx_text

    

