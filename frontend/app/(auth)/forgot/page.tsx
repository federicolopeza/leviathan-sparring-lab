"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { forgotAction } from "@/lib/auth-client";

export default function ForgotPage() {
  const [message, setMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setMessage(null);
    setFormError(null);
    setPending(true);
    const formData = new FormData(event.currentTarget);
    try {
      await forgotAction(String(formData.get("email") ?? ""));
      setMessage("Si el email existe, enviaremos instrucciones de recuperacion.");
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "No se pudo procesar la solicitud");
    } finally {
      setPending(false);
    }
  }

  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Recuperar acceso</h1>
      <p className="mt-2 text-sm text-muted-foreground">Te enviaremos instrucciones si el email tiene una cuenta activa.</p>
      <form className="mt-8 grid gap-5" onSubmit={onSubmit}>
        <Input label="Email" name="email" type="email" autoComplete="email" required />
        {message ? <p className="rounded-lg bg-muted px-3 py-2 text-sm text-foreground">{message}</p> : null}
        {formError ? <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-destructive">{formError}</p> : null}
        <Button type="submit" disabled={pending}>
          {pending ? "Enviando..." : "Enviar instrucciones"}
        </Button>
      </form>
    </div>
  );
}
