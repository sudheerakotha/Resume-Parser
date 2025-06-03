import streamlit as st

import re

import pdfplumber

from docx import Document

import spacy



# Load the English NLP model

# Ensure you have downloaded the model: python -m spacy download en_core_web_sm

nlp = spacy.load("en_core_web_sm")



# Function to extract text from PDF

def extract_text_from_pdf(file):

    """

    Extracts text content from a PDF file.



    Args:

        file: A file-like object representing the PDF.



    Returns:

        A string containing all extracted text from the PDF.

    """

    text = ""

    with pdfplumber.open(file) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:

                text += page_text + "\n"

    return text



# Function to extract text from DOCX

def extract_text_from_docx(file):

    """

    Extracts text content from a DOCX file.



    Args:

        file: A file-like object representing the DOCX.



    Returns:

        A string containing all extracted text from the DOCX.

    """

    doc = Document(file)

    return "\n".join([para.text for para in doc.paragraphs])



# Function to extract details from resume text

def extract_details(text):

    """

    Extracts key details (Name, Email, Phone, Profile, Experience, Education, Skills, Projects,

    Position of Responsibility) from the resume text using a combination of regex and spaCy NLP.



    Args:

        text: The full text content of the resume.



    Returns:

        A dictionary containing the extracted details.

    """

    doc = nlp(text)



    # Initialize details dictionary with default "Not found" for all fields

    details = {

        "Name": "Not found",

        "Email": "Not found",

        "Phone": "Not found",

        "Profile": "Not found",

        "Professional Experience": "Not found",

        "Education": "Not found",

        "Skills": "Not found",

        "Projects": "Not found",

        "Position of Responsibility": "Not found"

    }



    # Extract email and phone using regular expressions

    email = re.findall(r'[\w\.-]+@[\w\.-]+', text)

    phone = re.findall(r'\+?\d[\d\-\s]{8,}\d', text)

    if email:

        details["Email"] = email[0]

    if phone:

        details["Phone"] = phone[0]



    # Split text into lines and clean them (remove empty lines and strip whitespace)

    lines = text.splitlines()

    cleaned_lines = [line.strip() for line in lines if line.strip()]



    # Attempt to extract name from the first few lines using spaCy's PERSON entity recognition

    # and a fallback to the first line if it looks like a name.

    name_candidates = []

    for i in range(min(5, len(cleaned_lines))): # Check the first 5 lines for potential names

        line_doc = nlp(cleaned_lines[i])

        for ent in line_doc.ents:

            # Look for PERSON entities that are at least two words long (e.g., "K SUDHEERA")

            if ent.label_ == "PERSON" and len(ent.text.split()) >= 2:

                name_candidates.append(ent.text)

        # Also consider the very first line as a strong name candidate if it's short and capitalized

        if i == 0 and (cleaned_lines[0].isupper() or cleaned_lines[0].istitle()) and len(cleaned_lines[0].split()) <= 4:

            name_candidates.append(cleaned_lines[0])

    

    # Prioritize the first strong name candidate found

    if name_candidates:

        details["Name"] = name_candidates[0]



    # Define common resume section keywords and their corresponding keys in the details dictionary.

    # The order here can influence parsing if sections have similar keywords.

    section_keywords = {

        "PROFILE": "Profile",

        "PROFESSIONAL EXPERIENCE": "Professional Experience",

        "EDUCATION": "Education",

        "SKILLS": "Skills",

        "PROJECTS": "Projects",

        "POSITION OF RESPONSIBILITY": "Position of Responsibility"

    }



    # Temporary dictionary to hold lists of lines for each section before joining

    current_section_data = {key: [] for key in details if key not in ["Name", "Email", "Phone"]}

    current_section_name = None # Tracks the current section being parsed



    for line in cleaned_lines:

        line_upper = line.upper()

        found_new_section = False

        # Check if the current line is a new section header

        for keyword, section_key in section_keywords.items():

            # Match if the keyword is present and the line isn't too long (to avoid false positives)

            if keyword in line_upper and len(line_upper) < len(keyword) + 15: # Increased buffer slightly

                current_section_name = section_key

                found_new_section = True

                break

        

        # If not a new section header, and we are currently in a section, add the line to it

        if not found_new_section and current_section_name:

            if current_section_name == "Skills":

                # Special handling for skills: split by common delimiters and bullet points

                # This regex splits by spaces, unicode bullet (•), comma, and semicolon

                skill_items = re.split(r'[\s\u2022,\;]+', line.replace('•', '').strip())

                # Filter out any empty strings resulting from the split and add to skills list

                current_section_data[current_section_name].extend([s.strip() for s in skill_items if s.strip()])

            else:

                # For other sections, just append the line

                current_section_data[current_section_name].append(line)



    # Join the lists of lines into single strings for the final output dictionary

    for key, value_list in current_section_data.items():

        if value_list:

            if key == "Skills":

                # Ensure unique skills and join them with ", "

                details[key] = ", ".join(sorted(list(set(value_list))))

            else:

                # Join other sections with newlines

                details[key] = "\n".join(value_list)

        # If a section's list is empty, it remains "Not found" as initialized



    return details



# ----------------------------

# Streamlit App Starts Here

# ----------------------------



st.set_page_config(page_title="Resume Parser", layout="centered")

st.title("📄 Resume Parser")

st.write("Upload a PDF or DOCX resume to extract key information in a simple format.")



# File uploader widget

uploaded_file = st.file_uploader("Choose your resume file", type=["pdf", "docx"])



if uploaded_file is not None:

    # Determine file type and extract text accordingly

    if uploaded_file.name.endswith(".pdf"):

        text = extract_text_from_pdf(uploaded_file)

    elif uploaded_file.name.endswith(".docx"):

        text = extract_text_from_docx(uploaded_file)

    else:

        st.error("Unsupported file format. Please upload a .pdf or .docx file.")

        st.stop() # Stop execution if file format is not supported



    # Process and display extracted details

    st.success("✅ Resume uploaded and processed successfully!")

    st.subheader("📋 Extracted Resume Details:")



    details = extract_details(text)



    # Display the extracted details in a formatted way

    for key, value in details.items():

        st.markdown(f"**{key}:**") # Always display the key as a header

        if key in ["Profile", "Professional Experience", "Education", "Projects", "Position of Responsibility"]:

            # For these sections, split by newline and display as bullet points

            if value != "Not found":

                for line in value.split('\n'):

                    if line.strip(): # Only display non-empty lines

                        st.markdown(f"- {line.strip()}")

            else:

                st.markdown(value) # Display "Not found" if no content

        else:

            # For Name, Email, Phone, Skills, display directly

            st.markdown(value)



    st.markdown("---")

    st.info("You can upload another resume to re-analyze.")



