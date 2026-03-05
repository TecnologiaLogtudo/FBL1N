import axios from "axios";
import { JobHistoryItem, MetricsResponse, ResultsResponse, StatusResponse } from "../types";

const APP_BASE_PATH = import.meta.env.VITE_APP_BASE_PATH ?? "/";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? APP_BASE_PATH;

function getOrCreateUserId(): string {
  const key = "notas_compensadas_user_id";
  const existing = window.localStorage.getItem(key);
  if (existing) {
    return existing;
  }
  const generated = `web-${crypto.randomUUID()}`;
  window.localStorage.setItem(key, generated);
  return generated;
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "X-User-Id": getOrCreateUserId(),
  },
});

export async function startProcess(
  baseFile: File,
  reportFile: File,
  analysisYear: number,
  onUploadProgress?: (progress: number) => void
): Promise<{ job_id: string }> {
  const formData = new FormData();
  formData.append("base_file", baseFile);
  formData.append("report_file", reportFile);
  formData.append("analysis_year", String(analysisYear));

  const { data } = await api.post("/api/process", formData, {
    onUploadProgress: (event) => {
      if (!onUploadProgress || !event.total) return;
      onUploadProgress(Math.max(0, Math.min(1, event.loaded / event.total)));
    },
  });
  return data;
}

export async function fetchStatus(jobId: string): Promise<StatusResponse> {
  const { data } = await api.get(`/api/process/${jobId}/status`);
  return data;
}

export async function fetchResults(jobId: string): Promise<ResultsResponse> {
  const { data } = await api.get(`/api/process/${jobId}/results`);
  return data;
}

export async function fetchHistory(limit = 20): Promise<JobHistoryItem[]> {
  const { data } = await api.get(`/api/process/history?limit=${limit}`);
  return data;
}

export async function fetchMetrics(): Promise<MetricsResponse> {
  const { data } = await api.get("/api/metrics");
  return data;
}

export function getDownloadUrl(jobId: string, fileType: "xlsx" | "pdf"): string {
  const prefix = API_BASE_URL.endsWith("/") ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
  return `${prefix}/api/process/${jobId}/download/${fileType}`;
}

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
    if (typeof error.message === "string" && error.message.trim()) {
      return error.message;
    }
  }
  return "Falha ao iniciar processamento";
}
