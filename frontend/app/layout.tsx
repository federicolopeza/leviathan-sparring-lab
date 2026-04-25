import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { QueryClientProvider } from "@/lib/queryClient";

export const metadata: Metadata = {
  title: "Melispy",
  description: "SaaS fintech AI-native para LATAM"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body>
        <QueryClientProvider>{children}</QueryClientProvider>
      </body>
    </html>
  );
}
