"use client";

import { useEffect } from "react";

import { useSessionStore } from "@/lib/auth/session-store";

/** Restores the session from stored tokens so guards and headers can trust it. */
export function SessionBootstrap() {
  const bootstrap = useSessionStore((state) => state.bootstrap);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  return null;
}
