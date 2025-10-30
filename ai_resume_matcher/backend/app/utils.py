# app/utils.py
import re
import pdfplumber
import spacy

nlp = spacy.load("en_core_web_sm")

SKILL_SET = [
    "python","pandas","numpy","scikit-learn","tensorflow","pytorch",
    "fastapi","flask","django","sql","postgresql","mongodb","aws","docker",
    "git","nlp","deep learning","computer vision"
]

def extract_text_from_pdf_fileobj(file_obj):
    text = ""
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def clean_text(text):
    text = re.sub(r'\r', '\n', text)
    text = re.sub(r'\n\s+', '\n', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def extract_email_phone(text):
    email = re.search(r'[\w\.-]+@[\w\.-]+', text)
    phone = re.search(r'(\+?\d[\d \-]{7,}\d)', text)
    return email.group(0) if email else None, phone.group(0) if phone else None

def extract_name(text):
    doc = nlp(text[:200])  # small window to find name at top
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return None

def extract_skills(text):
    found = set()
    text_lower = text.lower()
    for skill in SKILL_SET:
        if skill.lower() in text_lower:
            found.add(skill)
    return list(found)
