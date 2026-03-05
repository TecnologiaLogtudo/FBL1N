import { useEffect } from "react";
import { AppShell, Container } from "@mantine/core";
import { HomePage } from "./pages/HomePage";
import { ProcessingView } from "./components/ProcessingView";
import { ResultView } from "./pages/ResultView";
import { fetchResults, fetchStatus } from "./api/client";
import { useAppStore } from "./store/useAppStore";
import { JobStatus } from "./types";

function connectWebSocket(jobId: string, onMessage: (event: MessageEvent) => void): WebSocket {
  const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL;
  if (wsBaseUrl) {
    const base = wsBaseUrl.endsWith("/") ? wsBaseUrl.slice(0, -1) : wsBaseUrl;
    const ws = new WebSocket(`${base}/ws/jobs/${jobId}`);
    ws.onmessage = onMessage;
    return ws;
  }

  const appBasePath = import.meta.env.VITE_APP_BASE_PATH ?? "";
  const normalizedBasePath = appBasePath === "/" ? "" : appBasePath.replace(/\/$/, "");
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${protocol}://${window.location.host}${normalizedBasePath}/ws/jobs/${jobId}`);
  ws.onmessage = onMessage;
  return ws;
}

export default function App() {
  const jobId = useAppStore((s) => s.jobId);
  const status = useAppStore((s) => s.status);
  const setStatus = useAppStore((s) => s.setStatus);
  const setProgress = useAppStore((s) => s.setProgress);
  const addLog = useAppStore((s) => s.addLog);
  const setResults = useAppStore((s) => s.setResults);
  const setError = useAppStore((s) => s.setError);

  useEffect(() => {
    if (!jobId) return;

    const ws = connectWebSocket(jobId, async (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "progress") {
          setProgress(Number(payload.value ?? 0));
        }
        if (payload.type === "status") {
          setStatus(payload.status as JobStatus);
        }
        if (payload.type === "log") {
          addLog({
            level: payload.level ?? "info",
            message: payload.message ?? "",
            timestamp: payload.timestamp ?? new Date().toISOString(),
          });
        }
        if (payload.type === "error") {
          setError(payload.error ?? "Erro no processamento");
        }
      } catch {
        setError("Falha ao interpretar mensagens do WebSocket");
      }
    });

    const poll = window.setInterval(async () => {
      try {
        const current = await fetchStatus(jobId);
        setStatus(current.status);
        setProgress(current.progress);

        if (current.status === "completed") {
          const result = await fetchResults(jobId);
          setResults(result);
          window.clearInterval(poll);
        }
        if (current.status === "failed" || current.status === "expired") {
          setError(current.error ?? `Job em status ${current.status}`);
          window.clearInterval(poll);
        }
      } catch {
        setError("Falha ao obter status do job");
      }
    }, 2500);

    return () => {
      ws.close();
      window.clearInterval(poll);
    };
  }, [jobId, setStatus, setProgress, addLog, setResults, setError]);

  return (
    <AppShell padding="md">
      <AppShell.Main>
        <Container size="lg">
          <HomePage />
          {jobId && <ProcessingView />}
          {status === "completed" && <ResultView />}
        </Container>
      </AppShell.Main>
    </AppShell>
  );
}
