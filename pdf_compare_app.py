import streamlit as st
import fitz  # PyMuPDF
import difflib
from sentence_transformers import SentenceTransformer, util
from docx import Document

# Load model once
model = SentenceTransformer('all-MiniLM-L6-v2')

# Extract lines from PDF
def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    lines = []
    for page in doc:
        lines.extend(page.get_text().splitlines())
    return lines

# Extract lines from DOCX
def extract_text_from_docx(uploaded_file):
    doc = Document(uploaded_file)
    lines = [para.text for para in doc.paragraphs if para.text.strip()]
    return lines

# General file handler
def extract_lines(file):
    if file.name.endswith(".pdf"):
        return extract_text_from_pdf(file)
    elif file.name.endswith(".docx"):
        return extract_text_from_docx(file)
    else:
        return ["Unsupported file format."]

# Highlight line-by-line differences
def highlight_differences(a_lines, b_lines):
    diff = difflib.ndiff(a_lines, b_lines)
    a_diff, b_diff = [], []

    for line in diff:
        code = line[:2]
        content = line[2:]

        if code == '  ':
            a_diff.append(f'<div style="background-color: #f0f0f0; padding: 4px;">{content}</div>')
            b_diff.append(f'<div style="background-color: #f0f0f0; padding: 4px;">{content}</div>')

        elif code == '- ':
            a_diff.append(f'<div style="background-color: #ffe6e6; color: #a00; padding: 4px;">[-] {content}</div>')
        elif code == '+ ':
            b_diff.append(f'<div style="background-color: #e6ffe6; color: #0a0; padding: 4px;">[+] {content}</div>')

    return a_diff, b_diff

# Streamlit App
st.set_page_config(layout="wide")
st.title("📄 AI Document Comparison Tool")
st.write("Upload two documents (PDF or DOCX). See AI similarity and content differences.")

# Upload columns
col1, col2 = st.columns(2)

with col1:
    file1 = st.file_uploader("Upload First File (.pdf or .docx)", type=["pdf", "docx"], key="file1")

with col2:
    file2 = st.file_uploader("Upload Second File (.pdf or .docx)", type=["pdf", "docx"], key="file2")

# When both files are uploaded
if file1 and file2:
    # Extract text from both files
    lines1 = extract_lines(file1)
    lines2 = extract_lines(file2)

    # Highlight line-by-line differences
    a_diff, b_diff = highlight_differences(lines1, lines2)

    # Show side-by-side results with styled HTML
    left, right = st.columns(2)

    with left:
        st.markdown("### 📄 Document 1")
        for line in a_diff:
            st.markdown(line, unsafe_allow_html=True)

    with right:
        st.markdown("### 📄 Document 2")
        for line in b_diff:
            st.markdown(line, unsafe_allow_html=True)

else:
    st.info("Upload both files to compare them.")

