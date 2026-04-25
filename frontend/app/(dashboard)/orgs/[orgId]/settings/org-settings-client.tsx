"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { usePatchOrg } from "@/lib/hooks/mutations";
import { useMembers } from "@/lib/hooks/useMembers";
import { useOrg } from "@/lib/hooks/useOrg";
import { useUser } from "@/lib/hooks/useUser";
import type { Org } from "@/lib/schemas";

export function OrgSettingsClient({ orgId }: { orgId: string }) {
  const { data: user } = useUser();
  const { data: org, isLoading } = useOrg(orgId);
  const { data: members = [] } = useMembers(orgId);
  const patchOrg = usePatchOrg(orgId);
  const [formError, setFormError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const membership = members.find((member) => member.user_id === user?.id);
  const isOwner = membership?.role === "owner" || org?.owner_user_id === user?.id;

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setFormError(null);
    setSaved(false);
    const formData = new FormData(event.currentTarget);
    try {
      await patchOrg.mutateAsync({
        name: String(formData.get("name") ?? ""),
        plan: String(formData.get("plan") ?? "free") as Org["plan"],
        region: String(formData.get("region") ?? "")
      });
      setSaved(true);
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "No se pudo actualizar la organizacion");
    }
  }

  if (isLoading) {
    return <Skeleton className="h-80 w-full" />;
  }

  if (!org) {
    return <p className="text-sm text-muted-foreground">No se pudo cargar la organizacion.</p>;
  }

  if (!isOwner) {
    return (
      <Card className="mx-auto max-w-3xl">
        <CardHeader>
          <h1 className="text-2xl font-semibold">Ajustes restringidos</h1>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Solo el owner puede modificar nombre, plan y region de la organizacion.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <section className="mx-auto grid max-w-4xl gap-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Ajustes de organizacion</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">{org.name}</h1>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold">Configuracion general</h2>
          <p className="text-sm text-muted-foreground">Cambios visibles para todos los miembros del tenant.</p>
        </CardHeader>
        <CardContent>
          <form className="grid max-w-xl gap-4" onSubmit={onSubmit}>
            <Input label="Nombre" name="name" defaultValue={org.name} required />
            <label className="grid gap-2 text-sm font-medium">
              Plan
              <select name="plan" className="h-11 rounded-lg border border-border bg-card px-3 text-sm" defaultValue={org.plan}>
                <option value="free">Free</option>
                <option value="pro">Pro</option>
                <option value="enterprise">Enterprise</option>
              </select>
            </label>
            <Input label="Region" name="region" defaultValue={org.region} required />
            {formError ? <p className="text-sm text-destructive">{formError}</p> : null}
            {saved ? <p className="text-sm text-accent">Organizacion actualizada.</p> : null}
            <Button className="w-fit" type="submit" disabled={patchOrg.isPending}>
              {patchOrg.isPending ? "Guardando..." : "Guardar cambios"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </section>
  );
}
