import streamlit as st
import re
import pdfplumber
from docx import Document
import spacy

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

# Basic list of common skills (can be extended)
COMMON_SKILLS = [
    "python", "java", "c++", "html", "css", "javascript", "sql", "react",
    "node.js", "aws", "docker", "git", "excel", "machine learning", "data analysis"
]

def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def clean_text(text):
    return re.sub(r'\s+', ' ', text.strip())

def extract_details(text):
    doc = nlp(text)

    # Extract name (first PERSON entity)
    name = next((ent.text for ent in doc.ents if ent.label_ == "PERSON"), "Not found")

    # Extract email
    email = re.findall(r'[\w\.-]+@[\w\.-]+', text)
    email = email[0] if email else "Not found"

    # Extract phone
    phone = re.findall(r'\+?\d[\d\-\s]{8,}\d', text)
    phone = phone[0] if phone else "Not found"

    # Extract skills (simple keyword match)
    text_lower = text.lower()
    found_skills = sorted(set([skill for skill in COMMON_SKILLS if skill.lower() in text_lower]))
    skills = ", ".join(found_skills) if found_skills else "Not found"

    # Extract education (keywords + organizations)
    education_keywords = ["bachelor", "master", "b.tech", "b.sc", "m.tech", "mba", "msc", "school", "university", "college"]
    education = [line for line in text.splitlines() if any(word in line.lower() for word in education_keywords)]
    education = clean_text(" | ".join(education)) if education else "Not found"

    # Extract experience (based on keywords + ORG entities)
    experience_keywords = ["experience", "intern", "worked", "at", "company"]
    experience_lines = [line for line in text.splitlines() if any(word in line.lower() for word in experience_keywords)]
    orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    experience = clean_text(" | ".join(set(experience_lines + orgs))) if experience_lines or orgs else "Not found"

    return {
        "Name": name,
        "Email": email,
        "Phone": phone,
        "Skills": skills,
        "Education": education,
        "Experience": experience
    }
