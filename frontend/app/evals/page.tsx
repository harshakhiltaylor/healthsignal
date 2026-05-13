"use client";
import { useEffect, useState } from "react";
import { api, EvalResult, EvalSummary } from "@/lib/api";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";

export default function EvalsPage() {
  const [summary, setSummary] = useState<EvalSummary | null>(null);
  const [evals, setEvals] = useState<EvalResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.evalSummary(), api.evalList(100)])
      .then(([s, e]) => { setSummary(s); setEvals(e); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const chartData = evals
    .filter((e) => e.faithfulness !== null && e.faithfulness !== undefined)
    .slice(0, 50)
    .reverse()
    .map((e, i) => ({
      i,
      faithfulness: e.faithfulness,
      relevance: e.answer_relevance,
      recall: e.context_recall,
    }));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-softly-dark">Eval Dashboard</h1>
        <p className="text-stone-500 text-sm mt-1">
          RAGAS + LLM-as-judge scores over time. Faithfulness threshold: {summary?.threshold ?? 0.80}.
        </p>
      </div>

      {loading ? (
        <div className="text-stone-500 text-sm">Loading...</div>
      ) : (
        <>
          {summary && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Avg Faithfulness", val: summary.avg_faithfulness, color: "text-green-400" },
                { label: "Avg Relevance", val: summary.avg_answer_relevance, color: "text-blue-400" },
                { label: "Avg Recall", val: summary.avg_context_recall, color: "text-purple-400" },
                { label: "Judge Score", val: summary.avg_judge_score, color: "text-amber-400" },
              ].map(({ label, val, color }) => (
                <div key={label} className="card">
                  <div className={`text-2xl font-semibold ${color}`}>{val.toFixed(3)}</div>
                  <div className="text-xs text-stone-400 mt-1">{label}</div>
                </div>
              ))}
            </div>
          )}

          {chartData.length > 0 && (
            <div className="card">
              <div className="text-xs text-stone-500 mb-4">Faithfulness over last {chartData.length} evals</div>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={chartData}>
                  <XAxis dataKey="i" hide />
                  <YAxis domain={[0, 1]} tick={{ fontSize: 11, fill: "#6b7280" }} />
                  <Tooltip
                    contentStyle={{ background: "#ffffff", border: "1px solid #f5f5f4", borderRadius: "8px", fontSize: 12 }}
                    formatter={(v: any) => [Number(v).toFixed(3)]}
                  />
                  <ReferenceLine y={summary?.threshold ?? 0.8} stroke="#f59e0b" strokeDasharray="4 4" />
                  <Line dataKey="faithfulness" stroke="#34d399" dot={false} strokeWidth={2} />
                  <Line dataKey="relevance" stroke="#60a5fa" dot={false} strokeWidth={1.5} strokeDasharray="3 3" />
                </LineChart>
              </ResponsiveContainer>
              <div className="flex gap-4 mt-2 text-xs text-stone-500">
                <span><span className="text-green-400">—</span> Faithfulness</span>
                <span><span className="text-blue-400">- -</span> Relevance</span>
                <span><span className="text-amber-400">- -</span> Threshold ({summary?.threshold})</span>
              </div>
            </div>
          )}

          <div>
            <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-3">Recent evals</h2>
            <div className="space-y-2">
              {evals.slice(0, 20).map((e) => (
                <div key={e.id} className="card py-3 px-4 text-sm">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-softly-dark font-medium truncate">{e.query}</p>
                      <p className="text-xs text-stone-400 mt-0.5">
                        {new Date(e.created_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      {e.faithfulness !== null && (
                        <span className={`badge text-xs ${(e.faithfulness ?? 0) >= 0.8 ? "bg-softly-sage text-green-700" : "bg-red-50 text-red-700"}`}>
                          F: {e.faithfulness?.toFixed(2)}
                        </span>
                      )}
                      {e.judge_score !== null && (
                        <span className="badge bg-amber-50 text-amber-700 text-xs">
                          J: {e.judge_score?.toFixed(2)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
