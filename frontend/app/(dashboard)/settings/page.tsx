"use client";

import { Bell, KeyRound, Shield, User } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { usePatchProfile } from "@/lib/hooks/mutations";
import { useUser } from "@/lib/hooks/useUser";

const tabs = [
  { id: "perfil", label: "Perfil", icon: User },
  { id: "seguridad", label: "Seguridad", icon: Shield },
  { id: "api", label: "API Keys", icon: KeyRound },
  { id: "notificaciones", label: "Notificaciones", icon: Bell }
] as const;

type TabId = (typeof tabs)[number]["id"];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabId>("perfil");
  const [formError, setFormError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const { data: user, isLoading } = useUser();
  const patchProfile = usePatchProfile();

  async function onProfileSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setFormError(null);
    setSaved(false);
    const formData = new FormData(event.currentTarget);
    try {
      await patchProfile.mutateAsync({
        name: String(formData.get("name") ?? ""),
        bio: String(formData.get("bio") ?? "") || null,
        avatar_url: String(formData.get("avatar_url") ?? "") || null
      });
      setSaved(true);
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "No se pudo guardar el perfil");
    }
  }

  return (
    <div className="mx-auto grid max-w-6xl gap-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Configuracion</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">Ajustes</h1>
      </div>

      <div className="flex flex-wrap gap-2" role="tablist" aria-label="Secciones de ajustes">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const selected = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={selected}
              className={`inline-flex h-10 items-center gap-2 rounded-lg px-4 text-sm font-semibold ${
                selected ? "bg-primary text-white" : "border border-border bg-card text-muted-foreground"
              }`}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon className="h-4 w-4" /> {tab.label}
            </button>
          );
        })}
      </div>

      {activeTab === "perfil" ? (
        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Perfil</h2>
            <p className="text-sm text-muted-foreground">Datos visibles para auditoria y soporte.</p>
          </CardHeader>
          <CardContent>
            {isLoading || !user ? (
              <Skeleton className="h-56 w-full" />
            ) : (
              <form className="grid max-w-xl gap-4" onSubmit={onProfileSubmit}>
                <Input label="Nombre" name="name" defaultValue={user.name} required />
                <Input label="Bio" name="bio" defaultValue={user.bio ?? ""} />
                <Input label="Avatar URL" name="avatar_url" type="url" defaultValue={user.avatar_url ?? ""} />
                {formError ? <p className="text-sm text-destructive">{formError}</p> : null}
                {saved ? <p className="text-sm text-accent">Perfil actualizado.</p> : null}
                <Button className="w-fit" type="submit" disabled={patchProfile.isPending}>
                  {patchProfile.isPending ? "Guardando..." : "Guardar perfil"}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      ) : null}

      {activeTab === "seguridad" ? (
        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Seguridad</h2>
            <p className="text-sm text-muted-foreground">Controles de cuenta diferidos para Phase 2.</p>
          </CardHeader>
          <CardContent>
            <p className="rounded-lg border border-border bg-muted p-4 text-sm text-muted-foreground">Cambio de contrasena, MFA y sesiones activas quedan pendientes para Phase 2.</p>
          </CardContent>
        </Card>
      ) : null}

      {activeTab === "api" ? (
        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">API Keys</h2>
            <p className="text-sm text-muted-foreground">No hay claves creadas.</p>
          </CardHeader>
          <CardContent>
            <p className="rounded-lg border border-border bg-muted p-4 text-sm text-muted-foreground">La gestion de API keys queda pendiente para Phase 2.</p>
          </CardContent>
        </Card>
      ) : null}

      {activeTab === "notificaciones" ? (
        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Notificaciones</h2>
            <p className="text-sm text-muted-foreground">Preferencias locales de interfaz, sin persistencia backend.</p>
          </CardHeader>
          <CardContent className="grid gap-4">
            {["Alertas de billing", "Eventos de riesgo alto", "Invitaciones de organizacion"].map((label) => (
              <label key={label} className="flex items-center justify-between rounded-lg border border-border px-4 py-3 text-sm">
                <span>{label}</span>
                <input type="checkbox" className="h-4 w-4 accent-primary" defaultChecked />
              </label>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
