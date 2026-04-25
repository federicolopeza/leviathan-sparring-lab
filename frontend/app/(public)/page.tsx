import Link from "next/link";
import { ArrowRight, Bot, Building2, CreditCard, Network } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

const features = [
  {
    title: "Agentes IA",
    text: "Flujos deterministas para soporte financiero, cobranza y analisis operativo.",
    icon: Bot
  },
  {
    title: "Billing multi-tenant",
    text: "Planes, invoices y controles por organizacion con trazabilidad de auditoria.",
    icon: CreditCard
  },
  {
    title: "API en espanol",
    text: "Contratos claros para equipos LATAM, con eventos, webhooks y conciliacion.",
    icon: Network
  }
];

const logos = ["PagoSur", "AndesPay", "RioBank", "CobreHub", "NexoLatam"];

export default function LandingPage() {
  return (
    <>
      <section className="relative overflow-hidden px-4 py-20 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-12 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
          <div className="max-w-3xl">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-sm text-muted-foreground">
              <span className="h-2 w-2 rounded-full bg-accent" />
              Fintech operating layer para LATAM
            </div>
            <h1 className="font-display text-[clamp(2.75rem,7vw,6.3rem)] leading-[0.92] tracking-normal">
              Melispy el SaaS fintech AI-native de LATAM.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-muted-foreground">
              Agentes inteligentes que automatizan billing, riesgo y conciliacion para fintechs en espanol.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/signup"
                className="group inline-flex h-12 items-center justify-center gap-2 rounded-lg bg-primary px-5 text-base font-semibold text-white shadow-[0_12px_30px_rgba(110,86,207,0.24)] transition hover:bg-[#5f49bc]"
              >
                Empezar gratis <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
              </Link>
              <Link
                href="/login"
                className="inline-flex h-12 items-center justify-center rounded-lg border border-border bg-card px-5 font-semibold text-foreground transition hover:bg-muted"
              >
                Probar demo
              </Link>
            </div>
          </div>

          <div className="rounded-[2rem] border border-border bg-card/84 p-4 shadow-[var(--shadow-soft)]">
            <div className="rounded-[1.5rem] bg-[#10131E] p-5 text-white">
              <div className="mb-6 flex items-center justify-between text-sm text-white/60">
                <span>Risk automation</span>
                <span>Q2 LATAM</span>
              </div>
              <div className="grid gap-4">
                <div className="rounded-2xl bg-white/8 p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-sm text-white/70">Conciliacion</span>
                    <span className="rounded-full bg-accent px-2 py-1 text-xs font-semibold text-[#062319]">98.4%</span>
                  </div>
                  <div className="h-3 rounded-full bg-white/10">
                    <div className="h-3 w-[82%] rounded-full bg-accent" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-2xl bg-white/8 p-4">
                    <p className="text-sm text-white/60">Riesgo</p>
                    <p className="mt-2 text-3xl font-semibold">Bajo</p>
                  </div>
                  <div className="rounded-2xl bg-white/8 p-4">
                    <p className="text-sm text-white/60">API calls</p>
                    <p className="mt-2 text-3xl font-semibold">1.8M</p>
                  </div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/6 p-4">
                  <div className="flex items-center gap-3">
                    <Building2 className="h-5 w-5 text-accent" />
                    <div>
                      <p className="font-semibold">Tenant AndesPay</p>
                      <p className="text-sm text-white/55">3 agentes activos, 0 alertas abiertas</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="producto" className="px-4 pb-20 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-5 md:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Card key={feature.title} className="bg-card/82">
                <CardHeader>
                  <Icon className="h-6 w-6 text-primary" aria-hidden="true" />
                  <h2 className="text-xl font-semibold">{feature.title}</h2>
                </CardHeader>
                <CardContent>
                  <p className="leading-7 text-muted-foreground">{feature.text}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      <section className="border-y border-border bg-card/55 px-4 py-10 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-muted-foreground">Equipos fintech que confian en Melispy</p>
          <div className="grid grid-cols-2 gap-x-8 gap-y-4 text-lg font-semibold text-foreground/76 sm:grid-cols-5">
            {logos.map((logo) => (
              <span key={logo}>{logo}</span>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
