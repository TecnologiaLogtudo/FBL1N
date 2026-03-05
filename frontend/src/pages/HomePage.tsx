import { useState } from "react";
import { Alert, Button, Card, FileInput, Group, NumberInput, Progress, Text } from "@mantine/core";
import { getApiErrorMessage, startProcess } from "../api/client";
import { useAppStore } from "../store/useAppStore";

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
  const [analysisYear, setAnalysisYear] = useState<number>(new Date().getFullYear());
  const [localError, setLocalError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const setJob = useAppStore((s) => s.setJob);
  const setError = useAppStore((s) => s.setError);

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

    const reportErr = validateFile(reportFile, [".xls", ".xlsx"]);
    if (reportErr) {
      setLocalError(`Relatório: ${reportErr}`);
      return;
    }

    try {
      setIsSubmitting(true);
      const { job_id } = await startProcess(baseFile!, reportFile!, analysisYear, setUploadProgress);
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
      {localError && <Alert color="red" mb="md">{localError}</Alert>}
      <FileInput label="Base de Dados (.xlsx)" value={baseFile} onChange={setBaseFile} clearable mb="sm" />
      <FileInput label="Relatório Externo (.xls/.xlsx)" value={reportFile} onChange={setReportFile} clearable mb="sm" />
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
    </Card>
  );
}
