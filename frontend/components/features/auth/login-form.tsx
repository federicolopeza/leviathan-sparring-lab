"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { LoginSchema, type LoginInput } from "@/lib/schemas";

export function LoginForm() {
  const router = useRouter();
  const [formError, setFormError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<LoginInput>({
    resolver: zodResolver(LoginSchema),
    defaultValues: {
      email: "",
      password: ""
    }
  });

  async function onSubmit(values: LoginInput): Promise<void> {
    setFormError(null);
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(values)
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({ message: "No se pudo iniciar sesion" }));
      setFormError(typeof payload.message === "string" ? payload.message : "No se pudo iniciar sesion");
      return;
    }

    router.push("/dashboard");
  }

  return (
    <form className="grid gap-5" onSubmit={handleSubmit(onSubmit)}>
      <Input label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} />
      <Input
        label="Contrasena"
        type="password"
        autoComplete="current-password"
        error={errors.password?.message}
        {...register("password")}
      />
      {formError ? <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-destructive">{formError}</p> : null}
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Ingresando..." : "Ingresar"}
      </Button>
    </form>
  );
}
