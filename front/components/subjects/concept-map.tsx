"use client";

import { Check, Circle, Lock, Timer } from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Concept, CourseGraph } from "@/lib/api/types";
import { cn } from "@/lib/utils";

type ConceptMapProps = {
  concepts: Concept[];
  graph?: CourseGraph;
  completedConceptIds: Set<string>;
  onComplete: (conceptId: string) => void;
  completingId?: string | null;
};

type Enriched = {
  concept: Concept;
  module: string | null;
  difficulty: string | null;
  estimatedMinutes: number | null;
  locked: boolean;
  prerequisites: string[];
};

export function ConceptMap({
  concepts,
  graph,
  completedConceptIds,
  onComplete,
  completingId,
}: ConceptMapProps) {
  const t = useTranslations("subjects.detail");

  const enriched = React.useMemo<Enriched[]>(() => {
    const nodeByTitle = new Map(
      (graph?.nodes ?? []).map((node) => [node.title.trim().toLowerCase(), node]),
    );

    const idByTitle = new Map(
      (graph?.nodes ?? []).map((node) => [
        node.title.trim().toLowerCase(),
        node.node_id,
      ]),
    );

    // Build prerequisite links keyed by graph node ids.
    const prerequisiteIdsByNode = new Map<string, string[]>();

    for (const edge of graph?.edges ?? []) {
      if (edge.relation !== "prerequisite") continue;

      const existing = prerequisiteIdsByNode.get(edge.to_node) ?? [];
      existing.push(edge.from_node);
      prerequisiteIdsByNode.set(edge.to_node, existing);
    }

    const completedNodeIds = new Set<string>();

    for (const concept of concepts) {
      if (!completedConceptIds.has(concept.id)) continue;

      const nodeId = idByTitle.get(concept.name.trim().toLowerCase());
      if (nodeId) completedNodeIds.add(nodeId);
    }

    return concepts.map((concept) => {
      const key = concept.name.trim().toLowerCase();
      const node = nodeByTitle.get(key);
      const nodeId = idByTitle.get(key);

      const prerequisites = nodeId
        ? prerequisiteIdsByNode.get(nodeId) ?? []
        : [];

      const titleByNodeId = new Map(
        (graph?.nodes ?? []).map((item) => [item.node_id, item.title]),
      );

      return {
        concept,
        module: node?.module ?? null,
        difficulty: node?.difficulty ?? null,
        estimatedMinutes: node?.estimated_minutes ?? null,
        locked: prerequisites.some((id) => !completedNodeIds.has(id)),
        prerequisites: prerequisites.map(
          (id) => titleByNodeId.get(id) ?? "",
        ).filter(Boolean),
      };
    });
  }, [concepts, graph, completedConceptIds]);

  return (
    <ol className="relative space-y-3">
      {enriched.map((item, index) => {
        const done = completedConceptIds.has(item.concept.id);
        const isCompleting = completingId === item.concept.id;

        return (
          <li key={item.concept.id} className="relative">
            {/* Connector between steps, drawn behind the marker. */}
            {index < enriched.length - 1 ? (
              <span
                aria-hidden
                className={cn(
                  "absolute start-[1.4rem] top-12 h-[calc(100%-1.5rem)] w-px",
                  done ? "bg-brand-500/40" : "bg-cocoa-800/12",
                )}
              />
            ) : null}

            <article
              className={cn(
                "relative flex gap-4 rounded-2xl border bg-white p-4 transition duration-300",
                done
                  ? "border-brand-500/30 bg-brand-50/40"
                  : "border-cocoa-800/10 hover:border-brand-500/25 hover:shadow-soft",
              )}
            >
              <span
                className={cn(
                  "z-10 flex size-11 shrink-0 items-center justify-center rounded-2xl text-sm font-medium",
                  done
                    ? "brand-gradient-surface text-white"
                    : item.locked
                      ? "bg-muted text-muted-fg"
                      : "bg-white text-cocoa-800 ring-1 ring-cocoa-800/12",
                )}
              >
                {done ? (
                  <Check aria-hidden className="size-5" />
                ) : item.locked ? (
                  <Lock aria-hidden className="size-4" />
                ) : (
                  <span className="tabular">{index + 1}</span>
                )}
              </span>

              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-display text-base text-cocoa-900 break-arabic">
                    {item.concept.name}
                  </h3>

                  {done ? (
                    <Badge tone="success">{t("completedBadge")}</Badge>
                  ) : null}

                  {item.module ? (
                    <Badge tone="neutral">{item.module}</Badge>
                  ) : null}

                  {item.difficulty ? (
                    <Badge tone="yellow">{item.difficulty}</Badge>
                  ) : null}
                </div>

                {item.concept.description ? (
                  <p className="mt-1.5 text-sm leading-relaxed text-muted-fg break-arabic">
                    {item.concept.description}
                  </p>
                ) : null}

                <div className="mt-2.5 flex flex-wrap items-center gap-x-4 gap-y-1.5">
                  {item.estimatedMinutes ? (
                    <span className="inline-flex items-center gap-1.5 text-xs text-muted-fg">
                      <Timer aria-hidden className="size-3.5" />
                      <span className="tabular">{item.estimatedMinutes}</span>
                    </span>
                  ) : null}

                  {item.prerequisites.length ? (
                    <span className="inline-flex items-center gap-1.5 text-xs text-muted-fg break-arabic">
                      <Circle aria-hidden className="size-2.5" />
                      {t("prerequisiteBadge")}: {item.prerequisites.join(" · ")}
                    </span>
                  ) : null}
                </div>
              </div>

              <div className="flex items-center">
                {done ? null : (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={item.locked}
                    loading={isCompleting}
                    loadingText={t("markingComplete")}
                    onClick={() => onComplete(item.concept.id)}
                  >
                    {t("markComplete")}
                  </Button>
                )}
              </div>
            </article>
          </li>
        );
      })}
    </ol>
  );
}
