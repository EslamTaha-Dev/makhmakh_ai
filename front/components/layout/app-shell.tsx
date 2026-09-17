"use client";

import {
  LayoutDashboard,
  LibraryBig,
  LogOut,
  Menu,
  MessageSquareText,
  Settings,
  FolderOpen,
  UploadCloud,
  X,
} from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";

import { BrandLogo } from "@/components/brand/logo";
import { LocaleSwitcher } from "@/components/layout/locale-switcher";
import { Button } from "@/components/ui/button";
import { Link, usePathname, useRouter } from "@/i18n/routing";
import { useSessionStore } from "@/lib/auth/session-store";
import { initialsFromName } from "@/lib/format";
import { isRoleKey } from "@/lib/roles";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { key: "dashboard", href: "/dashboard", icon: LayoutDashboard },
  { key: "subjects", href: "/subjects", icon: LibraryBig },
  { key: "materials", href: "/materials", icon: FolderOpen },
  { key: "upload", href: "/upload", icon: UploadCloud },
  { key: "chat", href: "/chat", icon: MessageSquareText },
  { key: "settings", href: "/settings", icon: Settings },
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const t = useTranslations("nav");
  const tCommon = useTranslations("common");
  const tRoles = useTranslations("roles");
  const pathname = usePathname();
  const router = useRouter();

  const user = useSessionStore((state) => state.user);
  const signOut = useSessionStore((state) => state.signOut);

  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [isSigningOut, setIsSigningOut] = React.useState(false);

  // Closing on link clicks rather than on a pathname effect keeps navigation snappy.
  const closeDrawer = React.useCallback(() => setDrawerOpen(false), []);

  React.useEffect(() => {
    if (!drawerOpen) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setDrawerOpen(false);
    };

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [drawerOpen]);

  const handleSignOut = async () => {
    setDrawerOpen(false);
    setIsSigningOut(true);
    try {
      await signOut();
      router.replace("/");
    } finally {
      setIsSigningOut(false);
    }
  };

  const isActive = (href: string) =>
    pathname === href || pathname.startsWith(`${href}/`);

  const nav = (
    <nav className="flex flex-col gap-1" aria-label={t("home")}>
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        const active = isActive(item.href);

        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={closeDrawer}
            aria-current={active ? "page" : undefined}
            className={cn(
              "group flex items-center gap-3 rounded-2xl px-3.5 py-2.5 text-sm font-medium transition duration-200",
              active
                ? "bg-brand-500/12 text-brand-700"
                : "text-cocoa-800/80 hover:bg-cocoa-800/6 hover:text-cocoa-900",
            )}
          >
            <span
              className={cn(
                "flex size-8 items-center justify-center rounded-xl transition duration-200",
                active
                  ? "brand-gradient-surface text-white"
                  : "bg-muted text-cocoa-800/70 group-hover:bg-white",
              )}
            >
              <Icon aria-hidden className="size-4" />
            </span>

            {t(item.key)}
          </Link>
        );
      })}
    </nav>
  );

  const account = user ? (
    <div className="rounded-2xl border border-cocoa-800/10 bg-muted/60 p-3.5">
      <div className="flex items-center gap-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-xl brand-gradient-surface text-sm font-medium text-white">
          {initialsFromName(user.name)}
        </span>

        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-cocoa-900">
            {user.name}
          </p>
          <p className="truncate text-xs text-muted-fg">
            {isRoleKey(user.role) ? tRoles(user.role) : user.role}
          </p>
        </div>
      </div>

      <Button
        variant="outline"
        size="sm"
        block
        className="mt-3"
        onClick={handleSignOut}
        loading={isSigningOut}
        loadingText={tCommon("saving")}
      >
        <LogOut aria-hidden />
        {t("logout")}
      </Button>
    </div>
  ) : null;

  return (
    <div className="flex min-h-dvh bg-surface">
      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-dvh w-72 shrink-0 flex-col gap-6 border-e border-cocoa-800/8 bg-white px-4 py-6 lg:flex">
        <Link href="/dashboard" aria-label={tCommon("appName")}>
          <BrandLogo height={38} />
        </Link>

        {nav}

        <div className="mt-auto space-y-3">
          <LocaleSwitcher variant="outline" className="w-full justify-center" />
          {account}
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Mobile top bar */}
        <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-cocoa-800/8 bg-white/90 px-4 backdrop-blur lg:hidden">
          <Link href="/dashboard" aria-label={tCommon("appName")}>
            <BrandLogo height={32} />
          </Link>

          <Button
            variant="ghost"
            size="icon"
            className="ms-auto"
            onClick={() => setDrawerOpen(true)}
            aria-label={tCommon("openMenu")}
            aria-expanded={drawerOpen}
            aria-controls="app-drawer"
          >
            <Menu aria-hidden />
          </Button>
        </header>

        <main id="main" className="flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-10">
          <div className="mx-auto w-full max-w-6xl">{children}</div>
        </main>
      </div>

      {/* Mobile drawer */}
      {drawerOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-cocoa-950/40 backdrop-blur-sm"
            onClick={() => setDrawerOpen(false)}
            aria-hidden
          />

          <div
            id="app-drawer"
            role="dialog"
            aria-modal="true"
            aria-label={tCommon("openMenu")}
            className="absolute inset-y-0 start-0 flex w-72 max-w-[85vw] flex-col gap-6 bg-white px-4 py-6 shadow-lift motion-safe:animate-in motion-safe:slide-in-from-start"
          >
            <div className="flex items-center justify-between">
              <Link
                href="/dashboard"
                onClick={closeDrawer}
                aria-label={tCommon("appName")}
              >
                <BrandLogo height={34} />
              </Link>

              <Button
                variant="ghost"
                size="icon-sm"
                onClick={() => setDrawerOpen(false)}
                aria-label={tCommon("closeMenu")}
              >
                <X aria-hidden />
              </Button>
            </div>

            {nav}

            <div className="mt-auto space-y-3">
              <LocaleSwitcher variant="outline" className="w-full justify-center" />
              {account}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
