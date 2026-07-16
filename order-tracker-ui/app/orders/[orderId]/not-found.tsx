import Link from "next/link";

export default function OrderNotFound() {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-10 text-center shadow-sm">
      <h1 className="text-xl font-semibold">Order not found</h1>
      <p className="mt-2 text-sm text-gray-500">
        No order with that ID has received any events yet.
      </p>
      <Link href="/" className="mt-4 inline-block text-sm text-blue-600 hover:underline">
        &larr; Back to all orders
      </Link>
    </div>
  );
}
