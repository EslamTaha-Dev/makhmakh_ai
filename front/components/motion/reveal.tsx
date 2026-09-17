"use client";

import { motion, useReducedMotion } from "motion/react";
import * as React from "react";

type RevealElement = "div" | "section" | "li" | "article";

type RevealProps = {
  children: React.ReactNode;
  /** Stagger delay in seconds. */
  delay?: number;
  /** Distance travelled on entry, in pixels. */
  distance?: number;
  className?: string;
  as?: RevealElement;
};

/**
 * Declared at module scope: motion components must never be created during render.
 */
const MOTION_ELEMENTS = {
  div: motion.div,
  section: motion.section,
  li: motion.li,
  article: motion.article,
} as const satisfies Record<RevealElement, unknown>;

/**
 * Subtle on-scroll reveal. Disabled entirely when the user prefers reduced motion,
 * so the educational content is never hidden behind an animation.
 */
export function Reveal({
  children,
  delay = 0,
  distance = 18,
  className,
  as = "div",
}: RevealProps) {
  const reduceMotion = useReducedMotion();
  const Component = MOTION_ELEMENTS[as];

  if (reduceMotion) {
    const Static = as;
    return <Static className={className}>{children}</Static>;
  }

  return (
    <Component
      className={className}
      initial={{ opacity: 0, y: distance }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </Component>
  );
}
