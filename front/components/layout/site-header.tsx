"use client";

import { LayoutDashboard, Menu, X } from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";

import { BrandLogo } from "@/components/brand/logo";
import { LocaleSwitcher } from "@/components/layout/locale-switcher";
import { Button, buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/routing";
import { useSessionStore } from "@/lib/auth/session-store";
import { cn } from "@/lib/utils";

export function SiteHeader() {
  const t = useTranslations("nav");
  const tSections = useTranslations("landing.sections");
  const [open, setOpen] = React.useState(false);
  const status = useSessionStore((state) => state.status);

  React.useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open]);

  const sections = [
    { href: "#features", label: tSections("features") },
    { href: "#how", label: tSections("how") },
    { href: "#formats", label: tSections("formats") },
    { href: "#faq", label: tSections("faq") },
  ];

  const isAuthenticated = status === "authenticated";

  return (
    <header className="sticky top-0 z-40 border-b border-cocoa-800/8 bg-white/85 backdrop-blur-lg">
      <div className="mx-auto flex h-18 max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center" aria-label="مخمخ">
          <BrandLogo height={38} priority />
        </Link>

        <nav className="ms-6 hidden items-center gap-1 lg:flex" aria-label="sections">
          {sections.map((section) => (
            <a
              key={section.href}
              href={section.href}
              className="rounded-xl px-3 py-2 text-sm font-medium text-cocoa-800/85 transition hover:bg-cocoa-800/6 hover:text-cocoa-900"
            >
              {section.label}
            </a>
          ))}
        </nav>

        <div className="ms-auto flex items-center gap-2">
          <LocaleSwitcher className="hidden sm:inline-flex" />

          {isAuthenticated ? (
            <Link href="/dashboard" className={buttonVariants({ size: "sm" })}>
              <LayoutDashboard aria-hidden />
              {t("dashboard")}
            </Link>
          ) : (
            <>
              <Link
                href="/login"
                className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "hidden sm:inline-flex")}
              >
                {t("login")}
              </Link>
              <Link
                href="/register"
                className={cn(buttonVariants({ size: "sm" }), "hidden sm:inline-flex")}
              >
                {t("register")}
              </Link>
            </>
          )}

          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setOpen((value) => !value)}
            aria-expanded={open}
            aria-controls="mobile-menu"
            aria-label={open ? "close" : "menu"}
          >
            {open ? <X aria-hidden /> : <Menu aria-hidden />}
          </Button>
        </div>
      </div>

      {open ? (
        <div
          id="mobile-menu"
          className="border-t border-cocoa-800/8 bg-white px-4 py-4 lg:hidden motion-safe:animate-in motion-safe:slide-in-from-top-2"
        >
          <nav className="flex flex-col gap-1" aria-label="sections">
            {sections.map((section) => (
              <a
                key={section.href}
                href={section.href}
                onClick={() => setOpen(false)}
                className="rounded-xl px-3 py-2.5 text-sm font-medium text-cocoa-900 transition hover:bg-muted"
              >
                {section.label}
              </a>
            ))}
          </nav>

          <div className="mt-4 flex flex-col gap-2">
            <LocaleSwitcher variant="outline" className="justify-center" />

            {isAuthenticated ? (
              <Link
                href="/dashboard"
                className={buttonVariants({ block: true })}
                onClick={() => setOpen(false)}
              >
                {t("dashboard")}
              </Link>
            ) : (
              <>
                <Link
                  href="/login"
                  className={buttonVariants({ variant: "outline", block: true })}
                  onClick={() => setOpen(false)}
                >
                  {t("login")}
                </Link>
                <Link
                  href="/register"
                  className={buttonVariants({ block: true })}
                  onClick={() => setOpen(false)}
                >
                  {t("register")}
                </Link>
              </>
            )}
          </div>
        </div>
      ) : null}
    </header>
  );
}
