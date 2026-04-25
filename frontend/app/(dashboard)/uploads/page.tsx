import { UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export default function UploadsPage() {
  return (
    <section className="mx-auto grid max-w-6xl gap-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Uploads</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">Archivos</h1>
      </div>
      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold">Carga segura</h2>
          <p className="text-sm text-muted-foreground">Ingesta de CSV, contratos y soportes de conciliacion.</p>
        </CardHeader>
        <CardContent>
          <div className="grid place-items-center rounded-2xl border border-dashed border-border bg-muted/70 px-6 py-16 text-center">
            <UploadCloud className="h-10 w-10 text-primary" />
            <p className="mt-4 font-semibold">Arrastra archivos o selecciona desde disco</p>
            <Button className="mt-5" variant="secondary">Seleccionar archivo</Button>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
