import { Shield, Stethoscope } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { DEFAULT_ENTITY_COLOR, ENTITY_COLORS } from "../lib/constants";
import {
  buildHighlightSegments,
  entityAssertionTags,
  isMutedEntity,
  linkedCodeLabel,
} from "../lib/entityHighlight";
import type { AnalyzeResponse, Entity } from "../types/api";

interface EntityHighlighterProps {
  result: AnalyzeResponse | null;
}

function EntityPopover({
  entity,
  anchorRect,
}: {
  entity: Entity;
  anchorRect: DOMRect;
}) {
  const tags = entityAssertionTags(entity);
  const linked = linkedCodeLabel(entity);
  const popoverRef = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ top: 0, left: 0 });

  useEffect(() => {
    const el = popoverRef.current;
    const width = el?.offsetWidth ?? 288;
    const height = el?.offsetHeight ?? 160;
    const margin = 8;
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    let top = anchorRect.bottom + margin;
    let left = anchorRect.left;

    if (left + width > vw - margin) left = vw - width - margin;
    if (left < margin) left = margin;
    if (top + height > vh - margin) top = anchorRect.top - height - margin;

    setPos({ top, left });
  }, [anchorRect]);

  return createPortal(
    <div
      ref={popoverRef}
      className="pointer-events-none fixed z-[100] w-72 rounded-lg border border-clinical-200 bg-white p-3 text-xs shadow-xl"
      style={{ top: pos.top, left: pos.left }}
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="font-semibold text-clinical-900">{entity.label}</span>
        {entity.section && (
          <span className="rounded bg-clinical-100 px-1.5 py-0.5 text-clinical-600">
            {entity.section}
          </span>
        )}
      </div>
      <p className="mb-2 text-clinical-700">&ldquo;{entity.text}&rdquo;</p>
      {tags.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-1">
          {tags.map((t) => (
            <span
              key={t}
              className="rounded bg-amber-50 px-1.5 py-0.5 text-amber-700 ring-1 ring-amber-200"
            >
              {t}
            </span>
          ))}
        </div>
      )}
      {linked ? (
        <div className="border-t border-clinical-100 pt-2 text-clinical-600">
          <span className="font-medium text-clinical-800">Linked: </span>
          {linked}
          {entity.link_score != null && (
            <span className="ml-1 text-clinical-400">
              (score {(entity.link_score * 100).toFixed(0)}%)
            </span>
          )}
        </div>
      ) : (
        <p className="border-t border-clinical-100 pt-2 text-clinical-400">No terminology link</p>
      )}
    </div>,
    document.body,
  );
}

export default function EntityHighlighter({ result }: EntityHighlighterProps) {
  const [activeEntity, setActiveEntity] = useState<Entity | null>(null);
  const [anchorRect, setAnchorRect] = useState<DOMRect | null>(null);

  const showPopover = useCallback((entity: Entity, target: HTMLElement) => {
    setActiveEntity(entity);
    setAnchorRect(target.getBoundingClientRect());
  }, []);

  const hidePopover = useCallback(() => {
    setActiveEntity(null);
    setAnchorRect(null);
  }, []);

  if (!result) {
    return (
      <div className="flex h-64 flex-col items-center justify-center rounded-lg border border-dashed border-clinical-200 bg-clinical-50/40 text-center">
        <Stethoscope className="mb-2 h-8 w-8 text-clinical-300" />
        <p className="text-sm text-clinical-500">
          Run analysis to see de-identified text with highlighted entities.
        </p>
      </div>
    );
  }

  const segments = buildHighlightSegments(result.deid_text, result.entities);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-clinical-100 px-3 py-1 text-xs font-medium text-clinical-700 ring-1 ring-clinical-200">
          <Shield className="h-3.5 w-3.5" />
          PHI scrubbed: {result.deid_redactions} identifier
          {result.deid_redactions === 1 ? "" : "s"}
        </span>
      </div>

      <div className="overflow-x-auto rounded-lg border border-clinical-200 bg-white p-4">
        <p className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-clinical-800">
          {segments.map((seg, idx) => {
            if (!seg.entity) {
              return <span key={idx}>{seg.text}</span>;
            }
            const colors = ENTITY_COLORS[seg.entity.label] ?? DEFAULT_ENTITY_COLOR;
            const muted = isMutedEntity(seg.entity);
            const tags = entityAssertionTags(seg.entity);
            const isActive =
              activeEntity?.start_char === seg.entity.start_char &&
              activeEntity?.end_char === seg.entity.end_char;

            return (
              <mark
                key={idx}
                role="button"
                tabIndex={0}
                onMouseEnter={(e) => showPopover(seg.entity!, e.currentTarget)}
                onMouseLeave={hidePopover}
                onFocus={(e) => showPopover(seg.entity!, e.currentTarget)}
                onBlur={hidePopover}
                onClick={(e) => {
                  if (isActive) hidePopover();
                  else showPopover(seg.entity!, e.currentTarget);
                }}
                className={`cursor-pointer rounded px-0.5 ring-1 ring-inset ${
                  muted ? colors.muted : `${colors.bg} ${colors.text} ${colors.ring}`
                } ${isActive ? "ring-2" : ""}`}
              >
                {seg.text}
                {tags.length > 0 && (
                  <sup className="ml-0.5 text-[9px] font-medium text-amber-600">
                    {tags[0]}
                  </sup>
                )}
              </mark>
            );
          })}
        </p>
      </div>

      {activeEntity && anchorRect && (
        <EntityPopover entity={activeEntity} anchorRect={anchorRect} />
      )}

      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-clinical-500">
          Entity legend
        </h3>
        <div className="flex flex-wrap gap-2">
          {Object.entries(ENTITY_COLORS).map(([label, colors]) => (
            <span
              key={label}
              className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${colors.bg} ${colors.text} ${colors.ring}`}
            >
              {label}
            </span>
          ))}
        </div>
      </div>

      {result.key_problems.length > 0 && (
        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-clinical-500">
            Key conditions
          </h3>
          <ul className="divide-y divide-clinical-100 rounded-lg border border-clinical-200 bg-white">
            {result.key_problems.map((kp) => (
              <li key={kp.icd10} className="flex items-start gap-3 px-3 py-2.5 text-sm">
                <code className="shrink-0 rounded bg-clinical-100 px-1.5 py-0.5 text-xs font-semibold text-clinical-700">
                  {kp.icd10}
                </code>
                <div className="min-w-0">
                  <span className="font-medium text-clinical-900">{kp.text}</span>
                  {kp.icd10_desc && (
                    <p className="text-xs text-clinical-500">{kp.icd10_desc}</p>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
