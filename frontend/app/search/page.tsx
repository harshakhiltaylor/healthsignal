"use client";
import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { api, SearchResult } from "@/lib/api";

const PHASES = [
  { value: "PHASE1", label: "Phase 1" },
  { value: "PHASE2", label: "Phase 2" },
  { value: "PHASE3", label: "Phase 3" },
  { value: "PHASE4", label: "Phase 4" }
];
const STATUSES = ["RECRUITING", "ACTIVE_NOT_RECRUITING", "COMPLETED", "NOT_YET_RECRUITING"];

function TrialCard({ result }: { result: SearchResult }) {
  const { trial, score, chunk_text, rank } = result;
  return (
    <div className="card hover:border-softly-coral transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-xs text-stone-500 font-mono">{trial.id}</span>
            {trial.phase && (
              <span className="badge bg-blue-50 text-blue-700">{trial.phase}</span>
            )}
            {trial.status && (
              <span className={`badge ${trial.status === "RECRUITING" ? "bg-softly-sage text-green-700" : "bg-stone-100 text-stone-600"}`}>
                {trial.status.replace(/_/g, " ")}
              </span>
            )}
            {trial.therapeutic_area && (
              <span className="badge bg-softly-lavender text-purple-700">{trial.therapeutic_area}</span>
            )}
          </div>
          <h3 className="text-sm font-medium text-softly-dark leading-snug">{trial.title}</h3>
          {trial.sponsor && (
            <p className="text-xs text-stone-500 mt-1">{trial.sponsor}</p>
          )}
          <p className="text-xs text-stone-600 mt-2 italic leading-relaxed line-clamp-3">
            "{chunk_text}"
          </p>
        </div>
        <div className="text-right shrink-0">
          <div className="text-sm font-semibold text-softly-coral">{(score * 100).toFixed(1)}%</div>
          <div className="text-xs text-stone-500">match</div>
          <div className="text-xs text-stone-500 mt-1">#{rank}</div>
        </div>
      </div>
    </div>
  );
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [phase, setPhase] = useState("");
  const [status, setStatus] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [latency, setLatency] = useState<number | null>(null);
  const { getToken } = useAuth();

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setSearched(true);
    const t0 = Date.now();
    try {
      const token = await getToken();
      const res = await api.search(query, {
        phase: phase || undefined,
        status: status || undefined,
      }, token || undefined);
      setResults(res.results);
      setLatency(Date.now() - t0);
    } catch (e) {
      console.error(e);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (searched && query.trim()) {
      handleSearch();
    }
  }, [phase, status]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-softly-dark">Semantic Search</h1>
        <p className="text-stone-500 text-sm mt-1">
          Search 400k+ trials using natural language. Powered by PubMedBERT + PGVector.
        </p>
      </div>

      <div className="space-y-3">
        <div className="flex gap-3">
          <input
            className="input"
            placeholder='e.g. "GLP-1 agonists Phase 2 pediatric obesity"'
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
          <button className="btn-primary whitespace-nowrap" onClick={handleSearch} disabled={loading}>
            {loading ? "Searching..." : "Search"}
          </button>
        </div>

        <div className="flex gap-3 flex-wrap">
          <select
            className="input max-w-[180px]"
            value={phase}
            onChange={(e) => setPhase(e.target.value)}
          >
            <option value="">Any Phase</option>
            {PHASES.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
          </select>
          <select
            className="input max-w-[220px]"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="">Any Status</option>
            {STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}
          </select>
        </div>
      </div>

      {searched && (
        <div className="flex items-center justify-between text-sm text-stone-500">
          <span>{results.length} results</span>
          {latency && <span>{latency}ms</span>}
        </div>
      )}

      <div className="space-y-3">
        {results.map((r) => <TrialCard key={`${r.trial.id}-${r.rank}`} result={r} />)}
        {searched && !loading && results.length === 0 && (
          <div className="card text-stone-500 text-sm text-center py-8">
            No results. Try a different query or run the ingestion pipeline first.
          </div>
        )}
      </div>
    </div>
  );
}
