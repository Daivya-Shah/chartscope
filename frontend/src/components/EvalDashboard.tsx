import { BarChart3 } from "lucide-react";

export default function EvalDashboard() {
  return (
    <div className="flex min-h-[280px] flex-col items-center justify-center rounded-lg border border-dashed border-clinical-200 bg-clinical-50/40 p-8 text-center">
      <BarChart3 className="mb-3 h-10 w-10 text-clinical-300" />
      <h3 className="font-display text-lg font-semibold text-clinical-800">
        Model Evaluation
      </h3>
      <p className="mt-2 max-w-md text-sm text-clinical-500">
        Fine-tuned BiomedBERT vs d4data baseline on NCBI-Disease — metrics loaded from{" "}
        <code className="rounded bg-clinical-100 px-1 text-clinical-600">/api/eval</code>.
        Full dashboard coming in the next build step.
      </p>
    </div>
  );
}
