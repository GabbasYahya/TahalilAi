import pytesseract
from PIL import Image
import sys
import os

# Set the path to the tesseract executable
# If tesseract is in your PATH, this line is not needed.
# Otherwise, uncomment and set the correct path, e.g.:
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\pc\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

def perform_ocr(image_path, lang='fra+eng+ara'):
    """
    Perform OCR on an image and return the text.
    """
    if not os.path.exists(image_path):
        return f"Error: File not found at {image_path}"

    try:
        image = Image.open(image_path)
        # Optional: Pre-processing can be added here (e.g., converting to grayscale)
        # image = image.convert('L') 
        text = pytesseract.image_to_string(image, lang=lang)
        return text
    except Exception as e:
        return f"Error during OCR: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ocr_service.py <image_path> [lang]")
        sys.exit(1)

    image_path = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) > 2 else 'fra+eng'
    
    result = perform_ocr(image_path, lang)
    print("--- OCR Result Start ---")
    print(result)
    print("--- OCR Result End ---")
