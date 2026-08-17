import clsx from "clsx";

const styles: Record<string, string> = {
  draft: "bg-slate-50 text-slate-700 ring-slate-200",
  submitted: "bg-sky-50 text-sky-800 ring-sky-200",
  impact_assessment: "bg-violet-50 text-violet-800 ring-violet-200",
  pending_approval: "bg-amber-50 text-amber-900 ring-amber-200",
  approved: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  rejected: "bg-rose-50 text-rose-800 ring-rose-200",
  implementing: "bg-blue-50 text-blue-800 ring-blue-200",
  verification: "bg-indigo-50 text-indigo-800 ring-indigo-200",
  closed: "bg-slate-100 text-slate-600 ring-slate-300",
  cancelled: "bg-slate-100 text-slate-500 ring-slate-200",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={clsx("badge", styles[status] ?? styles.draft)}>{status.replaceAll("_", " ")}</span>
  );
}

export function PriorityBadge({ priority }: { priority: string }) {
  const map: Record<string, string> = {
    low: "bg-slate-50 text-slate-600 ring-slate-200",
    medium: "bg-sky-50 text-sky-800 ring-sky-200",
    high: "bg-orange-50 text-orange-900 ring-orange-200",
    critical: "bg-rose-50 text-rose-900 ring-rose-300",
  };
  return <span className={clsx("badge", map[priority] ?? map.medium)}>{priority}</span>;
}
