import {
  AlertTriangle,
  BarChart3,
  Code2,
  Highlighter,
  Layers,
} from "lucide-react";
import type { ReactNode } from "react";
import EntityHighlighter from "./EntityHighlighter";
import ErrorBanner from "./ErrorBanner";
import EvalDashboard from "./EvalDashboard";
import FhirViewer from "./FhirViewer";
import GapsPanel from "./GapsPanel";
import ResultsSkeleton from "./ResultsSkeleton";
import type { AnalyzeResponse } from "../types/api";

export type ResultsTab = "extraction" | "gaps" | "fhir" | "evaluation";

interface ResultsTabsProps {
  activeTab: ResultsTab;
  onTabChange: (tab: ResultsTab) => void;
  result: AnalyzeResponse | null;
  claimedCodes: string;
  onClaimedCodesChange: (codes: string) => void;
  onReanalyze: () => void;
  loading: boolean;
  error: string | null;
}

const TABS: { id: ResultsTab; label: string; icon: ReactNode }[] = [
  { id: "extraction", label: "Extraction", icon: <Highlighter className="h-4 w-4" /> },
  { id: "gaps", label: "Coding Gaps", icon: <Layers className="h-4 w-4" /> },
  { id: "fhir", label: "FHIR", icon: <Code2 className="h-4 w-4" /> },
  { id: "evaluation", label: "Evaluation", icon: <BarChart3 className="h-4 w-4" /> },
];

export default function ResultsTabs({
  activeTab,
  onTabChange,
  result,
  claimedCodes,
  onClaimedCodesChange,
  onReanalyze,
  loading,
  error,
}: ResultsTabsProps) {
  const needsAnalysis = activeTab === "extraction" || activeTab === "gaps" || activeTab === "fhir";

  return (
    <div className="panel min-h-[420px]">
      <div className="border-b border-clinical-100 bg-clinical-50/50 px-2 pt-2">
        <nav className="flex gap-1 overflow-x-auto" role="tablist">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`inline-flex shrink-0 items-center gap-2 rounded-t-lg px-3 py-2.5 text-sm font-medium transition-colors sm:px-4 ${
                activeTab === tab.id
                  ? "bg-white text-clinical-800 shadow-sm ring-1 ring-clinical-200 ring-b-white"
                  : "text-clinical-500 hover:bg-white/60 hover:text-clinical-700"
              }`}
            >
              {tab.icon}
              <span className="hidden sm:inline">{tab.label}</span>
              {tab.id === "gaps" && result && result.gaps.length > 0 && (
                <span className="rounded-full bg-clinical-600 px-1.5 py-0.5 text-[10px] font-semibold text-white">
                  {result.gaps.length}
                </span>
              )}
              {tab.id === "fhir" && result?.fhir_valid && (
                <span className="h-2 w-2 rounded-full bg-emerald-500" title="Valid FHIR" />
              )}
            </button>
          ))}
        </nav>
      </div>

      <div className="p-4 sm:p-5">
        {error && !loading && <ErrorBanner message={error} />}

        {loading ? (
          <ResultsSkeleton />
        ) : (
          <>
            {activeTab === "extraction" && <EntityHighlighter result={result} />}
            {activeTab === "gaps" && (
              <GapsPanel
                result={result}
                claimedCodes={claimedCodes}
                onClaimedCodesChange={onClaimedCodesChange}
                onReanalyze={onReanalyze}
                loading={loading}
              />
            )}
            {activeTab === "fhir" && <FhirViewer result={result} />}
            {activeTab === "evaluation" && <EvalDashboard />}

            {needsAnalysis && !result && !error && (
              <div className="mt-4 flex items-center gap-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800 ring-1 ring-amber-200">
                <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                Select an example note and click Analyze to populate this tab.
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
