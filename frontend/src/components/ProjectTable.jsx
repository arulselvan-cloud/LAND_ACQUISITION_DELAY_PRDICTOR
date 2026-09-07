import React from 'react';
import { Search, Filter, ChevronLeft, ChevronRight, ArrowUpRight, GitFork } from 'lucide-react';

const INDIAN_STATES = [
  'Andhra Pradesh', 'Bihar', 'Gujarat', 'Karnataka', 'Madhya Pradesh',
  'Maharashtra', 'Odisha', 'Rajasthan', 'Tamil Nadu', 'Telangana',
  'Uttar Pradesh', 'West Bengal'
];

export default function ProjectTable({
  projects = [],
  total = 0,
  page = 1,
  pageSize = 20,
  totalPages = 1,
  onPageChange = () => {},
  onPageSizeChange = () => {},
  selectedState = '',
  onStateChange = () => {},
  selectedRisk = '',
  onRiskChange = () => {},
  searchQuery = '',
  onSearchChange = () => {},
  onSelectProject = () => {},
  selectedProjectId = null,
  loading = false,
  comparisonSelectedIds = [],
  onToggleComparison = () => {},
  onOpenComparison = () => {},
  onSelectTrio = () => {},
  onClearComparison = () => {},
}) {
  // Filter by local search query on code or name
  const filteredProjects = projects.filter((p) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (p.project_code || '').toLowerCase().includes(q) ||
      (p.name || '').toLowerCase().includes(q) ||
      (p.district || '').toLowerCase().includes(q)
    );
  });

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2 className="card-title">Infrastructure Project Catalog</h2>
          <p className="card-subtitle">
            Statutory land acquisition monitoring, milestone status, and live calibrated risk classification
          </p>
        </div>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Showing <strong>{projects.length}</strong> of <strong>{total.toLocaleString()}</strong> projects
        </div>
      </div>

      {/* Toolbar: Filters and Search */}
      <div className="table-toolbar">
        <div className="filter-group">
          {/* Search Box */}
          <div style={{ position: 'relative' }}>
            <input
              type="text"
              placeholder="Search code or name..."
              className="input-control"
              style={{ paddingLeft: '32px', width: '220px' }}
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
            />
            <Search
              size={15}
              style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}
            />
          </div>

          {/* State Filter */}
          <select
            className="select-control"
            value={selectedState}
            onChange={(e) => onStateChange(e.target.value)}
          >
            <option value="">All States (12)</option>
            {INDIAN_STATES.map((st) => (
              <option key={st} value={st}>
                {st}
              </option>
            ))}
          </select>

          {/* Risk Filter */}
          <select
            className="select-control"
            value={selectedRisk}
            onChange={(e) => onRiskChange(e.target.value)}
          >
            <option value="">All Risk Categories</option>
            <option value="critical">Critical Risk</option>
            <option value="high">High Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="low">Low Risk</option>
          </select>

          {(selectedState || selectedRisk || searchQuery) && (
            <button
              onClick={() => {
                onStateChange('');
                onRiskChange('');
                onSearchChange('');
              }}
              className="btn-paginate"
              style={{ color: 'var(--text-muted)' }}
            >
              Clear Filters
            </button>
          )}
        </div>

        {/* Page size selector & Comparison Quick Trigger */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <button
            className="chip-btn"
            style={{ fontSize: '0.74rem', padding: '5px 10px', display: 'flex', alignItems: 'center', gap: '5px' }}
            onClick={onSelectTrio}
            title="Compare Showcase Projects: CBIC, BSRP, MAHSR side-by-side"
          >
            <GitFork size={13} />
            <span>Compare Showcase Trio</span>
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span>Rows:</span>
            <select
              className="select-control"
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              style={{ padding: '4px 8px' }}
            >
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100 (Max)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Comparison Action Bar */}
      {comparisonSelectedIds.length > 0 && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 16px',
            background: 'rgba(30, 58, 138, 0.08)',
            border: '1px solid rgba(30, 58, 138, 0.25)',
            borderRadius: '8px',
            margin: '0 20px 12px 20px',
            fontSize: '0.82rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <GitFork size={16} style={{ color: 'var(--gov-blue)' }} />
            <span>
              <strong>{comparisonSelectedIds.length}</strong> {comparisonSelectedIds.length === 1 ? 'project' : 'projects'} selected for comparison:
              <span style={{ marginLeft: '6px', color: 'var(--gov-blue)', fontWeight: 600 }}>
                {comparisonSelectedIds.join(', ')}
              </span>
              {comparisonSelectedIds.length < 2 && (
                <span style={{ color: 'var(--text-muted)', marginLeft: '6px' }}>(Select 2 or 3 to compare)</span>
              )}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {comparisonSelectedIds.length >= 2 && (
              <button
                className="btn-primary"
                style={{ padding: '6px 14px', fontSize: '0.78rem' }}
                onClick={onOpenComparison}
              >
                Compare Side-by-Side ({comparisonSelectedIds.length})
              </button>
            )}
            <button
              className="btn-paginate"
              style={{ padding: '6px 10px', fontSize: '0.78rem' }}
              onClick={onClearComparison}
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {/* Table Container */}
      <div className="table-container">
        <table className="gov-table">
          <thead>
            <tr>
              <th style={{ width: '40px', textAlign: 'center' }}>Select</th>
              <th>Project Code</th>
              <th>Project Name</th>
              <th>District & State</th>
              <th>Sector Type</th>
              <th>Risk Tier</th>
              <th>Delay Probability</th>
              <th style={{ textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                  Loading project records from PostgreSQL...
                </td>
              </tr>
            ) : filteredProjects.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                  No infrastructure projects match the selected criteria.
                </td>
              </tr>
            ) : (
              filteredProjects.map((p) => {
                const code = p.project_code || p.id;
                const isSelected = selectedProjectId === p.id || selectedProjectId === p.project_code;
                const isCompared = comparisonSelectedIds.includes(code) || comparisonSelectedIds.includes(p.id);
                const riskCat = (p.risk_category || 'low').toLowerCase();
                const probPct = ((p.delay_probability || 0) * 100).toFixed(1);

                return (
                  <tr
                    key={p.id}
                    className={`${isSelected ? 'selected' : ''} ${isCompared ? 'compared-row' : ''}`}
                    onClick={() => onSelectProject(code)}
                  >
                    <td
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleComparison(code);
                      }}
                      style={{ width: '40px', textAlign: 'center' }}
                    >
                      <input
                        type="checkbox"
                        checked={isCompared}
                        onChange={() => {}}
                        style={{ cursor: 'pointer', transform: 'scale(1.15)' }}
                        title="Select for comparison (up to 3)"
                      />
                    </td>
                    <td style={{ fontFamily: 'monospace', fontWeight: 700, color: 'var(--gov-blue)' }}>
                      {p.project_code}
                    </td>
                    <td style={{ fontWeight: 600, maxWidth: '280px' }}>
                      <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {p.name}
                      </div>
                    </td>
                    <td>
                      <div>{p.district}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{p.state}</div>
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>
                      {p.project_type}
                    </td>
                    <td>
                      <span className={`risk-badge ${riskCat}`}>
                        {p.risk_category}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ flex: 1, height: '6px', background: '#e2e8f0', borderRadius: '3px', width: '60px', overflow: 'hidden' }}>
                          <div
                            style={{
                              height: '100%',
                              width: `${probPct}%`,
                              background:
                                riskCat === 'critical'
                                  ? 'var(--risk-critical)'
                                  : riskCat === 'high'
                                  ? 'var(--risk-high)'
                                  : riskCat === 'medium'
                                  ? 'var(--risk-medium)'
                                  : 'var(--risk-low)',
                            }}
                          />
                        </div>
                        <span style={{ fontWeight: 700, fontSize: '0.78rem' }}>{probPct}%</span>
                      </div>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '2px',
                          color: 'var(--gov-blue)',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                        }}
                      >
                        Inspect <ArrowUpRight size={13} />
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="table-pagination">
        <div>
          Page <strong>{page}</strong> of <strong>{totalPages}</strong> ({total.toLocaleString()} total entries)
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className="btn-paginate"
            disabled={page <= 1 || loading}
            onClick={() => onPageChange(page - 1)}
          >
            <ChevronLeft size={14} style={{ verticalAlign: 'middle' }} /> Prev
          </button>
          <button
            className="btn-paginate"
            disabled={page >= totalPages || loading}
            onClick={() => onPageChange(page + 1)}
          >
            Next <ChevronRight size={14} style={{ verticalAlign: 'middle' }} />
          </button>
        </div>
      </div>
    </div>
  );
}
