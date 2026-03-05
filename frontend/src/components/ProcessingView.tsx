import { Alert, Card, Group, Progress, ScrollArea, Text } from "@mantine/core";
import { useAppStore } from "../store/useAppStore";

export function ProcessingView() {
  const progress = useAppStore((s) => s.progress);
  const logs = useAppStore((s) => s.logs);
  const status = useAppStore((s) => s.status);
  const error = useAppStore((s) => s.error);

  return (
    <Card withBorder mt="md" p="md">
      <Text fw={600} mb="sm">Processamento</Text>
      <Group justify="space-between" mb="xs">
        <Text size="sm">Status: {status}</Text>
        <Text size="sm">{Math.round(progress * 100)}%</Text>
      </Group>
      <Progress value={progress * 100} mb="md" />
      {error && <Alert color="red" mb="md">{error}</Alert>}
      <ScrollArea h={280}>
        {logs.map((log, idx) => (
          <Text key={idx} size="sm" c={log.level === "error" ? "red" : "gray"}>
            [{new Date(log.timestamp).toLocaleTimeString()}] {log.message}
          </Text>
        ))}
      </ScrollArea>
    </Card>
  );
}
