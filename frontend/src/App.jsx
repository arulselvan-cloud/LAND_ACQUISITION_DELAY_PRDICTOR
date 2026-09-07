import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import OverviewPanel from './components/OverviewPanel';
import DistrictHeatmap from './components/DistrictHeatmap';
import ProjectTable from './components/ProjectTable';
import AlertsFeed from './components/AlertsFeed';
import ProjectDetail from './components/ProjectDetail';
import ProjectComparisonModal from './components/ProjectComparisonModal';
import {
  getHealthCheck,
  getExecutiveSummary,
  getDistrictsSummary,
  listProjects,
  getAlerts
} from './api/client';
import { AlertTriangle, X } from 'lucide-react';

export default function App() {
  const [health, setHealth] = useState(null);
  const [summary, setSummary] = useState(null);
  const [districtsSummary, setDistrictsSummary] = useState([]);
  const [projectsData, setProjectsData] = useState({ total: 0, page: 1, page_size: 20, total_pages: 1, projects: [] });
  const [alertsData, setAlertsData] = useState({ total_alerts: 0, alerts: [] });

  // Filters & State
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [selectedDistrict, setSelectedDistrict] = useState(null);
  const [selectedState, setSelectedState] = useState('');
  const [selectedRisk, setSelectedRisk] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // Multi-Project Comparison State (2-3 projects)
  const [comparisonSelectedIds, setComparisonSelectedIds] = useState([]);
  const [showComparisonModal, setShowComparisonModal] = useState(false);

  const [loadingProjects, setLoadingProjects] = useState(false);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [globalError, setGlobalError] = useState(null);

  // 1. Initial Load: Health, Summary, Heatmap Districts, and Alerts
  useEffect(() => {
    // Health check
    getHealthCheck()
      .then((h) => setHealth(h))
      .catch((err) => console.warn('Health check warning:', err));

    // Executive summary
    getExecutiveSummary()
      .then((s) => {
        setSummary(s);
        setLoadingSummary(false);
      })
      .catch((err) => {
        console.error('Summary fetch error:', err);
        setLoadingSummary(false);
      });

    // Districts summary for heatmap
    getDistrictsSummary()
      .then((ds) => setDistrictsSummary(ds))
      .catch((err) => console.error('Districts summary error:', err));

    // Priority delay alerts
    getAlerts(50)
      .then((res) => setAlertsData(res))
      .catch((err) => console.error('Alerts error:', err));
  }, []);

  // 2. Fetch projects when table filters or pagination change
  useEffect(() => {
    setLoadingProjects(true);
    setGlobalError(null);

    listProjects({
      page,
      pageSize,
      state: selectedState,
      riskCategory: selectedRisk,
    })
      .then((res) => {
        setProjectsData(res);
        setLoadingProjects(false);
      })
      .catch((err) => {
        console.error('List projects error:', err);
        setGlobalError(err.message || 'Failed to load projects list.');
        setLoadingProjects(false);
      });
  }, [page, pageSize, selectedState, selectedRisk]);

  // When a district is selected on the heatmap, filter search or state
  const handleSelectDistrict = (districtName) => {
    setSelectedDistrict(districtName);
    if (districtName) {
      setSearchQuery(districtName);
    } else {
      setSearchQuery('');
    }
  };

  const handleSelectShowcase = (projectCode) => {
    setSelectedProjectId(projectCode);
  };

  // Comparison Handlers
  const handleToggleComparison = (projectCode) => {
    setComparisonSelectedIds((prev) => {
      if (prev.includes(projectCode)) {
        return prev.filter((id) => id !== projectCode);
      }
      if (prev.length >= 3) {
        alert('You can select a maximum of 3 projects for parallel comparison.');
        return prev;
      }
      return [...prev, projectCode];
    });
  };

  const handleSelectTrio = () => {
    const trio = ['CBIC-TN-PKG02', 'BSRP-KA-CORR04', 'MAHSR-MH-PAL03'];
    setComparisonSelectedIds(trio);
    setShowComparisonModal(true);
  };

  const handleOpenComparison = () => {
    if (comparisonSelectedIds.length < 2) {
      alert('Please select at least 2 projects from the catalog (using the checkboxes) to compare.');
      return;
    }
    setShowComparisonModal(true);
  };

  const handleClearComparison = () => {
    setComparisonSelectedIds([]);
  };

  return (
    <div className="dashboard-root">
      {/* Executive Header with Showcase Selector & Retrain Action */}
      <Header
        health={health}
        onSelectShowcase={handleSelectShowcase}
        activeProjectId={selectedProjectId}
        onOpenComparison={handleSelectTrio}
      />

      <main className="dashboard-main">
        {/* Global Error Banner if API disconnected */}
        {globalError && (
          <div className="error-banner">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle size={18} />
              <span>{globalError}</span>
            </div>
            <button
              onClick={() => setGlobalError(null)}
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'inherit' }}
            >
              <X size={16} />
            </button>
          </div>
        )}

        {/* 1. Executive Overview Metrics & Donut Risk Chart */}
        <OverviewPanel summary={summary} loading={loadingSummary} />

        {/* 2. Geospatial Heatmap & Alerts Feed Grid */}
        <div className="dashboard-grid-2col">
          <DistrictHeatmap
            districtsSummary={districtsSummary}
            selectedDistrict={selectedDistrict}
            onSelectDistrict={handleSelectDistrict}
          />

          <AlertsFeed
            alerts={alertsData.alerts}
            totalAlerts={alertsData.total_alerts}
            onSelectProject={(code) => setSelectedProjectId(code)}
            loading={loadingSummary}
          />
        </div>

        {/* 3. Paginated Infrastructure Projects Table */}
        <ProjectTable
          projects={projectsData.projects}
          total={projectsData.total}
          page={projectsData.page}
          pageSize={projectsData.page_size}
          totalPages={projectsData.total_pages}
          onPageChange={(newPage) => setPage(newPage)}
          onPageSizeChange={(newSize) => {
            setPageSize(newSize);
            setPage(1);
          }}
          selectedState={selectedState}
          onStateChange={(st) => {
            setSelectedState(st);
            setPage(1);
          }}
          selectedRisk={selectedRisk}
          onRiskChange={(r) => {
            setSelectedRisk(r);
            setPage(1);
          }}
          searchQuery={searchQuery}
          onSearchChange={(q) => setSearchQuery(q)}
          onSelectProject={(code) => setSelectedProjectId(code)}
          selectedProjectId={selectedProjectId}
          loading={loadingProjects}
          comparisonSelectedIds={comparisonSelectedIds}
          onToggleComparison={handleToggleComparison}
          onOpenComparison={handleOpenComparison}
          onSelectTrio={handleSelectTrio}
          onClearComparison={handleClearComparison}
        />
      </main>

      {/* 4. Project Detail Modal (5-Stage Story Flow) */}
      {selectedProjectId && (
        <ProjectDetail
          projectId={selectedProjectId}
          onClose={() => setSelectedProjectId(null)}
        />
      )}

      {/* 5. Project Comparison Modal (Side-by-Side 2-3 Corridors) */}
      {showComparisonModal && (
        <ProjectComparisonModal
          projectIds={comparisonSelectedIds.length >= 2 ? comparisonSelectedIds : ['CBIC-TN-PKG02', 'BSRP-KA-CORR04', 'MAHSR-MH-PAL03']}
          onClose={() => setShowComparisonModal(false)}
          onSelectProject={(code) => {
            setShowComparisonModal(false);
            setSelectedProjectId(code);
          }}
          onSelectTrio={handleSelectTrio}
        />
      )}
    </div>
  );
}
