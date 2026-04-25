import Link from "next/link";
import { LoginForm } from "@/components/features/auth/login-form";

export default function LoginPage() {
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Ingresar</h1>
      <p className="mt-2 text-sm text-muted-foreground">Accede al dashboard operativo de Melispy.</p>
      <div className="mt-8">
        <LoginForm />
      </div>
      <div className="mt-5 flex justify-between text-sm text-muted-foreground">
        <Link href="/forgot" className="hover:text-foreground">
          Olvide mi contrasena
        </Link>
        <Link href="/signup" className="hover:text-foreground">
          Crear cuenta
        </Link>
      </div>
    </div>
  );
}
