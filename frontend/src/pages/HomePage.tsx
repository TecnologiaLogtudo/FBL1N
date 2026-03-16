import { useEffect, useState } from "react";
import {
  Alert,
  Badge,
  Button,
  Card,
  FileInput,
  Group,
  NumberInput,
  Progress,
  SegmentedControl,
  Table,
  Text,
} from "@mantine/core";
import { fetchHistory, fetchMetrics, getApiErrorMessage, startProcess } from "../api/client";
import { useAppStore } from "../store/useAppStore";
import { JobHistoryItem, MetricsResponse, ProcessMode } from "../types";

const MAX_BYTES = 25 * 1024 * 1024;

function validateFile(file: File | null, allowedExtensions: string[]): string | null {
  if (!file) return "Arquivo obrigatório";
  if (file.size > MAX_BYTES) return "Arquivo excede 25MB";
  const lower = file.name.toLowerCase();
  if (!allowedExtensions.some((ext) => lower.endsWith(ext))) {
    return `Formato inválido (${allowedExtensions.join(", ")})`;
  }
  return null;
}

export function HomePage() {
  const [baseFile, setBaseFile] = useState<File | null>(null);
  const [reportFile, setReportFile] = useState<File | null>(null);
  const [openTitlesFile, setOpenTitlesFile] = useState<File | null>(null);
  const [analysisYear, setAnalysisYear] = useState<number>(new Date().getFullYear());
  const [localError, setLocalError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [history, setHistory] = useState<JobHistoryItem[]>([]);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [isLoadingOps, setIsLoadingOps] = useState(false);
  const [processMode, setProcessMode] = useState<ProcessMode>("standard");

  const setJob = useAppStore((s) => s.setJob);
  const setError = useAppStore((s) => s.setError);
  const currentJobId = useAppStore((s) => s.jobId);

  const loadOperationalData = async () => {
    try {
      setIsLoadingOps(true);
      const [historyData, metricsData] = await Promise.all([fetchHistory(10), fetchMetrics()]);
      setHistory(historyData);
      setMetrics(metricsData);
    } catch {
      // Silencioso para não poluir UX principal.
    } finally {
      setIsLoadingOps(false);
    }
  };

  useEffect(() => {
    loadOperationalData();
  }, []);

  useEffect(() => {
    if (!currentJobId) return;
    const timer = window.setTimeout(() => {
      loadOperationalData();
    }, 1500);
    return () => window.clearTimeout(timer);
  }, [currentJobId]);

  const statusColor = (status: string): string => {
    if (status === "completed") return "green";
    if (status === "failed") return "red";
    if (status === "running") return "blue";
    if (status === "queued") return "yellow";
    return "gray";
  };

  useEffect(() => {
    setLocalError(null);
    setReportFile(null);
    setOpenTitlesFile(null);
  }, [processMode]);

  const modeLabel = (mode?: ProcessMode) =>
    mode === "open_titles" ? "Títulos em aberto" : "Conciliação";

  const handleStart = async () => {
    if (isSubmitting) return;
    setLocalError(null);
    setError(null);
    setUploadProgress(0);

    const baseErr = validateFile(baseFile, [".xlsx"]);
    if (baseErr) {
      setLocalError(`Base: ${baseErr}`);
      return;
    }

    if (processMode === "standard") {
      const reportErr = validateFile(reportFile, [".xls", ".xlsx"]);
      if (reportErr) {
        setLocalError(`Relatório: ${reportErr}`);
        return;
      }
    } else {
      const openErr = validateFile(openTitlesFile, [".xls", ".xlsx"]);
      if (openErr) {
        setLocalError(`Títulos em aberto: ${openErr}`);
        return;
      }
    }

    try {
      setIsSubmitting(true);
      const { job_id } = await startProcess(
        baseFile!,
        processMode === "standard" ? reportFile : null,
        analysisYear,
        processMode,
        processMode === "open_titles" ? openTitlesFile : null,
        setUploadProgress
      );
      setJob(job_id);
    } catch (error) {
      setLocalError(getApiErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card withBorder p="md">
      <Text fw={700} mb="md">Conciliação de Pagamentos de Frete</Text>
      <SegmentedControl
        value={processMode}
        onChange={(value) => setProcessMode(value as ProcessMode)}
        data={[
          { label: "Conciliação", value: "standard" },
          { label: "Títulos em aberto", value: "open_titles" },
        ]}
        fullWidth
        mb="sm"
      />
      <Text size="sm" color="dimmed" mb="md">
        {processMode === "standard"
          ? "Envie a base FBL1 e o relatório BSoft para conciliar valores."
          : "Envie a base FBL1 e a planilha filtrada com os títulos em aberto para verificar quais já foram pagos."}
      </Text>
      {localError && <Alert color="red" mb="md">{localError}</Alert>}
      <FileInput label="Base de Dados FBL1N(.xlsx)" value={baseFile} onChange={setBaseFile} clearable mb="sm" />
      {processMode === "standard" && (
        <FileInput
          label="Relatório Externo BSOFT(.xls/.xlsx)"
          value={reportFile}
          onChange={setReportFile}
          clearable
          mb="sm"
        />
      )}
      {processMode === "open_titles" && (
        <FileInput
          label="Planilha BSOFT - títulos em aberto (.xls/.xlsx)"
          value={openTitlesFile}
          onChange={setOpenTitlesFile}
          clearable
          mb="sm"
        />
      )}
      <NumberInput
        label="Ano de Análise"
        value={analysisYear}
        onChange={(value) => setAnalysisYear(Number(value))}
        min={2020}
        max={2100}
        mb="md"
      />
      {isSubmitting && (
        <>
          <Text size="sm" mb="xs">Enviando arquivos...</Text>
          <Progress value={uploadProgress * 100} mb="md" />
        </>
      )}
      <Group justify="flex-end">
        <Button onClick={handleStart} loading={isSubmitting} disabled={isSubmitting}>
          Executar Processamento
        </Button>
      </Group>

      <Group justify="space-between" mt="lg" mb="xs">
        <Text fw={600}>Operação</Text>
        <Button variant="light" size="xs" onClick={loadOperationalData} loading={isLoadingOps}>
          Atualizar
        </Button>
      </Group>

      {metrics && (
        <Group mb="md" gap="xs">
          <Badge variant="light">Total: {metrics.total_jobs}</Badge>
          <Badge variant="light" color="blue">Ativos: {metrics.active_jobs}</Badge>
          <Badge variant="light" color="green">Concluídos: {metrics.completed_jobs}</Badge>
          <Badge variant="light" color="red">Falhos: {metrics.failed_jobs}</Badge>
          <Badge variant="light" color="grape">Sucesso: {(metrics.success_rate * 100).toFixed(1)}%</Badge>
        </Group>
      )}

      <Table striped withColumnBorders withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Job</Table.Th>
        <Table.Th>Processo</Table.Th>
        <Table.Th>Status</Table.Th>
            <Table.Th>Ano</Table.Th>
            <Table.Th>Criado em</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {history.length === 0 ? (
            <Table.Tr>
              <Table.Td colSpan={5}>Sem histórico recente</Table.Td>
            </Table.Tr>
          ) : (
            history.map((item) => (
              <Table.Tr key={item.job_id}>
                <Table.Td>{item.job_id.slice(0, 8)}</Table.Td>
                <Table.Td>{modeLabel(item.process_mode)}</Table.Td>
                <Table.Td>
                  <Badge color={statusColor(item.status)} variant="light">
                    {item.status}
                  </Badge>
                </Table.Td>
                <Table.Td>{item.analysis_year}</Table.Td>
                <Table.Td>{new Date(item.created_at).toLocaleString()}</Table.Td>
              </Table.Tr>
            ))
          )}
        </Table.Tbody>
      </Table>
    </Card>
  );
}
