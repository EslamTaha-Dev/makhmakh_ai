"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";
import * as React from "react";
import { Toaster } from "sonner";

import type { Locale } from "@/i18n/routing";

type ProvidersProps = {
  children: React.ReactNode;
  locale: Locale;
  messages: Record<string, unknown>;
  timeZone: string;
};

export function Providers({
  children,
  locale,
  messages,
  timeZone,
}: ProvidersProps) {
  const [queryClient] = React.useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            retry: (failureCount, error) => {
              const status = (error as { status?: number })?.status;
              // Never retry auth/permission/validation failures.
              if (typeof status === "number" && status >= 400 && status < 500) {
                return false;
              }
              return failureCount < 2;
            },
          },
        },
      }),
  );

  return (
    <NextIntlClientProvider
      locale={locale}
      messages={messages}
      timeZone={timeZone}
    >
      <QueryClientProvider client={queryClient}>
        {children}
        <Toaster
          position="top-center"
          dir={locale === "ar" ? "rtl" : "ltr"}
          toastOptions={{
            style: {
              borderRadius: "1rem",
              border: "1px solid rgb(102 51 0 / 0.12)",
              fontFamily: "var(--font-thmanyah)",
            },
          }}
        />
      </QueryClientProvider>
    </NextIntlClientProvider>
  );
}
