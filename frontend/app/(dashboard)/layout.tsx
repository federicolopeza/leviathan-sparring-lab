import type { ReactNode } from "react";
import { AuthGate } from "@/components/auth/auth-gate";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";

const dashboardNav = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/billing", label: "Billing" },
  { href: "/dashboard/uploads", label: "Uploads" },
  { href: "/dashboard/webhooks", label: "Webhooks" },
  { href: "/dashboard/orgs", label: "Orgs" },
  { href: "/dashboard/settings", label: "Settings" }
];

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <Topbar navItems={dashboardNav} showUserMenu />
      <div className="flex min-h-[calc(100vh-4rem)]">
        <Sidebar />
        <main className="min-w-0 flex-1 px-4 py-8 sm:px-6 lg:px-8">
          <AuthGate>{children}</AuthGate>
        </main>
      </div>
    </div>
  );
}
