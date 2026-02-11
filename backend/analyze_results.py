import sys
import os
import subprocess
from ocr_service import perform_ocr

# Paths
# Assumes this script is in tahalilAillm/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LLAMA_CLI_PATH = os.path.join(BASE_DIR, "bin", "llama-cli.exe")
MODEL_PATH = os.path.join(BASE_DIR, "Models", "Ministral-3-3B-Instruct-2512-Q5_K_M.gguf")

def analyze_image(image_path):
    # 1. Perform OCR
    print("Extracting text from image... (This may take a moment)", file=sys.stderr)
    ocr_text = perform_ocr(image_path, lang='fra+eng')
    
    if "Error" in ocr_text and len(ocr_text) < 50:
         # If it's a short error message
         print(ocr_text)
         return

    print("Text extracted. Analyzing with AI...", file=sys.stderr)

    # 2. Construct Prompt
    system_prompt = """You are a medical explanation assistant.
Your role is ONLY to explain medical analysis results in very simple language.
You do NOT diagnose diseases.
You do NOT give treatment advice.

Rules:
- Use simple words (explain like to a 12-year-old)
- Explain what the value measures
- Say if it is low, normal, or high based on the provided values
- Explain why doctors care about it
- Be calm and reassuring
- If abnormal, recommend seeing a doctor politely
- Format your response with clear bullet points for each parameter found

Never say:
- "You have X disease"
- "You should take medication"
"""
    
    user_input = f"Here are the text results extracted from a lab report:\n\n{ocr_text}\n\nPlease explain these results strictly following the rules."

    # Mistral Instruct Format: [INST] Instruction [/INST]
    full_prompt = f"[INST] {system_prompt}\n\n{user_input} [/INST]"

    # 3. Call llama-cli
    cmd = [
        LLAMA_CLI_PATH,
        "-m", MODEL_PATH,
        "-p", full_prompt,
        "-n", "1024",       # Max tokens to predict
        "-c", "4096",       # Limit context to 4k to save RAM
        "--temp", "0.7",    # Temperature
        "--no-display-prompt", # Don't echo the prompt back
        "-t", "4"           # Threads (adjust based on CPU)
    ]

    try:
        # Run process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, # Capture stderr to keep terminal clean-ish
            text=True,
            encoding='utf-8',
            cwd=BASE_DIR # Run inside tahalilAillm directory so dependencies (dlls) are found if needed
        )
        
        # Stream output line by line or wait for finish? 
        # Waiting is safer for now to avoid token printing issues in this environment
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"Error running AI model: {stderr}")
            # Fallback printing just in case stdout has something
            if stdout: print(stdout)
        else:
            # Print the AI's response
            print("\n--- AI Analysis ---")
            print(stdout)
            print("-------------------")
            
    except Exception as e:
        print(f"Failed to execute AI model: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_results.py <image_path>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    # Ensure image path is absolute if possible, or relative to CWD
    analyze_image(image_path)
