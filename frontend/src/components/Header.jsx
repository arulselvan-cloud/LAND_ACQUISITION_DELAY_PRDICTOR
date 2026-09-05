import React from 'react';
import { ShieldAlert, Activity, CheckCircle2, AlertCircle, Building2 } from 'lucide-react';

export default function Header({
  health,
  onSelectShowcase,
  activeProjectId
}) {
  const showcaseProjects = [
    { code: 'CBIC-TN-PKG02', label: 'CBIC Industrial Pkg 2', state: 'Tamil Nadu' },
    { code: 'BSRP-KA-CORR04', label: 'BSRP Suburban Rail', state: 'Karnataka' },
    { code: 'MAHSR-MH-PAL03', label: 'MAHSR High-Speed Rail', state: 'Maharashtra' },
  ];

  const isOnline = health && health.status === 'healthy';

  return (
    <header className="gov-header">
      <div className="gov-tricolor-bar" />
      <div className="gov-header-inner">
        {/* Brand & Emblem */}
        <div className="gov-brand">
          <div className="gov-emblem-badge">
            <Building2 size={24} className="text-white opacity-90" />
            <div style={{ lineHeight: 1.1 }}>
              <div style={{ fontSize: '0.65rem', letterSpacing: '0.08em', opacity: 0.8, textTransform: 'uppercase' }}>
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
              <span style={{ fontSize: '0.7rem', fontWeight: 600, padding: '2px 6px', background: 'rgba(255,255,255,0.15)', borderRadius: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                SIH26017 Prototype
              </span>
            </h1>
            <p>Predictive Delay Analytics & Statutory RFCTLARR Milestone Risk Intelligence</p>
          </div>
        </div>

        {/* Showcase Fast Selector & Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
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

          {/* Health Status */}
          <div className={`header-status-badge ${isOnline ? 'online' : 'offline'}`}>
            <span className="pulse-dot" />
            <span>{isOnline ? 'API & Models Online' : 'Connecting to API...'}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
