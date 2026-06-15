import { FileText } from "lucide-react";

export default function NoteInput() {
  return (
    <div className="panel">
      <div className="panel-header flex items-center gap-2">
        <FileText className="h-4 w-4 text-clinical-500" />
        <h2 className="text-sm font-semibold text-clinical-800">Clinical Note Input</h2>
        <span className="placeholder-badge ml-auto">Coming soon</span>
      </div>
      <div className="p-5">
        <div className="flex h-48 items-center justify-center rounded-lg border-2 border-dashed border-clinical-200 bg-clinical-50/50">
          <p className="text-sm text-clinical-400">
            Paste or load a clinical note to analyze
          </p>
        </div>
      </div>
    </div>
  );
}
