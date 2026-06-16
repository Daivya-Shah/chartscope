import { useCallback, useEffect, useState } from "react";
import AppShell from "./components/AppShell";
import NoteInput from "./components/NoteInput";
import ResultsTabs, { type ResultsTab } from "./components/ResultsTabs";
import { analyze, getHealth, parseClaimedCodes } from "./lib/api";
import type { AnalyzeResponse } from "./types/api";

export default function App() {
  const [backendStatus, setBackendStatus] = useState<
    "connected" | "unreachable" | "checking"
  >("checking");
  const [noteText, setNoteText] = useState("");
  const [claimedCodes, setClaimedCodes] = useState("");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [activeTab, setActiveTab] = useState<ResultsTab>("extraction");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(() => setBackendStatus("connected"))
      .catch(() => setBackendStatus("unreachable"));
  }, []);

  const runAnalyze = useCallback(async () => {
    if (!noteText.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const response = await analyze({
        note_text: noteText,
        claimed_codes: parseClaimedCodes(claimedCodes),
      });
      setResult(response);
      setActiveTab("gaps");
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Analysis failed. Is the backend running?";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [noteText, claimedCodes]);

  return (
    <AppShell backendStatus={backendStatus}>
      <div className="mb-8">
        <h2 className="font-display text-2xl font-semibold text-clinical-900">
          Clinical Note Analyzer
        </h2>
        <p className="mt-1 max-w-2xl text-sm text-clinical-500">
          De-identify, extract entities, detect HCC coding gaps, and prepare FHIR
          bundles — powered by a modular clinical NLP pipeline.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <NoteInput
            noteText={noteText}
            claimedCodes={claimedCodes}
            onNoteTextChange={setNoteText}
            onClaimedCodesChange={setClaimedCodes}
            onAnalyze={runAnalyze}
            loading={loading}
            error={error}
          />
        </div>
        <div className="lg:col-span-3">
          <ResultsTabs
            activeTab={activeTab}
            onTabChange={setActiveTab}
            result={result}
            claimedCodes={claimedCodes}
            onClaimedCodesChange={setClaimedCodes}
            onReanalyze={runAnalyze}
            loading={loading}
          />
        </div>
      </div>
    </AppShell>
  );
}
