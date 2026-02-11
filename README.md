# TahalilAI

**TahalilAI** is a privacy-focused, local-first web application designed to interpret medical laboratory reports. By leveraging OCR (Optical Character Recognition) and a locally running Large Language Model (LLM), it converts complex medical data into easy-to-understand summaries without sending sensitive patient data to external cloud servers.

![Integration](https://img.shields.io/badge/Status-Beta-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Privacy](https://img.shields.io/badge/Privacy-Local--First-red)

## 🚀 Key Features

*   **🔒 Privacy First**: All processing (OCR & AI analysis) happens locally on your machine. No data leaves your network.
*   **📄 OCR Integration**: Extracts text from images of lab reports (supports English, French, and Arabic) using Tesseract.
*   **🤖 Local AI Analysis**: Uses optimized quantized LLMs (like Ministral 3B) to interpret results and provide simplified explanations.
*   **⚡ Modern Stack**: Built with **Next.js 15** (Frontend) and **FastAPI** (Backend).
*   **🏎️ Efficiency**: Asynchronous background processing ensures the UI remains responsive even during heavy AI inference.

---

## 🛠️ Tech Stack

### Frontend
*   **Next.js 15**: React framework for the UI.
*   **Tailwind CSS**: For responsive and modern styling.
*   **TypeScript**: Ensures type safety.

### Backend
*   **FastAPI**: High-performance Python web framework.
*   **Tesseract OCR**: For extracting text from report images.
*   **Llama.cpp (via CLI)**: Efficient CPU-based inference for running LLMs locally.
*   **Python Subprocesses**: Manages AI tasks safely with timeouts and resource limits.

---

## 📦 Installation & Setup

### Prerequisites
1.  **Node.js** (v18 or newer)
2.  **Python** (v3.10 or newer)
3.  **Tesseract OCR**:
    *   **Windows**: [Download Installer](https://github.com/UB-Mannheim/tesseract/wiki)
    *   **Linux**: `sudo apt install tesseract-ocr tesseract-ocr-fra tesseract-ocr-ara`
    *   *Note: Ensure Tesseract is in your system PATH or configured in `ocr_service.py`.*

### 1. Clone the Repository
```bash
git clone https://github.com/GabbasYahya/TahalilAi.git
cd TahalilAi
```

### 2. Backend Setup
Navigate to the backend folder and set up a virtual environment.

```bash
cd backend
python -m venv .venv
# Activate:
# Windows:
.venv\Scripts\activate
# Linux/Mac:
# source .venv/bin/activate

pip install -r requirements.txt
```

**Model & Binaries Setup**:
Since the repo does not include heavy binary files, you need to:
1.  Download `llama-cli.exe` (from [llama.cpp releases](https://github.com/ggerganov/llama.cpp/releases)) and place it in `backend/bin/`.
2.  Download a GGUF model (e.g., `Ministral-3-3B-Instruct...gguf`) and place it in `backend/Models/`.
3.  *Optional*: Update `analyze_results_v2.py` if your model filename differs.

**Run the Server**:
```bash
uvicorn server:app --reload
```
The API will run at `http://localhost:8000`. Documentation at `/docs`.

### 3. Frontend Setup
Open a new terminal and navigate to the frontend folder.

```bash
cd frontend
npm install
npm run dev
```
The application will run at `http://localhost:3000`.

---

## 🧪 Usage Workflow

1.  Open the web app at `http://localhost:3000`.
2.  Upload an image of a medical lab report (PNG/JPG).
3.  (Optional) Provide patient context (Age/Gender).
4.  The system will:
    *   Perform OCR to extract text.
    *   Pass the text to the local LLM.
    *   Return a simplified explanation of the results.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to verify the `BACKEND_DEVELOPMENT_REPORT.pdf` (compiled from `.tex`) for detailed architecture decisions.

## 📄 License

This project is licensed under the MIT License.
