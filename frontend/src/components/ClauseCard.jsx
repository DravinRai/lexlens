import { ShieldCheck, ShieldAlert, Shield, AlertCircle, MapPin } from "lucide-react";

const RISK_CONFIG = {
  low: {
    icon: "🟢",
    ariaLabel: "Low risk",
    label: "Low",
    iconComponent: ShieldCheck,
  },
  medium: {
    icon: "🟡",
    ariaLabel: "Medium risk",
    label: "Medium",
    iconComponent: Shield,
  },
  high: {
    icon: "🔴",
    ariaLabel: "High risk",
    label: "High",
    iconComponent: ShieldAlert,
  },
};

export default function ClauseCard({ clause }) {
  const risk = RISK_CONFIG[clause.risk_level] || RISK_CONFIG.medium;
  const RiskIcon = risk.iconComponent;

  if (!clause.found) {
    return (
      <div className="clause-card not-found" role="article" aria-label={`${clause.name} — not found in document`}>
        <div className="clause-header">
          <span className="clause-name" style={{ opacity: 0.6 }}>
            <AlertCircle size={16} style={{ display: "inline", verticalAlign: "middle", marginRight: "6px" }} aria-hidden="true" />
            {clause.name}
          </span>
          <span className="risk-tag medium" role="status" aria-label="Attention: clause not found">
            <span className="risk-icon" aria-hidden="true">⚠️</span>
            Not Found
          </span>
        </div>
        <p className="clause-summary" style={{ fontStyle: "italic" }}>
          This clause was not found in the document. Depending on the document type, a missing clause
          may itself be a concern worth raising with a legal professional.
        </p>
      </div>
    );
  }

  return (
    <div className="clause-card" role="article" aria-label={`${clause.name} — ${risk.ariaLabel}`}>
      <div className="clause-header">
        <span className="clause-name">{clause.name}</span>
        <span
          className={`risk-tag ${clause.risk_level}`}
          role="status"
          aria-label={risk.ariaLabel}
        >
          <RiskIcon size={14} className="risk-icon" aria-hidden="true" />
          <span className="risk-icon" aria-hidden="true">{risk.icon}</span>
          {risk.label}
        </span>
      </div>

      <p className="clause-summary">{clause.plain_summary}</p>

      {clause.extracted_text && (
        <div className="clause-extracted" role="blockquote">
          {clause.extracted_text}
        </div>
      )}

      {clause.risk_rationale && (
        <p className="clause-rationale">
          <RiskIcon size={12} style={{ display: "inline", verticalAlign: "middle", marginRight: "4px" }} aria-hidden="true" />
          {clause.risk_rationale}
        </p>
      )}

      {clause.location && (
        <p className="clause-location">
          <MapPin size={12} style={{ display: "inline", verticalAlign: "middle", marginRight: "4px" }} aria-hidden="true" />
          {clause.location}
        </p>
      )}
    </div>
  );
}
