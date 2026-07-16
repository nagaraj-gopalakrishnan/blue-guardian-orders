const STATUS_STYLES: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800 ring-amber-600/20",
  paid: "bg-blue-100 text-blue-800 ring-blue-600/20",
  processing: "bg-blue-100 text-blue-800 ring-blue-600/20",
  filled: "bg-green-100 text-green-800 ring-green-600/20",
  executed: "bg-green-100 text-green-800 ring-green-600/20",
  completed: "bg-green-100 text-green-800 ring-green-600/20",
  settled: "bg-green-100 text-green-800 ring-green-600/20",
  cancelled: "bg-red-100 text-red-800 ring-red-600/20",
  failed: "bg-red-100 text-red-800 ring-red-600/20",
  rejected: "bg-red-100 text-red-800 ring-red-600/20",
};

const FALLBACK = "bg-gray-100 text-gray-800 ring-gray-600/20";

export default function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status.toLowerCase()] ?? FALLBACK;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${style}`}
    >
      {status}
    </span>
  );
}
