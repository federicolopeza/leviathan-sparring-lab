const tabs = [
  {
    title: "Empezando",
    body: "Crea una organizacion, invita a tu equipo y conecta el primer flujo de billing. Los entornos demo usan datos sinteticos."
  },
  {
    title: "Agentes",
    body: "Configura agentes por rol operativo: riesgo, conciliacion, soporte o cobranzas. Cada agente tiene permisos y trazabilidad."
  },
  {
    title: "Integraciones",
    body: "Conecta webhooks, archivos CSV y eventos de core bancario. Esta documentacion es comercial; las specs API no se exponen aqui."
  }
];

export default function DocsPage() {
  return (
    <section className="px-4 py-16 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <h1 className="font-display text-5xl leading-none tracking-normal">Docs de producto</h1>
        <p className="mt-5 max-w-2xl text-lg leading-8 text-muted-foreground">
          Una guia ejecutiva para entender como Melispy organiza agentes, billing e integraciones sin publicar especificaciones API.
        </p>
        <div className="mt-10 inline-flex rounded-xl border border-border bg-card p-1" role="tablist" aria-label="Documentacion">
          {tabs.map((tab, index) => (
            <button
              key={tab.title}
              type="button"
              role="tab"
              aria-selected={index === 0}
              className={`rounded-lg px-4 py-2 text-sm font-semibold ${index === 0 ? "bg-primary text-white" : "text-muted-foreground"}`}
            >
              {tab.title}
            </button>
          ))}
        </div>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {tabs.map((tab) => (
            <article key={tab.title} className="rounded-2xl border border-border bg-card p-6">
              <h2 className="text-xl font-semibold">{tab.title}</h2>
              <p className="mt-4 leading-7 text-muted-foreground">{tab.body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
