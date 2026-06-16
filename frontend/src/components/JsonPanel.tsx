import { ChevronDown, ChevronRight } from "lucide-react";
import { useState, type ReactNode } from "react";

interface JsonTreeProps {
  data: unknown;
  depth?: number;
  label?: string;
  defaultOpen?: boolean;
}

function JsonValue({ value }: { value: unknown }): ReactNode {
  if (value === null) return <span className="text-clinical-400">null</span>;
  if (typeof value === "boolean")
    return <span className="text-violet-600">{String(value)}</span>;
  if (typeof value === "number")
    return <span className="text-amber-600">{value}</span>;
  if (typeof value === "string")
    return <span className="text-emerald-700">&quot;{value}&quot;</span>;
  return null;
}

function JsonNode({ data, depth = 0, label, defaultOpen = depth < 1 }: JsonTreeProps) {
  const [open, setOpen] = useState(defaultOpen);
  const indent = depth * 16;

  if (data === null || typeof data !== "object") {
    return (
      <div style={{ paddingLeft: indent }} className="py-0.5 font-mono text-xs leading-relaxed">
        {label != null && (
          <span className="text-clinical-600">&quot;{label}&quot;: </span>
        )}
        <JsonValue value={data} />
      </div>
    );
  }

  if (Array.isArray(data)) {
    if (data.length === 0) {
      return (
        <div style={{ paddingLeft: indent }} className="py-0.5 font-mono text-xs text-clinical-500">
          {label != null && <span className="text-clinical-600">&quot;{label}&quot;: </span>}
          []
        </div>
      );
    }
    return (
      <div style={{ paddingLeft: indent }}>
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="flex items-center gap-1 py-0.5 font-mono text-xs text-clinical-700 hover:text-clinical-900"
        >
          {open ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
          {label != null && <span className="text-clinical-600">&quot;{label}&quot;: </span>}
          <span className="text-clinical-400">[{data.length}]</span>
        </button>
        {open &&
          data.map((item, i) => (
            <JsonNode key={i} data={item} depth={depth + 1} label={String(i)} defaultOpen={depth < 2} />
          ))}
      </div>
    );
  }

  const entries = Object.entries(data as Record<string, unknown>);
  if (entries.length === 0) {
    return (
      <div style={{ paddingLeft: indent }} className="py-0.5 font-mono text-xs text-clinical-500">
        {label != null && <span className="text-clinical-600">&quot;{label}&quot;: </span>}
        {"{}"}
      </div>
    );
  }

  return (
    <div style={{ paddingLeft: indent }}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 py-0.5 font-mono text-xs text-clinical-700 hover:text-clinical-900"
      >
        {open ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
        {label != null && <span className="text-clinical-600">&quot;{label}&quot;: </span>}
        <span className="text-clinical-400">{"{…}"}</span>
      </button>
      {open &&
        entries.map(([key, val]) => (
          <JsonNode key={key} data={val} depth={depth + 1} label={key} defaultOpen={depth < 1} />
        ))}
    </div>
  );
}

interface JsonPanelProps {
  data: unknown;
  maxHeight?: string;
}

export default function JsonPanel({ data, maxHeight = "28rem" }: JsonPanelProps) {
  return (
    <div
      className="overflow-auto rounded-lg border border-clinical-200 bg-clinical-950/5 p-3"
      style={{ maxHeight }}
    >
      <JsonNode data={data} defaultOpen />
    </div>
  );
}
