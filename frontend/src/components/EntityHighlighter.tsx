import { Highlighter } from "lucide-react";

export default function EntityHighlighter() {
  return (
    <div className="panel">
      <div className="panel-header flex items-center gap-2">
        <Highlighter className="h-4 w-4 text-clinical-500" />
        <h2 className="text-sm font-semibold text-clinical-800">Entity Highlights</h2>
        <span className="placeholder-badge ml-auto">Coming soon</span>
      </div>
      <div className="p-5">
        <div className="flex h-32 items-center justify-center rounded-lg bg-clinical-50/50">
          <p className="text-sm text-clinical-400">
            NER entities with negation &amp; temporality overlays
          </p>
        </div>
      </div>
    </div>
  );
}
