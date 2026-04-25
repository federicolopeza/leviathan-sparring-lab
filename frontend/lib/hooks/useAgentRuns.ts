"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { authHeaders } from "@/lib/auth-client";
import { AgentRunSchema, type AgentRun } from "@/lib/schemas";

export type CreateAgentRunInput = {
  name: string;
  input_json: Record<string, unknown>;
};

type UseAgentRunsResult = {
  runs: AgentRun[];
  loading: boolean;
  error: string | null;
  createRun: (payload: CreateAgentRunInput) => Promise<AgentRun>;
  refresh: () => Promise<void>;
};

async function fetchRuns(): Promise<AgentRun[]> {
  return AgentRunSchema.array().parse(await apiFetch<unknown>("/agents/runs", { headers: authHeaders() }));
}

export function useAgentRuns(): UseAgentRunsResult {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      setRuns(await fetchRuns());
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudieron cargar las ejecuciones");
    } finally {
      setLoading(false);
    }
  }, []);

  const createRun = useCallback(async (payload: CreateAgentRunInput): Promise<AgentRun> => {
    const run = AgentRunSchema.parse(
      await apiFetch<unknown>("/agents/runs", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(payload)
      })
    );
    setRuns((current) => [run, ...current]);
    return run;
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { runs, loading, error, createRun, refresh };
}
