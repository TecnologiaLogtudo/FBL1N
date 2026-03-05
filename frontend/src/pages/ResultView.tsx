import { Button, Card, Group, Tabs, Text } from "@mantine/core";
import { DataTable } from "../components/DataTable";
import { useAppStore } from "../store/useAppStore";
import { getDownloadUrl } from "../api/client";

export function ResultView() {
  const results = useAppStore((s) => s.results);
  const jobId = useAppStore((s) => s.jobId);

  if (!results) {
    return null;
  }

  return (
    <Card withBorder mt="md" p="md">
      <Group justify="space-between" mb="md">
        <Text fw={600}>Resultados</Text>
        {jobId && (
          <Group>
            <Button component="a" href={getDownloadUrl(jobId, "xlsx")}>
              Baixar XLSX
            </Button>
            <Button component="a" href={getDownloadUrl(jobId, "pdf")} variant="light">
              Baixar PDF
            </Button>
          </Group>
        )}
      </Group>
      <Tabs defaultValue="summary">
        <Tabs.List>
          <Tabs.Tab value="summary">Resumo Consolidado</Tabs.Tab>
          <Tabs.Tab value="details">Detalhes de Pendências</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="summary" pt="sm">
          <DataTable rows={results.summary} />
        </Tabs.Panel>
        <Tabs.Panel value="details" pt="sm">
          <DataTable rows={results.details} />
        </Tabs.Panel>
      </Tabs>
    </Card>
  );
}
