import type { ReactNode } from "react";
import { Topbar } from "@/components/layout/topbar";

export default function PublicLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <Topbar />
      <main>{children}</main>
    </div>
  );
}
