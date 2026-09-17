#!/usr/bin/env node
/**
 * Verifies the frontend/backend contract.
 *
 * Every `apiRequest*` call in `lib/api/*.ts` is matched against the backend's
 * OpenAPI document, so a renamed route or a wrong HTTP method fails loudly instead
 * of surfacing as a mystery 404 in the browser.
 *
 * Usage:
 *   node scripts/check-api-contract.mjs                       # fetches /openapi.json
 *   node scripts/check-api-contract.mjs --spec ../back/_openapi.json
 *   API_URL=http://localhost:8000 node scripts/check-api-contract.mjs
 */

import { readFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? process.env.API_URL ?? "http://localhost:8000").replace(/\/$/, "");
const API_PREFIX = "/api/v1";

const SOURCE_FILES = ["lib/api/endpoints.ts", "lib/api/client.ts"];

const specArgIndex = process.argv.indexOf("--spec");
const specFile = specArgIndex === -1 ? null : process.argv[specArgIndex + 1];

const CALL_PATTERN =
  /apiRequest(?:WithMeta)?(?:<[\s\S]*?>)?\(\s*(`[^`]*`|"[^"]*")([\s\S]{0,600}?)\);/g;

const METHOD_PATTERN = /method:\s*"([A-Z]+)"/;

function normalizePath(rawPath) {
  const substituted = rawPath.replace(/\$\{[^}]*\}/g, "{param}");
  return substituted.startsWith("/") ? substituted : `/${substituted}`;
}

function matchesSpecPath(frontendPath, specPath) {
  const toPattern = (value) =>
    new RegExp(
      `^${value
        .replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
        .replace(/\\\{[^}]+\\\}/g, "[^/]+")
        .replace(/\{[^}]+\}/g, "[^/]+")}$`,
    );

  return toPattern(specPath).test(frontendPath);
}

async function loadSpec() {
  if (specFile) {
    const raw = await readFile(path.resolve(process.cwd(), specFile), "utf8");
    return JSON.parse(raw).paths ?? JSON.parse(raw);
  }

  const response = await fetch(`${API_URL}/openapi.json`).catch(
    () => null,
  );

  if (!response || !response.ok) {
    throw new Error(
      `Could not fetch the OpenAPI document from ${API_URL}. Start the backend or pass --spec <file>.`,
    );
  }

  const document = await response.json();
  return document.paths ?? {};
}

async function extractCalls() {
  const calls = [];

  for (const relative of SOURCE_FILES) {
    const filePath = path.resolve(process.cwd(), relative);
    const source = await readFile(filePath, "utf8");

    for (const match of source.matchAll(CALL_PATTERN)) {
      const [, rawPath, options] = match;
      const cleanPath = rawPath.slice(1, -1);

      if (!cleanPath.startsWith("/")) continue;

      const method = (options.match(METHOD_PATTERN)?.[1] ?? "GET").toUpperCase();

      calls.push({
        file: relative,
        path: normalizePath(cleanPath),
        method,
      });
    }
  }

  return calls;
}

function methodsOf(operations) {
  const names = Array.isArray(operations)
    ? operations
    : Object.keys(operations);

  return names
    .map((method) => String(method).toUpperCase())
    .filter((method) => method !== "PARAMETERS");
}

function main({ paths, calls }) {
  const normalizedSpec = Object.entries(paths).map(([specPath, operations]) => ({
    path: specPath.startsWith(API_PREFIX)
      ? specPath.slice(API_PREFIX.length)
      : specPath,
    methods: methodsOf(operations),
  }));

  const failures = [];
  const matched = new Set();

  for (const call of calls) {
    const candidate = normalizedSpec.find((entry) =>
      matchesSpecPath(call.path, entry.path),
    );

    if (!candidate) {
      failures.push(
        `${call.file}: ${call.method} ${call.path} — no such route in the backend`,
      );
      continue;
    }

    if (!candidate.methods.includes(call.method)) {
      failures.push(
        `${call.file}: ${call.method} ${call.path} — backend only allows ${candidate.methods.join(", ")}`,
      );
      continue;
    }

    matched.add(`${candidate.path} ${call.method}`);
  }

  console.log(`Checked ${calls.length} frontend calls against ${normalizedSpec.length} backend routes.`);

  if (failures.length) {
    console.error("\nContract mismatches:");
    for (const failure of failures) console.error(`  ✗ ${failure}`);
    process.exitCode = 1;
    return;
  }

  console.log("✓ Every frontend API call matches a backend route and method.");
}

const spec = await loadSpec();
const calls = await extractCalls();
main({ paths: spec, calls });
