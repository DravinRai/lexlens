import { AlertTriangle, Info } from "lucide-react";

export function GlobalDisclaimer() {
  return (
    <div className="disclaimer-global" role="contentinfo" aria-label="Legal disclaimer">
      <span>⚖️ LexLens is an informational tool — not a substitute for licensed legal advice. Accuracy is not guaranteed. Always consult a qualified attorney.</span>
    </div>
  );
}

export function TierBDisclaimer() {
  return (
    <div className="disclaimer-tier-b" role="alert" aria-label="Jurisdictional information disclaimer">
      <AlertTriangle className="disclaimer-icon" size={18} aria-hidden="true" />
      <div>
        <strong>Jurisdictional Context — General Information Only.</strong>{" "}
        The information below is sourced from curated reference data and is provided for general informational purposes only. 
        It does not constitute legal advice, may not be complete or current, and should not be relied upon as a definitive legal conclusion 
        about your specific document or situation. Always verify with a licensed legal professional in the relevant jurisdiction.
      </div>
    </div>
  );
}

export function NoDataMessage({ jurisdiction, docType }) {
  return (
    <div className="no-data-message" role="status">
      <div className="icon-large" aria-hidden="true">
        <Info size={32} />
      </div>
      <h3>No Verified Reference Data Available</h3>
      <p style={{ marginTop: "0.5rem" }}>
        I don't have verified reference data for <strong>{jurisdiction}</strong> for{" "}
        <strong>{docType}</strong> documents. Jurisdictional context (Tier B) cannot be
        reliably generated for this combination.
      </p>
      <p style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>
        Tier A analysis (what your document actually says) is still fully available.
        For jurisdiction-specific guidance, please consult a licensed legal professional
        familiar with this region.
      </p>
    </div>
  );
}
