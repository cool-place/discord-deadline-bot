from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel
from google import genai
from google.genai import types
from docx2python import docx2python
import os
import pymupdf

# Load API key
load_dotenv()
api_key = os.getenv("Gemini_API_KEY")
client = genai.Client(api_key=api_key)

def extract_text_from_docx(file_path):

    with docx2python(file_path) as doc:
        all_docx_text = doc.text

    return all_docx_text

def extract_text_from_pdf(file_path):

    with pymupdf.open(file_path) as doc:
        all_pdf_text = "".join([page.get_text() for page in doc])

    return all_pdf_text

def extract_text_from_txt(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8")

class deadline(BaseModel):
    name: str
    due_date: str
    due_time: str | None = None

class syllabusdata(BaseModel):
    course_name: str
    deadlines: list[deadline]

async def send_text_to_llm(text):
    llmprompt = f"""
    Read the following syllabus.

    Identify:
    - The course name
    - Important deadlines such as exams, finals, projects, papers, and major assignments

    Do not invent deadlines that are not explicitly present.
    Use YYYY-MM-DD for dates.
    Use HH:MM for times when a time is provided.

    SYLLABUS:
    {text}
    """

    response = await client.aio.models.generate_content(
        model ="gemini-3.6-flash" ,
        contents=llmprompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=syllabusdata
        )
    )

    return response.parsed

