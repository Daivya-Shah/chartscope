export default function ResultsSkeleton() {
  return (
    <div className="animate-pulse space-y-5" aria-busy="true" aria-label="Loading results">
      <div className="flex gap-2">
        <div className="h-7 w-32 rounded-full bg-clinical-200" />
        <div className="h-7 w-24 rounded-full bg-clinical-200" />
      </div>
      <div className="space-y-3 rounded-xl border border-clinical-200 bg-clinical-50/50 p-5">
        <div className="h-4 w-3/4 rounded bg-clinical-200" />
        <div className="h-4 w-full rounded bg-clinical-200" />
        <div className="h-4 w-5/6 rounded bg-clinical-200" />
        <div className="h-4 w-2/3 rounded bg-clinical-200" />
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="h-28 rounded-xl bg-clinical-200" />
        <div className="h-28 rounded-xl bg-clinical-200" />
      </div>
      <div className="h-40 rounded-xl bg-clinical-200" />
    </div>
  );
}
