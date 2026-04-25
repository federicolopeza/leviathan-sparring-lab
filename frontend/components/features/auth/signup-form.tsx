"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SignupSchema, type SignupInput } from "@/lib/schemas";

export function SignupForm() {
  const router = useRouter();
  const [formError, setFormError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<SignupInput>({
    resolver: zodResolver(SignupSchema),
    defaultValues: {
      name: "",
      email: "",
      password: "",
      org_name: ""
    }
  });

  async function onSubmit(values: SignupInput): Promise<void> {
    setFormError(null);
    const response = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(values)
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({ message: "No se pudo crear la cuenta" }));
      setFormError(typeof payload.message === "string" ? payload.message : "No se pudo crear la cuenta");
      return;
    }

    router.push(`/verify?email=${encodeURIComponent(values.email)}`);
  }

  return (
    <form className="grid gap-5" onSubmit={handleSubmit(onSubmit)}>
      <Input label="Nombre" autoComplete="name" error={errors.name?.message} {...register("name")} />
      <Input label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} />
      <Input label="Organizacion" autoComplete="organization" error={errors.org_name?.message} {...register("org_name")} />
      <Input
        label="Contrasena"
        type="password"
        autoComplete="new-password"
        error={errors.password?.message}
        {...register("password")}
      />
      {formError ? <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-destructive">{formError}</p> : null}
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Creando cuenta..." : "Crear cuenta"}
      </Button>
    </form>
  );
}
