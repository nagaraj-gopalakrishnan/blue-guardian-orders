import Link from "next/link";
import { notFound } from "next/navigation";
import StatusBadge from "@/components/StatusBadge";
import SourceBadge from "@/components/SourceBadge";
import { getOrder, type OrderDetail } from "@/lib/api";
import { formatTimestamp } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function OrderDetailPage({
  params,
}: {
  params: Promise<{ orderId: string }>;
}) {
  const { orderId } = await params;

  let order: OrderDetail;
  try {
    order = await getOrder(decodeURIComponent(orderId));
  } catch (err) {
    if (err instanceof Error && err.message.includes("404")) {
      notFound();
    }
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
        <p className="font-medium">Could not reach the orders API.</p>
        <p className="mt-1 text-sm">
          Make sure the Django server is running (see README), then refresh.
        </p>
      </div>
    );
  }

  return (
    <div>
      <Link href="/" className="text-sm text-blue-600 hover:underline">
        &larr; All orders
      </Link>

      <div className="mt-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{order.order_id}</h1>
            <p className="mt-1 text-sm text-gray-500">
              Last event {formatTimestamp(order.last_event_timestamp)}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge status={order.current_status} />
            <SourceBadge source={order.last_source} />
          </div>
        </div>
        <p className="mt-4 rounded-md bg-gray-50 px-3 py-2 text-xs text-gray-500">
          Current status is derived from the event with the latest{" "}
          <code>event_timestamp</code> — not the order events arrived in.
        </p>
      </div>

      <h2 className="mt-8 mb-3 text-lg font-semibold tracking-tight">
        Event history{" "}
        <span className="text-sm font-normal text-gray-500">
          ({order.events.length} event{order.events.length === 1 ? "" : "s"}, newest first)
        </span>
      </h2>

      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Source</th>
              <th className="px-4 py-3">Event Timestamp</th>
              <th className="px-4 py-3">Received At</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {order.events.map((event, i) => (
              <tr key={event.id} className={i === 0 ? "bg-blue-50/40" : "hover:bg-gray-50"}>
                <td className="px-4 py-3">
                  <StatusBadge status={event.status} />
                  {i === 0 && (
                    <span className="ml-2 text-xs font-medium text-blue-600">current</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <SourceBadge source={event.source} />
                </td>
                <td className="px-4 py-3 text-gray-700">
                  {formatTimestamp(event.event_timestamp)}
                </td>
                <td className="px-4 py-3 text-gray-500">{formatTimestamp(event.received_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
