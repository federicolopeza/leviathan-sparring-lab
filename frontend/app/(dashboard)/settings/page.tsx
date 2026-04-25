import { Bell, KeyRound, Shield, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const tabs = [
  { label: "Perfil", icon: User },
  { label: "Seguridad", icon: Shield },
  { label: "API Keys", icon: KeyRound },
  { label: "Notificaciones", icon: Bell }
];

export default function SettingsPage() {
  return (
    <div className="mx-auto grid max-w-6xl gap-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Configuracion</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">Settings</h1>
      </div>

      <div className="flex flex-wrap gap-2">
        {tabs.map((tab, index) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.label}
              type="button"
              className={`inline-flex h-10 items-center gap-2 rounded-lg px-4 text-sm font-semibold ${
                index === 0 ? "bg-primary text-white" : "border border-border bg-card text-muted-foreground"
              }`}
            >
              <Icon className="h-4 w-4" /> {tab.label}
            </button>
          );
        })}
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Perfil</h2>
            <p className="text-sm text-muted-foreground">Datos visibles para auditoria y soporte.</p>
          </CardHeader>
          <CardContent className="grid gap-4">
            <Input label="Nombre" defaultValue="Federico Lopez" />
            <Input label="Email" type="email" defaultValue="operator@melispy.com" />
            <Button className="w-fit">Guardar perfil</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Seguridad</h2>
            <p className="text-sm text-muted-foreground">Controles de acceso de cuenta.</p>
          </CardHeader>
          <CardContent className="grid gap-4">
            <Input label="Contrasena actual" type="password" />
            <Input label="Nueva contrasena" type="password" />
            <label className="flex items-center gap-3 text-sm">
              <input type="checkbox" className="h-4 w-4 accent-primary" defaultChecked /> Requerir MFA en proximo login
            </label>
            <Button className="w-fit">Actualizar seguridad</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">API Keys</h2>
            <p className="text-sm text-muted-foreground">Rotacion y scopes para integraciones.</p>
          </CardHeader>
          <CardContent className="grid gap-4">
            <Input label="Nombre de key" placeholder="billing-prod" />
            <Input label="Scopes" placeholder="billing:read webhooks:write" />
            <Button className="w-fit">Crear API key</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Notificaciones</h2>
            <p className="text-sm text-muted-foreground">Alertas operativas y de riesgo.</p>
          </CardHeader>
          <CardContent className="grid gap-4">
            <label className="flex items-center gap-3 text-sm">
              <input type="checkbox" className="h-4 w-4 accent-primary" defaultChecked /> Alertas de billing
            </label>
            <label className="flex items-center gap-3 text-sm">
              <input type="checkbox" className="h-4 w-4 accent-primary" defaultChecked /> Eventos de riesgo alto
            </label>
            <Input label="Canal webhook" placeholder="https://ops.example.com/hooks/melispy" />
            <Button className="w-fit">Guardar preferencias</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
