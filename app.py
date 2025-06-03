import streamlit as st
import re
import pdfplumber
from docx import Document
import spacy

nlp = spacy.load("en_core_web_sm")

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

def extract_details(text):
    doc = nlp(text)
    name = ""
    email = re.findall(r'[\w\.-]+@[\w\.-]+', text)
    phone = re.findall(r'\+?\d[\d\-\s]{8,}\d', text)

    # Get first PERSON entity as name
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text
            break

    skills = []
    education = []
    experience = []

    lines = text.splitlines()
    for line in lines:
        lower_line = line.lower()
        if "skill" in lower_line:
            skills.append(line.strip())
        elif any(x in lower_line for x in ["education", "bachelor", "master", "b.tech", "bsc", "msc"]):
            education.append(line.strip())
        elif any(x in lower_line for x in ["experience", "worked at", "intern"]):
            experience.append(line.strip())

    return {
        "Name": name,
        "Email": email[0] if email else "Not found",
        "Phone": phone[0] if phone else "Not found",
        "Skills": ", ".join(skills) if skills else "Not found",
        "Education": ", ".join(education) if education else "Not found",
        "Experience": ", ".join(experience) if experience else "Not found"
    }

# --- Streamlit App UI ---
st.set_page_config(page_title="Resume Parser", layout="centered")
st.title("📄 Resume Parser")
st.write("Upload your PDF or DOCX resume and extract key information.")

uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx"])

if uploaded_file is not None:
    if uploaded_file.name.endswith(".pdf"):
        text = extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        text = extract_text_from_docx(uploaded_file)
    else:
        st.error("Unsupported file format. Please upload a .pdf or .docx file.")
        st.stop()

    st.success("Resume uploaded successfully!")
    st.subheader("🔍 Extracted Details")

    details = extract_details(text)

    for key, value in details.items():
        st.markdown(f"**{key}:** {value}")
