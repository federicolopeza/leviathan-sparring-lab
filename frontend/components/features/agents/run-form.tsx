"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAgentRuns } from "@/lib/hooks/useAgentRuns";

type RunFormProps = {
  onSuccess: () => void;
};

export function RunForm({ onSuccess }: RunFormProps) {
  const [name, setName] = useState("");
  const [inputJson, setInputJson] = useState("{\n  \"target\": \"fixture\"\n}");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const { createRun } = useAgentRuns();

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);

    let parsedInput: Record<string, unknown>;
    try {
      const parsed = JSON.parse(inputJson) as unknown;
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        setError("input_json debe ser un objeto JSON.");
        return;
      }
      parsedInput = parsed as Record<string, unknown>;
    } catch {
      setError("input_json no es JSON valido.");
      return;
    }

    setPending(true);
    try {
      await createRun({ name, input_json: parsedInput });
      setName("");
      setInputJson("{\n  \"target\": \"fixture\"\n}");
      onSuccess();
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudo crear la ejecucion");
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="grid gap-5" onSubmit={submit}>
      <Input label="Nombre" value={name} onChange={(event) => setName(event.target.value)} placeholder="Recon baseline" required />
      <div className="grid gap-2">
        <label htmlFor="input_json" className="text-sm font-medium">
          input_json
        </label>
        <textarea
          id="input_json"
          className="min-h-40 w-full rounded-lg border border-border bg-card px-3 py-2 font-mono text-sm text-card-foreground shadow-sm transition placeholder:text-muted-foreground focus:border-primary"
          value={inputJson}
          onChange={(event) => setInputJson(event.target.value)}
          spellCheck={false}
          required
        />
      </div>
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      <Button type="submit" disabled={pending || !name.trim()}>
        {pending ? "Creando..." : "Crear ejecucion"}
      </Button>
    </form>
  );
}
