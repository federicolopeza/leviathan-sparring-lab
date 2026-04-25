"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Bot, Building2, CreditCard, KeyRound, Menu, MessageSquare, UploadCloud, Webhook, X } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/dashboard/billing", label: "Billing", icon: CreditCard },
  { href: "/dashboard/uploads", label: "Uploads", icon: UploadCloud },
  { href: "/dashboard/webhooks", label: "Webhooks", icon: Webhook },
  { href: "/dashboard/orgs", label: "Orgs", icon: Building2 },
  { href: "/dashboard/settings", label: "Settings", icon: KeyRound }
];

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const content = (
    <nav className="grid gap-1" aria-label="Dashboard">
      {navItems.map((item) => {
        const Icon = item.icon;
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition",
              active ? "bg-primary text-white shadow-[0_12px_30px_rgba(110,86,207,0.2)]" : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
            onClick={() => setOpen(false)}
          >
            <Icon className="h-4 w-4" aria-hidden="true" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );

  return (
    <>
      <button
        type="button"
        className="fixed left-4 top-4 z-50 grid h-10 w-10 place-items-center rounded-lg border border-border bg-card shadow-sm lg:hidden"
        onClick={() => setOpen((current) => !current)}
        aria-label="Abrir navegacion"
      >
        {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>
      <aside className="hidden w-72 shrink-0 border-r border-border bg-card/72 p-4 lg:block">
        <div className="mb-8 px-2 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">Melispy Ops</div>
        {content}
      </aside>
      {open ? (
        <div className="fixed inset-0 z-40 bg-black/30 lg:hidden" onClick={() => setOpen(false)}>
          <aside className="h-full w-72 bg-card p-4 shadow-[var(--shadow-soft)]" onClick={(event) => event.stopPropagation()}>
            <div className="mb-8 pl-12 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">Melispy Ops</div>
            {content}
          </aside>
        </div>
      ) : null}
    </>
  );
}
