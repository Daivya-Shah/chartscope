import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Loader2,
  RefreshCw,
  TrendingUp,
} from "lucide-react";
import { GAP_STATUS_CONFIG, GAP_STATUS_ORDER, type GapStatus } from "../lib/constants";
import type { AnalyzeResponse, HccGap } from "../types/api";

interface GapsPanelProps {
  result: AnalyzeResponse | null;
  claimedCodes: string;
  onClaimedCodesChange: (codes: string) => void;
  onReanalyze: () => void;
  loading: boolean;
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-clinical-100">
        <div
          className="h-full rounded-full bg-clinical-500 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs tabular-nums text-clinical-500">{pct}%</span>
    </div>
  );
}

function GapCard({ gap }: { gap: HccGap }) {
  const status = (gap.status in GAP_STATUS_CONFIG ? gap.status : "confirmed") as GapStatus;
  const cfg = GAP_STATUS_CONFIG[status];

  return (
    <article
      className={`rounded-xl border p-4 shadow-sm ${cfg.border} ${cfg.bg}`}
    >
      <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${cfg.dot}`} />
            <span className={`rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${cfg.badge}`}>
              {cfg.label}
            </span>
          </div>
          <h4 className="mt-2 font-display text-base font-semibold text-clinical-900">
            HCC {gap.hcc}
            <span className="ml-2 font-normal text-clinical-600">— {gap.label}</span>
          </h4>
        </div>
        {gap.icd10 && (
          <code className="rounded-lg bg-white/80 px-2 py-1 text-xs font-semibold text-clinical-700 ring-1 ring-clinical-200">
            {gap.icd10}
          </code>
        )}
      </div>

      <div className="mb-3 rounded-lg bg-white/70 px-3 py-2 text-sm text-clinical-700">
        <span className="text-xs font-medium uppercase tracking-wide text-clinical-400">
          MEAT evidence
        </span>
        <p className="mt-1 leading-relaxed">{gap.evidence}</p>
      </div>

      <div className="mb-3">
        <span className="text-xs font-medium text-clinical-500">Confidence</span>
        <ConfidenceBar value={gap.confidence} />
      </div>

      {gap.recommendation && (
        <p className="rounded-lg border border-white/80 bg-white/60 px-3 py-2 text-sm leading-relaxed text-clinical-800">
          {gap.recommendation}
        </p>
      )}
    </article>
  );
}

export default function GapsPanel({
  result,
  claimedCodes,
  onClaimedCodesChange,
  onReanalyze,
  loading,
}: GapsPanelProps) {
  if (!result) {
    return (
      <div className="flex h-64 flex-col items-center justify-center rounded-lg border border-dashed border-clinical-200 bg-clinical-50/40 text-center">
        <AlertTriangle className="mb-2 h-8 w-8 text-clinical-300" />
        <p className="text-sm text-clinical-500">
          Coding gaps and RAF impact will appear here after analysis.
        </p>
      </div>
    );
  }

  const delta = result.risk_score_delta;
  const positive = delta > 0.001;
  const neutral = Math.abs(delta) <= 0.001;
  const sexLabel = result.demographics.sex === "F" ? "Female" : result.demographics.sex === "M" ? "Male" : result.demographics.sex;

  const grouped = GAP_STATUS_ORDER.reduce(
    (acc, status) => {
      acc[status] = result.gaps.filter((g) => g.status === status);
      return acc;
    },
    {} as Record<GapStatus, HccGap[]>,
  );

  return (
    <div className="space-y-6">
      <div
        className={`rounded-xl border p-5 shadow-sm ${
          positive
            ? "border-emerald-200 bg-gradient-to-br from-emerald-50 to-white"
            : "border-clinical-200 bg-gradient-to-br from-clinical-50 to-white"
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-clinical-500">
              CMS-HCC V28 Risk Adjustment Factor
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-3 font-display text-2xl font-semibold text-clinical-900">
              <span>{result.risk_score_current.toFixed(2)}</span>
              <ArrowRight className="h-5 w-5 text-clinical-400" />
              <span>{result.risk_score_potential.toFixed(2)}</span>
            </div>
            <p className="mt-1 text-xs text-clinical-500">
              Demographics used: {result.demographics.age} y/o {sexLabel}
            </p>
          </div>

          <div className="text-right">
            {positive && (
              <div className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2 text-white shadow-md">
                <TrendingUp className="h-5 w-5" />
                <span className="font-display text-xl font-bold">
                  +{delta.toFixed(2)} RAF
                </span>
              </div>
            )}
            {neutral && (
              <div className="inline-flex items-center gap-1.5 rounded-xl bg-clinical-200 px-4 py-2 text-clinical-700">
                <CheckCircle2 className="h-5 w-5" />
                <span className="font-display text-lg font-semibold">No RAF change</span>
              </div>
            )}
            {!positive && !neutral && (
              <div className="inline-flex rounded-xl bg-clinical-100 px-4 py-2 font-display text-lg font-semibold text-clinical-700">
                {delta.toFixed(2)} RAF
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-clinical-200 bg-white p-4">
        <label className="mb-1.5 block text-xs font-medium text-clinical-600">
          Edit claimed codes &amp; re-analyze
        </label>
        <div className="flex flex-wrap gap-2">
          <input
            type="text"
            value={claimedCodes}
            onChange={(e) => onClaimedCodesChange(e.target.value)}
            className="min-w-[200px] flex-1 rounded-lg border border-clinical-200 px-3 py-2 text-sm focus:border-clinical-400 focus:outline-none focus:ring-2 focus:ring-clinical-200"
          />
          <button
            type="button"
            onClick={onReanalyze}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg bg-clinical-600 px-4 py-2 text-sm font-medium text-white hover:bg-clinical-700 disabled:opacity-60"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Re-analyze
          </button>
        </div>
      </div>

      {GAP_STATUS_ORDER.map((status) => {
        const gaps = grouped[status];
        if (gaps.length === 0) return null;
        const cfg = GAP_STATUS_CONFIG[status];
        return (
          <section key={status}>
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-clinical-800">
              <span className={`h-2 w-2 rounded-full ${cfg.dot}`} />
              {cfg.label}
              <span className="font-normal text-clinical-400">({gaps.length})</span>
            </h3>
            <div className="space-y-3">
              {gaps.map((gap) => (
                <GapCard key={`${gap.hcc}-${gap.status}-${gap.icd10}`} gap={gap} />
              ))}
            </div>
          </section>
        );
      })}

      {result.gaps.length === 0 && (
        <p className="text-center text-sm text-clinical-500">No HCC gaps detected.</p>
      )}
    </div>
  );
}
