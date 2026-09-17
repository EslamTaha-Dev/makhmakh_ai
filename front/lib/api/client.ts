import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  notifyAuthLoss,
  setTokens,
} from "@/lib/auth/tokens";

import type { TokenResponse } from "./types";

export const API_ORIGIN = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

export const API_PREFIX = "/api/v1";

export class ApiError extends Error {
  readonly status: number;
  readonly payload: unknown;

  constructor(message: string, status: number, payload?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }

  get isOffline(): boolean {
    return this.status === 0;
  }
}

export type QueryValue = string | number | boolean | null | undefined;

export type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  /** JSON body. Ignored when `form` is provided. */
  body?: unknown;
  /** multipart/form-data body. */
  form?: FormData;
  query?: Record<string, QueryValue>;
  signal?: AbortSignal;
  /** Attach the bearer token (default true). */
  auth?: boolean;
};

function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  const url = new URL(`${API_ORIGIN}${API_PREFIX}${path}`);

  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === null || value === undefined || value === "") continue;
      url.searchParams.set(key, String(value));
    }
  }

  return url.toString();
}

/** FastAPI returns `{detail: string}` or `{detail: [{loc, msg}]}` for validation. */
function extractMessage(payload: unknown, status: number): string {
  if (typeof payload === "string" && payload.trim()) {
    return payload;
  }

  if (payload && typeof payload === "object") {
    const detail = (payload as { detail?: unknown }).detail;

    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }

    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          if (item && typeof item === "object") {
            const record = item as { msg?: unknown; loc?: unknown };
            const field = Array.isArray(record.loc)
              ? record.loc.filter((part) => part !== "body").join(".")
              : "";
            const message =
              typeof record.msg === "string" ? record.msg : "Invalid value";
            return field ? `${field}: ${message}` : message;
          }
          return null;
        })
        .filter((value): value is string => Boolean(value));

      if (messages.length) {
        return messages.join(" · ");
      }
    }

    const message = (payload as { message?: unknown }).message;

    if (typeof message === "string" && message.trim()) {
      return message;
    }
  }

  if (status === 0) {
    return "NETWORK";
  }

  return `HTTP ${status}`;
}

async function parseBody(response: Response): Promise<unknown> {
  if (response.status === 204) return null;

  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }

  try {
    const text = await response.text();
    return text || null;
  } catch {
    return null;
  }
}

let refreshPromise: Promise<boolean> | null = null;

/**
 * Rotate the refresh token. Concurrent 401s share one request so the backend's
 * reuse-detection does not revoke the whole token family.
 */
async function refreshSession(): Promise<boolean> {
  if (refreshPromise) return refreshPromise;

  const token = getRefreshToken();

  if (!token) {
    clearTokens();
    notifyAuthLoss();
    return false;
  }

  refreshPromise = (async () => {
    try {
      const response = await fetch(buildUrl("/auth/refresh"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: token }),
        cache: "no-store",
      });

      if (!response.ok) {
        clearTokens();
        notifyAuthLoss();
        return false;
      }

      const data = (await response.json()) as TokenResponse;
      setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      // Network failure: keep tokens so the user can retry once back online.
      return false;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

async function send(
  url: string,
  options: RequestOptions,
): Promise<Response> {
  const headers = new Headers();

  let body: BodyInit | undefined;

  if (options.form) {
    body = options.form;
  } else if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.body);
  }

  if (options.auth !== false) {
    const token = getAccessToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  return fetch(url, {
    method: options.method ?? "GET",
    headers,
    body,
    signal: options.signal,
    cache: "no-store",
  });
}

/** Core request helper. Retries exactly once after a successful token refresh. */
export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const url = buildUrl(path, options.query);

  let response: Response;

  try {
    response = await send(url, options);
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ApiError("NETWORK", 0, null);
  }

  if (response.status === 401 && options.auth !== false) {
    const refreshed = await refreshSession();

    if (refreshed) {
      try {
        response = await send(url, options);
      } catch {
        throw new ApiError("NETWORK", 0, null);
      }
    }
  }

  if (!response.ok) {
    const payload = await parseBody(response);
    throw new ApiError(
      extractMessage(payload, response.status),
      response.status,
      payload,
    );
  }

  return (await parseBody(response)) as T;
}

/** Like `apiRequest` but keeps the response so pagination headers stay readable. */
export async function apiRequestWithMeta<T>(
  path: string,
  options: RequestOptions = {},
): Promise<{ data: T; nextCursor: string | null }> {
  const url = buildUrl(path, options.query);

  let response: Response;

  try {
    response = await send(url, options);
  } catch {
    throw new ApiError("NETWORK", 0, null);
  }

  if (response.status === 401 && options.auth !== false) {
    const refreshed = await refreshSession();

    if (refreshed) {
      try {
        response = await send(url, options);
      } catch {
        throw new ApiError("NETWORK", 0, null);
      }
    }
  }

  if (!response.ok) {
    const payload = await parseBody(response);
    throw new ApiError(
      extractMessage(payload, response.status),
      response.status,
      payload,
    );
  }

  return {
    data: (await parseBody(response)) as T,
    nextCursor: response.headers.get("X-Next-Cursor"),
  };
}
