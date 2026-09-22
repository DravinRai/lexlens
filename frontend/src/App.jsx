import { useState } from "react";
import {
  Upload, FileSearch, Globe, BarChart3, ListChecks,
  MessageCircle, GitCompare, CheckCircle
} from "lucide-react";
import UploadView from "./components/UploadView";
import JurisdictionSelector from "./components/JurisdictionSelector";
import AnalysisView from "./components/AnalysisView";
import ChecklistView from "./components/ChecklistView";
import ChatView from "./components/ChatView";
import CompareView from "./components/CompareView";
import { GlobalDisclaimer } from "./components/Disclaimer";
import * as api from "./api";
import "./index.css";

const STEPS = [
  { key: "upload", label: "Upload", icon: Upload },
  { key: "classify", label: "Classify", icon: FileSearch },
  { key: "jurisdiction", label: "Jurisdiction", icon: Globe },
  { key: "analyze", label: "Analyze", icon: BarChart3 },
];

const TABS = [
  { key: "analysis", label: "Analysis", icon: BarChart3 },
  { key: "checklist", label: "Checklist", icon: ListChecks },
  { key: "chat", label: "Q&A Chat", icon: MessageCircle },
  { key: "compare", label: "Compare", icon: GitCompare },
];

export default function App() {
  // Workflow state
  const [currentStep, setCurrentStep] = useState("upload");
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Data
  const [docType, setDocType] = useState(null);
  const [classification, setClassification] = useState(null);
  const [jurisdiction, setJurisdiction] = useState(null);
  const [hasReferenceData, setHasReferenceData] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);

  // Active tab (after analysis is complete)
  const [activeTab, setActiveTab] = useState("analysis");

  // Loading messages
  const [loadingMessage, setLoadingMessage] = useState("");

  const stepIndex = STEPS.findIndex((s) => s.key === currentStep);

  // ─── Upload Handler ──────────────────────────────────
  const handleUpload = async (file) => {
    setError(null);
    setIsLoading(true);
    setLoadingMessage("Uploading and extracting text...");
    try {
      const result = await api.uploadDocument(file);
      setSessionId(result.session_id);

      // Auto-classify
      setLoadingMessage("Classifying document type...");
      const classResult = await api.classifyDocument(result.session_id);
      setClassification(classResult);
      setDocType(classResult.doc_type);
      setCurrentStep("jurisdiction");
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setIsLoading(false);
      setLoadingMessage("");
    }
  };

  // ─── Upload Comparison Document ─────────────────────
  const handleUploadCompare = async (file) => {
    setError(null);
    setIsLoading(true);
    setLoadingMessage("Uploading comparison document...");
    try {
      await api.uploadCompareDocument(file, sessionId);
      setLoadingMessage("Comparing documents clause-by-clause...");
      const result = await api.compareDocuments(sessionId);
      setComparison(result);
      setActiveTab("compare");
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setIsLoading(false);
      setLoadingMessage("");
    }
  };

  // ─── Jurisdiction Handler ───────────────────────────
  const handleJurisdiction = async (country, state) => {
    setError(null);
    setIsLoading(true);
    setLoadingMessage("Setting jurisdiction...");
    try {
      const result = await api.setJurisdiction(sessionId, country, state);
      setJurisdiction(result.jurisdiction_display || `${country}${state ? `-${state}` : ""}`);
      setHasReferenceData(result.has_reference_data);

      // Auto-analyze
      setLoadingMessage("Analyzing document — extracting clauses, assessing risk, generating insights...");
      const analysisResult = await api.analyzeDocument(sessionId);
      setAnalysis(analysisResult);
      setCurrentStep("analyze");
      setActiveTab("analysis");
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setIsLoading(false);
      setLoadingMessage("");
    }
  };

  // ─── Chat Handler ───────────────────────────────────
  const handleChat = async (message) => {
    setChatHistory((prev) => [...prev, { role: "user", content: message }]);
    setIsLoading(true);
    try {
      const result = await api.chatMessage(sessionId, message);
      setChatHistory((prev) => [...prev, { role: "assistant", content: result.answer }]);
    } catch (err) {
      setChatHistory((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${err.response?.data?.detail || err.message}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // ─── Reset ──────────────────────────────────────────
  const handleReset = async () => {
    if (sessionId) {
      try { await api.deleteSession(sessionId); } catch {}
    }
    setCurrentStep("upload");
    setSessionId(null);
    setDocType(null);
    setClassification(null);
    setJurisdiction(null);
    setHasReferenceData(false);
    setAnalysis(null);
    setComparison(null);
    setChatHistory([]);
    setError(null);
    setActiveTab("analysis");
  };

  return (
    <div id="root">
      <div className="app-container">
        {/* ─── Header ─── */}
        <header className="app-header">
          <h1 className="logo-title">⚖️ LexLens</h1>
          <p className="logo-subtitle">AI-Powered Legal Document Assistant</p>
        </header>

        {/* ─── Step Indicator ─── */}
        <nav className="step-indicator" aria-label="Analysis progress">
          {STEPS.map((step, i) => {
            const StepIcon = step.icon;
            const isCompleted = i < stepIndex;
            const isActive = i === stepIndex;
            return (
              <div key={step.key} style={{ display: "contents" }}>
                <div
                  className={`step ${isActive ? "active" : ""} ${isCompleted ? "completed" : ""}`}
                  aria-current={isActive ? "step" : undefined}
                >
                  <div className="step-number">
                    {isCompleted ? <CheckCircle size={14} /> : <StepIcon size={14} />}
                  </div>
                  <span style={{ display: "none" }}>{step.label}</span>
                </div>
                {i < STEPS.length - 1 && (
                  <div className={`step-connector ${isCompleted ? "completed" : ""}`} />
                )}
              </div>
            );
          })}
        </nav>

        {/* ─── Classification Badge ─── */}
        {docType && (
          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem", flexWrap: "wrap", alignItems: "center" }}>
            <span className="doc-type-badge">
              <FileSearch size={14} aria-hidden="true" /> {docType}
            </span>
            {classification?.confidence && (
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                ({classification.confidence} confidence)
              </span>
            )}
            {jurisdiction && (
              <span className={`jurisdiction-badge ${hasReferenceData ? "has-data" : "no-data"}`}>
                <Globe size={14} aria-hidden="true" /> {jurisdiction}
                {hasReferenceData ? " ✓" : " (no ref data)"}
              </span>
            )}
            <button className="btn btn-ghost" onClick={handleReset} style={{ marginLeft: "auto" }}>
              ↺ New Document
            </button>
          </div>
        )}

        {/* ─── Error Display ─── */}
        {error && (
          <div className="card animate-in" style={{
            background: "var(--risk-high-bg)",
            border: "1px solid var(--risk-high-border)",
            marginBottom: "1rem",
          }}>
            <p style={{ color: "var(--risk-high)" }}>❌ {error}</p>
            <button className="btn btn-ghost" onClick={() => setError(null)} style={{ marginTop: "0.5rem" }}>
              Dismiss
            </button>
          </div>
        )}

        {/* ─── Loading State ─── */}
        {isLoading && currentStep !== "analyze" && (
          <div className="loading-spinner">
            <div className="spinner" />
            <p className="loading-text">{loadingMessage || "Processing..."}</p>
          </div>
        )}

        {/* ─── Step Content ─── */}
        {!isLoading && currentStep === "upload" && (
          <UploadView
            onUpload={handleUpload}
            onUploadCompare={handleUploadCompare}
            sessionId={sessionId}
            isLoading={isLoading}
          />
        )}

        {!isLoading && currentStep === "jurisdiction" && (
          <JurisdictionSelector
            onSubmit={handleJurisdiction}
            isLoading={isLoading}
            docType={docType}
          />
        )}

        {currentStep === "analyze" && (
          <>
            {/* Tab Navigation */}
            <nav className="nav-tabs" aria-label="Analysis views">
              {TABS.map((tab) => {
                const TabIcon = tab.icon;
                const disabled = tab.key === "compare" && !comparison;
                return (
                  <button
                    key={tab.key}
                    className={`nav-tab ${activeTab === tab.key ? "active" : ""}`}
                    onClick={() => setActiveTab(tab.key)}
                    disabled={disabled}
                    aria-selected={activeTab === tab.key}
                    role="tab"
                  >
                    <TabIcon size={16} aria-hidden="true" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>

            {/* Loading during analysis */}
            {isLoading && (
              <div className="loading-spinner">
                <div className="spinner" />
                <p className="loading-text">{loadingMessage || "Analyzing..."}</p>
              </div>
            )}

            {/* Tab Content */}
            {!isLoading && activeTab === "analysis" && (
              <AnalysisView
                analysis={analysis}
                jurisdiction={jurisdiction}
                docType={docType}
                hasReferenceData={hasReferenceData}
              />
            )}

            {!isLoading && activeTab === "checklist" && (
              <ChecklistView checklist={analysis?.checklist} />
            )}

            {activeTab === "chat" && (
              <ChatView
                onSendMessage={handleChat}
                chatHistory={chatHistory}
                isLoading={isLoading}
              />
            )}

            {activeTab === "compare" && (
              <>
                {comparison ? (
                  <CompareView comparison={comparison} />
                ) : (
                  <UploadView
                    onUpload={handleUpload}
                    onUploadCompare={handleUploadCompare}
                    sessionId={sessionId}
                    isLoading={isLoading}
                  />
                )}
              </>
            )}
          </>
        )}

        {/* ─── Global Disclaimer ─── */}
        <GlobalDisclaimer />
      </div>
    </div>
  );
}
