"use client";

import Link from "next/link";
import { Plus } from "lucide-react";
import { useState } from "react";
import { RunForm } from "@/components/features/agents/run-form";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { DataTable } from "@/components/ui/data-table";
import { Skeleton } from "@/components/ui/skeleton";
import { useAgentRuns } from "@/lib/hooks/useAgentRuns";
import type { AgentRun } from "@/lib/schemas";

const statusVariants: Record<AgentRun["status"], "default" | "success" | "warning" | "destructive" | "muted"> = {
  queued: "muted",
  running: "default",
  completed: "success",
  failed: "destructive",
  cancelled: "warning"
};

export default function AgentsPage() {
  const [formOpen, setFormOpen] = useState(false);
  const { runs, loading, error, refresh } = useAgentRuns();

  return (
    <section className="mx-auto grid max-w-6xl gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Agents</p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight">Agent runs</h1>
        </div>
        <Button type="button" onClick={() => setFormOpen((current) => !current)}>
          <Plus className="h-4 w-4" />
          New run
        </Button>
      </div>

      {formOpen ? (
        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Create run</h2>
            <p className="text-sm text-muted-foreground">Launch a deterministic agent fixture with raw JSON input.</p>
          </CardHeader>
          <CardContent>
            <RunForm
              onSuccess={() => {
                setFormOpen(false);
                void refresh();
              }}
            />
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold">Runs</h2>
          <p className="text-sm text-muted-foreground">Queued, running, and completed agent executions.</p>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <DataTable
              rows={runs}
              getRowId={(run) => run.id}
              emptyLabel="No agent runs yet."
              page={1}
              hasNextPage={false}
              onPageChange={() => undefined}
              columns={[
                {
                  key: "name",
                  header: "Name",
                  cell: (run) => (
                    <Link href={`/agents/${run.id}`} className="font-medium text-primary hover:underline">
                      {run.name}
                    </Link>
                  )
                },
                { key: "status", header: "Status", cell: (run) => <Badge variant={statusVariants[run.status]}>{run.status}</Badge> },
                { key: "created_at", header: "Created", cell: (run) => new Date(run.created_at).toLocaleString("es-UY") }
              ]}
            />
          )}
          {error ? <p className="mt-4 text-sm text-destructive">{error}</p> : null}
        </CardContent>
      </Card>
    </section>
  );
}
