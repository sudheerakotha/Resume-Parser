import streamlit as st
import re
import pdfplumber
from docx import Document
import spacy

# Load the English NLP model
nlp = spacy.load("en_core_web_sm")

# Function to extract text from PDF
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# Function to extract text from DOCX
def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

# Function to extract details from resume text
def extract_details(text):
    doc = nlp(text)

    # Extract name (first PERSON entity)
    name = ""
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text
            break

    # Extract email and phone
    email = re.findall(r'[\w\.-]+@[\w\.-]+', text)
    phone = re.findall(r'\+?\d[\d\-\s]{8,}\d', text)

    # Extract skills, education, experience based on keywords
    skills = []
    education = []
    experience = []

    lines = text.splitlines()
    for line in lines:
        line_lower = line.lower()
        if "skill" in line_lower:
            skills.append(line.strip())
        elif any(keyword in line_lower for keyword in ["education", "bachelor", "master", "b.tech", "m.tech", "bsc", "msc", "phd"]):
            education.append(line.strip())
        elif any(keyword in line_lower for keyword in ["experience", "intern", "worked at", "project"]):
            experience.append(line.strip())

    return {
        "Name": name if name else "Not found",
        "Email": email[0] if email else "Not found",
        "Phone": phone[0] if phone else "Not found",
        "Skills": ", ".join(skills) if skills else "Not found",
        "Education": ", ".join(education) if education else "Not found",
        "Experience": ", ".join(experience) if experience else "Not found"
    }

# ----------------------------
# Streamlit App Starts Here
# ----------------------------

st.set_page_config(page_title="Resume Parser", layout="centered")
st.title("📄 Resume Parser")
st.write("Upload a PDF or DOCX resume to extract key information in a simple format.")

# Upload file
uploaded_file = st.file_uploader("Choose your resume file", type=["pdf", "docx"])

if uploaded_file is not None:
    # Extract text
    if uploaded_file.name.endswith(".pdf"):
        text = extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        text = extract_text_from_docx(uploaded_file)
    else:
        st.error("Unsupported file format. Please upload a .pdf or .docx file.")
        st.stop()

    # Extract and show details
    st.success("✅ Resume uploaded and processed successfully!")
    st.subheader("📋 Extracted Resume Details:")

    details = extract_details(text)

    # Display in tabular format
    for key, value in details.items():
        st.markdown(f"**{key}:** {value}")

    st.markdown("---")
    st.info("You can upload another resume to re-analyze.")
