export type JobStatus = "queued" | "running" | "completed" | "failed" | "expired";
export type ProcessMode = "standard" | "open_titles";

export interface StatusResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  error?: string | null;
  process_mode: ProcessMode;
}

export interface ResultsResponse {
  summary: Record<string, unknown>[];
  details: Record<string, unknown>[];
  meta: Record<string, unknown>;
}

export interface JobHistoryItem {
  job_id: string;
  status: JobStatus;
  analysis_year: number;
  base_filename: string;
  report_filename: string;
  process_mode: ProcessMode;
  progress: number;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  error?: string | null;
}

export interface MetricsResponse {
  total_jobs: number;
  active_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  expired_jobs: number;
  avg_duration_seconds: number;
  success_rate: number;
}

export interface LogEntry {
  level: string;
  message: string;
  timestamp: string;
}
