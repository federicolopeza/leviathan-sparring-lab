import { Bot, PlayCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

const agents = ["Riesgo transaccional", "Conciliacion bancaria", "Soporte billing"];

export default function AgentsPage() {
  return (
    <section className="mx-auto grid max-w-6xl gap-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Agentes</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">Agentes operativos</h1>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {agents.map((agent) => (
          <Card key={agent}>
            <CardHeader>
              <Bot className="h-6 w-6 text-primary" />
              <h2 className="text-xl font-semibold">{agent}</h2>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-6 text-muted-foreground">Fixture deterministico, permisos por tenant y auditoria de cada decision.</p>
              <Button className="mt-5" variant="secondary">
                <PlayCircle className="h-4 w-4" /> Abrir
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
