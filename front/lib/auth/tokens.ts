/**
 * Token storage.
 *
 * The backend authenticates with `Authorization: Bearer <access>` and has no cookie
 * support, so tokens live in localStorage. Access is kept in memory as well so the
 * API client never hits storage on a hot path.
 */

const ACCESS_TOKEN_KEY = "makhmakh.access_token";
const REFRESH_TOKEN_KEY = "makhmakh.refresh_token";

let accessToken: string | null = null;
let refreshToken: string | null = null;
let hydrated = false;

const authLossListeners = new Set<() => void>();

function storage(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function hydrate(): void {
  if (hydrated) return;
  hydrated = true;

  const store = storage();
  if (!store) return;

  accessToken = store.getItem(ACCESS_TOKEN_KEY);
  refreshToken = store.getItem(REFRESH_TOKEN_KEY);
}

export function getAccessToken(): string | null {
  hydrate();
  return accessToken;
}

export function getRefreshToken(): string | null {
  hydrate();
  return refreshToken;
}

export function hasTokens(): boolean {
  hydrate();
  return Boolean(accessToken || refreshToken);
}

export function setTokens(access: string, refresh: string): void {
  hydrate();

  accessToken = access;
  refreshToken = refresh;

  const store = storage();
  store?.setItem(ACCESS_TOKEN_KEY, access);
  store?.setItem(REFRESH_TOKEN_KEY, refresh);
}

export function clearTokens(): void {
  hydrate();

  accessToken = null;
  refreshToken = null;

  const store = storage();
  store?.removeItem(ACCESS_TOKEN_KEY);
  store?.removeItem(REFRESH_TOKEN_KEY);
}

/** Notify listeners (the session store) that the session can no longer be restored. */
export function notifyAuthLoss(): void {
  for (const listener of authLossListeners) {
    listener();
  }
}

export function onAuthLoss(listener: () => void): () => void {
  authLossListeners.add(listener);
  return () => authLossListeners.delete(listener);
}
