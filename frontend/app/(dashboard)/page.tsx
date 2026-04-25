import { ArrowUpRight, Bot, CreditCard, Gauge, Plus, UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

const stats = [
  { label: "Uso del mes", value: "78%", trend: "+12%", icon: Gauge },
  { label: "Agentes activos", value: "14", trend: "+3", icon: Bot },
  { label: "Llamadas API", value: "1.82M", trend: "+18%", icon: CreditCard }
];

const activity = [
  { event: "Invoice reconciliada", org: "AndesPay", status: "Completado", time: "Hace 4 min" },
  { event: "Agente de riesgo ejecuto analisis", org: "RioBank", status: "Revision", time: "Hace 18 min" },
  { event: "Webhook billing.entitlement.updated", org: "CobreHub", status: "Entregado", time: "Hace 31 min" },
  { event: "API key rotada", org: "PagoSur", status: "Seguro", time: "Hace 1 h" }
];

export default function DashboardPage() {
  return (
    <div className="mx-auto grid max-w-7xl gap-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Operations</p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight">Dashboard</h1>
          <p className="mt-2 text-muted-foreground">Estado financiero, agentes y eventos criticos de la plataforma.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary">
            <UploadCloud className="h-4 w-4" /> Subir archivo
          </Button>
          <Button>
            <Plus className="h-4 w-4" /> Nuevo agente
          </Button>
        </div>
      </div>

      <div className="grid gap-5 md:grid-cols-3">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label}>
              <CardHeader className="flex-row items-start justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                  <p className="mt-2 text-4xl font-semibold">{stat.value}</p>
                </div>
                <span className="grid h-10 w-10 place-items-center rounded-lg bg-muted text-primary">
                  <Icon className="h-5 w-5" />
                </span>
              </CardHeader>
              <CardContent>
                <p className="flex items-center gap-1 text-sm font-medium text-accent">
                  <ArrowUpRight className="h-4 w-4" /> {stat.trend} vs mes anterior
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Actividad reciente</h2>
            <p className="text-sm text-muted-foreground">Eventos operativos con trazabilidad cross-tenant.</p>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-sm">
                <thead className="text-muted-foreground">
                  <tr>
                    <th className="pb-3 font-medium">Evento</th>
                    <th className="pb-3 font-medium">Org</th>
                    <th className="pb-3 font-medium">Estado</th>
                    <th className="pb-3 font-medium">Tiempo</th>
                  </tr>
                </thead>
                <tbody>
                  {activity.map((row) => (
                    <tr key={`${row.event}-${row.time}`} className="border-t border-border">
                      <td className="py-4 font-medium">{row.event}</td>
                      <td className="py-4 text-muted-foreground">{row.org}</td>
                      <td className="py-4">
                        <span className="rounded-full bg-muted px-2 py-1 text-xs font-semibold">{row.status}</span>
                      </td>
                      <td className="py-4 text-muted-foreground">{row.time}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Quick actions</h2>
          </CardHeader>
          <CardContent className="grid gap-3">
            {["Crear agente de riesgo", "Emitir invoice demo", "Configurar webhook", "Invitar auditor"].map((action) => (
              <button key={action} type="button" className="rounded-lg border border-border px-4 py-3 text-left text-sm font-medium transition hover:bg-muted">
                {action}
              </button>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
