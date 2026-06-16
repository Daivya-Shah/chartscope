export const ENTITY_COLORS: Record<string, { bg: string; text: string; ring: string; muted: string }> = {
  PROBLEM: {
    bg: "bg-sky-100",
    text: "text-sky-900",
    ring: "ring-sky-300",
    muted: "bg-sky-50 text-sky-500 ring-sky-200",
  },
  MEDICATION: {
    bg: "bg-violet-100",
    text: "text-violet-900",
    ring: "ring-violet-300",
    muted: "bg-violet-50 text-violet-500 ring-violet-200",
  },
  PROCEDURE: {
    bg: "bg-orange-100",
    text: "text-orange-900",
    ring: "ring-orange-300",
    muted: "bg-orange-50 text-orange-500 ring-orange-200",
  },
  TEST: {
    bg: "bg-cyan-100",
    text: "text-cyan-900",
    ring: "ring-cyan-300",
    muted: "bg-cyan-50 text-cyan-500 ring-cyan-200",
  },
  ANATOMY: {
    bg: "bg-rose-100",
    text: "text-rose-900",
    ring: "ring-rose-300",
    muted: "bg-rose-50 text-rose-500 ring-rose-200",
  },
  VITAL: {
    bg: "bg-emerald-100",
    text: "text-emerald-900",
    ring: "ring-emerald-300",
    muted: "bg-emerald-50 text-emerald-500 ring-emerald-200",
  },
};

export const DEFAULT_ENTITY_COLOR = {
  bg: "bg-clinical-100",
  text: "text-clinical-800",
  ring: "ring-clinical-300",
  muted: "bg-clinical-50 text-clinical-500 ring-clinical-200",
};

export type GapStatus = "suspected" | "superseded" | "unsupported" | "confirmed";

export const GAP_STATUS_CONFIG: Record<
  GapStatus,
  { label: string; border: string; bg: string; badge: string; dot: string }
> = {
  suspected: {
    label: "Captured opportunity",
    border: "border-emerald-200",
    bg: "bg-emerald-50/60",
    badge: "bg-emerald-100 text-emerald-800 ring-emerald-200",
    dot: "bg-emerald-500",
  },
  superseded: {
    label: "Specificity upgrade",
    border: "border-amber-200",
    bg: "bg-amber-50/60",
    badge: "bg-amber-100 text-amber-800 ring-amber-200",
    dot: "bg-amber-500",
  },
  unsupported: {
    label: "Compliance risk",
    border: "border-red-200",
    bg: "bg-red-50/60",
    badge: "bg-red-100 text-red-800 ring-red-200",
    dot: "bg-red-500",
  },
  confirmed: {
    label: "Documented & coded",
    border: "border-slate-200",
    bg: "bg-slate-50/60",
    badge: "bg-slate-100 text-slate-700 ring-slate-200",
    dot: "bg-slate-500",
  },
};

export const GAP_STATUS_ORDER: GapStatus[] = [
  "suspected",
  "superseded",
  "unsupported",
  "confirmed",
];

export const DEFAULT_EXAMPLE_ID = "ex-chf-systolic";
