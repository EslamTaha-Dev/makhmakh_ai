import Image from "next/image";

import { cn } from "@/lib/utils";

const LOGO_WIDTH = 1000;
const LOGO_HEIGHT = 396;

/**
 * The horizontal Makhmakh lockup. Used in headers, footers and auth panels —
 * the wordmark plus mark as the brand designed it.
 */
export function BrandLogo({
  className,
  height = 40,
  priority = false,
  alt = "مخمخ",
}: {
  className?: string;
  height?: number;
  priority?: boolean;
  alt?: string;
}) {
  return (
    <Image
      src="/brand/makhmakh-logo.png"
      alt={alt}
      width={LOGO_WIDTH}
      height={LOGO_HEIGHT}
      priority={priority}
      style={{ height, width: "auto" }}
      className={cn("select-none", className)}
    />
  );
}

/** The mark on its own — for compact spaces and decorative brand moments. */
export function BrandMark({
  className,
  height = 48,
  alt = "",
}: {
  className?: string;
  height?: number;
  alt?: string;
}) {
  return (
    <Image
      src="/brand/makhmakh-mark.png"
      alt={alt}
      width={620}
      height={813}
      style={{ height, width: "auto" }}
      className={cn("select-none", className)}
    />
  );
}

/** The stacked lockup with the tagline, for hero and marketing surfaces. */
export function BrandLockup({
  className,
  height = 120,
  alt = "مخمخ",
}: {
  className?: string;
  height?: number;
  alt?: string;
}) {
  return (
    <Image
      src="/brand/makhmakh-lockup.png"
      alt={alt}
      width={820}
      height={410}
      style={{ height, width: "auto" }}
      className={cn("select-none", className)}
    />
  );
}
