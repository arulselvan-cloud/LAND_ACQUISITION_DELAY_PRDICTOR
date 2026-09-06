import React, { useEffect, useState, useRef } from 'react';
import {
  X,
  Building2,
  FileSpreadsheet,
  Cpu,
  BarChart3,
  GitMerge,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingDown,
  Clock,
  Scale,
  Sparkles,
  RefreshCw,
  FileText
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LabelList
} from 'recharts';
import {
  predictProject,
  getProjectExplanation,
  getProjectPropagation,
  simulateWhatIf,
  getProjectDetails,
  generateProjectRecommendation,
  getProjectRecommendations
} from '../api/client';

export default function ProjectDetail({
  projectId,
  onClose = () => {}
}) {
  const [project, setProject] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [propagation, setPropagation] = useState([]);
  const [whatIfData, setWhatIfData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [whatIfLoading, setWhatIfLoading] = useState(false);
  const [error, setError] = useState(null);

  // What-if interactive slider states
  const [compDisbursedPct, setCompDisbursedPct] = useState(50);
  const [stakeholderResp, setStakeholderResp] = useState(50);
  const [activeDispute, setActiveDispute] = useState(0);

  // Recommendations and AI memo states
  const [recommendations, setRecommendations] = useState([]);
  const [aiMemo, setAiMemo] = useState(null);
  const [generatingRec, setGeneratingRec] = useState(false);
  const [recError, setRecError] = useState(null);

  const debounceTimerRef = useRef(null);

  // Load project data, initial predictions, and recommendations
  useEffect(() => {
    if (!projectId) return;

    let isMounted = true;
    setLoading(true);
    setError(null);
    setRecError(null);

    Promise.all([
      getProjectDetails(projectId),
      predictProject(projectId),
      getProjectExplanation(projectId),
      getProjectPropagation(projectId),
      getProjectRecommendations(projectId).catch(() => ({ recommendations: [] }))
    ])
      .then(([projData, predData, expData, propData, recsData]) => {
        if (!isMounted) return;
        setProject(projData);
        setPrediction(predData);
        setExplanation(expData);
        setPropagation(propData);

        const recList = recsData?.recommendations || [];
        setRecommendations(recList);
        const execDirective = recList.find(r => r.category === 'Executive Directive');
        if (execDirective) {
          setAiMemo(execDirective.action_text);
        }

        // Find initial feature values for what-if sliders
        const compDriver = expData.factors.find(f => f.feature === 'compensation_disbursed_pct');
        const disputeDriver = expData.factors.find(f => f.feature === 'has_active_legal_dispute');
        const respDriver = expData.factors.find(f => f.feature === 'avg_stakeholder_responsiveness');

        const initialComp = compDriver && compDriver.value !== null ? Number(compDriver.value) : 50;
        const initialDispute = disputeDriver && disputeDriver.value !== null ? Number(disputeDriver.value) : 0;
        const initialResp = respDriver && respDriver.value !== null ? Number(respDriver.value) : 50;

        setCompDisbursedPct(Math.round(initialComp));
        setActiveDispute(initialDispute ? 1 : 0);
        setStakeholderResp(Math.round(initialResp));

        // Trigger initial what-if baseline
        return simulateWhatIf(projectId, {
          compensation_disbursed_pct: initialComp,
          has_active_legal_dispute: initialDispute ? 1 : 0,
          avg_stakeholder_responsiveness: initialResp,
        });
      })
      .then((whatIfRes) => {
        if (!isMounted || !whatIfRes) return;
        setWhatIfData(whatIfRes);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error('Error loading project detail:', err);
        setError(err.message || 'Could not load project telemetry.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    };
  }, [projectId]);

  // Triggers Gemini 2.5 Flash administrative memo and recommendations generation
  const handleGenerateRecommendation = async (simulateFailure = false) => {
    setGeneratingRec(true);
    setRecError(null);
    try {
      const res = await generateProjectRecommendation(projectId, simulateFailure);
      setAiMemo(res.memo);
      setRecommendations(res.recommendations || []);
    } catch (err) {
      console.error('Failed to generate recommendation:', err);
      setRecError(err.message || 'Failed to generate administrative action plan.');
    } finally {
      setGeneratingRec(false);
    }
  };

  // Debounced what-if counterfactual trigger on slider change
  const triggerWhatIf = (newComp, newResp, newDispute) => {
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);

    setWhatIfLoading(true);
    debounceTimerRef.current = setTimeout(() => {
      simulateWhatIf(projectId, {
        compensation_disbursed_pct: Number(newComp),
        avg_stakeholder_responsiveness: Number(newResp),
        has_active_legal_dispute: Number(newDispute),
      })
        .then((res) => {
          setWhatIfData(res);
          setWhatIfLoading(false);
        })
        .catch((err) => {
          console.error('What-if error:', err);
          setWhatIfLoading(false);
        });
    }, 300);
  };

  const handleCompChange = (val) => {
    setCompDisbursedPct(val);
    triggerWhatIf(val, stakeholderResp, activeDispute);
  };

  const handleRespChange = (val) => {
    setStakeholderResp(val);
    triggerWhatIf(compDisbursedPct, val, activeDispute);
  };

  const handleDisputeToggle = () => {
    const nextVal = activeDispute ? 0 : 1;
    setActiveDispute(nextVal);
    triggerWhatIf(compDisbursedPct, stakeholderResp, nextVal);
  };

  const formatFeatureValue = (feature, val) => {
    if (val === null || val === undefined) return '';
    if (feature === 'compensation_disbursed_pct') {
      return `${Number(val).toFixed(1)}%`;
    }
    if (feature === 'rehabilitation_completion_pct') {
      return `${Number(val).toFixed(1)}%`;
    }
    if (feature === 'avg_stakeholder_responsiveness') {
      return `${Number(val).toFixed(1)} / 100`;
    }
    if (feature === 'dispute_delay_impact_days') {
      return `${Math.round(Number(val))} days`;
    }
    if (feature === 'has_active_legal_dispute') {
      return Number(val) > 0 ? 'Active (Yes)' : '0 (None)';
    }
    if (feature === 'land_area_hectares') {
      return `${Number(val).toFixed(1)} Ha`;
    }
    if (feature === 'affected_families_count') {
      return `${Math.round(Number(val))} PAFs`;
    }
    if (feature === 'state_encoded') {
      return project?.state || `${val}`;
    }
    if (feature === 'project_type_encoded') {
      return project?.project_type || `${val}`;
    }
    if (typeof val === 'number') {
      return Number.isInteger(val) ? `${val}` : Number(val).toFixed(1);
    }
    return `${val}`;
  };

  // Format SHAP data for horizontal bar chart with actual underlying values
  const shapChartData = (explanation?.factors || []).map((f) => {
    const rawFormatted = formatFeatureValue(f.feature, f.value);
    const labelWithVal = rawFormatted ? `${f.display_name} — ${rawFormatted}` : f.display_name;
    return {
      name: labelWithVal,
      displayName: f.display_name,
      rawName: f.feature,
      magnitude: f.magnitude,
      direction: f.direction,
      value: f.value,
      formattedValue: rawFormatted,
      color: f.direction === 'increases_risk' ? '#EF4444' : '#10B981',
    };
  });

  const totalCumulativeDelay = propagation.reduce((acc, s) => acc + (s.delay_days || 0), 0);

  return (
    <div className="detail-overlay" onClick={onClose}>
      <div className="detail-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="detail-header">
          <div className="detail-title-group">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontFamily: 'monospace', fontWeight: 800, background: 'rgba(255,255,255,0.15)', padding: '2px 8px', borderRadius: '4px' }}>
                {project?.project_code || projectId}
              </span>
              <h2>{project?.name || 'Infrastructure Corridor Inspection'}</h2>
            </div>
            <p>
              {project?.district}, {project?.state} &bull; Sector: {project?.project_type || 'Transport'}
            </p>
          </div>

          <button className="close-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="detail-body">
          {error && (
            <div className="error-banner">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertTriangle size={18} />
                <span>{error}</span>
              </div>
            </div>
          )}

          {loading ? (
            <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
              Querying database milestones and running ML inference pipeline...
            </div>
          ) : (
            <>
              {/* STAGE 1 & 2: Land Data & AI Prediction Header */}
              <div className="story-section">
                <div className="story-section-title">
                  <span className="story-stage-num">Stages 1 & 2</span>
                  <FileSpreadsheet size={16} />
                  <span>Land Parcel Attributes & Calibrated AI Risk Category</span>
                </div>

                <div className="meta-grid">
                  <div className="meta-item">
                    <div className="meta-label">Acquisition Area</div>
                    <div className="meta-val">{project?.land_area_hectares?.toLocaleString()} Hectares</div>
                  </div>
                  <div className="meta-item">
                    <div className="meta-label">Affected Families</div>
                    <div className="meta-val">{project?.affected_families_count?.toLocaleString()} PAFs</div>
                  </div>
                  <div className="meta-item">
                    <div className="meta-label">AI Risk Classification</div>
                    <div className="meta-val" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className={`risk-badge ${(prediction?.risk_category || 'low').toLowerCase()}`}>
                        {prediction?.risk_category || 'unassessed'}
                      </span>
                    </div>
                  </div>
                  <div className="meta-item">
                    <div className="meta-label">Delay Probability</div>
                    <div className="meta-val" style={{ color: 'var(--gov-blue)' }}>
                      {((prediction?.delay_probability || 0) * 100).toFixed(1)}%
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginLeft: '4px' }}>
                        (Conf: {((prediction?.confidence_score || 0) * 100).toFixed(0)}%)
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* STAGE 3: SHAP Explainability Engine */}
              <div className="story-section">
                <div className="story-section-title">
                  <span className="story-stage-num">Stage 3</span>
                  <BarChart3 size={16} />
                  <span>SHAP Explainability: Top 5 Contributing Risk Factors</span>
                </div>

                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
                  TreeExplainer feature attributions with actual project values. <span style={{ color: '#EF4444', fontWeight: 700 }}>Red bars</span> increase delay risk, while <span style={{ color: '#10B981', fontWeight: 700 }}>green bars</span> accelerate milestone progress.
                </p>

                <div style={{ height: '230px', width: '100%' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      layout="vertical"
                      data={shapChartData}
                      margin={{ top: 5, right: 60, left: 320, bottom: 5 }}
                    >
                      <XAxis type="number" tick={{ fontSize: 11 }} />
                      <YAxis
                        type="category"
                        dataKey="name"
                        tick={{ fontSize: 11, fill: 'var(--text-primary)', width: 310 }}
                      />
                      <Tooltip
                        formatter={(val, name, item) => [
                          `${val.toFixed(3)} (${item.payload.direction === 'increases_risk' ? 'Increases Risk' : 'Accelerates Progress'})${item.payload.formattedValue ? ` • Actual Value: ${item.payload.formattedValue}` : ''}`,
                          'Attribution Magnitude'
                        ]}
                        labelFormatter={(lbl) => `Driver: ${lbl}`}
                      />
                      <Bar dataKey="magnitude" radius={[0, 4, 4, 0]}>
                        <LabelList
                          dataKey="formattedValue"
                          position="right"
                          style={{ fontSize: '11px', fontWeight: 600, fill: 'var(--text-secondary)' }}
                        />
                        {shapChartData.map((entry, idx) => (
                          <Cell key={`cell-${idx}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* STAGE 4: Impact Map (Delay Propagation Timeline) */}
              <div className="story-section">
                <div className="story-section-title">
                  <span className="story-stage-num">Stage 4</span>
                  <GitMerge size={16} />
                  <span>Sequential Delay Propagation ("Impact Map")</span>
                </div>

                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                  Autoregressive cascading delay model across the 5 statutory milestones.
                  <span style={{ fontWeight: 700, marginLeft: '6px' }}>Solid borders</span> indicate actual observed delays;
                  <span style={{ fontWeight: 700, marginLeft: '6px', color: 'var(--gov-blue)' }}>dashed borders</span> indicate predicted downstream cascade.
                </p>

                <div className="timeline-container">
                  <div className="timeline-connector" />
                  {propagation.map((stage) => {
                    const isPred = stage.is_predicted;
                    const isCompleted = stage.status === 'completed';
                    const isDelayed = stage.status === 'delayed';

                    let circleClass = 'step-circle';
                    if (isPred) circleClass += ' predicted';
                    else if (isDelayed) circleClass += ' delayed';
                    else if (isCompleted) circleClass += ' completed';

                    return (
                      <div key={stage.stage_name} className="timeline-step">
                        <div className={circleClass}>
                          {stage.stage_order}
                        </div>
                        <div className="step-name">{stage.stage_name}</div>
                        <div
                          className="step-delay"
                          style={{
                            color: stage.delay_days > 30 ? 'var(--risk-critical)' : 'var(--text-secondary)',
                            fontWeight: 700
                          }}
                        >
                          {stage.delay_days} days
                        </div>
                        <span
                          style={{
                            fontSize: '0.65rem',
                            textTransform: 'uppercase',
                            padding: '1px 5px',
                            borderRadius: '3px',
                            marginTop: '3px',
                            background: isPred ? 'var(--gov-blue-subtle)' : '#f1f5f9',
                            color: isPred ? 'var(--gov-blue)' : 'var(--text-muted)',
                            fontWeight: 600,
                          }}
                        >
                          {isPred ? 'Predicted' : 'Actual'}
                        </span>
                      </div>
                    );
                  })}
                </div>

                <div style={{ marginTop: '12px', textAlign: 'right', fontSize: '0.85rem', fontWeight: 700, color: 'var(--gov-navy)' }}>
                  Total Cumulative Gated Delay across All 5 Milestones: <span style={{ color: 'var(--risk-critical)' }}>{totalCumulativeDelay} days</span>
                </div>
              </div>

              {/* STAGE 5: What-If Counterfactual Simulation */}
              <div className="story-section">
                <div className="story-section-title">
                  <span className="story-stage-num">Stage 5</span>
                  <Sliders size={16} />
                  <span>Interactive Intervention Simulator ("What-If")</span>
                </div>

                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                  Simulate policy interventions (accelerating compensation disbursement or resolving litigation injunctions) and measure quantitative reductions in acquisition delay days.
                </p>

                <div className="whatif-grid">
                  {/* Controls */}
                  <div className="whatif-controls">
                    <div className="slider-group">
                      <div className="slider-header">
                        <span>Compensation Disbursement Rate</span>
                        <strong style={{ color: 'var(--gov-blue)' }}>{compDisbursedPct}%</strong>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={compDisbursedPct}
                        onChange={(e) => handleCompChange(e.target.value)}
                        className="slider-control"
                      />
                    </div>

                    <div className="slider-group">
                      <div className="slider-header">
                        <span>Stakeholder Responsiveness Score</span>
                        <strong style={{ color: 'var(--gov-blue)' }}>{stakeholderResp} / 100</strong>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={stakeholderResp}
                        onChange={(e) => handleRespChange(e.target.value)}
                        className="slider-control"
                      />
                    </div>

                    <div className="toggle-group">
                      <div>
                        <div style={{ fontSize: '0.82rem', fontWeight: 700 }}>Active Court Injunction / Stay Order</div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                          {activeDispute ? 'Stay order currently halts land possession' : 'Litigation resolved / No active injunction'}
                        </div>
                      </div>
                      <label className="switch">
                        <input
                          type="checkbox"
                          checked={activeDispute === 1}
                          onChange={handleDisputeToggle}
                        />
                        <span className="slider-round" />
                      </label>
                    </div>

                    {whatIfLoading && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--gov-blue)', textAlign: 'right', fontStyle: 'italic' }}>
                        Simulating counterfactual outcomes...
                      </div>
                    )}
                  </div>

                  {/* Side-by-Side Comparison */}
                  <div className="whatif-comparison">
                    {/* Baseline Box */}
                    <div className="comparison-box">
                      <div style={{ fontSize: '0.74rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px' }}>
                        Baseline State
                      </div>
                      <div style={{ marginBottom: '8px' }}>
                        <span className={`risk-badge ${(whatIfData?.baseline?.risk_category || 'low').toLowerCase()}`}>
                          {whatIfData?.baseline?.risk_category || 'low'}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                        <div>Delay Prob: <strong>{((whatIfData?.baseline?.delay_probability || 0) * 100).toFixed(1)}%</strong></div>
                        <div>Actual Delay So Far: <strong>{whatIfData?.baseline?.actual_delay_so_far_days || 0} days</strong></div>
                        <div style={{ marginTop: '4px', borderTop: '1px dashed #cbd5e1', paddingTop: '4px' }}>
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Additional Delay Forecast:</span>
                          <div style={{ fontSize: '0.74rem' }}>
                            &bull; Comp: {whatIfData?.baseline?.stage_breakdown?.additional_expected_compensation_delay_days || 0}d
                          </div>
                          <div style={{ fontSize: '0.74rem' }}>
                            &bull; Poss: {whatIfData?.baseline?.stage_breakdown?.additional_expected_possession_delay_days || 0}d
                          </div>
                          <div style={{ fontWeight: 700 }}>
                            Total Addl: {whatIfData?.baseline?.expected_delay_days || 0}d
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Counterfactual Box */}
                    <div className="comparison-box counterfactual">
                      <div style={{ fontSize: '0.74rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--gov-blue)', marginBottom: '8px' }}>
                        Counterfactual State
                      </div>
                      <div style={{ marginBottom: '8px' }}>
                        <span className={`risk-badge ${(whatIfData?.counterfactual?.risk_category || 'low').toLowerCase()}`}>
                          {whatIfData?.counterfactual?.risk_category || 'low'}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                        <div>Delay Prob: <strong style={{ color: 'var(--gov-blue)' }}>{((whatIfData?.counterfactual?.delay_probability || 0) * 100).toFixed(1)}%</strong></div>
                        <div>Actual Delay So Far: <strong>{whatIfData?.baseline?.actual_delay_so_far_days || 0} days</strong></div>
                        <div style={{ marginTop: '4px', borderTop: '1px dashed #93c5fd', paddingTop: '4px' }}>
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Additional Delay Forecast:</span>
                          <div style={{ fontSize: '0.74rem' }}>
                            &bull; Comp: {whatIfData?.counterfactual?.stage_breakdown?.additional_expected_compensation_delay_days || 0}d
                          </div>
                          <div style={{ fontSize: '0.74rem' }}>
                            &bull; Poss: {whatIfData?.counterfactual?.stage_breakdown?.additional_expected_possession_delay_days || 0}d
                          </div>
                          <div style={{ fontWeight: 700, color: 'var(--gov-blue)' }}>
                            Total Addl: {whatIfData?.counterfactual?.expected_delay_days || 0}d
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Net Impact Banner */}
                {whatIfData?.impact && (
                  <div className="impact-banner">
                    <TrendingDown size={22} style={{ flexShrink: 0 }} />
                    <div>
                      <div style={{ fontWeight: 700 }}>
                        {whatIfData.impact.risk_tier_change} &bull; Save ~{whatIfData.impact.estimated_delay_days_saved} statutory delay days
                      </div>
                      <div style={{ fontSize: '0.78rem', opacity: 0.9, marginTop: '2px' }}>
                        {whatIfData.impact.summary}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* STAGE 6: Recommended Actions & AI Policy Memo */}
              <div className="story-section" style={{ borderLeftColor: 'var(--gov-blue)' }}>
                <div className="story-section-title" style={{ justifyContent: 'space-between', width: '100%', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="story-stage-num" style={{ background: 'var(--gov-navy)' }}>Action</span>
                    <Sparkles size={16} style={{ color: 'var(--gov-blue)' }} />
                    <span>Recommended Administrative Directives & AI Action Memo</span>
                  </div>
                  <button
                    onClick={() => handleGenerateRecommendation(false)}
                    disabled={generatingRec}
                    className="btn-primary"
                    style={{
                      fontSize: '0.75rem',
                      padding: '5px 12px',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      cursor: generatingRec ? 'not-allowed' : 'pointer',
                    }}
                  >
                    <RefreshCw size={13} className={generatingRec ? 'spin' : ''} />
                    {generatingRec ? 'Generating AI Directive...' : (aiMemo ? 'Regenerate Action Plan' : 'Generate Action Plan')}
                  </button>
                </div>

                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                  Prescriptive administrative guidance synthesized from SHAP explainability drivers and RFCTLARR 2013 statutory frameworks using Google Gemini 2.5 Flash.
                </p>

                {recError && (
                  <div className="error-banner" style={{ marginBottom: '14px', fontSize: '0.8rem' }}>
                    {recError}
                  </div>
                )}

                {/* AI Executive Action Memo */}
                {aiMemo && (
                  <div className="ai-memo-container">
                    <div className="ai-memo-header">
                      <div className="ai-memo-tag">
                        <Sparkles size={14} style={{ color: 'var(--gov-blue)' }} />
                        <span>Executive Administrative Directive (Gemini 2.5 Flash)</span>
                      </div>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        Authority: District Collector & SLAO
                      </span>
                    </div>
                    <p className="ai-memo-text">{aiMemo}</p>
                  </div>
                )}

                {/* Actionable Directives List */}
                {recommendations && recommendations.filter(r => r.category !== 'Executive Directive').length > 0 ? (
                  <div>
                    <div style={{ fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <FileText size={14} />
                      <span>Statutory Administrative Directives</span>
                    </div>
                    <div className="rec-actions-list">
                      {recommendations
                        .filter(r => r.category !== 'Executive Directive')
                        .map((rec) => {
                          const priorityClass = (rec.priority || 'medium').toLowerCase();
                          return (
                            <div key={rec.id || rec.action_text} className="rec-action-item">
                              <div className="rec-action-top">
                                <span className="rec-category-tag">{rec.category || 'General Administrative'}</span>
                                <span className={`priority-badge ${priorityClass}`}>
                                  {rec.priority}
                                </span>
                              </div>
                              <div className="rec-action-title">{rec.action_text}</div>
                              {rec.expected_impact && (
                                <div className="rec-action-impact">
                                  <strong style={{ color: 'var(--gov-navy)' }}>Expected Impact:</strong> {rec.expected_impact}
                                </div>
                              )}
                            </div>
                          );
                        })}
                    </div>
                  </div>
                ) : !aiMemo && (
                  <div style={{ textAlign: 'center', padding: '24px 16px', background: '#f8fafc', borderRadius: 'var(--radius-md)', border: '1px dashed #cbd5e1' }}>
                    <Sparkles size={24} style={{ color: 'var(--gov-blue)', margin: '0 auto 8px', display: 'block' }} />
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                      No Action Plan Generated Yet
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', maxWidth: '420px', margin: '0 auto 12px' }}>
                      Synthesize an actionable administrative memo and prioritized directives tailored to this project's SHAP risk drivers.
                    </div>
                    <button
                      onClick={() => handleGenerateRecommendation(false)}
                      disabled={generatingRec}
                      className="btn-primary"
                      style={{ fontSize: '0.8rem', padding: '6px 16px', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                    >
                      <Sparkles size={14} />
                      {generatingRec ? 'Synthesizing with Gemini 2.5 Flash...' : 'Generate Action Plan Now'}
                    </button>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
