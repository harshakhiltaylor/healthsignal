"use client";
import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { api, RAGResponse } from "@/lib/api";
import ReactMarkdown from "react-markdown";

const EXAMPLE_QUESTIONS = [
  "What Phase 3 trials are recruiting for fibromyalgia?",
  "Which trials study hepatocellular carcinoma treatment?",
  "What narcolepsy trials has Pfizer or Alkermes sponsored?",
  "Show me recruiting trials for ischemic stroke or TIA.",
  "What Phase 3 trials are studying metastatic prostate cancer?",
  "Which trials study chronic pancreatitis treatments?",
];

function ScorePill({ label, value }: { label: string; value?: number | null }) {
  if (value === undefined || value === null) return null;
  const color = value >= 0.8 ? "bg-softly-sage text-green-700" : value >= 0.5 ? "bg-amber-50 text-amber-700" : "bg-red-50 text-red-700";
  return (
    <span className={`badge ${color}`}>
      {label}: {value.toFixed(2)}
    </span>
  );
}

export default function AskPage() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<RAGResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { getToken } = useAuth();

  const ask = async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    setError("");
    setResponse(null);
    try {
      const token = await getToken();
      const res = await api.rag(q, token || undefined);
      setResponse(res);
    } catch (e: any) {
      setError(e.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-xl font-semibold text-softly-dark">Ask AI</h1>
        <p className="text-stone-500 text-sm mt-1">
          RAG-powered Q&A over clinical trial data. Answers scored by Groq Llama 3.1 70B judge.
        </p>
      </div>

      <div className="flex gap-3">
        <input
          className="input"
          placeholder="Ask a question about clinical trials..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && ask(question)}
        />
        <button className="btn-primary whitespace-nowrap" onClick={() => ask(question)} disabled={loading}>
          {loading ? "Thinking..." : "Ask"}
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {EXAMPLE_QUESTIONS.map((q) => (
          <button
            key={q}
            className="text-xs border border-stone-200 rounded-full px-3 py-1 text-stone-500 hover:text-softly-dark hover:border-stone-300 hover:bg-stone-50 transition-colors"
            onClick={() => { setQuestion(q); ask(q); }}
          >
            {q}
          </button>
        ))}
      </div>

      {error && (
        <div className="card border-red-200 bg-red-50 text-red-600 text-sm">{error}</div>
      )}

      {response && (
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center gap-2 mb-3 flex-wrap">
              <span className="text-xs text-stone-500">AI Answer</span>
              <ScorePill label="Faithfulness" value={response.faithfulness_score} />
              {response.eval_id && (
                <span className="text-xs text-stone-400">eval #{response.eval_id}</span>
              )}
            </div>
            <div className="text-softly-dark text-sm leading-relaxed whitespace-pre-wrap prose prose-sm prose-stone max-w-none">
              <ReactMarkdown
                components={{
                  ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-4 space-y-1" {...props} />,
                  ol: ({node, ...props}) => <ol className="list-decimal pl-5 mb-4 space-y-1" {...props} />,
                  p: ({node, ...props}) => <p className="mb-4 last:mb-0" {...props} />,
                  strong: ({node, ...props}) => <strong className="font-semibold text-softly-dark" {...props} />
                }}
              >
                {response.answer}
              </ReactMarkdown>
            </div>
          </div>

          {response.sources.length > 0 && (
            <div>
              <h3 className="text-xs uppercase tracking-widest text-stone-500 mb-2">
                Sources ({response.sources.length})
              </h3>
              <div className="space-y-2">
                {response.sources.map((t) => (
                  <div key={t.id} className="card py-3 px-4">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-mono text-stone-500">{t.id}</span>
                      {t.phase && <span className="badge bg-blue-50 text-blue-700">{t.phase}</span>}
                      {t.therapeutic_area && <span className="badge bg-softly-lavender text-purple-700">{t.therapeutic_area}</span>}
                    </div>
                    <p className="text-sm text-softly-dark font-medium mt-1">{t.title}</p>
                    {t.sponsor && <p className="text-xs text-stone-500 mt-0.5">{t.sponsor}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
