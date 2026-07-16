import Link from "next/link";
import StatusBadge from "@/components/StatusBadge";
import SourceBadge from "@/components/SourceBadge";
import { getOrders, type Order } from "@/lib/api";
import { formatTimestamp } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function OrderListPage() {
  let orders: Order[];
  try {
    orders = await getOrders();
  } catch {
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
      <div className="mb-6 flex items-baseline justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Orders</h1>
        <p className="text-sm text-gray-500">
          {orders.length} order{orders.length === 1 ? "" : "s"}
        </p>
      </div>

      {orders.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-300 bg-white p-10 text-center text-gray-500">
          No orders yet. POST an event to{" "}
          <code className="rounded bg-gray-100 px-1.5 py-0.5 text-xs">
            /api/webhooks/order-events/
          </code>{" "}
          to create one.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
              <tr>
                <th className="px-4 py-3">Order ID</th>
                <th className="px-4 py-3">Current Status</th>
                <th className="px-4 py-3">Last Source</th>
                <th className="px-4 py-3">Last Event</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {orders.map((order) => (
                <tr key={order.order_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link
                      href={`/orders/${encodeURIComponent(order.order_id)}`}
                      className="font-medium text-blue-600 hover:underline"
                    >
                      {order.order_id}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={order.current_status} />
                  </td>
                  <td className="px-4 py-3">
                    <SourceBadge source={order.last_source} />
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {formatTimestamp(order.last_event_timestamp)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
