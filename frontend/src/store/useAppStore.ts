import { create } from "zustand";
import { LogEntry, ResultsResponse, JobStatus } from "../types";

interface AppState {
  jobId: string | null;
  status: JobStatus | null;
  progress: number;
  logs: LogEntry[];
  results: ResultsResponse | null;
  error: string | null;
  setJob: (jobId: string) => void;
  setStatus: (status: JobStatus) => void;
  setProgress: (progress: number) => void;
  addLog: (log: LogEntry) => void;
  setResults: (results: ResultsResponse) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  jobId: null,
  status: null,
  progress: 0,
  logs: [],
  results: null,
  error: null,
  setJob: (jobId) => set({ jobId, status: "queued", progress: 0, logs: [], results: null, error: null }),
  setStatus: (status) => set({ status }),
  setProgress: (progress) => set({ progress }),
  addLog: (log) => set((state) => ({ logs: [...state.logs, log] })),
  setResults: (results) => set({ results }),
  setError: (error) => set({ error }),
  reset: () => set({ jobId: null, status: null, progress: 0, logs: [], results: null, error: null }),
}));
