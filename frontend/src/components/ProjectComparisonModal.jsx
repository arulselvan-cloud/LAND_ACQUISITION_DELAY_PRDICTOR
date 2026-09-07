import React, { useState, useEffect } from 'react';
import {
  X,
  Layers,
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  Clock,
  ExternalLink,
  ShieldAlert,
  GitFork,
  CheckCircle2,
  Minus
} from 'lucide-react';
import {
  getProjectDetails,
  predictProject,
  getProjectExplanation,
  getProjectPropagation
} from '../api/client';

export default function ProjectComparisonModal({
  projectIds = [],
  onClose = () => {},
  onSelectProject = () => {},
  onSelectTrio = () => {},
}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [projectsData, setProjectsData] = useState([]);

  useEffect(() => {
    if (!projectIds || projectIds.length === 0) {
      setProjectsData([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    // Fetch details, prediction, explanation, and propagation for all selected projects in parallel
    Promise.all(
      projectIds.map(async (id) => {
        try {
          const [details, prediction, explanation, propagation] = await Promise.all([
            getProjectDetails(id).catch((err) => ({ name: id, project_code: id })),
            predictProject(id).catch((err) => null),
            getProjectExplanation(id).catch((err) => null),
            getProjectPropagation(id).catch((err) => []),
          ]);

          // Compute cumulative delay across statutory stages
          const cumulativeDelayDays = (propagation || []).reduce(
            (sum, s) => sum + (s.delay_days || 0),
            0
          );

          // Top 3 SHAP drivers
          const topFactors = (explanation?.factors || []).slice(0, 3);

          return {
            id,
            details,
            prediction,
            explanation,
            propagation: propagation || [],
            cumulativeDelayDays,
            topFactors,
          };
        } catch (err) {
          console.error(`Error loading comparison data for ${id}:`, err);
          return { id, error: err.message };
        }
      })
    )
      .then((results) => {
        setProjectsData(results);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load comparison dataset.');
        setLoading(false);
      });
  }, [projectIds]);

  return (
    <div className="detail-overlay" onClick={onClose}>
      <div
        className="detail-modal"
        style={{
          maxWidth: '1240px',
          width: '95vw',
          maxHeight: '92vh',
          display: 'flex',
          flexDirection: 'column',
          padding: '24px',
          background: 'var(--bg-surface)',
          borderRadius: '16px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingBottom: '16px',
            borderBottom: '1px solid var(--border-light)',
            marginBottom: '16px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '10px',
                background: 'rgba(30, 58, 138, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--gov-blue)',
              }}
            >
              <GitFork size={22} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800 }}>
                  Multi-Corridor Risk & Delay Comparison
                </h2>
                <span
                  style={{
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    padding: '2px 8px',
                    background: 'var(--gov-blue)',
                    color: '#ffffff',
                    borderRadius: 'var(--radius-full)',
                  }}
                >
                  {projectIds.length} Projects Side-by-Side
                </span>
              </div>
              <p style={{ margin: '2px 0 0', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Parallel comparative evaluation across calibrated risk probabilities, top SHAP drivers, and statutory milestone delay cascades.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {onSelectTrio && (
              <button
                className="chip-btn"
                style={{ fontSize: '0.75rem', padding: '6px 12px' }}
                onClick={onSelectTrio}
                title="Load Showcase Trio: CBIC, BSRP, and MAHSR"
              >
                Load Showcase Trio
              </button>
            )}
            <button
              onClick={onClose}
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-light)',
                borderRadius: '8px',
                padding: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-main)',
              }}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div style={{ flex: 1, overflowY: 'auto', paddingRight: '4px' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '8px' }}>
                Assembling comparative multi-project telemetry...
              </div>
              <div style={{ fontSize: '0.8rem' }}>
                Synchronizing XGBoost risk predictions, SHAP attribution vectors, and sequential milestone cascades.
              </div>
            </div>
          ) : error ? (
            <div
              style={{
                padding: '20px',
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid var(--risk-critical-border)',
                borderRadius: '8px',
                color: 'var(--risk-critical)',
              }}
            >
              <AlertTriangle size={18} style={{ marginBottom: '6px' }} />
              <div>{error}</div>
            </div>
          ) : projectsData.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
              No projects selected for comparison. Please select 2 to 3 projects.
            </div>
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: `repeat(${projectsData.length}, minmax(300px, 1fr))`,
                gap: '16px',
                alignItems: 'stretch',
              }}
            >
              {projectsData.map((item, idx) => {
                const details = item.details || {};
                const pred = item.prediction || {};
                const riskCat = (pred.risk_category || 'medium').toLowerCase();
                const probPct = ((pred.delay_probability || 0) * 100).toFixed(1);
                const code = details.project_code || item.id;

                return (
                  <div
                    key={item.id}
                    style={{
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--border-light)',
                      borderRadius: '12px',
                      padding: '16px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '16px',
                    }}
                  >
                    {/* Project Header */}
                    <div
                      style={{
                        borderBottom: '1px solid var(--border-light)',
                        paddingBottom: '12px',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span
                          style={{
                            fontWeight: 800,
                            fontSize: '0.95rem',
                            color: 'var(--gov-blue)',
                            letterSpacing: '0.04em',
                          }}
                        >
                          {code}
                        </span>
                        <span
                          className={`risk-badge ${riskCat}`}
                          style={{ fontSize: '0.72rem', textTransform: 'uppercase' }}
                        >
                          {riskCat} Risk
                        </span>
                      </div>
                      <div
                        style={{
                          fontWeight: 700,
                          fontSize: '0.88rem',
                          marginTop: '4px',
                          color: 'var(--text-main)',
                          minHeight: '2.4em',
                          lineHeight: 1.25,
                        }}
                      >
                        {details.name || code}
                      </div>
                      <div
                        style={{
                          fontSize: '0.72rem',
                          color: 'var(--text-muted)',
                          marginTop: '4px',
                          display: 'flex',
                          justifyContent: 'space-between',
                        }}
                      >
                        <span>{details.district}, {details.state}</span>
                        <span>{details.project_type || 'Infrastructure'}</span>
                      </div>
                    </div>

                    {/* Metric 1: Delay Probability & Confidence */}
                    <div
                      style={{
                        background: 'var(--bg-surface)',
                        padding: '12px',
                        borderRadius: '8px',
                        border: '1px solid var(--border-light)',
                      }}
                    >
                      <div
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          color: 'var(--text-muted)',
                          textTransform: 'uppercase',
                          letterSpacing: '0.05em',
                          marginBottom: '6px',
                        }}
                      >
                        Model Risk Likelihood
                      </div>
                      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                        <span
                          style={{
                            fontSize: '1.8rem',
                            fontWeight: 900,
                            color:
                              riskCat === 'critical'
                                ? 'var(--risk-critical)'
                                : riskCat === 'high'
                                ? 'var(--risk-high)'
                                : 'var(--gov-emerald)',
                          }}
                        >
                          {probPct}%
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          Delay Likelihood
                        </span>
                      </div>
                      {/* Gauge Bar */}
                      <div
                        style={{
                          width: '100%',
                          height: '6px',
                          background: 'rgba(0,0,0,0.06)',
                          borderRadius: '3px',
                          marginTop: '8px',
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            width: `${Math.min(100, Math.max(0, pred.delay_probability * 100 || 0))}%`,
                            height: '100%',
                            background:
                              riskCat === 'critical'
                                ? 'var(--risk-critical)'
                                : riskCat === 'high'
                                ? 'var(--risk-high)'
                                : 'var(--gov-emerald)',
                          }}
                        />
                      </div>
                    </div>

                    {/* Metric 2: Cumulative Propagation Delay */}
                    <div
                      style={{
                        background: 'var(--bg-surface)',
                        padding: '12px',
                        borderRadius: '8px',
                        border: '1px solid var(--border-light)',
                      }}
                    >
                      <div
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          color: 'var(--text-muted)',
                          textTransform: 'uppercase',
                          letterSpacing: '0.05em',
                          marginBottom: '6px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '5px',
                        }}
                      >
                        <Clock size={12} />
                        <span>Cumulative Milestone Delay</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                        <span
                          style={{
                            fontSize: '1.4rem',
                            fontWeight: 800,
                            color:
                              item.cumulativeDelayDays > 100
                                ? 'var(--risk-critical)'
                                : item.cumulativeDelayDays > 30
                                ? 'var(--risk-high)'
                                : 'var(--text-main)',
                          }}
                        >
                          +{item.cumulativeDelayDays}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          Days Total Forecast Delay
                        </span>
                      </div>

                      {/* 5-Stage Cascade Breakdown */}
                      <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {(item.propagation || []).map((stage) => (
                          <div
                            key={stage.stage_name}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              fontSize: '0.7rem',
                              padding: '2px 0',
                            }}
                          >
                            <span style={{ textTransform: 'capitalize', color: 'var(--text-main)' }}>
                              {stage.stage_name}
                            </span>
                            <span
                              style={{
                                fontWeight: 700,
                                color: stage.delay_days > 0 ? 'var(--risk-high)' : 'var(--text-muted)',
                              }}
                            >
                              {stage.delay_days > 0 ? `+${stage.delay_days}d` : '0d'}
                              {stage.is_predicted && ' (est)'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Metric 3: Top 3 SHAP Attribution Drivers */}
                    <div
                      style={{
                        background: 'var(--bg-surface)',
                        padding: '12px',
                        borderRadius: '8px',
                        border: '1px solid var(--border-light)',
                        flex: 1,
                      }}
                    >
                      <div
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          color: 'var(--text-muted)',
                          textTransform: 'uppercase',
                          letterSpacing: '0.05em',
                          marginBottom: '8px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '5px',
                        }}
                      >
                        <TrendingUp size={12} />
                        <span>Top 3 SHAP Delay Drivers</span>
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {(item.topFactors || []).map((f, fIdx) => {
                          const isRiskUp = f.direction === 'increases_risk';
                          const shapVal = typeof f.shap_value === 'number' ? f.shap_value.toFixed(3) : '0';

                          return (
                            <div
                              key={f.feature || fIdx}
                              style={{
                                padding: '6px 8px',
                                background: 'var(--bg-elevated)',
                                border: '1px solid var(--border-light)',
                                borderRadius: '6px',
                                fontSize: '0.72rem',
                              }}
                            >
                              <div
                                style={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'space-between',
                                  fontWeight: 600,
                                  color: 'var(--text-main)',
                                }}
                              >
                                <span title={f.feature}>{f.display_name || f.feature}</span>
                                <span
                                  style={{
                                    fontWeight: 800,
                                    fontSize: '0.68rem',
                                    color: isRiskUp ? 'var(--risk-critical)' : 'var(--gov-emerald)',
                                  }}
                                >
                                  {isRiskUp ? `+${shapVal}` : shapVal}
                                </span>
                              </div>
                              <div
                                style={{
                                  fontSize: '0.68rem',
                                  color: 'var(--text-muted)',
                                  marginTop: '2px',
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                }}
                              >
                                <span>
                                  Value:{' '}
                                  <strong style={{ color: 'var(--text-main)' }}>
                                    {f.value !== null && f.value !== undefined ? String(f.value) : 'N/A'}
                                  </strong>
                                </span>
                                <span>{isRiskUp ? 'Increases delay' : 'Mitigates delay'}</span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Jump to Project Detail Flow */}
                    <button
                      className="btn-secondary"
                      style={{
                        width: '100%',
                        fontSize: '0.78rem',
                        padding: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px',
                      }}
                      onClick={() => {
                        onClose();
                        onSelectProject(code);
                      }}
                    >
                      <span>Explore 5-Stage Story Flow</span>
                      <ExternalLink size={13} />
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
