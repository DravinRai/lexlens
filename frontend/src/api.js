import axios from "axios";

const API_BASE = "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 min — LLM calls can be slow
});

export async function uploadDocument(file, slot = "a") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("slot", slot);
  const { data } = await api.post("/upload", formData);
  return data;
}

export async function uploadCompareDocument(file, sessionId) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("session_id", sessionId);
  const { data } = await api.post("/upload-compare", formData);
  return data;
}

export async function classifyDocument(sessionId) {
  const { data } = await api.post("/classify", { session_id: sessionId });
  return data;
}

export async function setJurisdiction(sessionId, country, state = "") {
  const { data } = await api.post("/set-jurisdiction", {
    session_id: sessionId,
    country,
    state,
  });
  return data;
}

export async function analyzeDocument(sessionId) {
  const { data } = await api.post("/analyze", { session_id: sessionId });
  return data;
}

export async function compareDocuments(sessionId) {
  const { data } = await api.post("/compare", { session_id: sessionId });
  return data;
}

export async function chatMessage(sessionId, message) {
  const { data } = await api.post("/chat", {
    session_id: sessionId,
    message,
  });
  return data;
}

export async function getSupportedJurisdictions() {
  const { data } = await api.get("/supported-jurisdictions");
  return data;
}

export async function deleteSession(sessionId) {
  const { data } = await api.delete(`/session/${sessionId}`);
  return data;
}
