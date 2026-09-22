import { useState, useRef } from "react";
import { Upload, FileText, X, GitCompare } from "lucide-react";

export default function UploadView({ onUpload, onUploadCompare, sessionId, isLoading }) {
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState(null);
  const [compareFile, setCompareFile] = useState(null);
  const [mode, setMode] = useState("single"); // "single" or "compare"
  const fileInputRef = useRef(null);
  const compareInputRef = useRef(null);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  };

  const handleFileChange = (e) => {
    if (e.target.files[0]) setFile(e.target.files[0]);
  };

  const handleCompareFileChange = (e) => {
    if (e.target.files[0]) setCompareFile(e.target.files[0]);
  };

  const handleSubmit = () => {
    if (!file) return;
    onUpload(file);
  };

  const handleCompareSubmit = () => {
    if (!compareFile || !sessionId) return;
    onUploadCompare(compareFile);
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="animate-in">
      {/* Mode Toggle */}
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem" }}>
        <button
          className={`btn ${mode === "single" ? "btn-primary" : "btn-secondary"}`}
          onClick={() => setMode("single")}
          aria-pressed={mode === "single"}
        >
          <FileText size={16} aria-hidden="true" /> Analyze Document
        </button>
        <button
          className={`btn ${mode === "compare" ? "btn-primary" : "btn-secondary"}`}
          onClick={() => setMode("compare")}
          aria-pressed={mode === "compare"}
        >
          <GitCompare size={16} aria-hidden="true" /> Compare Documents
        </button>
      </div>

      {/* Primary Upload */}
      <div className="card">
        <div className="card-header">
          <Upload className="icon" size={20} aria-hidden="true" />
          <h2>{mode === "compare" ? "Document A" : "Upload Document"}</h2>
        </div>

        <div
          className={`upload-zone ${dragOver ? "drag-over" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          aria-label="Upload document. Click or drag and drop a file."
          onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") fileInputRef.current?.click(); }}
        >
          <div className="icon-large" aria-hidden="true">
            <Upload size={48} />
          </div>
          <p>Drop your document here or click to browse</p>
          <p className="supported-formats">Supported: PDF, DOCX, TXT (max 2 MB)</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={handleFileChange}
            style={{ display: "none" }}
            aria-label="Select document file"
          />
        </div>

        {file && (
          <div className="file-info">
            <FileText size={18} aria-hidden="true" />
            <span className="filename">{file.name}</span>
            <span className="file-size">{formatSize(file.size)}</span>
            <button
              className="btn-ghost"
              onClick={(e) => { e.stopPropagation(); setFile(null); }}
              aria-label={`Remove ${file.name}`}
            >
              <X size={16} />
            </button>
          </div>
        )}

        {file && !sessionId && (
          <div style={{ marginTop: "1rem", textAlign: "right" }}>
            <button
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={isLoading}
              aria-label="Upload and analyze document"
            >
              {isLoading ? "Uploading..." : "Upload & Analyze"}
            </button>
          </div>
        )}
      </div>

      {/* Comparison Upload */}
      {mode === "compare" && sessionId && (
        <div className="card animate-in" style={{ marginTop: "1rem" }}>
          <div className="card-header">
            <GitCompare className="icon" size={20} aria-hidden="true" />
            <h2>Document B (Comparison)</h2>
          </div>

          <div
            className="upload-zone"
            onClick={() => compareInputRef.current?.click()}
            role="button"
            tabIndex={0}
            aria-label="Upload comparison document"
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") compareInputRef.current?.click(); }}
          >
            <p>Upload a second document to compare clause-by-clause</p>
            <p className="supported-formats">Supported: PDF, DOCX, TXT (max 2 MB)</p>
            <input
              ref={compareInputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleCompareFileChange}
              style={{ display: "none" }}
              aria-label="Select comparison document file"
            />
          </div>

          {compareFile && (
            <>
              <div className="file-info">
                <FileText size={18} aria-hidden="true" />
                <span className="filename">{compareFile.name}</span>
                <span className="file-size">{formatSize(compareFile.size)}</span>
                <button
                  className="btn-ghost"
                  onClick={() => setCompareFile(null)}
                  aria-label={`Remove ${compareFile.name}`}
                >
                  <X size={16} />
                </button>
              </div>
              <div style={{ marginTop: "1rem", textAlign: "right" }}>
                <button
                  className="btn btn-primary"
                  onClick={handleCompareSubmit}
                  disabled={isLoading}
                >
                  {isLoading ? "Uploading..." : "Upload for Comparison"}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
