import { useEffect, useState } from "react";
import AppShell from "./components/AppShell";
import EntityHighlighter from "./components/EntityHighlighter";
import EvalDashboard from "./components/EvalDashboard";
import FhirViewer from "./components/FhirViewer";
import GapsPanel from "./components/GapsPanel";
import NoteInput from "./components/NoteInput";
import { getHealth } from "./lib/api";

export default function App() {
  const [backendStatus, setBackendStatus] = useState<
    "connected" | "unreachable" | "checking"
  >("checking");

  useEffect(() => {
    getHealth()
      .then(() => setBackendStatus("connected"))
      .catch(() => setBackendStatus("unreachable"));
  }, []);

  return (
    <AppShell backendStatus={backendStatus}>
      <div className="mb-8">
        <h2 className="font-display text-2xl font-semibold text-clinical-900">
          Clinical Note Analyzer
        </h2>
        <p className="mt-1 max-w-2xl text-sm text-clinical-500">
          De-identify, extract clinical entities, detect HCC coding gaps, and export
          FHIR bundles — powered by a modular NLP pipeline.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <NoteInput />
          <EntityHighlighter />
        </div>
        <div className="space-y-6">
          <GapsPanel />
          <FhirViewer />
          <EvalDashboard />
        </div>
      </div>
    </AppShell>
  );
}
