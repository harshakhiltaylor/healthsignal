"use client";
import { useEffect, useState } from "react";
import { api, IngestLog } from "@/lib/api";

export default function IngestPage() {
  const [logs, setLogs] = useState<IngestLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [triggerMsg, setTriggerMsg] = useState("");

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");

  const handleAuth = (e: React.FormEvent) => {
    e.preventDefault();
    if (password === (process.env.NEXT_PUBLIC_ADMIN_KEY || "admin123")) {
      setIsAuthenticated(true);
      load();
    } else {
      setAuthError("Invalid admin key");
    }
  };

  const load = () => {
    api.ingestLogs()
      .then(setLogs)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    // Only auto-load if auth isn't required (dev mode) or already authenticated
    if (process.env.NODE_ENV === "development" && !process.env.NEXT_PUBLIC_ADMIN_KEY) {
      setIsAuthenticated(true);
      load();
    }
  }, []);

  // Auto-poll if an ingestion is currently running or queued
  useEffect(() => {
    const hasActive = logs.some(l => l.status === "running" || l.status === "queued");
    if (hasActive) {
      const timer = setTimeout(load, 3000);
      return () => clearTimeout(timer);
    }
  }, [logs]);

  const trigger = async () => {
    setTriggering(true);
    setTriggerMsg("");
    try {
      await api.triggerIngest();
      setTriggerMsg("Ingest queued! Check back in a few minutes.");
      setTimeout(load, 3000);
    } catch (e: any) {
      setTriggerMsg(`Error: ${e.message}`);
    } finally {
      setTriggering(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-md mx-auto mt-20 p-6 card space-y-4">
        <h1 className="text-xl font-semibold text-softly-dark text-center">Admin Access Required</h1>
        <p className="text-stone-500 text-sm text-center">Please enter the admin key to access the ingestion pipeline.</p>
        <form onSubmit={handleAuth} className="space-y-4">
          <input
            type="password"
            className="input w-full"
            placeholder="Admin Key"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {authError && <p className="text-red-600 text-sm text-center">{authError}</p>}
          <button type="submit" className="btn-primary w-full">Access Pipeline</button>
        </form>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-softly-dark">Pipeline</h1>
        <p className="text-stone-500 text-sm mt-1">
          Nightly ingestion from ClinicalTrials.gov. Runs at 02:00 UTC via Celery Beat.
        </p>
      </div>

      <div className="card space-y-3">
        <h2 className="text-sm font-medium text-softly-dark">Manual trigger</h2>
        <p className="text-xs text-stone-500">
          Queues an immediate ingest run. Uses Celery if available, otherwise runs directly.
          First run: use the seed script instead (<code className="text-stone-400">python -m scripts.seed_trials</code>).
        </p>
        <button
          className="btn-primary"
          onClick={trigger}
          disabled={triggering}
        >
          {triggering ? "Queueing..." : "⚡ Trigger Ingest Now"}
        </button>
        {triggerMsg && <p className={`text-sm ${triggerMsg.startsWith("Error") ? "text-red-600" : "text-green-600"}`}>{triggerMsg}</p>}
      </div>

      <div>
        <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-3">Ingest history</h2>
        {loading ? (
          <div className="text-stone-500 text-sm">Loading...</div>
        ) : logs.length === 0 ? (
          <div className="card text-sm text-stone-500 text-center py-8">
            No runs yet. Trigger an ingest or run <code>python -m scripts.seed_trials</code>
          </div>
        ) : (
          <div className="space-y-2">
            {logs.map((log) => (
              <div key={log.id} className="card py-3 px-4">
                <div className="flex items-center justify-between flex-wrap gap-2 text-sm">
                  <div className="flex items-center gap-3">
                    <span className={`badge ${
                      log.status === "complete" ? "bg-softly-sage text-green-700" : 
                      log.status === "running" ? "bg-blue-50 text-blue-700" : 
                      log.status === "queued" ? "bg-purple-50 text-purple-700" : 
                      "bg-red-50 text-red-700"
                    }`}>
                      {log.status}
                    </span>
                    <span className="text-stone-500 text-xs">{new Date(log.run_at + "Z").toLocaleString()}</span>
                  </div>
                  <div className="flex gap-4 text-xs text-stone-500">
                    <span>Fetched: <span className="text-softly-dark font-medium">{log.trials_fetched}</span></span>
                    <span>New: <span className="text-green-600">{log.trials_new}</span></span>
                    <span>Updated: <span className="text-blue-600">{log.trials_updated}</span></span>
                    <span>Skipped: <span className="text-stone-400">{log.trials_skipped}</span></span>
                    {log.errors > 0 && <span>Errors: <span className="text-red-600">{log.errors}</span></span>}
                    {log.duration_seconds && <span>{log.duration_seconds.toFixed(1)}s</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
