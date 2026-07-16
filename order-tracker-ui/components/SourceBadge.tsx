const SOURCE_STYLES: Record<string, string> = {
  payment_processor: "bg-purple-50 text-purple-700 ring-purple-600/20",
  trading_platform: "bg-cyan-50 text-cyan-700 ring-cyan-600/20",
};

const FALLBACK = "bg-gray-50 text-gray-600 ring-gray-500/20";

export default function SourceBadge({ source }: { source: string }) {
  const style = SOURCE_STYLES[source.toLowerCase()] ?? FALLBACK;
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${style}`}
    >
      {source.replaceAll("_", " ")}
    </span>
  );
}
