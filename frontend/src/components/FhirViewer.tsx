import {
  AlertCircle,
  CheckCircle2,
  Code2,
  Copy,
  Download,
  FileJson,
} from "lucide-react";
import JsonPanel from "./JsonPanel";
import {
  bundleEntryCount,
  countResourceTypes,
  downloadJson,
  useCopyToClipboard,
} from "../lib/fhir";
import type { AnalyzeResponse } from "../types/api";

interface FhirViewerProps {
  result: AnalyzeResponse | null;
}

export default function FhirViewer({ result }: FhirViewerProps) {
  const { copied, copy } = useCopyToClipboard();

  if (!result) {
    return (
      <div className="flex min-h-[280px] flex-col items-center justify-center rounded-lg border border-dashed border-clinical-200 bg-clinical-50/40 p-8 text-center">
        <Code2 className="mb-3 h-10 w-10 text-clinical-300" />
        <h3 className="font-display text-lg font-semibold text-clinical-800">FHIR Export</h3>
        <p className="mt-2 max-w-md text-sm text-clinical-500">
          Run analysis to generate a FHIR R4 collection bundle from the note.
        </p>
      </div>
    );
  }

  const bundle = result.fhir_bundle;
  const entryCount = bundleEntryCount(bundle);
  const typeCounts = countResourceTypes(bundle);
  const jsonText = JSON.stringify(bundle, null, 2);

  return (
    <div className="space-y-4">
      <p className="text-sm text-clinical-600">
        Unstructured note → normalized FHIR R4 (US Core / Da Vinci profiles)
      </p>

      <div className="flex flex-wrap items-center gap-2">
        {result.fhir_valid ? (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800 ring-1 ring-emerald-200">
            <CheckCircle2 className="h-3.5 w-3.5" />
            FHIR R4 · valid
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-800 ring-1 ring-red-200">
            <AlertCircle className="h-3.5 w-3.5" />
            FHIR R4 · invalid
          </span>
        )}
        <span className="rounded-full bg-clinical-100 px-3 py-1 text-xs font-medium text-clinical-700 ring-1 ring-clinical-200">
          {entryCount} {entryCount === 1 ? "entry" : "entries"}
        </span>
      </div>

      {!result.fhir_valid && result.fhir_errors.length > 0 && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">
          <p className="mb-1 font-medium">Validation errors</p>
          <ul className="list-inside list-disc space-y-0.5">
            {result.fhir_errors.map((err, i) => (
              <li key={i} className="break-all font-mono">
                {err}
              </li>
            ))}
          </ul>
        </div>
      )}

      {Object.keys(typeCounts).length > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(typeCounts)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([type, count]) => (
              <span
                key={type}
                className="inline-flex items-center gap-1 rounded-lg bg-white px-2.5 py-1 text-xs font-medium text-clinical-700 ring-1 ring-clinical-200"
              >
                <FileJson className="h-3 w-3 text-clinical-400" />
                {type} ×{count}
              </span>
            ))}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => copy(jsonText)}
          className="inline-flex items-center gap-2 rounded-lg bg-clinical-100 px-3 py-2 text-sm font-medium text-clinical-700 ring-1 ring-clinical-200 hover:bg-clinical-200"
        >
          <Copy className="h-4 w-4" />
          {copied ? "Copied!" : "Copy JSON"}
        </button>
        <button
          type="button"
          onClick={() => downloadJson(bundle, "chartscope-fhir-bundle.json")}
          className="inline-flex items-center gap-2 rounded-lg bg-clinical-600 px-3 py-2 text-sm font-medium text-white hover:bg-clinical-700"
        >
          <Download className="h-4 w-4" />
          Download bundle (.json)
        </button>
      </div>

      <JsonPanel data={bundle} />
    </div>
  );
}
