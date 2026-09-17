"use client";

import * as React from "react";

const subscribe = () => () => {};

/**
 * `true` once the component runs on the client, `false` during server rendering.
 *
 * Backed by `useSyncExternalStore` so no state is written from an effect, which
 * keeps React's cascading-render lint rule (and hydration) happy.
 */
export function useHydrated(): boolean {
  return React.useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
}
