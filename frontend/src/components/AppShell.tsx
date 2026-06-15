import { Activity, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";

interface AppShellProps {
  children: ReactNode;
  backendStatus: "connected" | "unreachable" | "checking";
}

export default function AppShell({ children, backendStatus }: AppShellProps) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-clinical-200/80 bg-white/90 backdrop-blur-sm sticky top-0 z-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-clinical-600 text-white shadow-sm">
                <Activity className="h-5 w-5" strokeWidth={2.25} />
              </div>
              <div>
                <h1 className="font-display text-xl font-semibold tracking-tight text-clinical-900">
                  ChartScope
                </h1>
                <p className="text-xs text-clinical-500 -mt-0.5">
                  Clinical NLP &amp; HCC Intelligence
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full bg-sage-50 px-3 py-1 text-xs font-medium text-sage-700 ring-1 ring-sage-200">
                <ShieldCheck className="h-3.5 w-3.5" />
                Synthetic / public data only — HIPAA-safe
              </span>

              <div className="flex items-center gap-2 text-sm">
                <span
                  className={`h-2 w-2 rounded-full ${
                    backendStatus === "connected"
                      ? "bg-emerald-500"
                      : backendStatus === "checking"
                        ? "bg-amber-400 animate-pulse"
                        : "bg-red-500"
                  }`}
                />
                <span className="text-clinical-600">
                  {backendStatus === "connected"
                    ? "Backend connected"
                    : backendStatus === "checking"
                      ? "Checking backend…"
                      : "Backend unreachable"}
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
