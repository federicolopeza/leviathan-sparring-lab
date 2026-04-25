"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { authHeaders } from "@/lib/auth-client";
import { AgentRunSchema, type AgentRun } from "@/lib/schemas";

const statusVariants: Record<AgentRun["status"], "default" | "success" | "warning" | "destructive" | "muted"> = {
  queued: "muted",
  running: "default",
  completed: "success",
  failed: "destructive",
  cancelled: "warning"
};

type RenderResponse = {
  rendered_output: string;
};

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="overflow-x-auto rounded-lg border border-border bg-muted p-4 text-xs leading-5">{JSON.stringify(value, null, 2)}</pre>;
}

export default function AgentRunDetailPage() {
  const params = useParams<{ runId: string }>();
  const runId = params.runId;
  const [run, setRun] = useState<AgentRun | null>(null);
  const [renderedOutput, setRenderedOutput] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [rendering, setRendering] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRun = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      setRun(AgentRunSchema.parse(await apiFetch<unknown>(`/agents/runs/${runId}`, { headers: authHeaders() })));
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudo cargar la ejecucion");
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    void fetchRun();
  }, [fetchRun]);

  async function renderPreview(): Promise<void> {
    setRendering(true);
    setError(null);
    try {
      const response = await apiFetch<RenderResponse>(`/agents/runs/${runId}/render`, {
        method: "POST",
        headers: authHeaders()
      });
      setRenderedOutput(response.rendered_output);
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudo renderizar la salida");
    } finally {
      setRendering(false);
    }
  }

  if (loading) {
    return <Skeleton className="h-96 w-full" />;
  }

  return (
    <section className="mx-auto grid max-w-5xl gap-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Agent run</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">{run?.name ?? "Run detail"}</h1>
      </div>

      {error ? <p className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">{error}</p> : null}

      {run ? (
        <>
          <Card>
            <CardHeader>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="text-xl font-semibold">{run.name}</h2>
                  <p className="text-sm text-muted-foreground">{new Date(run.created_at).toLocaleString("es-UY")}</p>
                </div>
                <Badge variant={statusVariants[run.status]}>{run.status}</Badge>
              </div>
            </CardHeader>
            <CardContent className="grid gap-5">
              <div>
                <h3 className="mb-2 text-sm font-semibold">input_json</h3>
                <JsonBlock value={run.input_json} />
              </div>
              <div>
                <h3 className="mb-2 text-sm font-semibold">output_json</h3>
                <JsonBlock value={run.output_json} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold">Render Preview</h2>
              <p className="text-sm text-muted-foreground">Render the server-side template output for this run.</p>
            </CardHeader>
            <CardContent className="grid gap-4">
              <Button type="button" className="w-fit" disabled={rendering} onClick={() => void renderPreview()}>
                {rendering ? "Rendering..." : "Render Preview"}
              </Button>
              {renderedOutput ? (
                <div className="rounded-lg border border-border bg-muted p-4 text-sm leading-6">
                  {/* V-T6-001: rendered output is unsanitized — SSTI result displayed to user */}
                  <div dangerouslySetInnerHTML={{ __html: renderedOutput }} />
                </div>
              ) : null}
            </CardContent>
          </Card>
        </>
      ) : null}
    </section>
  );
}
