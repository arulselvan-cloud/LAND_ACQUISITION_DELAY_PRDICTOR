import React, { useState } from 'react';
import {
  ShieldAlert,
  Activity,
  CheckCircle2,
  AlertCircle,
  Building2,
  RefreshCw,
  GitFork,
  X,
  AlertTriangle,
} from 'lucide-react';
import { retrainModel } from '../api/client';

export default function Header({
  health,
  onSelectShowcase,
  activeProjectId,
  onOpenComparison = () => {},
}) {
  const [showRetrainDialog, setShowRetrainDialog] = useState(false);
  const [retraining, setRetraining] = useState(false);
  const [retrainResult, setRetrainResult] = useState(null);
  const [retrainError, setRetrainError] = useState(null);

  const showcaseProjects = [
    { code: 'CBIC-TN-PKG02', label: 'CBIC Industrial Pkg 2', state: 'Tamil Nadu' },
    { code: 'BSRP-KA-CORR04', label: 'BSRP Suburban Rail', state: 'Karnataka' },
    { code: 'MAHSR-MH-PAL03', label: 'MAHSR High-Speed Rail', state: 'Maharashtra' },
  ];

  const isOnline = health && health.status === 'healthy';

  const handleConfirmRetrain = async () => {
    setRetraining(true);
    setRetrainError(null);
    try {
      const res = await retrainModel(true);
      setRetrainResult(res);
      setShowRetrainDialog(false);
    } catch (err) {
      console.error('Retrain error:', err);
      setRetrainError(err.message || 'Model retraining failed.');
    } finally {
      setRetraining(false);
    }
  };

  return (
    <header className="gov-header">
      <div className="gov-tricolor-bar" />
      <div className="gov-header-inner">
        {/* Brand & Emblem */}
        <div className="gov-brand">
          <div className="gov-emblem-badge">
            <Building2 size={24} className="text-white opacity-90" />
            <div style={{ lineHeight: 1.1 }}>
              <div
                style={{
                  fontSize: '0.65rem',
                  letterSpacing: '0.08em',
                  opacity: 0.8,
                  textTransform: 'uppercase',
                }}
              >
                Government of India
              </div>
              <div style={{ fontSize: '0.72rem', fontWeight: 700 }}>
                Ministry of Infrastructure
              </div>
            </div>
          </div>

          <div className="gov-title-group">
            <h1>
              LandSight AI
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  padding: '2px 6px',
                  background: 'rgba(255,255,255,0.15)',
                  borderRadius: '4px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                SIH26017 Prototype
              </span>
            </h1>
            <p>Predictive Delay Analytics & Statutory RFCTLARR Milestone Risk Intelligence</p>
          </div>
        </div>

        {/* Showcase Fast Selector & Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <div className="showcase-chips">
            <span className="showcase-label">Showcase Corridors:</span>
            {showcaseProjects.map((p) => {
              const isSelected = activeProjectId === p.code;
              return (
                <button
                  key={p.code}
                  className={`chip-btn ${isSelected ? 'active' : ''}`}
                  onClick={() => onSelectShowcase(p.code)}
                  title={`${p.label} (${p.state})`}
                >
                  {p.code}
                </button>
              );
            })}
          </div>

          {/* Project Comparison Fast Trigger */}
          <button
            className="chip-btn"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              fontSize: '0.74rem',
              borderColor: 'rgba(255,255,255,0.3)',
            }}
            onClick={onOpenComparison}
            title="Open side-by-side corridor comparison"
          >
            <GitFork size={13} />
            <span>Compare Corridors</span>
          </button>

          {/* Retrain Model Action Button */}
          <button
            className="chip-btn"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              fontSize: '0.74rem',
              borderColor: 'rgba(255,255,255,0.3)',
            }}
            onClick={() => setShowRetrainDialog(true)}
            disabled={retraining}
            title="Retrain XGBoost risk classifier on current database state"
          >
            <RefreshCw size={12} className={retraining ? 'animate-spin' : ''} />
            <span>{retraining ? 'Retraining...' : 'Retrain Model'}</span>
          </button>

          {/* Health Status */}
          <div className={`header-status-badge ${isOnline ? 'online' : 'offline'}`}>
            <span className="pulse-dot" />
            <span>{isOnline ? 'API & Models Online' : 'Connecting to API...'}</span>
          </div>
        </div>
      </div>

      {/* Retrain Success Toast */}
      {retrainResult && (
        <div
          style={{
            background: '#065f46',
            color: '#ecfdf5',
            padding: '6px 16px',
            fontSize: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid rgba(255,255,255,0.2)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle2 size={14} />
            <span>
              XGBoost Classifier Retrained Successfully! Accuracy:{' '}
              <strong>{(retrainResult.before_accuracy * 100).toFixed(2)}%</strong> →{' '}
              <strong>{(retrainResult.after_accuracy * 100).toFixed(2)}%</strong> (In-memory models reloaded)
            </span>
          </div>
          <button
            onClick={() => setRetrainResult(null)}
            style={{ background: 'transparent', border: 'none', color: 'inherit', cursor: 'pointer' }}
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Retrain Error Banner */}
      {retrainError && (
        <div
          style={{
            background: '#991b1b',
            color: '#fef2f2',
            padding: '6px 16px',
            fontSize: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={14} />
            <span>Retrain Error: {retrainError}</span>
          </div>
          <button
            onClick={() => setRetrainError(null)}
            style={{ background: 'transparent', border: 'none', color: 'inherit', cursor: 'pointer' }}
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Confirmation Dialog for Retrain */}
      {showRetrainDialog && (
        <div className="modal-backdrop" onClick={() => !retraining && setShowRetrainDialog(false)}>
          <div
            className="modal-card"
            style={{
              maxWidth: '480px',
              padding: '24px',
              background: 'var(--bg-surface)',
              borderRadius: '12px',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '8px',
                  background: 'rgba(234, 88, 12, 0.12)',
                  color: 'var(--risk-high)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <RefreshCw size={18} />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 800 }}>
                  Confirm ML Model Retraining
                </h3>
                <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Administrative live model calibration
                </p>
              </div>
            </div>

            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: '12px 0' }}>
              You are about to execute <strong>5-fold Stratified Cross-Validation & Hyperparameter Tuning</strong> on
              the live database records. Once completed, the new XGBoost classifier and SHAP TreeExplainer will be
              <strong> atomically swapped</strong> into the active application state without restarting the server.
            </p>

            <div
              style={{
                background: 'var(--bg-elevated)',
                padding: '10px 12px',
                borderRadius: '6px',
                fontSize: '0.75rem',
                color: 'var(--text-muted)',
                marginBottom: '18px',
                border: '1px solid var(--border-light)',
              }}
            >
              🔒 <strong>Guard:</strong> Requires explicit admin confirmation (`?confirm=true`). Prevents unintended retrain calls during live evaluation.
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                className="btn-paginate"
                onClick={() => setShowRetrainDialog(false)}
                disabled={retraining}
                style={{ padding: '8px 14px' }}
              >
                Cancel
              </button>
              <button
                className="btn-primary"
                onClick={handleConfirmRetrain}
                disabled={retraining}
                style={{ padding: '8px 18px', display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <RefreshCw size={14} className={retraining ? 'animate-spin' : ''} />
                <span>{retraining ? 'Training Model...' : 'Confirm & Retrain'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
