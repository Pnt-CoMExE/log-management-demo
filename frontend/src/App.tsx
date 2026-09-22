import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  AlertItem,
  AuthSession,
  DashboardSummary,
  EventItem,
  fetchAlerts,
  fetchDashboard,
  fetchEvents,
  ingestJson,
  login,
  uploadFile,
} from "./api";

const SESSION_KEY = "logmgr_session";

function loadSession(): AuthSession | null {
  const raw = localStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthSession;
  } catch {
    return null;
  }
}

export default function App() {
  const [session, setSession] = useState<AuthSession | null>(() => loadSession());
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("password");
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"dashboard" | "events" | "alerts" | "ingest">("dashboard");
  const [tenantFilter, setTenantFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [q, setQ] = useState("");
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [eventTotal, setEventTotal] = useState(0);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");

  const onLogin = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const s = await login(username, password);
      localStorage.setItem(SESSION_KEY, JSON.stringify(s));
      setSession(s);
      if (s.role === "viewer") setTenantFilter(s.tenant);
    } catch {
      setError("Invalid credentials");
    }
  };

  const logout = () => {
    localStorage.removeItem(SESSION_KEY);
    setSession(null);
  };

  const refresh = useCallback(async () => {
    if (!session) return;
    setBusy(true);
    setError("");
    try {
      const tenant = tenantFilter || undefined;
      const [dash, ev, al] = await Promise.all([
        fetchDashboard(session.access_token, tenant),
        fetchEvents(session.access_token, {
          tenant,
          source: sourceFilter || undefined,
          q: q || undefined,
          limit: "100",
        }),
        fetchAlerts(session.access_token, tenant),
      ]);
      setSummary(dash);
      setEvents(ev.items);
      setEventTotal(ev.total);
      setAlerts(al);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setBusy(false);
    }
  }, [session, tenantFilter, sourceFilter, q]);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 15000);
    return () => clearInterval(id);
  }, [refresh]);

  const timelineData = useMemo(
    () =>
      (summary?.timeline || []).map((t) => ({
        ...t,
        label: t.timestamp ? new Date(t.timestamp).toLocaleString() : "",
      })),
    [summary]
  );

  if (!session) {
    return (
      <div className="login-shell">
        <form className="login-card" onSubmit={onLogin}>
          <p className="eyebrow">Log Management Demo</p>
          <h1>Sign in</h1>
          <p className="muted">Admin / Viewer · multi-tenant event console</p>
          <label>
            Username
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit">Continue</button>
          <p className="hint">Demo: admin / password · viewer / password · viewer_b / password</p>
        </form>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <p className="eyebrow">Log Management Demo</p>
          <h1>Operations Console</h1>
        </div>
        <div className="user-meta">
          <span>
            {session.username} · {session.role} · tenant {session.tenant}
          </span>
          <button className="ghost" onClick={refresh} disabled={busy}>
            Refresh
          </button>
          <button className="ghost" onClick={logout}>
            Logout
          </button>
        </div>
      </header>

      <nav className="tabs">
        {(["dashboard", "events", "alerts", "ingest"] as const).map((t) => (
          <button key={t} className={tab === t ? "active" : ""} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </nav>

      <section className="filters">
        <label>
          Tenant
          <select
            value={tenantFilter}
            onChange={(e) => setTenantFilter(e.target.value)}
            disabled={session.role === "viewer"}
          >
            <option value="">{session.role === "admin" ? "All tenants" : session.tenant}</option>
            <option value="demoA">demoA</option>
            <option value="demoB">demoB</option>
          </select>
        </label>
        <label>
          Source
          <select value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)}>
            <option value="">All sources</option>
            {["firewall", "network", "api", "crowdstrike", "aws", "m365", "ad"].map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="grow">
          Search
          <input
            placeholder="user, IP, event type…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </label>
      </section>

      {error && <p className="error banner">{error}</p>}
      {notice && <p className="ok banner">{notice}</p>}

      {tab === "dashboard" && summary && (
        <div className="stack">
          <div className="stat-row">
            <div className="stat">
              <span>Events (range)</span>
              <strong>{summary.total_events}</strong>
            </div>
            <div className="stat">
              <span>Open alerts</span>
              <strong>{alerts.filter((a) => a.status === "open").length}</strong>
            </div>
            <div className="stat">
              <span>Sources</span>
              <strong>{summary.by_source.length}</strong>
            </div>
          </div>

          <div className="panel">
            <h2>Timeline</h2>
            <div className="chart">
              <ResponsiveContainer width="100%" height={240}>
                <AreaChart data={timelineData}>
                  <defs>
                    <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#0f766e" stopOpacity={0.45} />
                      <stop offset="100%" stopColor="#0f766e" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#d6ddd8" />
                  <XAxis dataKey="label" hide />
                  <YAxis allowDecimals={false} width={40} />
                  <Tooltip />
                  <Area type="monotone" dataKey="count" stroke="#0f766e" fill="url(#fill)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid-3">
            <TopList title="Top IP" rows={summary.top_ips.map((r) => [r.src_ip, r.count])} />
            <TopList title="Top User" rows={summary.top_users.map((r) => [r.user, r.count])} />
            <TopList
              title="Top Event Type"
              rows={summary.top_event_types.map((r) => [r.event_type, r.count])}
            />
          </div>

          <div className="panel">
            <h2>By source</h2>
            <div className="chart">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={summary.by_source}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#d6ddd8" />
                  <XAxis dataKey="source" />
                  <YAxis allowDecimals={false} width={40} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#115e59" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {tab === "events" && (
        <div className="panel">
          <h2>
            Events <span className="muted">({eventTotal})</span>
          </h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Tenant</th>
                  <th>Source</th>
                  <th>Type</th>
                  <th>User</th>
                  <th>Src IP</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {events.map((ev) => (
                  <tr key={ev.id}>
                    <td className="mono">{new Date(ev.timestamp).toLocaleString()}</td>
                    <td>{ev.tenant}</td>
                    <td>{ev.source}</td>
                    <td>{ev.event_type}</td>
                    <td>{ev.user}</td>
                    <td className="mono">{ev.src_ip}</td>
                    <td>{ev.action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === "alerts" && (
        <div className="panel">
          <h2>Alerts</h2>
          {alerts.length === 0 ? (
            <p className="muted">No alerts yet. Send ≥3 failed logins from the same IP within 5 minutes.</p>
          ) : (
            <ul className="alert-list">
              {alerts.map((a) => (
                <li key={a.id}>
                  <div>
                    <strong>{a.title}</strong>
                    <p>{a.message}</p>
                    <p className="muted">
                      {a.rule_name} · {a.tenant} · {a.status} ·{" "}
                      {new Date(a.created_at).toLocaleString()}
                    </p>
                  </div>
                  <span className={`pill ${a.status}`}>{a.status}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {tab === "ingest" && (
        <IngestPanel
          session={session}
          onDone={async (msg) => {
            setNotice(msg);
            await refresh();
          }}
          onError={setError}
        />
      )}
    </div>
  );
}

function TopList({ title, rows }: { title: string; rows: [string, number][] }) {
  return (
    <div className="panel">
      <h2>{title}</h2>
      <ul className="toplist">
        {rows.length === 0 && <li className="muted">No data</li>}
        {rows.map(([k, v]) => (
          <li key={k}>
            <span className="mono">{k}</span>
            <strong>{v}</strong>
          </li>
        ))}
      </ul>
    </div>
  );
}

function IngestPanel({
  session,
  onDone,
  onError,
}: {
  session: AuthSession;
  onDone: (msg: string) => Promise<void>;
  onError: (msg: string) => void;
}) {
  const [jsonText, setJsonText] = useState(
    JSON.stringify(
      {
        tenant: "demoA",
        source: "api",
        event_type: "app_login_failed",
        user: "alice",
        ip: "203.0.113.7",
        reason: "wrong_password",
        "@timestamp": new Date().toISOString(),
      },
      null,
      2
    )
  );
  const [tenant, setTenant] = useState("demoA");
  const [sourceHint, setSourceHint] = useState("aws");

  if (session.role !== "admin") {
    return (
      <div className="panel">
        <h2>Ingest</h2>
        <p className="muted">Viewer role is read-only. Sign in as admin to ingest logs.</p>
      </div>
    );
  }

  return (
    <div className="stack">
      <div className="panel">
        <h2>POST /api/ingest (JSON)</h2>
        <textarea value={jsonText} onChange={(e) => setJsonText(e.target.value)} rows={12} />
        <button
          onClick={async () => {
            try {
              const payload = JSON.parse(jsonText);
              const res = await ingestJson(session.access_token, payload);
              await onDone(`Accepted ${res.accepted} event(s)`);
            } catch (e) {
              onError(e instanceof Error ? e.message : "Ingest failed");
            }
          }}
        >
          Send JSON
        </button>
      </div>
      <div className="panel">
        <h2>Upload sample file</h2>
        <div className="filters">
          <label>
            Tenant
            <input value={tenant} onChange={(e) => setTenant(e.target.value)} />
          </label>
          <label>
            Source hint
            <input value={sourceHint} onChange={(e) => setSourceHint(e.target.value)} />
          </label>
        </div>
        <input
          type="file"
          accept=".json,.ndjson,.jsonl,.log,.txt"
          onChange={async (e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            try {
              const res = await uploadFile(session.access_token, file, tenant, sourceHint);
              await onDone(`Uploaded ${res.accepted} event(s) from ${file.name}`);
            } catch (err) {
              onError(err instanceof Error ? err.message : "Upload failed");
            }
          }}
        />
      </div>
    </div>
  );
}
