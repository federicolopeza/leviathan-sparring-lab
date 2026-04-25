import { Webhook } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function WebhooksPage() {
  return (
    <section className="mx-auto grid max-w-6xl gap-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Webhooks</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">Eventos salientes</h1>
      </div>
      <Card>
        <CardHeader className="flex-row items-center gap-3">
          <Webhook className="h-6 w-6 text-primary" />
          <div>
            <h2 className="text-xl font-semibold">Nuevo endpoint</h2>
            <p className="text-sm text-muted-foreground">Configura un destino firmado para eventos criticos.</p>
          </div>
        </CardHeader>
        <CardContent className="grid gap-4">
          <Input label="URL" placeholder="https://ops.example.com/melispy" />
          <Input label="Eventos" placeholder="invoice.paid, risk.flagged" />
          <Button className="w-fit">Guardar webhook</Button>
        </CardContent>
      </Card>
    </section>
  );
}
