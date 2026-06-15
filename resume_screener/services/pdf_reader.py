# services/pdf_reader.py
from PyPDF2 import PdfReader
from docx import Document

def extract_text_from_pdf(file):
    """从PDF文件对象提取文本"""
    pdf = PdfReader(file)
    text = ""
    for page in pdf.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(file):
    """从DOCX文件对象提取文本"""
    doc = Document(file)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text