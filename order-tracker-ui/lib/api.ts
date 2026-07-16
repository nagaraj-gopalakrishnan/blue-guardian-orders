const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export interface Order {
  order_id: string;
  current_status: string;
  last_source: string;
  last_event_timestamp: string;
  created_at: string;
  updated_at: string;
}

export interface OrderEvent {
  id: number;
  status: string;
  source: string;
  event_timestamp: string;
  received_at: string;
}

export interface OrderDetail extends Order {
  events: OrderEvent[];
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API request failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export function getOrders(): Promise<Paginated<Order>> {
  return apiFetch<Paginated<Order>>("/orders/");
}

export function getOrder(orderId: string): Promise<OrderDetail> {
  return apiFetch<OrderDetail>(`/orders/${encodeURIComponent(orderId)}/`);
}
