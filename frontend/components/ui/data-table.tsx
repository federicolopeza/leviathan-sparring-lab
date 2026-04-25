import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";

export type DataTableColumn<T> = {
  key: string;
  header: ReactNode;
  cell: (row: T) => ReactNode;
  className?: string;
};

type DataTableProps<T> = {
  rows: T[];
  columns: DataTableColumn<T>[];
  getRowId: (row: T) => string;
  emptyLabel: string;
  page: number;
  hasNextPage: boolean;
  onPageChange: (page: number) => void;
};

export function DataTable<T>({ rows, columns, getRowId, emptyLabel, page, hasNextPage, onPageChange }: DataTableProps<T>) {
  return (
    <div className="grid gap-4">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="text-muted-foreground">
            <tr>
              {columns.map((column) => (
                <th key={column.key} className={column.className ?? "pb-3 font-medium"}>
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={getRowId(row)} className="border-t border-border">
                {columns.map((column) => (
                  <td key={column.key} className="py-4 pr-4 align-top">
                    {column.cell(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length === 0 ? <p className="rounded-lg border border-border bg-muted p-4 text-sm text-muted-foreground">{emptyLabel}</p> : null}
      <div className="flex items-center justify-end gap-3">
        <Button type="button" variant="secondary" size="sm" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
          Anterior
        </Button>
        <span className="text-sm text-muted-foreground">Pagina {page}</span>
        <Button type="button" variant="secondary" size="sm" disabled={!hasNextPage} onClick={() => onPageChange(page + 1)}>
          Siguiente
        </Button>
      </div>
    </div>
  );
}
