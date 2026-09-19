"use client";

import { create } from "zustand";

import { ApiError } from "@/lib/api/client";
import * as api from "@/lib/api/endpoints";
import type { User } from "@/lib/api/types";
import {
  clearTokens,
  hasTokens,
  onAuthLoss,
  setTokens,
} from "@/lib/auth/tokens";

export type SessionStatus = "loading" | "authenticated" | "guest";

type SessionState = {
  status: SessionStatus;
  user: User | null;
  bootstrap: () => Promise<void>;
  signIn: (email: string, password: string) => Promise<User>;
  signUp: (
    name: string,
    email: string,
    password: string,
  ) => Promise<User>;
  signOut: (options?: { remote?: boolean }) => Promise<void>;
  refreshUser: () => Promise<User | null>;
};

let bootstrapped = false;

export const useSessionStore = create<SessionState>((set, get) => ({
  status: "loading",
  user: null,

  async bootstrap() {
    // Only ever resolve the session once per page load.
    if (bootstrapped) return;
    bootstrapped = true;

    if (!hasTokens()) {
      set({ status: "guest", user: null });
      return;
    }

    try {
      const user = await api.getMe();
      set({ status: "authenticated", user });
    } catch (error) {
      if (error instanceof ApiError && error.isUnauthorized) {
        clearTokens();
      }
      set({ status: "guest", user: null });
    }
  },

  async signIn(email, password) {
    const tokens = await api.login({ email, password });
    setTokens(tokens.access_token, tokens.refresh_token);

    const user = await api.getMe();
    set({ status: "authenticated", user });

    return user;
  },

  async signUp(name, email, password) {
    await api.register({ name, email, password });

    // Registration returns the user only, so sign in to get a session.
    const user = await get().signIn(email, password);

    return user;
  },

  async signOut(options) {
    if (options?.remote !== false && hasTokens()) {
      try {
        await api.logout();
      } catch {
        // Signing out locally is what matters; the token may already be stale.
      }
    }

    clearTokens();
    set({ status: "guest", user: null });
  },

  async refreshUser() {
    if (!hasTokens()) {
      set({ status: "guest", user: null });
      return null;
    }

    try {
      const user = await api.getMe();
      set({ status: "authenticated", user });
      return user;
    } catch {
      return null;
    }
  },

}));

// The API client clears tokens when a refresh fails; mirror that into the store.
onAuthLoss(() => {
  useSessionStore.setState({ status: "guest", user: null });
});

export function useCurrentUser(): User | null {
  return useSessionStore((state) => state.user);
}

export function useIsAuthenticated(): boolean {
  return useSessionStore((state) => state.status === "authenticated");
}
