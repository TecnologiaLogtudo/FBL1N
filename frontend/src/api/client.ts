import axios from "axios";
import { ResultsResponse, StatusResponse } from "../types";

const APP_BASE_PATH = import.meta.env.VITE_APP_BASE_PATH ?? "/";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? APP_BASE_PATH;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "X-User-Id": "internal-web-user",
  },
});

export async function startProcess(baseFile: File, reportFile: File, analysisYear: number): Promise<{ job_id: string }> {
  const formData = new FormData();
  formData.append("base_file", baseFile);
  formData.append("report_file", reportFile);
  formData.append("analysis_year", String(analysisYear));

  const { data } = await api.post("/api/process", formData);
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

export function getDownloadUrl(jobId: string, fileType: "xlsx" | "pdf"): string {
  const prefix = API_BASE_URL.endsWith("/") ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
  return `${prefix}/api/process/${jobId}/download/${fileType}`;
}
