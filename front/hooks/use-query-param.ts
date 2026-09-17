"use client";

import * as React from "react";

function subscribeToLocation(onChange: () => void): () => void {
  window.addEventListener("popstate", onChange);
  return () => window.removeEventListener("popstate", onChange);
}

/**
 * Reads a query parameter on the client only.
 *
 * `useSearchParams` would force these screens behind a Suspense boundary during
 * static rendering; reading from `window` keeps them simple and safe, and
 * `useSyncExternalStore` supplies the server snapshot so hydration stays clean.
 */
export function useQueryParam(name: string): {
  value: string | null;
  ready: boolean;
} {
  const search = React.useSyncExternalStore(
    subscribeToLocation,
    () => window.location.search,
    () => null,
  );

  return React.useMemo(
    () => ({
      value: search === null ? null : new URLSearchParams(search).get(name),
      ready: search !== null,
    }),
    [search, name],
  );
}
