import { Button, Card, Group, Tabs, Text } from "@mantine/core";
import { DataTable } from "../components/DataTable";
import { useAppStore } from "../store/useAppStore";
import { getDownloadUrl } from "../api/client";
import { ProcessMode, modeLabel } from "../types";

export function ResultView() {
  const results = useAppStore((s) => s.results);
  const jobId = useAppStore((s) => s.jobId);
  const processMode = results?.meta?.process_mode as ProcessMode | undefined;
  const isMidas = processMode === "midas_correlation";

  if (!results) {
    return null;
  }

  return (
    <Card withBorder mt="md" p="md">
      <Group justify="space-between" mb="md">
        <Text fw={600}>Resultados</Text>
        {processMode && (
          <Text size="sm" color="dimmed">
            Processo: {modeLabel(processMode)}
          </Text>
        )}
        {jobId && (
          <Group>
            <Button component="a" href={getDownloadUrl(jobId, "xlsx")}>
              Baixar XLSX
            </Button>
            {!isMidas && (
              <Button component="a" href={getDownloadUrl(jobId, "pdf")} variant="light">
                Baixar PDF
              </Button>
            )}
          </Group>
        )}
      </Group>
      <Tabs defaultValue="summary">
        <Tabs.List>
          <Tabs.Tab value="summary">{isMidas ? "Resultado Midas" : "Resumo Consolidado"}</Tabs.Tab>
          {!isMidas && <Tabs.Tab value="details">Detalhes de Pendências</Tabs.Tab>}
        </Tabs.List>
        <Tabs.Panel value="summary" pt="sm">
          <DataTable rows={results.summary} />
        </Tabs.Panel>
        {!isMidas && (
          <Tabs.Panel value="details" pt="sm">
            <DataTable rows={results.details} />
          </Tabs.Panel>
        )}
      </Tabs>
    </Card>
  );
}
