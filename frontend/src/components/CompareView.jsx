import { GitCompare, ArrowRight, ArrowLeft, Minus, Equal } from "lucide-react";

const FAVOR_CONFIG = {
  party_a: { label: "Favors Doc A", className: "party-a", icon: ArrowLeft },
  party_b: { label: "Favors Doc B", className: "party-b", icon: ArrowRight },
  neutral: { label: "Neutral", className: "neutral", icon: Equal },
  unclear: { label: "Unclear", className: "neutral", icon: Minus },
};

export default function CompareView({ comparison }) {
  if (!comparison) return null;

  return (
    <div className="animate-in">
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div className="card-header">
          <GitCompare className="icon" size={20} aria-hidden="true" />
          <h2>Document Comparison</h2>
        </div>

        {comparison.comparison_summary && (
          <p className="summary-text" style={{ marginBottom: "1.5rem" }}>
            {comparison.comparison_summary}
          </p>
        )}

        {comparison.clause_comparisons?.map((comp, i) => {
          const favor = FAVOR_CONFIG[comp.favors] || FAVOR_CONFIG.unclear;
          const FavorIcon = favor.icon;

          return (
            <div key={i} className="clause-card" style={{ marginBottom: "1rem" }}>
              <div className="clause-header">
                <span className="clause-name">{comp.clause_name}</span>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  {comp.has_material_difference && (
                    <span className={`favor-badge ${favor.className}`} aria-label={favor.label}>
                      <FavorIcon size={12} aria-hidden="true" />
                      {favor.label}
                    </span>
                  )}
                  {!comp.in_doc_a && (
                    <span className="risk-tag medium" aria-label="Only in Document B">
                      Only in B
                    </span>
                  )}
                  {!comp.in_doc_b && (
                    <span className="risk-tag medium" aria-label="Only in Document A">
                      Only in A
                    </span>
                  )}
                </div>
              </div>

              {comp.has_material_difference && (
                <>
                  <div className="compare-grid">
                    {comp.in_doc_a && (
                      <div className="compare-cell doc-a">
                        <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--favor-a)", marginBottom: "0.25rem" }}>
                          DOCUMENT A
                        </div>
                        {comp.doc_a_text}
                      </div>
                    )}
                    {comp.in_doc_b && (
                      <div className="compare-cell doc-b">
                        <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--favor-b)", marginBottom: "0.25rem" }}>
                          DOCUMENT B
                        </div>
                        {comp.doc_b_text}
                      </div>
                    )}
                  </div>

                  {comp.difference_description && (
                    <p className="clause-summary" style={{ marginTop: "0.75rem" }}>
                      <strong>Difference:</strong> {comp.difference_description}
                    </p>
                  )}
                  {comp.impact && (
                    <p className="clause-rationale" style={{ marginTop: "0.25rem" }}>
                      Impact: {comp.impact}
                    </p>
                  )}
                </>
              )}

              {!comp.has_material_difference && comp.in_doc_a && comp.in_doc_b && (
                <p className="clause-summary" style={{ color: "var(--risk-low)" }}>
                  ✓ No material differences found for this clause.
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
