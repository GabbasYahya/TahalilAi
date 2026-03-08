"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import { ProcessingLoader } from "@/components/ProcessingLoader";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function UploadPage() {
  const { t } = useLanguage();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form state
  const [file, setFile] = useState<File | null>(null);
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("");
  const [city, setCity] = useState("");
  const [cities, setCities] = useState<{ city: string; count: number }[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  // Load cities for dropdown
  useEffect(() => {
    fetch(`${API_URL}/doctors/cities`)
      .then((r) => r.json())
      .then(setCities)
      .catch(() => {});
  }, []);

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) setFile(droppedFile);
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) setFile(selected);
  };

  const handleAnalyze = async () => {
    if (!file) return;

    setIsProcessing(true);
    setProcessingStep(0);
    setStatusMessage("Uploading document...");

    try {
      const formData = new FormData();
      formData.append("file", file);
      if (age) formData.append("age", age);
      if (gender) formData.append("gender", gender);
      if (city) formData.append("city", city);

      const startResponse = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        body: formData,
      });

      const startData = await startResponse.json();

      if (!startResponse.ok) {
        throw new Error(startData.message || "Server returned an error. Is the backend running?");
      }

      if (startData.status === "error") throw new Error(startData.message);
      
      const jobId = startData.job_id;
      setStatusMessage("Document uploaded. Starting analysis...");
      
      // Poll for status every 2.5s
      let errorCount = 0;
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch(`${API_URL}/status/${jobId}`);
          const statusData = await statusRes.json();
          errorCount = 0; // Reset on success
          
          // Update live message from backend
          if (statusData.message) {
             setStatusMessage(statusData.message);
             if (statusData.message.includes("OCR") || statusData.message.includes("Extracting")) {
                 setProcessingStep(0);
             } else if (statusData.message.includes("AI") || statusData.message.includes("analyzing")) {
                 setProcessingStep(1);
             } else if (statusData.message.includes("Generating") || statusData.message.includes("Audio") || statusData.message.includes("PDF")) {
                 setProcessingStep(2);
             }
          }

          if (statusData.status === "completed") {
            clearInterval(pollInterval);
            setProcessingStep(2);
            setStatusMessage("Analysis complete! Loading results...");
            
            localStorage.setItem("analysisResult", JSON.stringify({
              job_id: statusData.result.job_id || jobId,
              text: statusData.result.analysis,
              audioUrl: statusData.result.audio_url,
              pdfUrl: statusData.result.pdf_url,
              recommended_specialities: statusData.result.recommended_specialities || [],
              urgency: statusData.result.urgency || "routine",
              recommended_doctors: statusData.result.recommended_doctors || [],
              timestamp: Date.now()
            }));
            
            await new Promise((r) => setTimeout(r, 600));
            router.push("/results");
          } else if (statusData.status === "failed") {
            clearInterval(pollInterval);
            setStatusMessage("Analysis failed.");
            alert("Analysis failed: " + (statusData.error || "Unknown error"));
            setIsProcessing(false);
          }
        } catch (err) {
            errorCount++;
            console.warn("Polling attempt failed:", err);
            setStatusMessage(`Reconnecting... (attempt ${errorCount}/10)`);
            if (errorCount > 10) {
                clearInterval(pollInterval);
                setStatusMessage("Connection lost. Please check if the backend server is running.");
                alert("Connection error: Failed to reach the analysis server. Please check if the backend is running on port 8000.");
                setIsProcessing(false);
            }
        }
      }, 3000);

    } catch (error: any) {
      console.error(error);
      alert(error.message || "Failed to connect to the analysis server. Is the backend running?");
      setIsProcessing(false);
    }
  };

  // ─── Processing Screen ───
  if (isProcessing) {
    return (
      <div className="flex min-h-[80vh] items-center justify-center px-4">
        <div className="w-full max-w-md">
          <div className="rounded-3xl border border-slate-100 bg-white p-8 shadow-2xl shadow-slate-200/50">
            <ProcessingLoader currentStep={processingStep} customMessage={statusMessage} />
          </div>
          <p className="mt-4 text-center text-xs text-slate-400">
            This may take 30-90 seconds depending on document complexity.
          </p>
        </div>
      </div>
    );
  }

  // ─── Upload Form ───
  return (
    <div className="flex min-h-[80vh] items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg">
        <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-2xl shadow-slate-200/50 sm:p-8">
          
          {/* Title */}
          <div className="mb-6 text-center">
            <h2 className="text-xl font-bold text-slate-900">{t("upload.title")}</h2>
            <p className="mt-1 text-sm text-slate-400">Upload your lab results for AI-powered analysis</p>
          </div>

          {/* Upload Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`flex cursor-pointer flex-col items-center gap-4 rounded-2xl border-2 border-dashed p-8 text-center transition-all duration-200 ${
              isDragging
                ? "border-indigo-500 bg-indigo-50 scale-[1.02]"
                : file
                ? "border-emerald-300 bg-emerald-50/50"
                : "border-slate-200 bg-slate-50 hover:border-indigo-300 hover:bg-indigo-50/30"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={handleFileChange}
              className="hidden"
            />

            {file ? (
              <>
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-600">
                  <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">{file.name}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); setFile(null); }}
                  className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-500 hover:bg-red-50 hover:text-red-500 transition-colors"
                >
                  Remove file
                </button>
              </>
            ) : (
              <>
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-100 text-indigo-600">
                  <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-700">{t("upload.dragText")}</p>
                  <p className="mt-1 text-xs text-slate-400">{t("upload.formats")}</p>
                </div>
              </>
            )}
          </div>

          {/* Context Fields */}
          <div className="mt-6 space-y-4">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{t("upload.helperText")}</p>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-slate-600">{t("upload.age")}</label>
                <input
                  type="number"
                  min={0}
                  max={150}
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                  placeholder="e.g. 35"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 placeholder-slate-400 outline-none transition-all focus:border-indigo-400 focus:bg-white focus:ring-2 focus:ring-indigo-100"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-medium text-slate-600">{t("upload.gender")}</label>
                <select
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none transition-all focus:border-indigo-400 focus:bg-white focus:ring-2 focus:ring-indigo-100"
                >
                  <option value="">Select</option>
                  <option value="male">{t("upload.genderMale")}</option>
                  <option value="female">{t("upload.genderFemale")}</option>
                </select>
              </div>
            </div>

            {/* City for doctor recommendations */}
            <div>
              <label className="mb-1.5 block text-xs font-medium text-slate-600">{t("upload.city")}</label>
              <select
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none transition-all focus:border-indigo-400 focus:bg-white focus:ring-2 focus:ring-indigo-100"
              >
                <option value="">{t("upload.cityPlaceholder")}</option>
                {cities.map((c) => (
                  <option key={c.city} value={c.city}>
                    {c.city}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Analyze Button */}
          <button
            onClick={handleAnalyze}
            disabled={!file}
            className={`mt-6 w-full rounded-2xl py-3.5 text-sm font-bold tracking-wide transition-all duration-200 ${
              file
                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/25 hover:bg-indigo-700 hover:shadow-indigo-500/30 active:scale-[0.98]"
                : "cursor-not-allowed bg-slate-100 text-slate-400"
            }`}
          >
            {file ? "Analyze Results" : t("upload.analyze")}
          </button>
        </div>
      </div>
    </div>
  );
}
