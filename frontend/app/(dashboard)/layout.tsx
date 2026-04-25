import type { ReactNode } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";

const dashboardNav = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/settings", label: "Settings" }
];

// TODO Phase 1: gate dashboard behind auth (RSC redirect or middleware) — currently anonymous-accessible under static export
export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <Topbar navItems={dashboardNav} showUserMenu />
      <div className="flex min-h-[calc(100vh-4rem)]">
        <Sidebar />
        <main className="min-w-0 flex-1 px-4 py-8 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
