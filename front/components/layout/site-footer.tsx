import { useTranslations } from "next-intl";

import { BrandLogo } from "@/components/brand/logo";
import { Link } from "@/i18n/routing";

export function SiteFooter() {
  const t = useTranslations("landing.footer");
  const tNav = useTranslations("nav");
  const tSections = useTranslations("landing.sections");

  const productLinks = [
    { href: "/#features", label: tSections("features") },
    { href: "/#how", label: tSections("how") },
    { href: "/#faq", label: tSections("faq") },
  ];

  const accountLinks = [
    { href: "/login", label: tNav("login") },
    { href: "/register", label: tNav("register") },
  ];

  return (
    <footer className="border-t border-cocoa-800/8 bg-white">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-4 lg:col-span-2">
            <BrandLogo height={44} />
            <p className="max-w-sm text-sm text-muted-fg break-arabic">
              {t("tagline")}
            </p>
          </div>

          <nav className="space-y-3" aria-label={t("product")}>
            <p className="font-display text-sm text-cocoa-900">{t("product")}</p>
            <ul className="space-y-2">
              {productLinks.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-sm text-muted-fg transition hover:text-brand-600"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          <nav className="space-y-3" aria-label={t("account")}>
            <p className="font-display text-sm text-cocoa-900">{t("account")}</p>
            <ul className="space-y-2">
              {accountLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-muted-fg transition hover:text-brand-600"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <div className="mt-10 flex flex-col gap-3 border-t border-cocoa-800/8 pt-6 text-xs text-muted-fg sm:flex-row sm:items-center sm:justify-between">
          <p>{t("note")}</p>
          <p>
            © {new Date().getFullYear()} مخمخ — {t("rights")}
          </p>
        </div>
      </div>
    </footer>
  );
}
