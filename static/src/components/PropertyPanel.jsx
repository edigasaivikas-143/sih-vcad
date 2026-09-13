import React, { useEffect, useState } from "react";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const STATUS_STEPS = ["AI_GENERATED", "QA_PASSED", "SURVEY_REVIEW", "APPROVED", "PUBLISHED"];

/**
 * PropertyPanel — clicking a volumetric space in MapViewer should show its
 * "3D identity, elevation, geometry, rights, confidence, source data and
 * validation state" (Section 2, Hackathon differentiator). This is that panel.
 */
export default function PropertyPanel({ spaceId, onReview }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!spaceId) {
      setDetail(null);
      return;
    }
    setLoading(true);
    axios
      .get(`${API_BASE}/spaces/${spaceId}`)
      .then(({ data }) => setDetail(data))
      .catch((err) => console.error("Failed to load space detail", err))
      .finally(() => setLoading(false));
  }, [spaceId]);

  if (!spaceId) {
    return <div className="property-panel empty">Select a volumetric space on the map.</div>;
  }
  if (loading || !detail) {
    return <div className="property-panel">Loading…</div>;
  }

  const failedChecks = (detail.validations || []).filter((v) => v.result === "FAIL");
  const activeRights = (detail.rights || []).filter((r) => r.active);

  return (
    <div className="property-panel">
      <h3>{detail.ulpin_3d_code || detail.unit_id}</h3>

      <Section title="3D Identity">
        <Row label="Unit ID" value={detail.unit_id} />
        <Row label="Space class" value={detail.space_class} />
        <Row label="Rights code" value={detail.rights_code} />
        <Row label="Version" value={detail.version} />
        <Row label="Status" value={detail.status} />
      </Section>

      <Section title="Geometry">
        <Row label="Z range" value={`${detail.z_min} – ${detail.z_max} m`} />
        <Row label="Confidence" value={detail.confidence != null ? `${detail.confidence}%` : "—"} />
      </Section>

      <Section title={`Rights (${activeRights.length} active)`}>
        {activeRights.length === 0 && <div className="muted">No active rights records.</div>}
        {activeRights.map((r) => (
          <Row key={r.right_id} label={r.right_type} value={r.party_id} />
        ))}
      </Section>

      <Section title="Validation">
        {failedChecks.length === 0 ? (
          <div className="ok">All checks passed.</div>
        ) : (
          failedChecks.map((v, i) => (
            <div key={i} className="validation-fail">
              <strong>{v.rule}</strong>: {v.detail}
            </div>
          ))
        )}
      </Section>

      <Section title="Review workflow">
        <ReviewStepper current={detail.status} />
        <div style={{ marginTop: 8 }}>
          <button onClick={() => onReview?.(spaceId, "approve")}>Advance</button>
          <button onClick={() => onReview?.(spaceId, "reject")} style={{ marginLeft: 8 }}>
            Send to review
          </button>
        </div>
      </Section>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ fontWeight: 600, fontSize: 13, opacity: 0.8 }}>{title}</div>
      <div>{children}</div>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
      <span className="muted">{label}</span>
      <span>{String(value)}</span>
    </div>
  );
}

function ReviewStepper({ current }) {
  const idx = STATUS_STEPS.indexOf(current);
  return (
    <div style={{ display: "flex", gap: 4 }}>
      {STATUS_STEPS.map((step, i) => (
        <div
          key={step}
          title={step}
          style={{
            flex: 1,
            height: 6,
            borderRadius: 3,
            background: i <= idx ? "#34C759" : "#3a3a3c",
          }}
        />
      ))}
    </div>
  );
}
