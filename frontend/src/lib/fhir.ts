import { useCallback, useState } from "react";

interface FhirBundleEntry {
  resource?: { resourceType?: string };
}

export function countResourceTypes(bundle: Record<string, unknown>): Record<string, number> {
  const counts: Record<string, number> = {};
  const entries = bundle.entry as FhirBundleEntry[] | undefined;
  if (!entries) return counts;
  for (const entry of entries) {
    const type = entry.resource?.resourceType;
    if (type) counts[type] = (counts[type] ?? 0) + 1;
  }
  return counts;
}

export function bundleEntryCount(bundle: Record<string, unknown>): number {
  const entries = bundle.entry as unknown[] | undefined;
  return entries?.length ?? 0;
}

export function downloadJson(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function useCopyToClipboard() {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, []);

  return { copied, copy };
}
