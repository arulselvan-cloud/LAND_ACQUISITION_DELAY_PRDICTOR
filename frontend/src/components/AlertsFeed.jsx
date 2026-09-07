import React from 'react';
import { AlertCircle, ArrowUpRight, Flame, Send, ShieldAlert } from 'lucide-react';

export default function AlertsFeed({
  alerts = [],
  totalAlerts = 0,
  onSelectProject = () => {},
  loading = false,
}) {
  return (
    <div className="card" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="card-header" style={{ marginBottom: '12px' }}>
        <div>
          <h2 className="card-title" style={{ color: 'var(--risk-critical)' }}>
            <Flame size={18} />
            Priority Delay Alerts
          </h2>
          <p className="card-subtitle">
            Critical & High bottleneck queue ranked by delay risk
          </p>
        </div>
        <span
          style={{
            fontSize: '0.72rem',
            fontWeight: 800,
            background: 'var(--risk-critical-bg)',
            color: 'var(--risk-critical-text)',
            padding: '2px 8px',
            borderRadius: 'var(--radius-full)',
            border: '1px solid var(--risk-critical-border)',
          }}
        >
          {totalAlerts.toLocaleString()} Total
        </span>
      </div>

      <div className="alerts-list">
        {loading && alerts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
            Scanning real-time project risk queue...
          </div>
        ) : alerts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
            No high or critical alerts active.
          </div>
        ) : (
          alerts.map((alert) => {
            const riskCat = (alert.risk_category || 'high').toLowerCase();
            const probPct = ((alert.delay_probability || 0) * 100).toFixed(1);

            return (
              <div
                key={alert.id || alert.project_code}
                className={`alert-item ${riskCat}`}
                onClick={() => onSelectProject(alert.project_code || alert.id)}
              >
                <div className="alert-item-header">
                  <span className="alert-code">{alert.project_code}</span>
                  <span className={`risk-badge ${riskCat}`}>
                    {probPct}% Delay Risk
                  </span>
                </div>

                <div className="alert-name" title={alert.name}>
                  {alert.name}
                </div>

                <div className="alert-meta">
                  <span>
                    {alert.district}, {alert.state}
                  </span>
                  <span>{alert.affected_families_count || 0} PAFs</span>
                </div>

                {alert.recommendation_snippet && (
                  <div className="alert-rec-snippet">
                    <span style={{ fontWeight: 700, color: 'var(--gov-blue)', marginRight: '4px' }}>Action:</span>
                    {alert.recommendation_snippet}
                  </div>
                )}

                {alert.notification_preview && (
                  <div
                    style={{
                      marginTop: '8px',
                      padding: '7px 10px',
                      background: 'rgba(13, 148, 136, 0.08)',
                      border: '1px solid rgba(13, 148, 136, 0.3)',
                      borderRadius: '6px',
                      fontSize: '0.72rem',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px',
                        color: '#0d9488',
                        fontWeight: 700,
                        marginBottom: '3px',
                      }}
                    >
                      <Send size={11} />
                      <span>
                        Notification Sent • {alert.notification_channel?.toUpperCase() || 'SMS'} to{' '}
                        {alert.notification_recipient || 'District Collector'}
                      </span>
                    </div>
                    <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', lineHeight: 1.35 }}>
                      "{alert.notification_preview}"
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      <div
        style={{
          marginTop: 'auto',
          paddingTop: '12px',
          borderTop: '1px solid var(--border-light)',
          fontSize: '0.72rem',
          color: 'var(--text-muted)',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}
      >
        <ShieldAlert size={14} style={{ color: 'var(--gov-blue)' }} />
        <span>Live-scored by XGBoost Classifier</span>
      </div>
    </div>
  );
}
