"use client";

import { CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import type { Plan } from "@/lib/schemas";

type PlanCardProps = {
  plan: Plan;
  selected: boolean;
  onSelect: (plan: Plan) => void;
};

function planPrice(plan: Plan): string {
  if (plan.code === "enterprise") {
    return "Contacto";
  }
  return plan.monthly_price_cents === 0 ? "Gratis" : `USD ${plan.monthly_price_cents / 100}/mes`;
}

export function PlanCard({ plan, selected, onSelect }: PlanCardProps) {
  return (
    <Card className={selected ? "border-primary shadow-[0_18px_60px_rgba(110,86,207,0.14)]" : undefined}>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">{plan.name}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{plan.description}</p>
          </div>
          {selected ? <CheckCircle2 className="h-5 w-5 text-accent" aria-label="Plan seleccionado" /> : null}
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-semibold tracking-tight">{planPrice(plan)}</p>
      </CardContent>
      <CardFooter>
        <Button type="button" variant={selected ? "secondary" : "primary"} className="w-full" onClick={() => onSelect(plan)}>
          {selected ? "Seleccionado" : "Elegir plan"}
        </Button>
      </CardFooter>
    </Card>
  );
}
