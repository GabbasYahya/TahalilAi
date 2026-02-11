# Backend Development & AI Integration Report - TahalilAI

## 1. Executive Summary
This report outlines the technical development, architecture decisions, and testing protocols for the backend of **TahalilAI**, a local-first medical analysis interpretation tool. The system checks medical lab reports using offline OCR and Large Language Models (LLM).

## 2. Optical Character Recognition (OCR) Layer
To enable the system to "read" image-based lab reports, we integrated **Tesseract OCR**.

*   **Technology**: `pytesseract` (Python wrapper for Tesseract-OCR Engine).
*   **Configuration**: Configured for multi-language support (`eng+fra`) to handle the bilingual nature of typical medical reports.
*   **Process**:
    1.  Image Preprocessing (handled via `Pillow`).
    2.  Text Extraction.
    3.  Sanitization (removing artifacts).
*   **Testing**: Validated independently on sample "Resultats-de-laboratoire.png" files to ensure text fidelity before passing data to the AI.

## 3. Generative AI & Model Selection Strategy
This module is the core decision-making engine. We iterated through two distinct models to optimize the balance between **accuracy** and **performance**.

### Phase A: Initial Implementation (Mistral 7B)
*   **Model**: `mistral-7b-instruct-v0.2.Q4_K_M.gguf`
*   **Observation**: While highly capable, the 7-billion parameter model was extremely resource-intensive for a local CPU-based environment.
*   **Performance Issues**:
    *   Inference times often exceeded **7 minutes**.
    *   Caused browser timeouts ("Failed to fetch").
    *   High RAM consumption leading to system freeze.

### Phase B: The Switch to Ministral 3B (Current Solution)
*   **Model**: `Ministral-3-3B-Instruct-2512-Q5_K_M.gguf`
*   **Why we switched**: 
    1.  **Speed**: Reduced inference time drastically (from ~7 minutes to under 1 minute).
    2.  **Efficiency**: The 3B model offers a "sweet spot" for summarization tasks without requiring enterprise-grade GPU hardware.
    3.  **Stability**: Lower memory footprint prevents the backend from crashing the host machine.

### Technical Implementation Adjustment
We moved from basic script execution to a robust `subprocess` architecture using `llama-cli.exe`.
*   **Problem**: Direct bindings were causing "buffering deadlocks" and zombie processes that held port 8000 open.
*   **Solution**: implemented a `subprocess.communicate()` pattern to handle I/O streams safely and added strict process management to kill "zombie" AI tasks if they stall.

## 4. System Architecture & Workflow
The backend was built using **FastAPI** to ensure high performance and automatic documentation.

**The Pipeline:**
1.  **Ingestion**: User uploads image via API.
2.  **OCR**: Text is extracted from the image.
3.  **Prompt Engineering**: A medical persona prompt is constructed (injecting Age/Gender context).
4.  **Inference Interface**: The prompt is sent to `llama-cli` with a strict context window (2048/4096 tokens).
5.  **Polling Mechanism**: 
    *   *Issue*: Long-running AI tasks caused HTTP timeouts.
    *   *Fix*: Implemented an **Asynchronous Job Queue**. The API now returns a `job_id` immediately, and the client polls `/status/{job_id}`.

## 5. Testing & Validation
We followed a rigorous progressive testing approach:

1.  **Component Level 1 (OCR)**: Verified that text extraction correctly identified medical terms (e.g., "Hématocrite", "Cholestérol").
2.  **Component Level 2 (AI Model)**: Ran the model in isolation via CLI to tune parameters (Context Window, Temperature) for optimal coherence.
3.  **Integration Testing**: Combined OCR output -> AI Input. Verified that the AI didn't hallucinate values not present in the OCR text.
4.  **Automated API Tests**: Added `pytest` suite ensuring:
    *   Server Health (`200 OK`)
    *   Upload Flow
    *   Job Status Logic

## 6. API Documentation (Swagger UI)
Automatic interactive documentation is provided by FastAPI/Swagger. This allows the team to test endpoints without a frontend.

*   **URL**: `http://localhost:8000/docs`

### Swagger Interface Screenshots
*[Place screenshot of Swagger UI showing POST /analyze endpoint here]*

*[Place screenshot of Swagger UI showing GET /status/{job_id} endpoint here]*

## 7. Conclusion
The backend is now a stable, independent microservice. It successfully decouples the heavy AI processing from the web server using asynchronous background tasks, ensuring the application remains responsive even during complex analysis.
