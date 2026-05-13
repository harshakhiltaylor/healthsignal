"use client";
import { useState, useEffect } from "react";
import { api, Trial } from "@/lib/api";

const PHASES = [
  { value: "PHASE1", label: "Phase 1" },
  { value: "PHASE2", label: "Phase 2" },
  { value: "PHASE3", label: "Phase 3" },
  { value: "PHASE4", label: "Phase 4" }
];
const STATUSES = ["RECRUITING", "ACTIVE_NOT_RECRUITING", "COMPLETED", "NOT_YET_RECRUITING"];

function TrialCard({ trial }: { trial: Trial }) {
  return (
    <div className="card hover:border-softly-coral transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-xs text-stone-500 font-mono">{trial.id}</span>
            {trial.phase && (
              <span className="badge bg-blue-900 text-blue-300">{trial.phase}</span>
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
        </div>
      </div>
    </div>
  );
}

export default function TrialsPage() {
  const [trials, setTrials] = useState<Trial[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [skip, setSkip] = useState(0);
  const [pageInput, setPageInput] = useState("1");
  const [phase, setPhase] = useState("");
  const [status, setStatus] = useState("");
  const limit = 20;

  const fetchTrials = async (skipVal: number) => {
    setLoading(true);
    try {
      const res = await api.trialsList(skipVal, limit, phase || undefined, status || undefined);
      setTrials(res.items);
      setTotal(res.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrials(skip);
  }, [skip, phase, status]);

  const handlePhaseChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPhase(e.target.value);
    setSkip(0);
  };

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatus(e.target.value);
    setSkip(0);
  };

  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(skip / limit) + 1;

  useEffect(() => {
    setPageInput(currentPage.toString());
  }, [currentPage]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-softly-dark">Database Browser</h1>
        <p className="text-stone-500 text-sm mt-1">
          Browse all clinical trials currently stored in your local database. Total: {total.toLocaleString()} trials.
        </p>
      </div>

      <div className="flex gap-3 flex-wrap">
        <select
          className="input max-w-[180px]"
          value={phase}
          onChange={handlePhaseChange}
        >
          <option value="">Any Phase</option>
          {PHASES.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
        </select>
        <select
          className="input max-w-[220px]"
          value={status}
          onChange={handleStatusChange}
        >
          <option value="">Any Status</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="text-stone-500 text-sm py-8 text-center animate-pulse">Loading trials...</div>
      ) : (
        <div className="space-y-3">
          {trials.map((trial) => (
            <TrialCard key={trial.id} trial={trial} />
          ))}
          {trials.length === 0 && (
            <div className="card text-stone-500 text-sm text-center py-8">
              No trials found in the database. Run the ingestion pipeline first.
            </div>
          )}
        </div>
      )}

      {total > limit && (
        <div className="flex items-center justify-between mt-6">
          <button
            className="btn-secondary"
            disabled={skip === 0 || loading}
            onClick={() => setSkip(skip - limit)}
          >
            Previous
          </button>
          <div className="flex items-center gap-2 text-sm text-stone-500">
            <span>Page {currentPage} of {totalPages}</span>
            <span className="ml-2">Go to:</span>
            <input
              type="number"
              min={1}
              max={totalPages || 1}
              className="input py-1 px-2 w-16 text-center text-sm"
              value={pageInput}
              onChange={(e) => setPageInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  let p = parseInt(pageInput, 10);
                  if (!isNaN(p) && p >= 1 && p <= totalPages) {
                    setSkip((p - 1) * limit);
                  } else {
                    setPageInput(currentPage.toString());
                  }
                }
              }}
              onBlur={() => {
                let p = parseInt(pageInput, 10);
                if (!isNaN(p) && p >= 1 && p <= totalPages) {
                  setSkip((p - 1) * limit);
                } else {
                  setPageInput(currentPage.toString());
                }
              }}
            />
          </div>
          <button
            className="btn-secondary"
            disabled={skip + limit >= total || loading}
            onClick={() => setSkip(skip + limit)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
