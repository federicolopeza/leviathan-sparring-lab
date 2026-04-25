"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { verifyAction } from "@/lib/auth-client";

function VerifyContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const email = searchParams.get("email");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">(token ? "loading" : "idle");
  const [message, setMessage] = useState(token ? "Verificando cuenta..." : "Revisa tu email para completar la verificacion.");

  useEffect(() => {
    if (!token) {
      return;
    }

    let active = true;

    async function verify(): Promise<void> {
      try {
        await verifyAction(token);
        if (!active) {
          return;
        }
        setStatus("success");
        setMessage("Cuenta verificada. Ya puedes ingresar.");
      } catch (error) {
        if (!active) {
          return;
        }
        setStatus("error");
        setMessage(error instanceof Error ? error.message : "No se pudo verificar el token");
      }
    }

    void verify();

    return () => {
      active = false;
    };
  }, [token]);

  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Verificar cuenta</h1>
      <p className="mt-2 text-sm text-muted-foreground">{email ? `Enviamos el enlace a ${email}. Revisa tu bandeja de entrada.` : message}</p>
      <div className="mt-8 rounded-xl border border-border bg-muted p-4 text-sm">
        <p className={status === "error" ? "text-destructive" : "text-foreground"}>{message}</p>
      </div>
      {status === "success" ? (
        <Link
          href="/login"
          className="mt-6 inline-flex h-11 w-full items-center justify-center rounded-lg bg-primary px-4 text-sm font-semibold text-white"
        >
          Iniciar sesion
        </Link>
      ) : null}
    </div>
  );
}

export default function VerifyPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted-foreground">Cargando verificacion...</p>}>
      <VerifyContent />
    </Suspense>
  );
}
