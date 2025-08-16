import streamlit as st
import fitz  # PyMuPDF
from docx import Document
import tempfile
import os
import difflib

st.markdown(
    """
    <style>
    /* Set background to indigo and text to green */
    body {background-color: indigo; color: green;}
    /* Ensure Streamlit markdown text is green */
    .stMarkdown, .stText, .stButton, .stFileUploader {color: green;}
    /* Optional: ensure sidebar is also indigo blue */
    .css-1d391kg, .css-1v3fvcr {background-color: indigo blue;}
    </style>
    """,
    unsafe_allow_html=True
)
def is_color_red_rgb(r, g, b, threshold=150):
    return (r > threshold) and (g < threshold // 2) and (b < threshold // 2)

def extract_paragraphs_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    paragraphs = []
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            paragraph_text = ""
            for line in block["lines"]:
                for span in line["spans"]:
                    color_int = span.get("color", 0)
                    r = (color_int >> 16) & 255
                    g = (color_int >> 8) & 255
                    b = color_int & 255
                    if is_color_red_rgb(r, g, b):
                        continue  # skip red text
                    paragraph_text += span.get("text", "")
                paragraph_text += "\n"
            paragraph_text = paragraph_text.strip()
            if paragraph_text:
                paragraphs.append(paragraph_text)
    return paragraphs

def extract_paragraphs_from_docx(uploaded_file):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    try:
        tmp.write(uploaded_file.read())
        tmp.close()
        doc = Document(tmp.name)
        paragraphs = []
        for para in doc.paragraphs:
            new_text = ""
            for run in para.runs:
                font_color = run.font.color
                if font_color and font_color.rgb:
                    r, g, b = font_color.rgb[0], font_color.rgb[1], font_color.rgb[2]
                    if is_color_red_rgb(r, g, b):
                        continue  # skip red text runs
                new_text += run.text
            new_text = new_text.strip()
            if new_text:
                paragraphs.append(new_text)
    finally:
        os.unlink(tmp.name)
    return paragraphs

def extract_paragraphs(file):
    if file.name.endswith(".pdf"):
        return extract_paragraphs_from_pdf(file)
    elif file.name.endswith(".docx"):
        return extract_paragraphs_from_docx(file)
    else:
        return []

def trim_paragraphs_by_dear_and_kindregards(paragraphs):
    result = []
    inside_block = False
    for para in paragraphs:
        lower_para = para.lower()
        if "dear" in lower_para:
            inside_block = True
            result.append(para)
        elif "kind regards" in lower_para:
            inside_block = False
        else:
            if inside_block:
                result.append(para)
    return result

def highlight_word_differences(text1, text2):
    words1 = text1.split()
    words2 = text2.split()
    matcher = difflib.SequenceMatcher(None, words1, words2)

    def get_highlighted_line(words, opcodes, is_first):
        result = []
        for tag, i1, i2, j1, j2 in opcodes:
            segment = words[i1:i2] if is_first else words[j1:j2]
            segment_text = " ".join(segment)
            if tag == "equal":
                result.append(segment_text)
            else:
                result.append(f'<span style="background-color: #ffeb3b">{segment_text}</span>')
        return " ".join(result)

    opcodes = matcher.get_opcodes()
    highlighted1 = get_highlighted_line(words1, opcodes, True)
    highlighted2 = get_highlighted_line(words2, opcodes, False)

    return highlighted1, highlighted2

def compare_and_align_paragraphs(paras1, paras2):
    matcher = difflib.SequenceMatcher(None, paras1, paras2)
    result1 = []
    result2 = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for idx1, idx2 in zip(range(i1, i2), range(j1, j2)):
                h1, h2 = highlight_word_differences(paras1[idx1], paras2[idx2])
                result1.append(f'<div style="background-color:white; padding:4px;">{h1}</div>')
                result2.append(f'<div style="background-color:white; padding:4px;">{h2}</div>')
        elif tag == "replace":
            max_len = max(i2 - i1, j2 - j1)
            for k in range(max_len):
                p1 = paras1[i1 + k] if i1 + k < i2 else ""
                p2 = paras2[j1 + k] if j1 + k < j2 else ""
                if p1 and p2:
                    h1, h2 = highlight_word_differences(p1, p2)
                    result1.append(f'<div style="background-color:white; padding:4px;">{h1}</div>')
                    result2.append(f'<div style="background-color:white; padding:4px;">{h2}</div>')
                elif p1:
                    result1.append(f'<div style="background-color:white; padding:4px;">{p1}</div>')
                    result2.append('<div style="background-color:white; padding:4px;"></div>')
                else:
                    result1.append('<div style="background-color:white; padding:4px;"></div>')
                    result2.append(f'<div style="background-color:white; padding:4px;">{p2}</div>')
        elif tag == "delete":
            for idx in range(i1, i2):
                p = paras1[idx]
                result1.append(f'<div style="background-color:white; padding:4px;">{p}</div>')
                result2.append('<div style="background-color:white; padding:4px;"></div>')
        elif tag == "insert":
            for idx in range(j1, j2):
                p = paras2[idx]
                result1.append('<div style="background-color:white; padding:4px;"></div>')
                result2.append(f'<div style="background-color:white; padding:4px;">{p}</div>')

    return result1, result2

# Streamlit app
st.set_page_config(layout="wide")
st.title("📄 Testors Doc Comp")

col1, col2 = st.columns(2)

with col1:
    file1 = st.file_uploader("Upload First File (.pdf or .docx)", type=["pdf", "docx"])

with col2:
    file2 = st.file_uploader("Upload Second File (.pdf or .docx)", type=["pdf", "docx"])

if file1 and file2:
    paras1 = extract_paragraphs(file1)
    paras2 = extract_paragraphs(file2)

    paras1 = trim_paragraphs_by_dear_and_kindregards(paras1)
    paras2 = trim_paragraphs_by_dear_and_kindregards(paras2)

    if not paras1 or not paras2:
        st.error("Could not extract paragraphs from one or both files.")
    else:
        aligned1, aligned2 = compare_and_align_paragraphs(paras1, paras2)

        left, right = st.columns(2)

        with left:
            st.markdown("### 📄 Document 1")
            for para_html in aligned1:
                st.markdown(para_html, unsafe_allow_html=True)

        with right:
            st.markdown("### 📄 Document 2")
            for para_html in aligned2:
                st.markdown(para_html, unsafe_allow_html=True)
else:
    st.info("Upload both files to compare.")
