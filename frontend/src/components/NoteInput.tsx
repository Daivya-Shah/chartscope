import {
  AlertCircle,
  FileText,
  Loader2,
  Shuffle,
  Sparkles,
} from "lucide-react";
import { useCallback, useEffect, useState, type ReactNode } from "react";
import { getExamples, getRandomNote, getSpecialties } from "../lib/api";
import { DEFAULT_EXAMPLE_ID } from "../lib/constants";
import type { ExampleNote, SpecialtyCount } from "../types/api";

export type NoteSourceMode = "example" | "random" | "paste";

interface NoteInputProps {
  noteText: string;
  claimedCodes: string;
  onNoteTextChange: (text: string) => void;
  onClaimedCodesChange: (codes: string) => void;
  onAnalyze: () => void;
  loading: boolean;
  error: string | null;
}

export default function NoteInput({
  noteText,
  claimedCodes,
  onNoteTextChange,
  onClaimedCodesChange,
  onAnalyze,
  loading,
  error,
}: NoteInputProps) {
  const [mode, setMode] = useState<NoteSourceMode>("example");
  const [examples, setExamples] = useState<ExampleNote[]>([]);
  const [selectedExampleId, setSelectedExampleId] = useState(DEFAULT_EXAMPLE_ID);
  const [specialties, setSpecialties] = useState<SpecialtyCount[]>([]);
  const [selectedSpecialty, setSelectedSpecialty] = useState("");
  const [initError, setInitError] = useState<string | null>(null);
  const [randomLoading, setRandomLoading] = useState(false);

  const applyExample = useCallback(
    (example: ExampleNote) => {
      onNoteTextChange(example.note_text);
      onClaimedCodesChange(example.claimed_codes.join(", "));
    },
    [onNoteTextChange, onClaimedCodesChange],
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [ex, specs] = await Promise.all([getExamples(), getSpecialties()]);
        if (cancelled) return;
        setExamples(ex);
        setSpecialties(specs);
        if (specs.length > 0) setSelectedSpecialty(specs[0].specialty);
        const defaultEx =
          ex.find((e) => e.id === DEFAULT_EXAMPLE_ID) ?? ex[1] ?? ex[0];
        if (defaultEx) {
          setSelectedExampleId(defaultEx.id);
          applyExample(defaultEx);
        }
      } catch {
        if (!cancelled) setInitError("Could not load examples or specialties.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [applyExample]);

  const handleExampleChange = (id: string) => {
    setSelectedExampleId(id);
    const ex = examples.find((e) => e.id === id);
    if (ex) applyExample(ex);
  };

  const loadRandom = async () => {
    setRandomLoading(true);
    setInitError(null);
    try {
      const note = await getRandomNote(selectedSpecialty || undefined);
      onNoteTextChange(note.transcription);
      onClaimedCodesChange("");
    } catch {
      setInitError("Failed to load a random MTSamples note.");
    } finally {
      setRandomLoading(false);
    }
  };

  const modeButton = (value: NoteSourceMode, label: string, icon: ReactNode) => (
    <button
      type="button"
      onClick={() => setMode(value)}
      className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
        mode === value
          ? "bg-clinical-600 text-white shadow-sm"
          : "bg-clinical-50 text-clinical-600 ring-1 ring-clinical-200 hover:bg-clinical-100"
      }`}
    >
      {icon}
      {label}
    </button>
  );

  return (
    <div className="panel">
      <div className="panel-header flex flex-wrap items-center gap-2">
        <FileText className="h-4 w-4 text-clinical-500" />
        <h2 className="text-sm font-semibold text-clinical-800">Clinical Note Input</h2>
      </div>

      <div className="space-y-4 p-5">
        <div className="flex flex-wrap gap-2">
          {modeButton("example", "Example note", <Sparkles className="h-3.5 w-3.5" />)}
          {modeButton("random", "Random MTSamples", <Shuffle className="h-3.5 w-3.5" />)}
          {modeButton("paste", "Paste your own", <FileText className="h-3.5 w-3.5" />)}
        </div>

        {mode === "example" && examples.length > 0 && (
          <div>
            <label className="mb-1.5 block text-xs font-medium text-clinical-600">
              Select example
            </label>
            <select
              value={selectedExampleId}
              onChange={(e) => handleExampleChange(e.target.value)}
              className="w-full rounded-lg border border-clinical-200 bg-white px-3 py-2 text-sm text-clinical-800 shadow-sm focus:border-clinical-400 focus:outline-none focus:ring-2 focus:ring-clinical-200"
            >
              {examples.map((ex) => (
                <option key={ex.id} value={ex.id}>
                  {ex.title} — {ex.specialty}
                </option>
              ))}
            </select>
            {examples.find((e) => e.id === selectedExampleId)?.description && (
              <p className="mt-1.5 text-xs text-clinical-500">
                {examples.find((e) => e.id === selectedExampleId)?.description}
              </p>
            )}
          </div>
        )}

        {mode === "random" && (
          <div className="flex flex-wrap items-end gap-3">
            <div className="min-w-[200px] flex-1">
              <label className="mb-1.5 block text-xs font-medium text-clinical-600">
                Specialty
              </label>
              <select
                value={selectedSpecialty}
                onChange={(e) => setSelectedSpecialty(e.target.value)}
                className="w-full rounded-lg border border-clinical-200 bg-white px-3 py-2 text-sm text-clinical-800 shadow-sm focus:border-clinical-400 focus:outline-none focus:ring-2 focus:ring-clinical-200"
              >
                {specialties.map((s) => (
                  <option key={s.specialty} value={s.specialty}>
                    {s.specialty} ({s.count})
                  </option>
                ))}
              </select>
            </div>
            <button
              type="button"
              onClick={loadRandom}
              disabled={randomLoading}
              className="inline-flex items-center gap-2 rounded-lg bg-clinical-100 px-4 py-2 text-sm font-medium text-clinical-700 ring-1 ring-clinical-200 hover:bg-clinical-200 disabled:opacity-60"
            >
              {randomLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Shuffle className="h-4 w-4" />
              )}
              Load random note
            </button>
          </div>
        )}

        <div>
          <label className="mb-1.5 block text-xs font-medium text-clinical-600">
            Note text
          </label>
          <textarea
            value={noteText}
            onChange={(e) => onNoteTextChange(e.target.value)}
            rows={10}
            placeholder="Paste or load a clinical note…"
            className="w-full resize-y rounded-lg border border-clinical-200 bg-white px-3 py-2.5 font-mono text-sm leading-relaxed text-clinical-800 shadow-sm focus:border-clinical-400 focus:outline-none focus:ring-2 focus:ring-clinical-200"
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-medium text-clinical-600">
            Claimed ICD-10 codes
            <span className="ml-1 font-normal text-clinical-400">(comma-separated)</span>
          </label>
          <input
            type="text"
            value={claimedCodes}
            onChange={(e) => onClaimedCodesChange(e.target.value)}
            placeholder="e.g. I10, E11.9"
            className="w-full rounded-lg border border-clinical-200 bg-white px-3 py-2 text-sm text-clinical-800 shadow-sm focus:border-clinical-400 focus:outline-none focus:ring-2 focus:ring-clinical-200"
          />
        </div>

        {(error || initError) && (
          <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-800">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error ?? initError}</span>
          </div>
        )}

        <button
          type="button"
          onClick={onAnalyze}
          disabled={loading || !noteText.trim()}
          className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-clinical-600 to-clinical-700 px-5 py-3 text-sm font-semibold text-white shadow-md transition hover:from-clinical-700 hover:to-clinical-800 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Analyzing… first run may take a minute
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              Analyze note
            </>
          )}
        </button>
      </div>
    </div>
  );
}
