# from fastapi import FastAPI,File, UploadFile
# import pdfplumber

# app = FastAPI()

# @app.get("/")
# def hello_world():
#     return {"message":"Hellow, World!!!"}

# @app.post("/resume_data")
# def resume_data():
#     return {"message":"Resume data endpoint"}


# @app.post("/upload_resume")
# def upload_resume(file : UploadFile = File(...)):

#     if not file.filename.endswith('.pdf'):
#         return {"error": "Only PDF files are supported."}
    
#     with pdfplumber.open(file.file) as pdf:
#         text = ""
#         for page in pdf.pages:
#             text += page.extract_text() or ""

    
#     return {"filename": file.filename, "content": text}

# app/main.py
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from app.utils import extract_text_from_pdf_fileobj, clean_text, extract_email_phone, extract_name, extract_skills
from app.db import save_resume_doc
from app.embeddings import EmbeddingIndex
import uuid
import datetime

app = FastAPI()
index = EmbeddingIndex()
index.load()

@app.post("/upload_resume/")
async def upload_resume(user_id: str = Form(...), file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    if not file.filename.lower().endswith(".pdf"):
        return {"error": "Only PDF supported"}
    raw_text = extract_text_from_pdf_fileobj(file.file)
    text = clean_text(raw_text)
    email, phone = extract_email_phone(text)
    name = extract_name(text)
    skills = extract_skills(text)
    resume_id = str(uuid.uuid4())

    # Save metadata to MongoDB async
    doc = {
        "resume_id": resume_id,
        "user_id": user_id,
        "filename": file.filename,
        "text": text[:2000],   # store preview; store full if you want
        "email": email,
        "phone": phone,
        "name": name,
        "skills": skills,
        "uploaded_at": datetime.datetime.utcnow()
    }
    # background save so response is quick
    background_tasks.add_task(save_resume_doc, doc)

    # Add to FAISS index in background
    # note: index.add is CPU-bound; you may want to run in a threadpool for non-blocking
    def add_to_index():
        index.add([text], [ {"resume_id": resume_id, "user_id": user_id, "filename": file.filename, "skills": skills} ])

    background_tasks.add_task(add_to_index)

    return {"status": "uploaded", "resume_id": resume_id, "skills": skills}

# add to app/main.py
from pydantic import BaseModel

class JDIn(BaseModel):
    job_id: str = None
    title: str = None
    description: str

@app.post("/match_job/")
async def match_job(payload: JDIn):
    # create query text
    query_text = payload.title + " " + payload.description if payload.title else payload.description
    results = index.search(query_text, top_k=10)
    # Post-process results to compute skill-gap
    response = []
    for item in results:
        meta = item["meta"]
        score = item["score"]
        # compute skill gap
        job_skills = extract_skills(query_text)
        resume_skills = meta.get("skills", [])
        missing = list(set(job_skills) - set(resume_skills))
        response.append({
            "resume_id": meta["resume_id"],
            "user_id": meta["user_id"],
            "filename": meta["filename"],
            "score": score,
            "resume_skills": resume_skills,
            "job_skills": job_skills,
            "missing_skills": missing
        })
    return {"results": response}
