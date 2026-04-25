import Link from "next/link";
import { SignupForm } from "@/components/features/auth/signup-form";

export default function SignupPage() {
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Crear cuenta</h1>
      <p className="mt-2 text-sm text-muted-foreground">Configura tu organizacion y prueba los agentes fintech.</p>
      <div className="mt-8">
        <SignupForm />
      </div>
      <p className="mt-5 text-sm text-muted-foreground">
        Ya tienes cuenta?{" "}
        <Link href="/login" className="font-medium text-foreground">
          Ingresar
        </Link>
      </p>
    </div>
  );
}
