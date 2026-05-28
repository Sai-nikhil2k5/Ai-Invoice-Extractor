import os
import webbrowser
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from google import genai
from google.genai import types

# Load configuration
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("API Key missing from environment variables")

# Initialize clients
client = genai.Client(api_key=api_key)
app = FastAPI()

try:
    from .schemas import InvoiceData
except ImportError:
    from schemas import InvoiceData

@app.on_event("startup")
def start_browser():
    """Opens the local frontend file on server start."""
    file_path = Path("test.html").resolve()
    if file_path.exists():
        webbrowser.open_new_tab(file_path.as_uri())

@app.get("/")
async def health_check():
    return {"status": "online"}

@app.post("/extract", response_class=HTMLResponse)
async def extract_invoice(file: UploadFile = File(...)):
    # Basic file validation
    valid_formats = ["image/jpeg", "image/png", "application/pdf"]
    if file.content_type not in valid_formats:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    try:
        file_bytes = await file.read()
        
        extraction_prompt = (
            "Extract the following invoice data into JSON format: "
            "vendor name, invoice number, date, currency, and line items "
            "(description, quantity, unit price, and total). "
            "Ensure the total amount is a float."
        )

        # Process with Gemini 2.5 Flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                extraction_prompt,
                types.Part.from_bytes(data=file_bytes, mime_type=file.content_type)
            ],
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=InvoiceData,
            ),
        )

        result = response.parsed

        # Build table rows for HTML display
        rows = ""
        for item in result.line_items:
            rows += f"""
            <tr>
                <td>{item.description}</td>
                <td>{item.quantity}</td>
                <td>{item.unit_price}</td>
                <td>{item.total}</td>
            </tr>
            """

        # Simple high-readability report template
        report_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; }}
                .header {{ border-bottom: 2px solid #444; margin-bottom: 20px; }}
                .meta-data {{ display: flex; justify-content: space-between; margin-bottom: 30px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th {{ text-align: left; background: #f4f4f4; padding: 10px; border: 1px solid #ddd; }}
                td {{ padding: 10px; border: 1px solid #ddd; }}
                .summary {{ text-align: right; font-size: 1.2em; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Extraction Report</h2>
                </div>
                <div class="meta-data">
                    <div>
                        <strong>Vendor:</strong> {result.vendor_name}<br>
                        <strong>Date:</strong> {result.date}
                    </div>
                    <div>
                        <strong>Invoice Number:</strong> {result.invoice_number}
                    </div>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th>Qty</th>
                            <th>Unit Price</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                <div class="summary">
                    <strong>Total Amount: {result.total_amount} {result.currency}</strong>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=report_template)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)