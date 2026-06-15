import { Code2 } from "lucide-react";

export default function FhirViewer() {
  return (
    <div className="panel">
      <div className="panel-header flex items-center gap-2">
        <Code2 className="h-4 w-4 text-clinical-500" />
        <h2 className="text-sm font-semibold text-clinical-800">FHIR Bundle Export</h2>
        <span className="placeholder-badge ml-auto">Coming soon</span>
      </div>
      <div className="p-5">
        <div className="flex h-32 items-center justify-center rounded-lg bg-clinical-950/5 font-mono text-sm text-clinical-400">
          {"{ \"resourceType\": \"Bundle\", ... }"}
        </div>
      </div>
    </div>
  );
}
