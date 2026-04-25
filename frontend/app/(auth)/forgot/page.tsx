import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function ForgotPage() {
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Recuperar acceso</h1>
      <p className="mt-2 text-sm text-muted-foreground">Te enviaremos instrucciones si el email tiene una cuenta activa.</p>
      <form className="mt-8 grid gap-5" method="post" action="/api/auth/forgot">
        <Input label="Email" name="email" type="email" autoComplete="email" required />
        <Button type="submit">Enviar instrucciones</Button>
      </form>
    </div>
  );
}
