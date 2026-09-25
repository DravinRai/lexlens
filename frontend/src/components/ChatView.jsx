import { useState, useRef, useEffect } from "react";
import { Send, MessageCircle, Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";

export default function ChatView({ onSendMessage, chatHistory, isLoading }) {
  const [message, setMessage] = useState("");
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  const handleSend = () => {
    const trimmed = message.trim();
    if (!trimmed || isLoading) return;
    onSendMessage(trimmed);
    setMessage("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="card animate-in">
      <div className="card-header">
        <MessageCircle className="icon" size={20} aria-hidden="true" />
        <h2>Document Q&A</h2>
      </div>

      <p style={{ color: "var(--text-secondary)", fontSize: "0.8rem", marginBottom: "1rem" }}>
        Ask questions about your document. Answers are grounded ONLY in the document's content
        {" "}and any available jurisdictional reference data — never from general knowledge.
        Each answer cites the relevant section. For legal advice, consult a professional.
      </p>

      <div className="chat-container" role="log" aria-label="Chat conversation" aria-live="polite">
        <div className="chat-messages">
          {chatHistory.length === 0 && (
            <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "2rem 0" }}>
              <Bot size={32} style={{ marginBottom: "0.5rem", opacity: 0.5 }} aria-hidden="true" />
              <p>Ask a question about your document to get started.</p>
              <div style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "0.5rem", alignItems: "center" }}>
                <span style={{ fontSize: "0.8rem" }}>Try asking:</span>
                {[
                  "What are my key obligations under this document?",
                  "What is the termination notice period?",
                  "Are there any clauses I should be concerned about?",
                ].map((suggestion, i) => (
                  <button
                    key={i}
                    className="btn btn-secondary"
                    style={{ fontSize: "0.8rem" }}
                    onClick={() => {
                      setMessage(suggestion);
                      inputRef.current?.focus();
                    }}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {chatHistory.map((msg, i) => (
            <div key={i} className={`chat-message ${msg.role}`} role="article" aria-label={`${msg.role} message`}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem", fontSize: "0.75rem", opacity: 0.7 }}>
                {msg.role === "user" ? <User size={12} /> : <Bot size={12} />}
                {msg.role === "user" ? "You" : "LexLens"}
              </div>
              {msg.role === "assistant" ? (
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              ) : (
                <span>{msg.content}</span>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="chat-message assistant" role="status" aria-label="LexLens is thinking">
              <div className="spinner" style={{ width: "20px", height: "20px", borderWidth: "2px" }} />
              <span className="sr-only">Generating response...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <input
            ref={inputRef}
            className="chat-input"
            type="text"
            placeholder="Ask about your document..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            aria-label="Type your question about the document"
          />
          <button
            className="btn btn-primary"
            onClick={handleSend}
            disabled={!message.trim() || isLoading}
            aria-label="Send message"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
