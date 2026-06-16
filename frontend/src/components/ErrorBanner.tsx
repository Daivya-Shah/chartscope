import { AlertCircle } from "lucide-react";

interface ErrorBannerProps {
  message: string;
}

export default function ErrorBanner({ message }: ErrorBannerProps) {
  return (
    <div className="mb-4 flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 shadow-sm">
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
      <div>
        <p className="font-medium">Analysis failed</p>
        <p className="mt-0.5 text-red-700">{message}</p>
      </div>
    </div>
  );
}
