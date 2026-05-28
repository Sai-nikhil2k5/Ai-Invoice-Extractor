import google.generativeai as genai
from .schemas import InvoiceData

def get_extraction_model():
    # Setup Gemini 2.5 Flash
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": InvoiceData
        }
    )
    return model

def process_invoice(file_path):
    model = get_extraction_model()
   