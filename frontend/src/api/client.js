/**
 * LandSight AI - Frontend API Client Layer
 * 
 * Interfacing with FastAPI backend at http://localhost:8000/api
 * Handles network operations and user-visible error formatting for 404, 422, and 500 statuses.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Custom error class wrapping API failures with structured details.
 */
export class ApiError extends Error {
  constructor(message, status, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Generic request helper with robust error parsing.
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultHeaders = {
    'Accept': 'application/json',
  };

  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json';
    options.body = JSON.stringify(options.body);
  }

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...(options.headers || {}),
    },
  };

  try {
    const response = await fetch(url, config);

    // Parse JSON or fallback to text
    let data = null;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      let errorMessage = `Request failed with status ${response.status}`;

      if (data && typeof data === 'object') {
        if (typeof data.detail === 'string') {
          // Explicit FastAPI HTTPException message (e.g. 404 Project not found)
          errorMessage = data.detail;
        } else if (Array.isArray(data.detail)) {
          // Pydantic 422 validation errors array
          errorMessage = data.detail
            .map((err) => {
              const field = err.loc ? err.loc[err.loc.length - 1] : 'field';
              return `${field}: ${err.msg}`;
            })
            .join('; ');
        }
      }

      throw new ApiError(errorMessage, response.status, data);
    }

    return data;
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    // Network connectivity or unexpected parse error
    throw new ApiError(
      `Unable to connect to LandSight AI Backend at ${API_BASE_URL}. Please ensure the service is running.`,
      0,
      err
    );
  }
}

// ---------------------------------------------------------------------------
// API Endpoint Methods
// ---------------------------------------------------------------------------

/**
 * Performs real-time risk classification for a project.
 */
export async function predictProject(projectId) {
  return request(`/predict/${encodeURIComponent(projectId)}`, {
    method: 'POST',
  });
}

/**
 * Computes top SHAP feature attribution factors for a project.
 */
export async function getProjectExplanation(projectId) {
  return request(`/projects/${encodeURIComponent(projectId)}/explain`);
}

/**
 * Computes sequential milestone delay propagation cascade ("Impact Map").
 */
export async function getProjectPropagation(projectId) {
  return request(`/projects/${encodeURIComponent(projectId)}/propagation`);
}

/**
 * Runs interactive counterfactual what-if simulation.
 */
export async function simulateWhatIf(projectId, hypotheticalChanges) {
  return request(`/projects/${encodeURIComponent(projectId)}/what-if`, {
    method: 'POST',
    body: hypotheticalChanges,
  });
}

/**
 * Retrieves paginated project listings with optional filters.
 */
export async function listProjects({ page = 1, pageSize = 20, state = '', riskCategory = '' } = {}) {
  const params = new URLSearchParams();
  if (page) params.append('page', page);
  if (pageSize) params.append('page_size', pageSize);
  if (state) params.append('state', state);
  if (riskCategory) params.append('risk_category', riskCategory);

  const query = params.toString() ? `?${params.toString()}` : '';
  return request(`/projects${query}`);
}

/**
 * Retrieves detailed single project record.
 */
export async function getProjectDetails(projectId) {
  return request(`/projects/${encodeURIComponent(projectId)}`);
}

/**
 * Aggregates project count and delay risk per district for heatmap.
 */
export async function getDistrictsSummary(state = '') {
  const query = state ? `?state=${encodeURIComponent(state)}` : '';
  return request(`/districts/summary${query}`);
}

/**
 * Retrieves high/critical risk early warning alerts.
 */
export async function getAlerts(limit = 50) {
  return request(`/alerts?limit=${encodeURIComponent(limit)}`);
}

/**
 * Retrieves high-level executive KPI overview and risk breakdown for dashboard.
 */
export async function getExecutiveSummary() {
  return request('/summary');
}

/**
 * Queries system health and eager model loading status.
 */
export async function getHealthCheck() {
  return request('/health');
}

/**
 * Triggers AI recommendation and executive action memo generation (Gemini 2.5 Flash).
 */
export async function generateProjectRecommendation(projectId, simulateFailure = false) {
  const query = simulateFailure ? '?simulate_failure=true' : '';
  return request(`/projects/${encodeURIComponent(projectId)}/generate-recommendation${query}`, {
    method: 'POST',
  });
}

/**
 * Retrieves all stored administrative recommendations and action directives for a project.
 */
export async function getProjectRecommendations(projectId) {
  return request(`/projects/${encodeURIComponent(projectId)}/recommendations`);
}

/**
 * Retrieves simulated notification dispatch logs for an alert.
 */
export async function getAlertNotifications(alertId) {
  return request(`/alerts/${encodeURIComponent(alertId)}/notifications`);
}

/**
 * Triggers retraining of the XGBoost risk classifier against current database state.
 * Guarded by confirm query parameter.
 */
export async function retrainModel(confirm = true) {
  const query = confirm ? '?confirm=true' : '';
  return request(`/retrain${query}`, {
    method: 'POST',
  });
}

