"use client";

import Link from "next/link";
import { MailPlus, Settings } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { useInvite } from "@/lib/hooks/mutations";
import { useMembers } from "@/lib/hooks/useMembers";
import { useOrg } from "@/lib/hooks/useOrg";
import { InvitationSchema, type Invitation } from "@/lib/schemas";

function initials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("es", { dateStyle: "medium" }).format(new Date(value));
}

export function OrgDetailClient({ orgId }: { orgId: string }) {
  const { data: org, isLoading: orgLoading } = useOrg(orgId);
  const { data: members = [], isLoading: membersLoading } = useMembers(orgId);
  const invitations = useQuery({
    queryKey: ["orgs", orgId, "invitations"],
    queryFn: async () => InvitationSchema.array().parse(await apiFetch<unknown>(`/orgs/${orgId}/invitations`)),
    enabled: Boolean(orgId)
  });
  const invite = useInvite(orgId);
  const [open, setOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setFormError(null);
    const formData = new FormData(event.currentTarget);
    try {
      await invite.mutateAsync({
        email: String(formData.get("email") ?? ""),
        role: String(formData.get("role") ?? "member") as "admin" | "member"
      });
      setOpen(false);
      event.currentTarget.reset();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "No se pudo enviar la invitacion");
    }
  }

  if (orgLoading) {
    return <Skeleton className="h-80 w-full" />;
  }

  if (!org) {
    return <p className="text-sm text-muted-foreground">No se pudo cargar la organizacion.</p>;
  }

  const pendingInvitations: Invitation[] = (invitations.data ?? []).filter((invitation) => invitation.used_at === null);

  return (
    <section className="mx-auto grid max-w-6xl gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Organizacion</p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight">{org.name}</h1>
          <p className="mt-2 text-muted-foreground">
            Plan {org.plan} · {org.region}
          </p>
        </div>
        <div className="flex gap-3">
          <Link href={`/dashboard/orgs/${org.id}/settings`} className="inline-flex h-11 items-center gap-2 rounded-lg border border-border bg-card px-4 text-sm font-semibold">
            <Settings className="h-4 w-4" /> Ajustes
          </Link>
          <Button type="button" onClick={() => setOpen(true)}>
            <MailPlus className="h-4 w-4" /> Invitar miembro
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold">Miembros</h2>
          <p className="text-sm text-muted-foreground">Usuarios con acceso a esta organizacion.</p>
        </CardHeader>
        <CardContent>
          {membersLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[620px] text-left text-sm">
                <thead className="text-muted-foreground">
                  <tr>
                    <th className="pb-3 font-medium">Usuario</th>
                    <th className="pb-3 font-medium">Rol</th>
                    <th className="pb-3 font-medium">Ingreso</th>
                  </tr>
                </thead>
                <tbody>
                  {members.map((member) => {
                    const label = member.user_id.slice(0, 8);
                    return (
                      <tr key={member.user_id} className="border-t border-border">
                        <td className="py-4">
                          <div className="flex items-center gap-3">
                            <span className="grid h-9 w-9 place-items-center rounded-full bg-muted text-xs font-semibold">{initials(label)}</span>
                            <span className="font-medium">{label}</span>
                          </div>
                        </td>
                        <td className="py-4 capitalize text-muted-foreground">{member.role}</td>
                        <td className="py-4 text-muted-foreground">{formatDate(member.created_at)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {members.length === 0 ? <p className="py-8 text-sm text-muted-foreground">Todavia no hay miembros cargados.</p> : null}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold">Invitaciones pendientes</h2>
        </CardHeader>
        <CardContent className="grid gap-3">
          {pendingInvitations.length > 0 ? (
            pendingInvitations.map((invitation) => (
              <div key={invitation.id} className="flex items-center justify-between rounded-lg border border-border px-4 py-3 text-sm">
                <span>{invitation.email}</span>
                <span className="text-muted-foreground">
                  {invitation.role} · expira {formatDate(invitation.expires_at)}
                </span>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">No hay invitaciones pendientes.</p>
          )}
        </CardContent>
      </Card>

      {open ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true">
          <form className="grid w-full max-w-md gap-4 rounded-lg border border-border bg-card p-6 shadow-[var(--shadow-soft)]" onSubmit={onSubmit}>
            <div>
              <h2 className="text-xl font-semibold">Invitar miembro</h2>
              <p className="text-sm text-muted-foreground">La invitacion quedara pendiente hasta que el usuario la acepte.</p>
            </div>
            <Input label="Email" name="email" type="email" required />
            <label className="grid gap-2 text-sm font-medium">
              Rol
              <select name="role" className="h-11 rounded-lg border border-border bg-card px-3 text-sm" defaultValue="member">
                <option value="member">Member</option>
                <option value="admin">Admin</option>
              </select>
            </label>
            {formError ? <p className="text-sm text-destructive">{formError}</p> : null}
            <div className="flex justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={invite.isPending}>
                {invite.isPending ? "Enviando..." : "Enviar invitacion"}
              </Button>
            </div>
          </form>
        </div>
      ) : null}
    </section>
  );
}
