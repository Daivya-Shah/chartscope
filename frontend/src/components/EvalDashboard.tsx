import { AlertCircle, BarChart3, Loader2, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getEval } from "../lib/api";
import type { FinetuneMetrics } from "../types/api";

function shortModel(name: string): string {
  if (name.includes("BiomedBERT")) return "Fine-tuned PubMedBERT";
  if (name.includes("d4data")) return "d4data baseline";
  const parts = name.split("/");
  return parts[parts.length - 1] ?? name;
}

export default function EvalDashboard() {
  const [metrics, setMetrics] = useState<FinetuneMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await getEval();
        if (!cancelled) setMetrics(data);
      } catch {
        if (!cancelled) setError("Could not load evaluation metrics from /api/eval.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[280px] flex-col items-center justify-center gap-3 text-clinical-500">
        <Loader2 className="h-8 w-8 animate-spin text-clinical-400" />
        <p className="text-sm">Loading NER evaluation metrics…</p>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="flex min-h-[280px] flex-col items-center justify-center rounded-lg border border-dashed border-clinical-200 bg-clinical-50/40 p-8 text-center">
        <AlertCircle className="mb-3 h-10 w-10 text-clinical-300" />
        <p className="text-sm text-clinical-600">{error ?? "No metrics available."}</p>
      </div>
    );
  }

  const baseline = metrics.baseline;
  const advantage = metrics.comparison?.finetuned_advantage ?? metrics.f1 - (baseline?.f1 ?? 0);

  const chartData = [
    {
      metric: "Precision",
      finetuned: metrics.precision,
      baseline: baseline?.precision ?? 0,
    },
    {
      metric: "Recall",
      finetuned: metrics.recall,
      baseline: baseline?.recall ?? 0,
    },
    {
      metric: "F1",
      finetuned: metrics.f1,
      baseline: baseline?.f1 ?? 0,
    },
  ];

  const tableRows = [
    {
      label: "Fine-tuned",
      model: shortModel(metrics.model),
      precision: metrics.precision,
      recall: metrics.recall,
      f1: metrics.f1,
    },
    ...(baseline
      ? [
          {
            label: "Baseline",
            model: shortModel(baseline.model),
            precision: baseline.precision,
            recall: baseline.recall,
            f1: baseline.f1,
          },
        ]
      : []),
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-clinical-200 bg-gradient-to-br from-clinical-50 to-white p-5 shadow-sm">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-clinical-500">
              NCBI-Disease NER · entity-level strict F1
            </p>
            <p className="mt-1 font-display text-4xl font-bold text-clinical-900">
              {metrics.f1.toFixed(3)}
            </p>
            <p className="mt-1 text-sm text-clinical-600">Fine-tuned F1 score</p>
          </div>
          {baseline && (
            <div className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-white shadow-md">
              <TrendingUp className="h-5 w-5" />
              <span className="font-display text-lg font-semibold">
                +{advantage.toFixed(3)} F1 advantage over baseline
              </span>
            </div>
          )}
        </div>
      </div>

      {baseline && (
        <div className="rounded-xl border border-clinical-200 bg-white p-4">
          <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-clinical-800">
            <BarChart3 className="h-4 w-4" />
            Precision / Recall / F1 comparison
          </h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#daedf3" />
                <XAxis dataKey="metric" tick={{ fontSize: 12, fill: "#326a82" }} />
                <YAxis
                  domain={[0, 1]}
                  tick={{ fontSize: 11, fill: "#559fb8" }}
                  tickFormatter={(v) => v.toFixed(2)}
                />
                <Tooltip
                  formatter={(value: number) => value.toFixed(4)}
                  contentStyle={{
                    borderRadius: "0.5rem",
                    border: "1px solid #b8dbe8",
                    fontSize: "12px",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: "12px" }} />
                <Bar
                  dataKey="finetuned"
                  name="Fine-tuned PubMedBERT"
                  fill="#3a839e"
                  radius={[4, 4, 0, 0]}
                />
                <Bar
                  dataKey="baseline"
                  name="d4data baseline"
                  fill="#94a3b8"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-clinical-200">
        <table className="w-full min-w-[480px] text-left text-sm">
          <thead className="border-b border-clinical-200 bg-clinical-50 text-xs font-semibold uppercase tracking-wide text-clinical-500">
            <tr>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3">Precision</th>
              <th className="px-4 py-3">Recall</th>
              <th className="px-4 py-3">F1</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-clinical-100">
            {tableRows.map((row) => (
              <tr key={row.label} className="bg-white">
                <td className="px-4 py-3">
                  <span className="font-medium text-clinical-900">{row.label}</span>
                  <p className="text-xs text-clinical-500">{row.model}</p>
                </td>
                <td className="px-4 py-3 tabular-nums text-clinical-700">
                  {row.precision.toFixed(4)}
                </td>
                <td className="px-4 py-3 tabular-nums text-clinical-700">
                  {row.recall.toFixed(4)}
                </td>
                <td className="px-4 py-3 tabular-nums font-semibold text-clinical-900">
                  {row.f1.toFixed(4)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs leading-relaxed text-clinical-500">
        PubMedBERT fine-tuned on NCBI-Disease ({metrics.epochs} epoch
        {metrics.epochs === 1 ? "" : "s"}), entity-level strict F1 via seqeval, evaluated
        against d4data/biomedical-ner-all on the same test split. The baseline scores lower
        partly because its broader multi-type label scheme is penalized under strict
        single-type span matching — task-specific fine-tuning on the target annotation
        scheme is the point.
      </p>
    </div>
  );
}
