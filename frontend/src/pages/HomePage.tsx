import { useState } from "react";
import { Alert, Button, Card, FileInput, Group, NumberInput, Text } from "@mantine/core";
import { startProcess } from "../api/client";
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

  const setJob = useAppStore((s) => s.setJob);
  const setError = useAppStore((s) => s.setError);

  const handleStart = async () => {
    setLocalError(null);
    setError(null);

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
      const { job_id } = await startProcess(baseFile!, reportFile!, analysisYear);
      setJob(job_id);
    } catch (err) {
      setLocalError("Falha ao iniciar processamento");
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
      <Group justify="flex-end">
        <Button onClick={handleStart}>Executar Processamento</Button>
      </Group>
    </Card>
  );
}
