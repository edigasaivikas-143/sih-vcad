import React, { useState } from "react";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

// Suggested prompts pulled straight from the project guide's Module H
// examples and the Section 13 demo script, so judges see what's in scope.
const SUGGESTED_QUESTIONS = [
  "which objects have conflicting rights records?",
  "show all utility corridors under this parcel",
  "which units overlap the terrace's air rights?",
];

/**
 * NLQuryBox — Module H (natural-language query layer).
 * Deliberately narrow: sends the raw question to /api/v1/query, which maps
 * it onto a fixed set of structured intents server-side (never open-ended
 * chat), and renders the matched spaces plus the SQL-equivalent for
 * transparency during the demo.
 */
export default function NLQuryBox({ parcelId, onResults }) {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runQuery = async (q) => {
    const text = (q ?? question).trim();
    if (!text) return;
    setLoading(true);
    setError(null);
    try {
      const { data } = await axios.post(`${API_BASE}/query`, {
        question: text,
        parcel_id: parcelId,
      });
      setResponse(data);
      onResults?.(data.results);
    } catch (err) {
      setError(err?.response?.data?.detail || "Query failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="nl-query-box">
      <div style={{ display: "flex", gap: 8 }}>
        <input
          type="text"
          value={question}
          placeholder="Ask about this parcel in plain language…"
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && runQuery()}
          style={{ flex: 1, padding: "8px 10px" }}
        />
        <button onClick={() => runQuery()} disabled={loading}>
          {loading ? "Searching…" : "Ask"}
        </button>
      </div>

      <div style={{ marginTop: 6, fontSize: 12, opacity: 0.7 }}>
        Try:{" "}
        {SUGGESTED_QUESTIONS.map((q, i) => (
          <button
            key={q}
            onClick={() => { setQuestion(q); runQuery(q); }}
            style={{ marginRight: 6, fontSize: 12 }}
          >
            {q}
          </button>
        ))}
      </div>

      {error && <div style={{ color: "#FF3B30", marginTop: 8 }}>{error}</div>}

      {response && (
        <div style={{ marginTop: 10 }}>
          <div style={{ fontSize: 12, opacity: 0.6 }}>
            matched intent: <code>{response.matched_intent}</code>
          </div>
          <div style={{ fontSize: 12, opacity: 0.6, marginBottom: 6 }}>
            <code>{response.sql_equivalent}</code>
          </div>
          <ul>
            {response.results.map((s) => (
              <li key={s.parcel_3d_id}>
                {s.ulpin_3d_code || s.unit_id} — {s.status}
                {s.has_validation_failure && <strong style={{ color: "#FF3B30" }}> · FLAGGED</strong>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
