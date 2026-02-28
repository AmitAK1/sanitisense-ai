/**
 * SanitiSense AI — API Client
 * Connects to the deployed API Gateway backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://rh74yspy85.execute-api.us-east-1.amazonaws.com/prod';
const S3_BUCKET = 'sanitisense-media-982253889131';
const S3_REGION = 'us-east-1';

// ==================== TYPES ====================

export interface DashboardStats {
  total_reports: number;
  reports_today: number;
  pending_tasks: number;
  in_progress_tasks: number;
  completed_today: number;
  avg_resolution_hours: number;
  citizen_satisfaction: number;
  ai_accuracy: number;
  active_workers: number;
  wards_covered: number;
}

export interface CategoryBreakdown {
  category: string;
  count: number;
  percentage: number;
}

export interface WardHeatmap {
  ward_number: number;
  name: string;
  center_lat: number;
  center_lng: number;
  open_reports: number;
  severity_avg: number;
  risk_level: 'high' | 'medium' | 'low';
}

export interface TrendData {
  date: string;
  reports_filed: number;
  tasks_completed: number;
  avg_severity: number;
}

export interface WorkerLeaderboard {
  worker_id: string;
  name: string;
  completed_this_week: number;
  avg_rating: number;
  avg_resolution_hours: number;
}

export interface RecentReport {
  report_id: string;
  category: string;
  severity_score: number;
  ward_number: number;
  status: string;
  created_at: string;
  description: string;
}

export interface FullDashboard {
  stats: DashboardStats;
  categories: CategoryBreakdown[];
  heatmap: WardHeatmap[];
  trends: TrendData[];
  leaderboard: WorkerLeaderboard[];
  recent_reports: RecentReport[];
  generated_at: string;
}

export interface ReportSubmission {
  image_key: string;
  latitude: number;
  longitude: number;
  voice_key?: string;
}

export interface ReportResponse {
  ticket_id: string;
  status: string;
  ai_analysis: {
    is_spam: boolean;
    category: string;
    severity_score: number;
    description: string;
    health_risk: string;
    confidence: number;
  };
  message: string;
}

export interface Task {
  task_id: string;
  report_id: string;
  status: string;
  priority: string;
  sla_hours: number;
  category: string;
  severity_score: number;
  description: string;
  ward_number: number;
  assigned_worker_id: string | null;
  created_at: string;
  updated_at: string;
  // Extra fields from backend (may or may not be present)
  image_key?: string;
  health_risk?: string;
  location?: { lat: string; lng: string };
  ward_name?: string;
}

export interface UploadUrlResponse {
  upload_url: string;
  image_key: string;
  expires_in_seconds: number;
  bucket: string;
}

// ==================== API FUNCTIONS ====================

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(error.error || `API error: ${res.status}`);
  }
  return res.json();
}

// Dashboard
export const fetchDashboard = () => apiFetch<FullDashboard>('/dashboard');
export const fetchDashboardStats = () => apiFetch<DashboardStats>('/dashboard/stats');
export const fetchHeatmap = () => apiFetch<WardHeatmap[]>('/dashboard/heatmap');
export const fetchTrends = (days = 7) => apiFetch<TrendData[]>(`/dashboard/trends?days=${days}`);
export const fetchLeaderboard = () => apiFetch<WorkerLeaderboard[]>('/dashboard/leaderboard');
export const fetchRecentReports = () => apiFetch<RecentReport[]>('/dashboard/recent');

// Reports
export const submitReport = (data: ReportSubmission) =>
  apiFetch<ReportResponse>('/reports', {
    method: 'POST',
    body: JSON.stringify(data),
  });

// Tasks — backend wraps response in {tasks: [...], count: N}
export const fetchTasks = async (status = 'pending'): Promise<Task[]> => {
  const res = await apiFetch<{ tasks: Record<string, unknown>[]; count: number }>(`/tasks?status=${status}`);
  return (res.tasks || []).map(normalizeTask);
};
export const updateTask = (taskId: string, data: { status: string; notes?: string }) =>
  apiFetch<{ task_id: string; status: string }>(`/tasks/${taskId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
export const fetchWorkerTasks = async (workerId: string): Promise<Task[]> => {
  const res = await apiFetch<{ tasks: Record<string, unknown>[]; count: number }>(`/worker/${workerId}/tasks`);
  return (res.tasks || []).map(normalizeTask);
};

// S3 Upload — get presigned URL then PUT file directly
export const fetchUploadUrl = (filename: string, contentType = 'image/jpeg', type = 'citizen') =>
  apiFetch<UploadUrlResponse>(
    `/upload-url?filename=${encodeURIComponent(filename)}&content_type=${encodeURIComponent(contentType)}&type=${type}`
  );

export async function uploadImageToS3(file: File, type = 'citizen'): Promise<string> {
  // Step 1: Get presigned URL from backend
  const contentType = file.type || 'image/jpeg';
  const { upload_url, image_key } = await fetchUploadUrl(file.name, contentType, type);

  // Step 2: PUT file directly to S3 using presigned URL
  const uploadRes = await fetch(upload_url, {
    method: 'PUT',
    body: file,
    headers: { 'Content-Type': contentType },
  });
  if (!uploadRes.ok) {
    throw new Error(`S3 upload failed: ${uploadRes.status}`);
  }

  // Step 3: Return the S3 key for POST /reports
  return image_key;
}

/** Normalize a task from DynamoDB (seeded data may lack some fields) */
function normalizeTask(raw: Record<string, unknown>): Task {
  const severity = Number(raw.severity_score) || 0;
  // Derive priority from severity if missing
  let priority = raw.priority as string;
  let sla_hours = Number(raw.sla_hours) || 0;
  if (!priority) {
    if (severity >= 8) { priority = 'critical'; sla_hours = 4; }
    else if (severity >= 6) { priority = 'high'; sla_hours = 12; }
    else if (severity >= 4) { priority = 'medium'; sla_hours = 24; }
    else { priority = 'low'; sla_hours = 48; }
  }
  return {
    task_id: (raw.task_id || '') as string,
    report_id: (raw.report_id || raw.report_ticket || '') as string,
    status: (raw.status || 'pending') as string,
    priority,
    sla_hours,
    category: (raw.category || 'other') as string,
    severity_score: severity,
    description: (raw.description || '') as string,
    ward_number: Number(raw.ward_number) || 0,
    assigned_worker_id: (raw.assigned_worker_id as string) || null,
    created_at: (raw.created_at || '') as string,
    updated_at: (raw.updated_at || '') as string,
    image_key: (raw.image_key || '') as string,
    health_risk: (raw.health_risk || '') as string,
    ward_name: (raw.ward_name || '') as string,
  };
}

// Validation
export const validateCompletion = (data: {
  task_id: string;
  before_image_key: string;
  after_image_key: string;
}) =>
  apiFetch<{ task_id: string; validation_result: string }>('/validate', {
    method: 'POST',
    body: JSON.stringify(data),
  });

// Epidemic Advisory
export interface EpidemicAdvisory {
  ward_number: number;
  risk_level: string;
  advisory: string;
  diseases_at_risk: string[];
  recommended_actions: string[];
  stats: Record<string, unknown>;
  data_source: string;
  generated_at: string;
}

export interface CityOverview {
  city: string;
  overall_risk: string;
  high_risk_wards: { ward_number: number; name: string; risk_level: string; open_reports: number }[];
  total_open_reports: number;
  advisory_summary: string;
  generated_at: string;
}

export const fetchEpidemicAdvisory = (ward: number) =>
  apiFetch<EpidemicAdvisory>(`/epidemic?ward=${ward}`);

export const fetchCityOverview = () =>
  apiFetch<CityOverview>('/epidemic/city-overview');

// S3 Upload helper — generates a presigned-style path
export function getS3UploadKey(filename: string): string {
  const now = new Date();
  const datePath = `${now.getFullYear()}/${String(now.getMonth() + 1).padStart(2, '0')}/${String(now.getDate()).padStart(2, '0')}`;
  const uniqueId = Math.random().toString(36).substring(2, 10);
  const ext = filename.split('.').pop() || 'jpg';
  return `citizen-reports/${datePath}/${uniqueId}.${ext}`;
}

// Category display helpers
export const CATEGORY_LABELS: Record<string, string> = {
  garbage_pile: 'Garbage Pile',
  overflowing_drain: 'Overflowing Drain',
  blocked_sewer: 'Blocked Sewer',
  stagnant_water: 'Stagnant Water',
  medical_waste: 'Medical Waste',
  animal_carcass: 'Animal Carcass',
  other: 'Other',
};

export const CATEGORY_COLORS: Record<string, string> = {
  garbage_pile: '#ef4444',
  overflowing_drain: '#f97316',
  blocked_sewer: '#eab308',
  stagnant_water: '#3b82f6',
  medical_waste: '#a855f7',
  animal_carcass: '#6b7280',
  other: '#94a3b8',
};

export const STATUS_COLORS: Record<string, string> = {
  pending: '#f59e0b',
  assigned: '#3b82f6',
  in_progress: '#8b5cf6',
  completed: '#22c55e',
  verified: '#10b981',
  rejected: '#ef4444',
};

export const PRIORITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
};
