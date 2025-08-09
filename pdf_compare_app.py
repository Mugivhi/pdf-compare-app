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
            a_diff.append(content)
            b_diff.append(content)
        elif code == '- ':
            a_diff.append(f"🟥 [-] {content}")
        elif code == '+ ':
            b_diff.append(f"🟩 [+] {content}")

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
    with st.spinner("Processing and comparing..."):
        lines1 = extract_lines(file1)
        lines2 = extract_lines(file2)

        text1 = "\n".join(lines1)
        text2 = "\n".join(lines2)

        # Semantic similarity
        emb1 = model.encode(text1, convert_to_tensor=True)
        emb2 = model.encode(text2, convert_to_tensor=True)
        similarity = util.cos_sim(emb1, emb2).item()

        st.success(f"Semantic Similarity Score: **{similarity:.2f}**")

        # Differences
        a_diff, b_diff = highlight_differences(lines1, lines2)

        # Display side-by-side
        left, right = st.columns(2)

        with left:
            st.markdown("### 📄 Document 1")
            st.code("\n".join(a_diff), language="text")

        with right:
            st.markdown("### 📄 Document 2")
            st.code("\n".join(b_diff), language="text")
else:
    st.info("Upload both files to compare them.")
