import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";

const tiers = [
  { name: "Free", price: "/usr/bin/bash/mes", description: "Para probar agentes y billing basico.", features: ["1 organizacion", "2 agentes", "1k llamadas API"] },
  { name: "Pro", price: "9/mes", description: "Para fintechs en produccion temprana.", features: ["5 organizaciones", "20 agentes", "250k llamadas API"], popular: true },
  { name: "Enterprise", price: "contact sales", description: "Controles avanzados para operaciones reguladas.", features: ["SLA dedicado", "SAML/SCIM", "Auditoria extendida"] }
];

const rows = [
  ["Agentes activos", "2", "20", "Ilimitados"],
  ["Webhooks", "Basicos", "Firmados", "Firmados + replay guard"],
  ["Soporte", "Comunidad", "Email prioritario", "Canal dedicado"],
  ["Retencion auditoria", "7 dias", "90 dias", "Custom"]
];

export default function PricingPage() {
  return (
    <section className="px-4 py-16 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <div className="max-w-3xl">
          <h1 className="font-display text-5xl leading-none tracking-normal">Pricing simple para crecer sin friccion.</h1>
          <p className="mt-5 text-lg leading-8 text-muted-foreground">
            Empieza con automatizacion esencial y escala controles cuando el volumen regulatorio lo exige.
          </p>
        </div>

        <div className="mt-12 grid gap-5 lg:grid-cols-3">
          {tiers.map((tier) => (
            <Card key={tier.name} className={tier.popular ? "border-primary shadow-[0_24px_70px_rgba(110,86,207,0.18)]" : ""}>
              <CardHeader>
                <div className="flex items-center justify-between gap-4">
                  <h2 className="text-2xl font-semibold">{tier.name}</h2>
                  {tier.popular ? <span className="rounded-full bg-primary px-3 py-1 text-xs font-semibold text-white">Most popular</span> : null}
                </div>
                <p className="text-muted-foreground">{tier.description}</p>
                <p className="pt-4 text-4xl font-semibold">{tier.price}</p>
              </CardHeader>
              <CardContent>
                <ul className="grid gap-3 text-sm text-muted-foreground">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-accent" /> {feature}
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter>
                <Button variant={tier.popular ? "primary" : "secondary"} className="w-full">
                  {tier.name === "Enterprise" ? "Contactar ventas" : "Elegir plan"}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>

        <div className="mt-14 overflow-hidden rounded-2xl border border-border bg-card">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="bg-muted text-muted-foreground">
              <tr>
                <th className="px-5 py-4 font-semibold">Feature</th>
                <th className="px-5 py-4 font-semibold">Free</th>
                <th className="px-5 py-4 font-semibold">Pro</th>
                <th className="px-5 py-4 font-semibold">Enterprise</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row[0]} className="border-t border-border">
                  {row.map((cell) => (
                    <td key={cell} className="px-5 py-4">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
