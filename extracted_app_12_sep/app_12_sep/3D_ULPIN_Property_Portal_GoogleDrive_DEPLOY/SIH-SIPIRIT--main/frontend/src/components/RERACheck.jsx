import React, { useState } from "react";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

/**
 * RERACheck — Section 9's "NEW" use case: an independent, evidence-backed
 * comparison of RERA-declared carpet area against the AI-measured geometry,
 * framed explicitly as a comparison, not a legal ruling.
 */
export default function RERACheck({ spaceId }) {
  const [declared, setDeclared] = useState("");
  const [measured, setMeasured] = useState("");
  const [confidence, setConfidence] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runCheck = async () => {
    if (!spaceId || !declared || !measured || !confidence) return;
    setLoading(true);
    setError(null);
    try {
      const { data } = await axios.post(`${API_BASE}/spaces/${spaceId}/rera-check`, {
        declared_carpet_m2: parseFloat(declared),
        measured_carpet_m2: parseFloat(measured),
        confidence: parseFloat(confidence),
      });
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.detail || "RERA check failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rera-check">
      <h4>RERA carpet-area verification</h4>
      <p className="muted" style={{ fontSize: 12 }}>
        Independent comparison of declared vs. AI-measured carpet area — not a legal ruling.
      </p>

      <label>
        Declared (m²)
        <input type="number" value={declared} onChange={(e) => setDeclared(e.target.value)} />
      </label>
      <label>
        Measured (m²)
        <input type="number" value={measured} onChange={(e) => setMeasured(e.target.value)} />
      </label>
      <label>
        Confidence (%)
        <input type="number" value={confidence} onChange={(e) => setConfidence(e.target.value)} />
      </label>

      <button onClick={runCheck} disabled={loading || !spaceId}>
        {loading ? "Checking…" : "Run check"}
      </button>

      {error && <div style={{ color: "#FF3B30" }}>{error}</div>}

      {result && (
        <div style={{ marginTop: 10 }}>
          <strong>
            declared {result.declared_carpet_m2} m² vs. measured {result.measured_carpet_m2} m²
          </strong>
          <div>
            delta: {result.delta_m2 > 0 ? "+" : ""}
            {result.delta_m2} m² at {result.confidence}% confidence
          </div>
        </div>
      )}
    </div>
  );
}
