import { FileText, Users, Calendar, BookOpen, Globe } from "lucide-react";
import ClauseCard from "./ClauseCard";
import { TierBDisclaimer, NoDataMessage } from "./Disclaimer";

export default function AnalysisView({ analysis, jurisdiction, docType, hasReferenceData }) {
  if (!analysis) return null;

  const { tier_a, tier_b, checklist } = analysis;

  return (
    <div className="animate-in">
      {/* ─── Tier A: Document-Grounded Facts ─── */}
      <section className="tier-section tier-a" aria-labelledby="tier-a-heading">
        <div className="tier-badge tier-a-badge" aria-hidden="true">
          <FileText size={14} /> Tier A — Document Facts
        </div>
        <h2 id="tier-a-heading" style={{ marginBottom: "1rem" }}>
          What This Document Says
        </h2>

        {/* Document Summary */}
        {tier_a?.document_summary && (
          <div className="card" style={{ marginBottom: "1.5rem" }}>
            <div className="card-header">
              <BookOpen className="icon" size={18} aria-hidden="true" />
              <h3>Plain-Language Summary</h3>
            </div>
            <p className="summary-text">{tier_a.document_summary}</p>
          </div>
        )}

        {/* Parties */}
        {tier_a?.parties?.length > 0 && (
          <div className="card" style={{ marginBottom: "1.5rem" }}>
            <div className="card-header">
              <Users className="icon" size={18} aria-hidden="true" />
              <h3>Parties</h3>
            </div>
            <ul className="parties-list" aria-label="Parties to the agreement">
              {tier_a.parties.map((party, i) => (
                <li key={i}>
                  <span className="party-role">{party.role}:</span>
                  <span>{party.name || "Not specified"}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Key Dates */}
        {tier_a?.key_dates_and_deadlines?.length > 0 && (
          <div className="card" style={{ marginBottom: "1.5rem" }}>
            <div className="card-header">
              <Calendar className="icon" size={18} aria-hidden="true" />
              <h3>Key Dates & Deadlines</h3>
            </div>
            <ul className="deadlines-list" aria-label="Important dates and deadlines">
              {tier_a.key_dates_and_deadlines.map((item, i) => (
                <li key={i}>
                  <span className="deadline-label">{item.description}:</span>
                  <span>{item.date_or_period}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Extracted Clauses */}
        {tier_a?.clauses?.length > 0 && (
          <div>
            <h3 style={{ marginBottom: "1rem" }}>Extracted Clauses & Risk Assessment</h3>
            {tier_a.clauses.map((clause, i) => (
              <ClauseCard key={i} clause={clause} />
            ))}
          </div>
        )}
      </section>

      {/* ─── Tier B: Jurisdictional Context ─── */}
      <section className="tier-section tier-b" aria-labelledby="tier-b-heading">
        <div className="tier-badge tier-b-badge" aria-hidden="true">
          <Globe size={14} /> Tier B — Jurisdictional Context
        </div>
        <h2 id="tier-b-heading" style={{ marginBottom: "1rem" }}>
          Regional Context: {jurisdiction || "Not Selected"}
        </h2>

        {!hasReferenceData ? (
          <NoDataMessage jurisdiction={jurisdiction} docType={docType} />
        ) : (
          <>
            <TierBDisclaimer />

            {tier_b?.coverage_note && (
              <div className="card" style={{ marginBottom: "1rem" }}>
                <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                  <strong>Coverage:</strong> {tier_b.coverage_note}
                </p>
              </div>
            )}

            {tier_b?.clause_context?.map((ctx, i) => (
              <div key={i} className="card" style={{ marginBottom: "0.75rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                  <strong>{ctx.clause_name}</strong>
                  {ctx.has_jurisdiction_info ? (
                    <span className="jurisdiction-badge has-data" aria-label="Reference data available">
                      ✓ Data Available
                    </span>
                  ) : (
                    <span className="jurisdiction-badge no-data" aria-label="No specific data for this clause">
                      No Data
                    </span>
                  )}
                </div>
                {ctx.has_jurisdiction_info && (
                  <>
                    <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
                      {ctx.general_context}
                    </p>
                    {ctx.confidence && (
                      <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        Confidence: {ctx.confidence}
                      </p>
                    )}
                    {ctx.verification_note && (
                      <p style={{ fontSize: "0.8rem", color: "var(--tier-b-accent)", marginTop: "0.25rem" }}>
                        ⚠️ Verify: {ctx.verification_note}
                      </p>
                    )}
                  </>
                )}
              </div>
            ))}

            {tier_b?.items_to_verify?.length > 0 && (
              <div className="card" style={{ marginTop: "1rem" }}>
                <h3 style={{ marginBottom: "0.5rem" }}>Always Verify With a Professional</h3>
                <ul style={{ listStyle: "none" }}>
                  {tier_b.items_to_verify.map((item, i) => (
                    <li key={i} style={{ padding: "0.25rem 0", color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                      → {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}
