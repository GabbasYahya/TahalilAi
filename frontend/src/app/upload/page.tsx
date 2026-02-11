"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import { ProcessingLoader } from "@/components/ProcessingLoader";

/**
 * Upload Page — the most critical UX screen.
 * Centered card, drag-and-drop, optional context fields.
 * Emotionally calm, never overwhelming.
 */
export default function UploadPage() {
  const { t } = useLanguage();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form state
  const [file, setFile] = useState<File | null>(null);
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("");
  const [symptoms, setSymptoms] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState(0);

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
    setProcessingStep(0); // Uploading...
    
    // Slight delay to visual "Uploading" state before "Processing"
    // This makes the transition feel more natural
    await new Promise(r => setTimeout(r, 800));
    setProcessingStep(1); // "Processing / Understanding..."

    try {
      const formData = new FormData();
      formData.append("file", file);
      if (age) formData.append("age", age);
      if (gender) formData.append("gender", gender);

      // 1. Start Analysis
      const startResponse = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        body: formData,
      });

      if (!startResponse.ok) throw new Error("Analysis failed to start");
      const startData = await startResponse.json();
      
      if (startData.status === "error") throw new Error(startData.message);
      
      const jobId = startData.job_id;
      
      // 2. Poll for Status
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch(`http://localhost:8000/status/${jobId}`);
          const statusData = await statusRes.json();
          
          if (statusData.status === "completed") {
            clearInterval(pollInterval);
            
            setProcessingStep(2); // Finalizing...
            // Store results
            localStorage.setItem("analysisResult", JSON.stringify({
              text: statusData.result.analysis,
              reportPath: statusData.result.report_path,
              timestamp: Date.now()
            }));
            
            await new Promise((r) => setTimeout(r, 800));
            router.push("/results");
          } else if (statusData.status === "failed") {
            clearInterval(pollInterval);
            alert("Analysis failed: " + statusData.error);
            setIsProcessing(false);
          }
           // else: keep waiting ("processing" or "queued")
        } catch (err) {
            console.error("Polling error", err);
            // Don't clear interval immediately on loose network flake, but maybe count errors?
        }
      }, 2000);

    } catch (error) {
      console.error(error);
      alert("Failed to connect to the analysis server.");
      setIsProcessing(false);
    }
  };

  // Show processing state
  if (isProcessing) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center px-4">
        <div className="w-full max-w-md rounded-3xl border border-gray-100 bg-white p-8 shadow-xl shadow-gray-100/50">
          <ProcessingLoader currentStep={processingStep} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-[70vh] items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg">
        <div className="rounded-3xl border border-gray-100 bg-white p-6 shadow-xl shadow-gray-100/50 sm:p-8">
          {/* ─── Upload Zone ─── */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`flex cursor-pointer flex-col items-center gap-4 rounded-2xl border-2 border-dashed p-8 text-center transition-all ${
              isDragging
                ? "border-primary-500 bg-primary-50"
                : file
                ? "border-primary-300 bg-primary-50/50"
                : "border-gray-200 bg-gray-50 hover:border-primary-300 hover:bg-primary-50/30"
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
                {/* File selected state */}
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-100 text-primary-600">
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{file.name}</p>
                  <p className="mt-1 text-xs text-gray-500">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                  }}
                  className="text-xs text-gray-400 underline hover:text-gray-600"
                >
                  Remove
                </button>
              </>
            ) : (
              <>
                {/* Empty state */}
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-100 text-primary-600">
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700">
                    {t("upload.title")}
                  </p>
                  <p className="mt-1 text-xs text-gray-400">
                    {t("upload.dragText")}
                  </p>
                </div>
                <p className="text-xs text-gray-400">{t("upload.formats")}</p>
              </>
            )}
          </div>

          {/* ─── Optional Context Fields ─── */}
          <div className="mt-6 space-y-4">
            <p className="text-xs text-gray-400">{t("upload.helperText")}</p>

            <div className="grid grid-cols-2 gap-3">
              {/* Age */}
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600">
                  {t("upload.age")}
                </label>
                <input
                  type="number"
                  min={0}
                  max={150}
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                  placeholder="—"
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 outline-none transition-colors focus:border-primary-400 focus:bg-white focus:ring-2 focus:ring-primary-100"
                />
              </div>

              {/* Gender */}
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600">
                  {t("upload.gender")}
                </label>
                <select
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm text-gray-900 outline-none transition-colors focus:border-primary-400 focus:bg-white focus:ring-2 focus:ring-primary-100"
                >
                  <option value="">—</option>
                  <option value="male">{t("upload.genderMale")}</option>
                  <option value="female">{t("upload.genderFemale")}</option>
                </select>
              </div>
            </div>

            {/* Symptoms */}
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">
                {t("upload.symptoms")}
              </label>
              <textarea
                value={symptoms}
                onChange={(e) => setSymptoms(e.target.value)}
                placeholder={t("upload.symptomsPlaceholder")}
                rows={3}
                className="w-full resize-none rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 outline-none transition-colors focus:border-primary-400 focus:bg-white focus:ring-2 focus:ring-primary-100"
              />
            </div>
          </div>

          {/* ─── Analyze Button ─── */}
          <button
            onClick={handleAnalyze}
            disabled={!file}
            className={`mt-6 w-full rounded-full py-3.5 text-sm font-semibold transition-all ${
              file
                ? "bg-primary-600 text-white shadow-lg shadow-primary-500/20 hover:bg-primary-700 active:scale-[0.98]"
                : "cursor-not-allowed bg-gray-100 text-gray-400"
            }`}
          >
            {t("upload.analyze")}
          </button>
        </div>
      </div>
    </div>
  );
}
