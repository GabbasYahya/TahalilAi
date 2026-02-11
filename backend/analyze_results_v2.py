import sys
import os
import re
import subprocess
from ocr_service import perform_ocr

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LLAMA_CLI_PATH = os.path.join(BASE_DIR, "bin", "llama-cli.exe")
MODEL_PATH = os.path.join(BASE_DIR, "Models", "Ministral-3-3B-Instruct-2512-Q5_K_M.gguf")

# Generous timeout for CPU inference — large reports with 700+ chars of OCR can take 5+ minutes
MODEL_TIMEOUT = 600

def clean_llm_output(raw_output):
    """Remove ALL llama-cli noise: ASCII art, prompt echo, build info, speed stats, etc."""
    text = raw_output

    # STRATEGY: Find the LAST occurrence of [/INST] — everything after is the actual model response
    inst_marker = "[/INST]"
    last_inst = text.rfind(inst_marker)
    if last_inst != -1:
        text = text[last_inst + len(inst_marker):]

    # Also try: if [SYSTEM_PROMPT] is present, cut from after the last template block
    sys_marker = "[/SYSTEM_PROMPT]"
    if sys_marker in text:
        last_sys = text.rfind(inst_marker)
        if last_sys != -1:
            text = text[last_sys + len(inst_marker):]

    # Remove trailing speed stats: [ Prompt: X t/s | Generation: Y t/s ]
    text = re.sub(r'\[\s*Prompt:\s*[\d.]+\s*t/s\s*\|\s*Generation:\s*[\d.]+\s*t/s\s*\]', '', text)

    # Remove "Exiting..." line
    text = re.sub(r'Exiting\.\.\.\s*$', '', text)

    # Remove leading ">" prompt markers
    text = re.sub(r'^\s*>\s*', '', text)

    # Remove ASCII art banner (block drawing characters ▄█▀░▓▒)
    text = re.sub(r'[░▒▓█▄▀▐▌▖▗▘▙▚▛▜▝▞▟]+', '', text)

    # Remove loading spinner (braille patterns U+2800-U+28FF)
    text = re.sub(r'[\u2800-\u28FF]+', '', text)
    text = re.sub(r'Loading model[.\s]*', '', text)

    # Remove build/model/modalities info lines
    text = re.sub(r'^build\s*:.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^model\s*:.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^modalities\s*:.*$', '', text, flags=re.MULTILINE)

    # Remove "available commands:" block (multi-line)
    text = re.sub(r'available commands:.*?(?=\n\n)', '', text, flags=re.DOTALL)

    # Remove any leftover [SYSTEM_PROMPT]...[/SYSTEM_PROMPT] or [INST]...[/INST] blocks
    text = re.sub(r'\[SYSTEM_PROMPT\].*?\[/SYSTEM_PROMPT\]', '', text, flags=re.DOTALL)
    text = re.sub(r'\[INST\].*?\[/INST\]', '', text, flags=re.DOTALL)

    # Remove stray template markers
    text = text.replace('[SYSTEM_PROMPT]', '').replace('[/SYSTEM_PROMPT]', '')
    text = text.replace('[INST]', '').replace('[/INST]', '')

    # Collapse multiple blank lines into max 2
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

def analyze_image(image_path, age=None, gender=None):
    # 1. Perform OCR
    print(f"--- Step 1: Reading Text from {os.path.basename(image_path)} ---", file=sys.stderr)
    ocr_text = perform_ocr(image_path, lang='fra+eng')
    
    if "Error" in ocr_text and len(ocr_text) < 50:
         print(f"OCR Failed: {ocr_text}")
         return f"Error during OCR: {ocr_text}"

    print(f"Text read successfully ({len(ocr_text)} characters).", file=sys.stderr)
    print("--- Step 2: Running Medical AI Analysis ---", file=sys.stderr)

    # 2. Build prompt using the model's CORRECT template format
    # Ministral-3B uses: [SYSTEM_PROMPT]...[/SYSTEM_PROMPT][INST]...[/INST]
    system_prompt = """You are a medical explanation assistant.
Your task is to convert complex medical lab results into a simple, easy-to-read summary.
Rules:
- Start DIRECTLY with the analysis.
- Use simple language.
- For each parameter: name it, state the value, say if it's Normal/High/Low, and briefly explain.
- Do NOT diagnose or treat.
- Do NOT ask questions at the end.
Format: **Parameter Name**: Value (Status) - Explanation."""
    
    patient_context = ""
    if age and gender:
        patient_context = f"Patient info: {age} years old, {gender}.\n"
    elif age:
        patient_context = f"Patient info: {age} years old.\n"
    elif gender:
        patient_context = f"Patient info: {gender}.\n"

    user_input = f"{patient_context}Lab Results:\n{ocr_text}\n\nExplain these results."

    full_prompt = f"[SYSTEM_PROMPT] {system_prompt} [/SYSTEM_PROMPT][INST] {user_input} [/INST]"

    # 3. Call llama-cli with --single-turn to generate once and EXIT
    cmd = [
        LLAMA_CLI_PATH,
        "-m", MODEL_PATH,
        "-p", full_prompt,
        "-n", "900",       # Max tokens to predict
        "-c", "2048",      # Limit context to 2k to save RAM (OCR + prompt can be large)
        "--temp", "0.5",
        "--no-display-prompt",
        "--single-turn",     # CRITICAL: generates one response then exits (no interactive loop)
        "-t", "4",
    ]

    try:
        print(f"[AI] Starting inference (timeout={MODEL_TIMEOUT}s)...", file=sys.stderr)
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding='utf-8',
            cwd=BASE_DIR
        )
        
        try:
            captured_output, stderr_output = process.communicate(timeout=MODEL_TIMEOUT)
        except subprocess.TimeoutExpired:
            print(f"[ERROR] Model timed out after {MODEL_TIMEOUT}s, killing.", file=sys.stderr)
            process.kill()
            process.communicate()
            return "Error: AI model timed out. Please try again."
        
        print(f"[AI] Done. Exit code: {process.returncode}, Output: {len(captured_output)} chars", file=sys.stderr)

        # Save report to file
        result = clean_llm_output(captured_output)
        if result:
            base_name = os.path.basename(image_path)
            file_name_without_ext = os.path.splitext(base_name)[0]
            output_file = os.path.join(os.path.dirname(image_path), f"{file_name_without_ext}_analysis.txt")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("--- MEDICAL LAB REPORT EXPLANATION ---\n\n")
                f.write(result)
            print(f"[AI] Report saved to: {output_file}", file=sys.stderr)
        
        return result if result else "Error: Model returned empty output."

    except FileNotFoundError:
        return f"Error: llama-cli.exe not found at {LLAMA_CLI_PATH}"
    except Exception as e:
        try:
            process.kill()
        except:
            pass
        return f"Error executing AI model: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_results_v2.py <image_path> [age] [gender]")
        sys.exit(1)
        
    image_path = sys.argv[1]
    age_arg = sys.argv[2] if len(sys.argv) > 2 else None
    gender_arg = sys.argv[3] if len(sys.argv) > 3 else None

    print(analyze_image(image_path, age=age_arg, gender=gender_arg))
