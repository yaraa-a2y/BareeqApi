from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pdfplumber
import pandas as pd
import re
from pathlib import Path
import shutil
import os

app = FastAPI()

# Setup CORS
origins = [
    "http://127.0.0.1:8000",  # Adjust the port if your client runs on a different one
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

def allowed_file(filename: str):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path: str):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""  # Added or "" to handle cases where extract_text() returns None
    return text

@app.post("/upload")
async def upload_and_process_pdf(file: UploadFile = File(...)):
    if not allowed_file(file.filename):
        return JSONResponse(status_code=400, content={"message": "File type not allowed"})

    filename = Path(file.filename).name
    pdf_path = os.path.join(UPLOAD_FOLDER, filename)

    # Save file to disk
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)  # Adjusted for async file upload handling

    text = extract_text_from_pdf(pdf_path)

    ner = re.compile(r'([A-Za-z].*?) (\d+\.\d{2} +|\d+\.\d{1} +|\d+|\s+)')
    arr = {}
    for line in text.split('\n'):
        match = ner.match(line)
        if match:
            vand_name, vand_num = match.groups()
            arr[vand_name.strip()] = vand_num

    df = pd.DataFrame(list(arr.items()), columns=['Test', 'Result'])
    keywords = ['Haemoglobin', 'Hemoglobin', 'Iron', 'Vitamin D', 'Vitamin B12']
    filtered_df = df[df['Test'].str.contains('|'.join(keywords), case=False)]  # case=False for case insensitive match

    result_array = filtered_df.to_dict('records')
    return result_array

#if name == 'main':
  #  import uvicorn
  #  uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")