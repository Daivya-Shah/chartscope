import { Activity, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";

interface AppShellProps {
  children: ReactNode;
  backendStatus: "connected" | "unreachable" | "checking";
}

export default function AppShell({ children, backendStatus }: AppShellProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 border-b border-clinical-200/80 bg-white/90 backdrop-blur-sm">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex min-h-16 flex-wrap items-center justify-between gap-3 py-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-clinical-500 to-clinical-700 text-white shadow-sm">
                <Activity className="h-5 w-5" strokeWidth={2.25} />
              </div>
              <div>
                <h1 className="font-display text-xl font-semibold tracking-tight text-clinical-900">
                  ChartScope
                </h1>
                <p className="-mt-0.5 max-w-md text-xs leading-snug text-clinical-500">
                  Clinical NLP for Risk-Adjustment Gap Detection &amp; FHIR Upcycling
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 sm:gap-4">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-sage-50 px-3 py-1.5 text-xs font-medium text-sage-700 ring-1 ring-sage-200">
                <ShieldCheck className="h-3.5 w-3.5 shrink-0" />
                <span className="hidden sm:inline">Synthetic / public data only — HIPAA-safe</span>
                <span className="sm:hidden">HIPAA-safe demo</span>
              </span>

              <div className="flex items-center gap-2 text-sm">
                <span
                  className={`h-2.5 w-2.5 rounded-full ${
                    backendStatus === "connected"
                      ? "bg-emerald-500 shadow-[0_0_0_3px_rgba(16,185,129,0.25)]"
                      : backendStatus === "checking"
                        ? "animate-pulse bg-amber-400"
                        : "bg-red-500"
                  }`}
                />
                <span className="font-medium text-clinical-700">
                  {backendStatus === "connected"
                    ? "Connected"
                    : backendStatus === "checking"
                      ? "Checking…"
                      : "Unreachable"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">{children}</div>
      </main>

      <footer className="border-t border-clinical-200/60 bg-white/60 py-4">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <p className="text-center text-xs text-clinical-400">
            ChartScope processes synthetic and public-domain data only. See{" "}
            <code className="rounded bg-clinical-100 px-1 py-0.5 text-clinical-600">
              DATA_GOVERNANCE.md
            </code>{" "}
            for compliance details.
          </p>
        </div>
      </footer>
    </div>
  );
}
