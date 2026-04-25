import { Building2 } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

const orgs = ["PagoSur", "AndesPay", "RioBank", "CobreHub"];

export default function OrgsPage() {
  return (
    <section className="mx-auto grid max-w-6xl gap-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Orgs</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">Organizaciones</h1>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {orgs.map((org) => (
          <Card key={org}>
            <CardHeader className="flex-row items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-lg bg-muted text-primary">
                <Building2 className="h-5 w-5" />
              </span>
              <div>
                <h2 className="font-semibold">{org}</h2>
                <p className="text-sm text-muted-foreground">Tenant activo</p>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">Plan Pro, auditoria habilitada, 3 miembros.</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
