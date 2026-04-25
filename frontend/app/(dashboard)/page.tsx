"use client";

import { BarChart3, Building2, Gauge, Users } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useOrgs } from "@/lib/hooks/useOrgs";
import { useUser } from "@/lib/hooks/useUser";

export default function DashboardPage() {
  const { data: user, isLoading: userLoading } = useUser();
  const { data: orgs = [], isLoading: orgsLoading } = useOrgs();
  const loading = userLoading || orgsLoading;

  const stats = [
    { label: "Organizaciones", value: String(orgs.length), helper: "Tenants asociados a tu cuenta", icon: Building2 },
    { label: "Miembros", value: String(orgs.length), helper: "Conteo base hasta cargar membresias por org", icon: Users },
    { label: "Uso del mes", value: "0%", helper: "Metrica diferida para Phase 2", icon: Gauge }
  ];

  return (
    <div className="mx-auto grid max-w-7xl gap-8">
      <div className="flex flex-col gap-3">
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Panel operativo</p>
        <h1 className="text-4xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          {user ? `Resumen de ${user.name} y sus organizaciones.` : "Resumen de organizaciones, miembros y uso."}
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-3">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label}>
              <CardHeader className="flex-row items-start justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                  {loading ? <Skeleton className="mt-3 h-10 w-20" /> : <p className="mt-2 text-4xl font-semibold">{stat.value}</p>}
                </div>
                <span className="grid h-10 w-10 place-items-center rounded-lg bg-muted text-primary">
                  <Icon className="h-5 w-5" />
                </span>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{stat.helper}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
        <Card>
          <CardHeader>
            <h2 className="flex items-center gap-2 text-xl font-semibold">
              <BarChart3 className="h-5 w-5 text-primary" /> Uso de plataforma
            </h2>
            <p className="text-sm text-muted-foreground">Grafico reservado para metricas reales de Phase 2.</p>
          </CardHeader>
          <CardContent>
            <div className="grid h-72 content-end gap-3 rounded-lg border border-border bg-muted/40 p-5">
              {[36, 58, 42, 71, 64, 82, 55].map((height, index) => (
                <div key={index} className="flex items-end gap-3">
                  <span className="w-8 text-xs text-muted-foreground">D{index + 1}</span>
                  <div className="h-5 flex-1 rounded bg-card">
                    <div className="h-5 rounded bg-primary" style={{ width: `${height}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Organizaciones recientes</h2>
          </CardHeader>
          <CardContent className="grid gap-3">
            {orgs.length > 0 ? (
              orgs.slice(0, 4).map((org) => (
                <div key={org.id} className="rounded-lg border border-border px-4 py-3">
                  <p className="font-medium">{org.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {org.plan} · {org.region}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No hay organizaciones asociadas todavia.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
