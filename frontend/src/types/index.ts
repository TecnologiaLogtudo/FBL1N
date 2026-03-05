export type JobStatus = "queued" | "running" | "completed" | "failed" | "expired";

export interface StatusResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  error?: string | null;
}

export interface ResultsResponse {
  summary: Record<string, unknown>[];
  details: Record<string, unknown>[];
  meta: Record<string, unknown>;
}

export interface LogEntry {
  level: string;
  message: string;
  timestamp: string;
}
