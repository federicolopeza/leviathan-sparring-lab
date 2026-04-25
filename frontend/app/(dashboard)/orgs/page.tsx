"use client";

import Link from "next/link";
import { Building2, Plus } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useCreateOrg } from "@/lib/hooks/mutations";
import { useMembers } from "@/lib/hooks/useMembers";
import { useOrgs } from "@/lib/hooks/useOrgs";
import { useUser } from "@/lib/hooks/useUser";
import type { Org } from "@/lib/schemas";

function OrgRow({ org, userId }: { org: Org; userId?: string }) {
  const { data: members = [], isLoading } = useMembers(org.id);
  const membership = members.find((member) => member.user_id === userId);
  const role = membership?.role ?? (org.owner_user_id === userId ? "owner" : "member");

  return (
    <tr className="border-t border-border">
      <td className="py-4">
        <Link href={`/dashboard/orgs/${org.id}`} className="font-medium hover:text-primary">
          {org.name}
        </Link>
        <p className="text-xs text-muted-foreground">{org.region}</p>
      </td>
      <td className="py-4 capitalize text-muted-foreground">{org.plan}</td>
      <td className="py-4 capitalize text-muted-foreground">{role}</td>
      <td className="py-4 text-muted-foreground">{isLoading ? "Cargando..." : members.length}</td>
    </tr>
  );
}

export default function OrgsPage() {
  const { data: user } = useUser();
  const { data: orgs = [], isLoading } = useOrgs();
  const createOrg = useCreateOrg();
  const [open, setOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setFormError(null);
    const formData = new FormData(event.currentTarget);
    try {
      await createOrg.mutateAsync({
        name: String(formData.get("name") ?? ""),
        plan: String(formData.get("plan") ?? "free") as Org["plan"],
        region: String(formData.get("region") ?? "")
      });
      setOpen(false);
      event.currentTarget.reset();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "No se pudo crear la organizacion");
    }
  }

  return (
    <section className="mx-auto grid max-w-6xl gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Organizaciones</p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight">Tus organizaciones</h1>
        </div>
        <Button type="button" onClick={() => setOpen(true)}>
          <Plus className="h-4 w-4" /> Nueva organizacion
        </Button>
      </div>

      <Card>
        <CardHeader className="flex-row items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-lg bg-muted text-primary">
            <Building2 className="h-5 w-5" />
          </span>
          <div>
            <h2 className="font-semibold">Listado</h2>
            <p className="text-sm text-muted-foreground">Datos cargados desde Phase 1 backend.</p>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[680px] text-left text-sm">
                <thead className="text-muted-foreground">
                  <tr>
                    <th className="pb-3 font-medium">Nombre</th>
                    <th className="pb-3 font-medium">Plan</th>
                    <th className="pb-3 font-medium">Rol</th>
                    <th className="pb-3 font-medium">Miembros</th>
                  </tr>
                </thead>
                <tbody>
                  {orgs.map((org) => (
                    <OrgRow key={org.id} org={org} userId={user?.id} />
                  ))}
                </tbody>
              </table>
              {orgs.length === 0 ? <p className="py-8 text-sm text-muted-foreground">Todavia no hay organizaciones.</p> : null}
            </div>
          )}
        </CardContent>
      </Card>

      {open ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true">
          <form className="grid w-full max-w-md gap-4 rounded-lg border border-border bg-card p-6 shadow-[var(--shadow-soft)]" onSubmit={onSubmit}>
            <div>
              <h2 className="text-xl font-semibold">Nueva organizacion</h2>
              <p className="text-sm text-muted-foreground">Crea un tenant inicial para trabajar con el backend Phase 1.</p>
            </div>
            <Input label="Nombre" name="name" required />
            <label className="grid gap-2 text-sm font-medium">
              Plan
              <select name="plan" className="h-11 rounded-lg border border-border bg-card px-3 text-sm" defaultValue="free">
                <option value="free">Free</option>
                <option value="pro">Pro</option>
                <option value="enterprise">Enterprise</option>
              </select>
            </label>
            <Input label="Region" name="region" placeholder="latam-south" required />
            {formError ? <p className="text-sm text-destructive">{formError}</p> : null}
            <div className="flex justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createOrg.isPending}>
                {createOrg.isPending ? "Creando..." : "Crear"}
              </Button>
            </div>
          </form>
        </div>
      ) : null}
    </section>
  );
}
