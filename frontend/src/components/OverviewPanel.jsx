import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  FolderKanban,
  AlertTriangle,
  Clock,
  Users,
  MapPin
} from 'lucide-react';

const RISK_COLORS = {
  Low: '#10B981',
  Medium: '#F59E0B',
  High: '#F97316',
  Critical: '#EF4444',
};

export default function OverviewPanel({ summary, loading }) {
  if (loading && !summary) {
    return (
      <div className="card" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
        Loading executive summary metrics...
      </div>
    );
  }

  const {
    total_projects = 3503,
    high_critical_count = 1049,
    avg_delay_probability = 0.3485,
    total_affected_families = 1153921,
    total_land_area_hectares = 337370.85,
    risk_breakdown = { Low: 1384, Medium: 1070, High: 570, Critical: 479 },
  } = summary || {};

  const donutData = [
    { name: 'Low Risk', value: risk_breakdown.Low || 0, color: RISK_COLORS.Low, key: 'Low' },
    { name: 'Medium Risk', value: risk_breakdown.Medium || 0, color: RISK_COLORS.Medium, key: 'Medium' },
    { name: 'High Risk', value: risk_breakdown.High || 0, color: RISK_COLORS.High, key: 'High' },
    { name: 'Critical Risk', value: risk_breakdown.Critical || 0, color: RISK_COLORS.Critical, key: 'Critical' },
  ];

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      const pct = total_projects ? ((data.value / total_projects) * 100).toFixed(1) : 0;
      return (
        <div style={{ background: '#ffffff', border: '1px solid #cbd5e1', padding: '8px 12px', borderRadius: '6px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)', fontSize: '0.78rem' }}>
          <div style={{ fontWeight: 700, color: data.payload.color }}>{data.name}</div>
          <div style={{ color: '#334155', marginTop: '2px' }}>
            {data.value.toLocaleString()} projects ({pct}%)
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="overview-grid">
      {/* KPI Card 1: Total Infrastructure Projects */}
      <div className="kpi-card" style={{ '--kpi-accent': 'var(--gov-blue)' }}>
        <div className="kpi-top">
          <span className="kpi-label">Active Portfolio</span>
          <div className="kpi-icon">
            <FolderKanban size={18} />
          </div>
        </div>
        <div>
          <div className="kpi-value">{total_projects.toLocaleString()}</div>
          <div className="kpi-subtext">Monitored Infrastructure Projects across 12 States</div>
        </div>
      </div>

      {/* KPI Card 2: High & Critical Risk Alerts */}
      <div className="kpi-card" style={{ '--kpi-accent': 'var(--risk-critical)', '--kpi-icon-bg': 'var(--risk-critical-bg)' }}>
        <div className="kpi-top">
          <span className="kpi-label">Priority Delay Alerts</span>
          <div className="kpi-icon" style={{ color: 'var(--risk-critical)' }}>
            <AlertTriangle size={18} />
          </div>
        </div>
        <div>
          <div className="kpi-value" style={{ color: 'var(--risk-critical)' }}>
            {high_critical_count.toLocaleString()}
          </div>
          <div className="kpi-subtext">
            {total_projects ? `${((high_critical_count / total_projects) * 100).toFixed(1)}%` : '0%'} Projects in High or Critical Risk Tiers
          </div>
        </div>
      </div>

      {/* KPI Card 3: Average Delay Probability */}
      <div className="kpi-card" style={{ '--kpi-accent': 'var(--risk-medium)', '--kpi-icon-bg': 'var(--risk-medium-bg)' }}>
        <div className="kpi-top">
          <span className="kpi-label">Avg Delay Exposure</span>
          <div className="kpi-icon" style={{ color: 'var(--risk-medium)' }}>
            <Clock size={18} />
          </div>
        </div>
        <div>
          <div className="kpi-value">
            {(avg_delay_probability * 100).toFixed(1)}%
          </div>
          <div className="kpi-subtext">Calibrated National Mean Acquisition Delay Probability</div>
        </div>
      </div>

      {/* KPI Card 4: Families Affected & Land Area */}
      <div className="kpi-card" style={{ '--kpi-accent': '#0284c7', '--kpi-icon-bg': '#e0f2fe' }}>
        <div className="kpi-top">
          <span className="kpi-label">Affected Land & Citizens</span>
          <div className="kpi-icon" style={{ color: '#0284c7' }}>
            <Users size={18} />
          </div>
        </div>
        <div>
          <div className="kpi-value" style={{ fontSize: '1.45rem' }}>
            {(total_affected_families / 100000).toFixed(2)}L PAFs
          </div>
          <div className="kpi-subtext">
            {Math.round(total_land_area_hectares).toLocaleString()} Hectares total acquisition area
          </div>
        </div>
      </div>

      {/* KPI Card 5: Donut Chart Risk Breakdown */}
      <div className="donut-card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)' }}>
            Statutory Risk Distribution
          </span>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            4-Tier Classifier
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', height: '100px' }}>
          <div style={{ width: '110px', height: '100px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={donutData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={28}
                  outerRadius={45}
                  paddingAngle={3}
                >
                  {donutData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div style={{ flex: 1, paddingLeft: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
            {donutData.map((d) => {
              const pct = total_projects ? ((d.value / total_projects) * 100).toFixed(0) : 0;
              return (
                <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.74rem' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: d.color, display: 'inline-block' }} />
                  <div>
                    <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>{d.key}: </span>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{d.value}</span>
                    <span style={{ color: 'var(--text-muted)', marginLeft: '2px', fontSize: '0.68rem' }}>({pct}%)</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
