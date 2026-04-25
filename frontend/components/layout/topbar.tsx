"use client";

import Link from "next/link";
import { ChevronDown, LogOut, Settings, User } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

type NavItem = {
  href: string;
  label: string;
};

const defaultNav: NavItem[] = [
  { href: "/#producto", label: "Producto" },
  { href: "/pricing", label: "Pricing" },
  { href: "/docs", label: "Docs" },
  { href: "/login", label: "Login" }
];

export function Topbar({
  navItems = defaultNav,
  showUserMenu = false,
  className
}: {
  navItems?: NavItem[];
  showUserMenu?: boolean;
  className?: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <header className={cn("sticky top-0 z-40 border-b border-border bg-background/82 backdrop-blur-xl", className)}>
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-3 font-semibold">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-white">
            <span
              aria-hidden="true"
              className="h-6 w-6 bg-white [mask:url('/melispy-logo.svg')_center/contain_no-repeat]"
            />
          </span>
          <span className="text-base tracking-tight">Melispy</span>
        </Link>

        <nav className="hidden items-center gap-7 text-sm font-medium text-muted-foreground md:flex" aria-label="Principal">
          {navItems.map((item) => (
            <Link key={item.href} href={item.href} className="transition hover:text-foreground">
              {item.label}
            </Link>
          ))}
        </nav>

        {showUserMenu ? (
          <div className="relative">
            <button
              type="button"
              className="flex h-10 items-center gap-2 rounded-lg border border-border bg-card px-2 text-sm"
              onClick={() => setOpen((current) => !current)}
              aria-expanded={open}
              aria-haspopup="menu"
            >
              <span className="grid h-7 w-7 place-items-center rounded-full bg-muted text-xs font-semibold">ML</span>
              <ChevronDown className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            </button>
            {open ? (
              <div
                role="menu"
                className="absolute right-0 mt-2 w-48 rounded-xl border border-border bg-card p-1 text-sm shadow-[var(--shadow-soft)]"
              >
                <Link role="menuitem" href="/dashboard/settings" className="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-muted">
                  <User className="h-4 w-4" /> Perfil
                </Link>
                <Link role="menuitem" href="/dashboard/settings" className="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-muted">
                  <Settings className="h-4 w-4" /> Ajustes
                </Link>
                {/* TODO Phase 1: wire onClick to /api/auth/logout + router.push('/') */}
                <button type="button" role="menuitem" className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left hover:bg-muted">
                  <LogOut className="h-4 w-4" /> Cerrar sesion
                </button>
              </div>
            ) : null}
          </div>
        ) : (
          <Link
            href="/signup"
            className="hidden h-10 items-center rounded-lg bg-primary px-4 text-sm font-semibold text-white shadow-[0_12px_30px_rgba(110,86,207,0.22)] sm:inline-flex"
          >
            Empezar
          </Link>
        )}
      </div>
    </header>
  );
}
