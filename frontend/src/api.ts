const API_BASE = import.meta.env.VITE_API_BASE || "";

export type AuthSession = {
  access_token: string;
  role: string;
  tenant: string;
  username: string;
};

export async function login(username: string, password: string): Promise<AuthSession> {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error("Login failed");
  return res.json();
}

async function api<T>(
  path: string,
  token: string,
  params?: Record<string, string | undefined>
): Promise<T> {
  const qs = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v) qs.set(k, v);
    });
  }
  const url = `${API_BASE}${path}${qs.toString() ? `?${qs}` : ""}`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function fetchDashboard(token: string, tenant?: string) {
  return api<DashboardSummary>("/api/dashboard/summary", token, { tenant });
}

export function fetchEvents(
  token: string,
  filters: Record<string, string | undefined>
) {
  return api<{ total: number; items: EventItem[] }>("/api/events/search", token, filters);
}

export function fetchAlerts(token: string, tenant?: string) {
  return api<AlertItem[]>("/api/alerts", token, { tenant });
}

export async function ingestJson(token: string, payload: unknown) {
  const res = await fetch(`${API_BASE}/api/ingest`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function uploadFile(
  token: string,
  file: File,
  tenant: string,
  sourceHint?: string
) {
  const form = new FormData();
  form.append("file", file);
  form.append("tenant", tenant);
  if (sourceHint) form.append("source_hint", sourceHint);
  const res = await fetch(`${API_BASE}/api/ingest/file`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export type DashboardSummary = {
  total_events: number;
  top_ips: { src_ip: string; count: number }[];
  top_users: { user: string; count: number }[];
  top_event_types: { event_type: string; count: number }[];
  timeline: { timestamp: string; count: number }[];
  by_source: { source: string; count: number }[];
};

export type EventItem = {
  id: number;
  timestamp: string;
  tenant: string;
  source: string;
  event_type: string | null;
  action: string | null;
  src_ip: string | null;
  user: string | null;
  host: string | null;
  severity: number | null;
};

export type AlertItem = {
  id: number;
  rule_name: string;
  tenant: string;
  title: string;
  message: string;
  src_ip: string | null;
  event_count: number;
  status: string;
  created_at: string;
  severity: number;
};
