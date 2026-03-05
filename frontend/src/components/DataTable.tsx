import { useMemo } from "react";
import { Table, ScrollArea } from "@mantine/core";

interface DataTableProps {
  rows: Record<string, unknown>[];
}

export function DataTable({ rows }: DataTableProps) {
  const columns = useMemo(() => (rows.length > 0 ? Object.keys(rows[0]) : []), [rows]);

  return (
    <ScrollArea h={420}>
      <Table striped withColumnBorders withTableBorder>
        <Table.Thead>
          <Table.Tr>
            {columns.map((col) => (
              <Table.Th key={col}>{col}</Table.Th>
            ))}
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {rows.map((row, idx) => (
            <Table.Tr key={idx}>
              {columns.map((col) => (
                <Table.Td key={col}>{String(row[col] ?? "")}</Table.Td>
              ))}
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </ScrollArea>
  );
}
