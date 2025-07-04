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
        "Skills": "Not found", # Skills will now be a list
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
                # Special handling for skills: remove common bullet points and extra whitespace
                cleaned_skill_line = line.replace('•', '').replace('-', '').strip()
                if cleaned_skill_line:
                    # Attempt to split by common skill separators (comma or semicolon)
                    # If multiple skills are on one line separated by these, split them.
                    # Otherwise, treat the whole cleaned line as a single skill.
                    if ';' in cleaned_skill_line:
                        skill_items = [s.strip() for s in cleaned_skill_line.split(';') if s.strip()]
                        current_section_data[current_section_name].extend(skill_items)
                    elif ',' in cleaned_skill_line:
                        skill_items = [s.strip() for s in cleaned_skill_line.split(',') if s.strip()]
                        current_section_data[current_section_name].extend(skill_items)
                    else:
                        current_section_data[current_section_name].append(cleaned_skill_line)
            else:
                # For other sections, just append the line
                current_section_data[current_section_name].append(line)

    # Finalize details dictionary
    for key, value_list in current_section_data.items():
        if value_list:
            if key == "Skills":
                # Store skills as a list of unique items
                details[key] = sorted(list(set(value_list)))
            else:
                # Join other sections with newlines
                details[key] = "\n".join(value_list)
        # If a section's list is empty, it remains "Not found" as initialized

    return details

def display_extracted_details(details, title="Extracted Resume Details"):
    """
    Displays the extracted resume details in a formatted way.
    """
    st.subheader(f"📋 {title}:")
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
            # For Name, Email, Phone, display directly. For Skills, join the list.
            if key == "Skills":
                if value != "Not found":
                    st.markdown(", ".join(value)) # Join list to string for display
                else:
                    st.markdown(value)
            else:
                st.markdown(value)


def calculate_resume_score(details):
    """
    Calculates a numerical score for a resume based on its extracted details.
    Score is out of 10. This can be considered a basic ATS compatibility score.
    """
    score = 0
    # Max possible score for each criterion
    MAX_SECTIONS_SCORE = 3 # Profile, Experience, Education, Skills, Projects, Responsibility (6 sections) -> 0.5 each
    MAX_EXPERIENCE_SCORE = 3 # Based on lines of experience
    MAX_SKILLS_SCORE = 2 # Based on number of skills
    MAX_PROJECTS_SCORE = 2 # Based on number of projects

    # Criteria 1: Completeness of sections (max 3 points)
    sections_found = 0
    sections_to_check = ["Profile", "Professional Experience", "Education", "Skills", "Projects", "Position of Responsibility"]
    for section in sections_to_check:
        # Check if the value is not "Not found" and is not an empty string/list
        if details.get(section) != "Not found" and (isinstance(details.get(section), list) and details.get(section)) or (isinstance(details.get(section), str) and details.get(section).strip() != ""):
            sections_found += 1
    score += (sections_found / len(sections_to_check)) * MAX_SECTIONS_SCORE

    # Criteria 2: Length of Professional Experience (max 3 points)
    exp_lines = len(details.get("Professional Experience", "").split('\n')) if details.get("Professional Experience") != "Not found" else 0
    # Simple scaling: 0-2 lines = 0, 3-5 lines = 1, 6-9 lines = 2, 10+ lines = 3
    if exp_lines >= 10:
        score += MAX_EXPERIENCE_SCORE
    elif exp_lines >= 6:
        score += 2
    elif exp_lines >= 3:
        score += 1

    # Criteria 3: Number of Skills (max 2 points)
    # Now details["Skills"] is a list
    skills_count = len(details.get("Skills", [])) if details.get("Skills") != "Not found" else 0
    # Simple scaling: 0-5 skills = 0, 6-10 skills = 1, 11+ skills = 2
    if skills_count >= 11:
        score += MAX_SKILLS_SCORE
    elif skills_count >= 6:
        score += 1

    # Criteria 4: Number of Projects (max 2 points)
    projects_lines = len(details.get("Projects", "").split('\n')) if details.get("Projects") != "Not found" else 0
    # Simple scaling: 0 projects = 0, 1-2 projects = 1, 3+ projects = 2
    if projects_lines >= 3:
        score += MAX_PROJECTS_SCORE
    elif projects_lines >= 1:
        score += 1

    return round(score, 1) # Round to one decimal place


def compare_resumes(details1, details2):
    """
    Compares two resumes based on extracted details and provides a side-by-side comparison
    and a rating out of 10.
    """
    st.subheader("📊 Resume Comparison Results:")

    # Display names at the top
    col_name1, col_name2 = st.columns(2)
    with col_name1:
        st.markdown(f"**Resume 1: {details1.get('Name', 'Unnamed Resume 1')}**")
    with col_name2:
        st.markdown(f"**Resume 2: {details2.get('Name', 'Unnamed Resume 2')}**")

    st.markdown("---") # Separator after names

    # Specific categories for side-by-side comparison
    comparison_categories_detailed = {
        "Skills": lambda d: d.get("Skills", []), # Now it's already a list
        "Professional Experience": lambda d: [line.strip() for line in d.get("Professional Experience", "").split('\n') if line.strip()],
        "Projects": lambda d: [line.strip() for line in d.get("Projects", "").split('\n') if line.strip()],
        "Position of Responsibility": lambda d: [line.strip() for line in d.get("Position of Responsibility", "").split('\n') if line.strip()]
    }

    # Create columns for the comparison table
    for category_name, get_items_func in comparison_categories_detailed.items():
        items1 = get_items_func(details1)
        items2 = get_items_func(details2)

        st.markdown(f"**{category_name}:**") # Category header above the comparison rows

        # Determine the maximum number of bullet points to display for proper alignment
        max_lines = max(len(items1), len(items2))
        
        # Pad the shorter list with placeholder for alignment
        padded_items1 = items1 + [''] * (max_lines - len(items1))
        padded_items2 = items2 + [''] * (max_lines - len(items2))

        for i in range(max_lines):
            col_cat, col_res1, col_res2 = st.columns([1, 4, 4])
            with col_cat:
                st.markdown("") # Empty for alignment
            with col_res1:
                if padded_items1[i]:
                    st.markdown(f"- {padded_items1[i]}")
                else:
                    st.markdown("") # Leave blank if no item
            with col_res2:
                if padded_items2[i]:
                    st.markdown(f"- {padded_items2[i]}")
                else:
                    st.markdown("") # Leave blank if no item
        
        st.markdown("---") # Separator for each category

    # Calculate and display overall ATS scores
    ats_score1 = calculate_resume_score(details1)
    ats_score2 = calculate_resume_score(details2)

    st.markdown("### ATS Score (Out of 10):")
    rating_col1, rating_col2 = st.columns(2)
    with rating_col1:
        st.metric(label=f"**{details1.get('Name', 'Resume 1')} ATS Score**", value=f"{ats_score1}/10")
    with rating_col2:
        st.metric(label=f"**{details2.get('Name', 'Resume 2')} ATS Score**", value=f"{ats_score2}/10")

    st.markdown("---")
    if ats_score1 > ats_score2:
        st.success(f"**Overall, Resume 1 ({details1.get('Name', 'Unnamed Resume 1')}) appears to be stronger based on the scoring criteria.**")
    elif ats_score2 > ats_score1:
        st.success(f"**Overall, Resume 2 ({details2.get('Name', 'Unnamed Resume 2')}) appears to be stronger based on the scoring criteria.**")
    else:
        st.info("**Both resumes appear to be of similar strength based on the current scoring criteria.**")


# ----------------------------
# Streamlit App Starts Here
# ----------------------------

st.set_page_config(page_title="Resume Parser & Comparer", layout="wide")
st.title("📄 ResumeIQ: Resume Parser and Analyser")
st.write("Upload resumes to extract key information or compare them side-by-side.")

# Sidebar for navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a mode:", ["Parse Single Resume", "Compare Resumes"])

if app_mode == "Parse Single Resume":
    st.header("Single Resume Parser")
    st.write("Upload a PDF or DOCX resume to extract key information in a simple format.")

    # Upload file
    uploaded_file = st.file_uploader("Choose your resume file", type=["pdf", "docx"], key="single_upload")

    if uploaded_file is not None:
        # Extract text
        if uploaded_file.name.endswith(".pdf"):
            text = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.name.endswith(".docx"):
            text = extract_text_from_docx(uploaded_file)
        else:
            st.error("Unsupported file format. Please upload a .pdf or .docx file.")
            st.stop() # Stop execution if file format is not supported

        # Extract and show details
        st.success("✅ Resume uploaded and processed successfully!")
        details = extract_details(text)
        display_extracted_details(details)

        # Display ATS Score for single resume
        ats_score = calculate_resume_score(details)
        st.markdown("---")
        st.subheader("🎯 ATS Score:")
        st.metric(label=f"**{details.get('Name', 'Your Resume')} ATS Score**", value=f"{ats_score}/10")


        st.markdown("---")
        st.info("You can upload another resume to re-analyze.")

elif app_mode == "Compare Resumes":
    st.header("Resume Comparison Tool")
    st.write("Upload two PDF or DOCX resumes to compare them side-by-side.")

    col1, col2 = st.columns(2)

    # Resume 1 upload
    with col1:
        st.subheader("Resume 1")
        uploaded_file1 = st.file_uploader("Choose Resume 1 file", type=["pdf", "docx"], key="compare_upload1")
        details1 = None
        if uploaded_file1 is not None:
            if uploaded_file1.name.endswith(".pdf"):
                text1 = extract_text_from_pdf(uploaded_file1)
            elif uploaded_file1.name.endswith(".docx"):
                text1 = extract_text_from_docx(uploaded_file1)
            else:
                st.error("Unsupported file format for Resume 1. Please upload a .pdf or .docx file.")
                st.stop()
            details1 = extract_details(text1)
            # Display extracted details for Resume 1 immediately after upload
            display_extracted_details(details1, title="Extracted Details (Resume 1)")

    # Resume 2 upload
    with col2:
        st.subheader("Resume 2")
        uploaded_file2 = st.file_uploader("Choose Resume 2 file", type=["pdf", "docx"], key="compare_upload2")
        details2 = None
        if uploaded_file2 is not None:
            if uploaded_file2.name.endswith(".pdf"):
                text2 = extract_text_from_pdf(uploaded_file2)
            elif uploaded_file2.name.endswith(".docx"):
                text2 = extract_text_from_docx(uploaded_file2)
            else:
                st.error("Unsupported file format for Resume 2. Please upload a .pdf or .docx file.")
                st.stop()
            details2 = extract_details(text2)
            # Display extracted details for Resume 2 immediately after upload
            display_extracted_details(details2, title="Extracted Details (Resume 2)")

    st.markdown("---")
    if details1 and details2:
        # The comparison will be displayed only after the button is clicked
        if st.button("Compare Resumes"):
            compare_resumes(details1, details2)
    elif uploaded_file1 or uploaded_file2:
        st.warning("Please upload both resumes to compare.")
    else:
        st.info("Upload two resumes above to start the comparison.")
