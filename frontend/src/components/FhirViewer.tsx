import { Code2 } from "lucide-react";
import type { AnalyzeResponse } from "../types/api";

interface FhirViewerProps {
  result: AnalyzeResponse | null;
}

export default function FhirViewer({ result }: FhirViewerProps) {
  return (
    <div className="flex min-h-[280px] flex-col items-center justify-center rounded-lg border border-dashed border-clinical-200 bg-clinical-50/40 p-8 text-center">
      <Code2 className="mb-3 h-10 w-10 text-clinical-300" />
      <h3 className="font-display text-lg font-semibold text-clinical-800">FHIR Export</h3>
      <p className="mt-2 max-w-md text-sm text-clinical-500">
        R4 Bundle viewer with Patient, Condition, MedicationStatement, and RiskAssessment
        resources — coming in the next build step.
      </p>
      {result?.fhir_valid != null && (
        <p className="mt-4 text-xs text-clinical-400">
          Last bundle: {result.fhir_valid ? "valid" : "validation errors"} ·{" "}
          {(result.fhir_bundle?.entry as unknown[] | undefined)?.length ?? 0} entries
        </p>
      )}
    </div>
  );
}
