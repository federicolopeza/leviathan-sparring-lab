import type { ReactNode } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <main className="grid min-h-screen place-items-center bg-muted px-4 py-10">
      <Card className="w-full max-w-md p-6 shadow-[var(--shadow-soft)]">
        <Link href="/" className="mb-8 inline-flex text-lg font-semibold">
          Melispy
        </Link>
        {children}
      </Card>
    </main>
  );
}
