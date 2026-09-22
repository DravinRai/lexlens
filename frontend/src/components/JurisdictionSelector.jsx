import { useState } from "react";
import { Globe, MapPin, ChevronRight } from "lucide-react";

const COUNTRIES = [
  { value: "", label: "Select a country..." },
  { value: "IN", label: "India" },
  { value: "US", label: "United States" },
  { value: "UK", label: "United Kingdom" },
  { value: "CA", label: "Canada" },
  { value: "AU", label: "Australia" },
  { value: "DE", label: "Germany" },
  { value: "FR", label: "France" },
  { value: "SG", label: "Singapore" },
  { value: "AE", label: "UAE" },
  { value: "OTHER", label: "Other" },
];

const STATES = {
  US: [
    { value: "", label: "Select a state..." },
    { value: "CA", label: "California" },
    { value: "NY", label: "New York" },
    { value: "TX", label: "Texas" },
    { value: "FL", label: "Florida" },
    { value: "IL", label: "Illinois" },
    { value: "WA", label: "Washington" },
    { value: "MA", label: "Massachusetts" },
    { value: "OTHER", label: "Other" },
  ],
  IN: [
    { value: "", label: "Select a state (optional)..." },
    { value: "MH", label: "Maharashtra" },
    { value: "KA", label: "Karnataka" },
    { value: "DL", label: "Delhi" },
    { value: "TN", label: "Tamil Nadu" },
    { value: "WB", label: "West Bengal" },
    { value: "OTHER", label: "Other" },
  ],
  CA: [
    { value: "", label: "Select a province..." },
    { value: "ON", label: "Ontario" },
    { value: "BC", label: "British Columbia" },
    { value: "QC", label: "Quebec" },
    { value: "AB", label: "Alberta" },
    { value: "OTHER", label: "Other" },
  ],
};

export default function JurisdictionSelector({ onSubmit, isLoading, docType }) {
  const [country, setCountry] = useState("");
  const [state, setState] = useState("");
  const [customCountry, setCustomCountry] = useState("");
  const [customState, setCustomState] = useState("");

  const hasStates = STATES[country];

  const handleSubmit = () => {
    const finalCountry = country === "OTHER" ? customCountry : country;
    const finalState = state === "OTHER" ? customState : state;
    if (!finalCountry) return;
    onSubmit(finalCountry, finalState);
  };

  return (
    <div className="card animate-in">
      <div className="card-header">
        <Globe className="icon" size={20} aria-hidden="true" />
        <h2>Select Jurisdiction</h2>
      </div>

      <p style={{ color: "var(--text-secondary)", marginBottom: "1.5rem", fontSize: "0.9rem" }}>
        Jurisdiction determines which curated reference data (if available) we can use to provide
        context about how this region typically treats clauses in{" "}
        <span className="doc-type-badge">{docType || "this"}</span> documents.
        This is a critical step — different jurisdictions have very different rules.
      </p>

      <div className="jurisdiction-selector">
        <div className="form-group">
          <label htmlFor="country-select">
            <MapPin size={14} style={{ display: "inline", verticalAlign: "middle" }} />{" "}
            Country / Region
          </label>
          <select
            id="country-select"
            value={country}
            onChange={(e) => { setCountry(e.target.value); setState(""); }}
            aria-required="true"
          >
            {COUNTRIES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
        </div>

        {country === "OTHER" && (
          <div className="form-group animate-in">
            <label htmlFor="custom-country">Country Name</label>
            <input
              id="custom-country"
              type="text"
              placeholder="Enter country name..."
              value={customCountry}
              onChange={(e) => setCustomCountry(e.target.value)}
            />
          </div>
        )}

        {hasStates && (
          <div className="form-group animate-in">
            <label htmlFor="state-select">State / Province</label>
            <select
              id="state-select"
              value={state}
              onChange={(e) => setState(e.target.value)}
            >
              {STATES[country].map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
        )}

        {state === "OTHER" && (
          <div className="form-group animate-in">
            <label htmlFor="custom-state">State / Province Name</label>
            <input
              id="custom-state"
              type="text"
              placeholder="Enter state or province..."
              value={customState}
              onChange={(e) => setCustomState(e.target.value)}
            />
          </div>
        )}

        <div style={{ textAlign: "right", marginTop: "0.5rem" }}>
          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={isLoading || (!country || (country === "OTHER" && !customCountry))}
          >
            {isLoading ? "Setting jurisdiction..." : (
              <>Continue to Analysis <ChevronRight size={16} /></>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
