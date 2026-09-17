"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Surface the failure in the browser console for debugging.
    console.error("Unhandled application error:", error);
  }, [error]);

  return (
    <html lang="ar" dir="rtl">
      <body
        style={{
          margin: 0,
          minHeight: "100dvh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "1.25rem",
          padding: "2rem",
          textAlign: "center",
          fontFamily: "system-ui, sans-serif",
          background: "#F4F4F4",
          color: "#0C0C0C",
        }}
      >
        <p style={{ fontSize: "2rem", margin: 0, color: "#FF5900" }}>مخمخ</p>

        <h1 style={{ fontSize: "1.35rem", margin: 0 }}>
          حصلت مشكلة غير متوقّعة
        </h1>

        <p style={{ margin: 0, color: "#6f6357", maxWidth: "28rem" }}>
          Something went wrong while rendering the application. You can try again.
        </p>

        <button
          type="button"
          onClick={reset}
          style={{
            border: "none",
            borderRadius: "999px",
            background: "#FF5900",
            color: "white",
            padding: "0.75rem 1.75rem",
            fontSize: "0.95rem",
            cursor: "pointer",
          }}
        >
          إعادة المحاولة
        </button>
      </body>
    </html>
  );
}
