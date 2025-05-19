# -*- coding: utf-8 -*-
from dotenv import load_dotenv
load_dotenv()

import base64
import streamlit as st
import os
import io
from PIL import Image
import pdf2image
import google.generativeai as genai
from docx import Document

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Functions for resume processing
def extract_text_from_docx(docx_file):
    doc = Document(docx_file)
    return "\n".join([para.text for para in doc.paragraphs])

def convert_pdf_to_image_parts(uploaded_file):
    images = pdf2image.convert_from_bytes(uploaded_file.read())
    first_page = images[0]

    img_byte_arr = io.BytesIO()
    first_page.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    return [{
        "mime_type": "image/jpeg",
        "data": base64.b64encode(img_byte_arr).decode()
    }]

def get_resume_parts(uploaded_file):
    file_type = uploaded_file.name.split('.')[-1].lower()
    if file_type == "pdf":
        return convert_pdf_to_image_parts(uploaded_file), "pdf"
    elif file_type == "docx":
        text = extract_text_from_docx(uploaded_file)
        return [text], "docx"
    else:
        raise ValueError("Unsupported file type")

def get_gemini_response(input_prompt, resume_parts, file_type, input_text):
    model = genai.GenerativeModel('gemini-1.5-flash')
    if file_type == "pdf":
        response = model.generate_content([input_prompt, resume_parts[0], input_text])
    else:
        response = model.generate_content(f"{input_prompt}\n\nResume:\n{resume_parts[0]}\n\nJob Description:\n{input_text}")
    return response.text

# --- Streamlit UI ---

st.set_page_config(page_title="✨ ATS Resume Expert", page_icon="📄", layout="wide")

st.markdown("""
    <style>
    /* Background gradient */
    .main {
        background: linear-gradient(135deg, #74ebd5 0%, #ACB6E5 100%);
        min-height: 100vh;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #333333;
    }

    /* Header styling */
    .title {
        font-size: 48px;
        font-weight: 700;
        color: #0B3954;
        text-align: center;
        margin-bottom: 5px;
    }
    .subtitle {
        font-size: 20px;
        color: #09557F;
        text-align: center;
        margin-bottom: 40px;
        font-weight: 500;
    }

    /* Text area styling */
    textarea {
        font-size: 18px !important;
        line-height: 1.6 !important;
        padding: 15px !important;
        border-radius: 12px !important;
        border: 2px solid #0B3954 !important;
        background-color: #f0faff !important;
        resize: vertical !important;
        min-height: 160px !important;
    }

    /* File uploader styling */
    .stFileUploader > div {
        border: 2px dashed #0B3954;
        border-radius: 12px;
        padding: 20px;
        background-color: #eaf6fc;
        font-weight: 600;
        font-size: 18px;
        color: #0B3954;
    }

    /* Buttons styling */
    div.stButton > button {
        background: #0B3954;
        color: white;
        font-size: 20px;
        padding: 14px 28px;
        border-radius: 15px;
        font-weight: 600;
        transition: background-color 0.3s ease;
        width: 100%;
        margin-top: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    div.stButton > button:hover {
        background: #064273;
        cursor: pointer;
    }

    /* Response box styling */
    .response-box {
        background-color: #ffffffcc;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.1);
        font-size: 18px;
        line-height: 1.5;
        color: #05386B;
        white-space: pre-wrap;
        max-height: 400px;
        overflow-y: auto;
        margin-top: 30px;
    }

    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: #0B3954;
        color: white;
        padding: 20px;
        border-radius: 15px;
    }
    .sidebar .sidebar-content h2 {
        color: #ffffff;
    }
    .sidebar .sidebar-content p {
        font-size: 16px;
        line-height: 1.5;
    }

    /* Footer */
    footer {
        text-align: center;
        color: #0B3954;
        margin: 50px 0 20px 0;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# Layout with Sidebar

with st.sidebar:
    st.markdown("<h2>💡 How to use</h2>", unsafe_allow_html=True)
    st.markdown("""
    - Paste your **Job Description** in the main area.  
    - Upload your **Resume** (PDF or Word).  
    - Choose either:
      - **Tell Me About the Resume** for detailed HR feedback, or  
      - **Percentage Match** for ATS score and missing keywords.  
    - Get instant AI-powered insights to improve your application!
    """)
    st.markdown("---")
    st.markdown("Developed by **Samvit Acharya & Lavina Tangralu** • Powered by Google Gemini API")

# Main app header
st.markdown('<div class="title">📄 ATS Resume Expert</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-powered Resume Evaluation and ATS Matching Tool</div>', unsafe_allow_html=True)

# Inputs
input_text = st.text_area("Paste the Job Description here:", placeholder="Paste job description...", key="input")

uploaded_file = st.file_uploader("Upload your Resume (PDF or Word)", type=["pdf", "docx"])

if uploaded_file:
    st.success(f"✅ Resume '{uploaded_file.name}' uploaded successfully!")

col1, col2 = st.columns([1,1], gap="large")
with col1:
    submit1 = st.button("🧠 Tell Me About the Resume")
with col2:
    submit2 = st.button("📊 Percentage Match")

input_prompt1 = """
You are an experienced Technical Human Resource Manager. Your task is to review the provided resume against the job description. 
Please share your professional evaluation on whether the candidate's profile aligns with the role. 
Highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.
"""

input_prompt2 = """
You are a skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality. 
Your task is to evaluate the resume against the provided job description. Give me the percentage of match if the resume matches
the job description. First, the output should come as percentage, then keywords missing, and lastly final thoughts.
"""

response_text = None
if (submit1 or submit2) and uploaded_file is not None:
    if not input_text.strip():
        st.warning("⚠️ Please enter the Job Description text to proceed.")
    else:
        try:
            with st.spinner("🔎 Analyzing resume and job description..."):
                resume_parts, file_type = get_resume_parts(uploaded_file)
                prompt = input_prompt1 if submit1 else input_prompt2
                response_text = get_gemini_response(prompt, resume_parts, file_type, input_text)
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
elif (submit1 or submit2) and uploaded_file is None:
    st.warning("⚠️ Please upload your resume (PDF or Word) before proceeding.")

if response_text:
    st.markdown(f'<div class="response-box">{response_text}</div>', unsafe_allow_html=True)

st.markdown("<footer>Built using Streamlit & Google Gemini API</footer>", unsafe_allow_html=True)
