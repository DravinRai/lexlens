import { CheckCircle, Circle, AlertTriangle, HelpCircle, ListChecks, MessageSquareMore } from "lucide-react";

const PRIORITY_CONFIG = {
  high: { icon: AlertTriangle, color: "var(--risk-high)" },
  medium: { icon: Circle, color: "var(--risk-medium)" },
  low: { icon: CheckCircle, color: "var(--risk-low)" },
};

export default function ChecklistView({ checklist }) {
  if (!checklist) return null;

  const { next_steps, questions_for_lawyer } = checklist;

  return (
    <div className="animate-in">
      {/* Next Steps */}
      {next_steps?.length > 0 && (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <div className="card-header">
            <ListChecks className="icon" size={20} aria-hidden="true" />
            <h2>Next Steps</h2>
          </div>

          <div role="list" aria-label="Recommended next steps">
            {next_steps.map((step, i) => {
              const config = PRIORITY_CONFIG[step.priority] || PRIORITY_CONFIG.medium;
              const PriorityIcon = config.icon;
              return (
                <div key={i} className="checklist-item" role="listitem">
                  <PriorityIcon
                    size={18}
                    className="checklist-priority"
                    style={{ color: config.color }}
                    aria-hidden="true"
                  />
                  <div className="checklist-text">
                    <div style={{ fontWeight: 500 }}>
                      <span
                        className={`risk-tag ${step.priority}`}
                        style={{ marginRight: "0.5rem", fontSize: "0.65rem" }}
                        aria-label={`${step.priority} priority`}
                      >
                        {step.priority === "high" ? "🔴" : step.priority === "medium" ? "🟡" : "🟢"}{" "}
                        {step.priority}
                      </span>
                      {step.item}
                    </div>
                    {step.reason && (
                      <div className="checklist-reason">{step.reason}</div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Questions for a Lawyer */}
      {questions_for_lawyer?.length > 0 && (
        <div className="card">
          <div className="card-header">
            <MessageSquareMore className="icon" size={20} aria-hidden="true" />
            <h2>Questions to Ask a Lawyer</h2>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "1rem" }}>
            These questions are tailored to your document and jurisdiction. Bring them
            to a consultation with a licensed attorney.
          </p>

          {questions_for_lawyer.map((q, i) => (
            <div key={i} className="question-card">
              <div className="question-text">
                <HelpCircle size={14} style={{ display: "inline", verticalAlign: "middle", marginRight: "6px", color: "var(--text-accent)" }} aria-hidden="true" />
                {q.question}
              </div>
              <div className="question-meta">
                {q.related_clause && <span>Related to: {q.related_clause}</span>}
                {q.why_important && <span>• {q.why_important}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
