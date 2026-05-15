"use client";
import { useState, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

interface Topic {
  rank: number;
  condition: string;
  therapeutic_area: string;
  trial_count: number;
  headline: string;
  teaser: string;
  body: string;
}

interface NewsletterResponse {
  generated_at: string | null;
  topics: Topic[];
  status: string;
}

// ─── Therapeutic area → gradient map ───────────────────────────────────────
const AREA_GRADIENTS: Record<string, string> = {
  Oncology: "from-rose-500/20 to-pink-500/10",
  Cardiology: "from-red-500/20 to-orange-400/10",
  Neurology: "from-violet-500/20 to-purple-400/10",
  "Infectious Disease": "from-emerald-500/20 to-teal-400/10",
  "Endocrinology and Metabolism": "from-amber-400/20 to-yellow-300/10",
  "Immunology and Rheumatology": "from-sky-500/20 to-blue-400/10",
  "Respiratory Medicine": "from-cyan-500/20 to-sky-400/10",
  Gastroenterology: "from-lime-500/20 to-green-400/10",
  Psychiatry: "from-indigo-500/20 to-violet-400/10",
  "Rare Disease": "from-fuchsia-500/20 to-pink-400/10",
};

const AREA_ICON: Record<string, string> = {
  Oncology: "🔬",
  Cardiology: "❤️",
  Neurology: "🧠",
  "Infectious Disease": "🦠",
  "Endocrinology and Metabolism": "⚗️",
  "Immunology and Rheumatology": "🛡️",
  "Respiratory Medicine": "🫁",
  Gastroenterology: "💊",
  Psychiatry: "🧘",
  "Rare Disease": "🔭",
};

function getGradient(area: string) {
  return AREA_GRADIENTS[area] || "from-softly-coral/20 to-orange-300/10";
}
function getIcon(area: string) {
  return AREA_ICON[area] || "📋";
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const h = Math.floor(diff / 3600000);
  if (h < 1) return "just now";
  if (h === 1) return "1 hour ago";
  if (h < 24) return `${h} hours ago`;
  return `${Math.floor(h / 24)} days ago`;
}

// ─── Full-article modal ─────────────────────────────────────────────────────
function ArticleModal({ topic, onClose }: { topic: Topic; onClose: () => void }) {
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", handleKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  const paragraphs = topic.body.split(/\n\n+/).filter(Boolean);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />

      {/* Modal panel — slides up from bottom on mobile, centered on desktop */}
      <div
        className={`
          relative w-full sm:max-w-2xl bg-white rounded-t-3xl sm:rounded-3xl
          shadow-[0_-20px_60px_-10px_rgba(0,0,0,0.15)] sm:shadow-2xl
          max-h-[90vh] overflow-y-auto
          animate-[slideUp_0.3s_ease-out]
        `}
        style={{
          animation: "slideUp 0.28s cubic-bezier(0.32,0.72,0,1) both",
        }}
      >
        {/* Drag handle */}
        <div className="flex justify-center pt-4 pb-1 sm:hidden">
          <div className="w-10 h-1 rounded-full bg-stone-200" />
        </div>

        {/* Gradient header */}
        <div className={`bg-gradient-to-br ${getGradient(topic.therapeutic_area)} px-6 pt-4 pb-6 rounded-t-3xl sm:rounded-t-3xl`}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-2xl">{getIcon(topic.therapeutic_area)}</span>
              <span className="text-xs font-semibold uppercase tracking-widest text-stone-500">
                {topic.therapeutic_area}
              </span>
            </div>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-white/70 flex items-center justify-center text-stone-400 hover:text-stone-700 hover:bg-white transition-colors"
            >
              ✕
            </button>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-softly-dark leading-snug">
            {topic.headline}
          </h2>
          <p className="mt-2 text-stone-500 text-sm">{topic.teaser}</p>
          <div className="flex items-center gap-3 mt-4">
            <span className="text-xs bg-white/60 backdrop-blur px-3 py-1 rounded-full text-stone-600 font-medium">
              {topic.trial_count.toLocaleString()} active trials
            </span>
            <span className="text-xs bg-softly-coral/10 text-softly-coral px-3 py-1 rounded-full font-semibold">
              #{topic.rank} Trending
            </span>
          </div>
        </div>

        {/* Article body */}
        <div className="px-6 py-6 space-y-4">
          {paragraphs.map((para, i) => (
            <p key={i} className="text-stone-600 text-[15px] leading-relaxed">
              {para}
            </p>
          ))}
        </div>

        {/* Footer */}
        <div className="px-6 pb-6">
          <div className="border-t border-stone-100 pt-4 flex items-center justify-between">
            <span className="text-xs text-stone-400">HealthSignal • AI-generated clinical insight</span>
            <button
              onClick={onClose}
              className="text-sm text-softly-coral font-medium hover:underline"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Hero card (rank 1) ─────────────────────────────────────────────────────
function HeroCard({ topic, onReadMore }: { topic: Topic; onReadMore: () => void }) {
  return (
    <div
      className={`
        relative overflow-hidden rounded-3xl border border-white/60
        bg-gradient-to-br ${getGradient(topic.therapeutic_area)}
        bg-white shadow-[0_8px_40px_-8px_rgba(0,0,0,0.10)]
        p-7 sm:p-10 transition-all duration-300 hover:shadow-[0_16px_50px_-8px_rgba(0,0,0,0.15)]
        group cursor-pointer
      `}
      onClick={onReadMore}
    >
      {/* Decorative blobs */}
      <div className="pointer-events-none absolute -top-12 -right-12 w-48 h-48 rounded-full bg-softly-coral/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-10 -left-10 w-40 h-40 rounded-full bg-violet-300/10 blur-3xl" />

      <div className="relative z-10">
        {/* Top row */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{getIcon(topic.therapeutic_area)}</span>
            <div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 text-[11px] font-bold uppercase tracking-widest text-softly-coral">
                  <span className="w-1.5 h-1.5 rounded-full bg-softly-coral animate-pulse inline-block" />
                  Trending #1
                </span>
              </div>
              <span className="text-xs text-stone-500 font-medium">{topic.therapeutic_area}</span>
            </div>
          </div>
          <span className="hidden sm:block text-xs bg-white/60 backdrop-blur px-3 py-1 rounded-full text-stone-600 font-medium shrink-0">
            {topic.trial_count.toLocaleString()} trials
          </span>
        </div>

        {/* Headline */}
        <h2 className="text-2xl sm:text-3xl font-bold text-softly-dark leading-tight tracking-tight mb-3 group-hover:text-softly-coral transition-colors duration-200">
          {topic.headline}
        </h2>

        {/* Teaser */}
        <p className="text-stone-500 text-[15px] leading-relaxed mb-6 max-w-2xl">
          {topic.teaser}
        </p>

        {/* CTA */}
        <button
          onClick={(e) => { e.stopPropagation(); onReadMore(); }}
          className="inline-flex items-center gap-2 bg-softly-dark text-white text-sm font-semibold px-6 py-2.5 rounded-full shadow-sm hover:scale-105 transition-transform duration-150"
        >
          Read Full Article
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}

// ─── Small topic card (ranks 2-5) ──────────────────────────────────────────
function TopicCard({ topic, onReadMore }: { topic: Topic; onReadMore: () => void }) {
  return (
    <div
      className={`
        relative overflow-hidden rounded-2xl border border-stone-100
        bg-white shadow-sm hover:shadow-md hover:border-softly-coral/30
        p-5 transition-all duration-200 group cursor-pointer
      `}
      onClick={onReadMore}
    >
      <div className={`absolute inset-0 bg-gradient-to-br ${getGradient(topic.therapeutic_area)} opacity-40`} />
      <div className="relative z-10">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <span className="text-xl">{getIcon(topic.therapeutic_area)}</span>
            <span className="text-[11px] font-bold text-softly-coral uppercase tracking-widest">
              #{topic.rank}
            </span>
          </div>
          <span className="text-[11px] text-stone-400 shrink-0 bg-white/70 px-2 py-0.5 rounded-full">
            {topic.trial_count.toLocaleString()} trials
          </span>
        </div>

        <h3 className="text-[14px] font-semibold text-softly-dark leading-snug mb-1.5 group-hover:text-softly-coral transition-colors line-clamp-2">
          {topic.headline}
        </h3>
        <p className="text-[12px] text-stone-500 leading-relaxed line-clamp-2 mb-3">
          {topic.teaser}
        </p>

        <button
          onClick={(e) => { e.stopPropagation(); onReadMore(); }}
          className="text-[12px] font-semibold text-softly-coral hover:underline flex items-center gap-1"
        >
          Read More
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}

// ─── Skeleton loaders ───────────────────────────────────────────────────────
function HeroSkeleton() {
  return (
    <div className="rounded-3xl bg-stone-100 h-64 animate-pulse" />
  );
}
function CardSkeleton() {
  return (
    <div className="rounded-2xl bg-stone-100 h-44 animate-pulse" />
  );
}

// ─── Main page ──────────────────────────────────────────────────────────────
export default function NewsletterPage() {
  const [data, setData] = useState<NewsletterResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/newsletter`)
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const hero = data?.topics?.[0];
  const rest = data?.topics?.slice(1) ?? [];

  return (
    <>
      {/* Slide-up animation keyframes */}
      <style>{`
        @keyframes slideUp {
          from { transform: translateY(100%); opacity: 0; }
          to   { transform: translateY(0);    opacity: 1; }
        }
      `}</style>

      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xl">📰</span>
              <span className="text-xs font-bold uppercase tracking-widest text-softly-coral">
                Trending Topics in 5 Mins
              </span>
            </div>
            <h1 className="text-2xl font-bold text-softly-dark tracking-tight">Newsletter</h1>
            <p className="text-stone-500 text-sm mt-1 max-w-lg">
              The top 5 hot topics in clinical research today — AI-synthesised from{" "}
              <span className="text-softly-dark font-medium">10,000+</span> active trials, refreshed daily.
            </p>
          </div>

          {/* Freshness badge */}
          {data?.generated_at && (
            <div className="flex items-center gap-2 text-xs text-stone-500 bg-white border border-stone-100 rounded-full px-4 py-2 shadow-sm self-start mt-1">
              <span className={`w-2 h-2 rounded-full ${data.status === "refreshing" ? "bg-amber-400 animate-pulse" : "bg-green-400"}`} />
              Updated {timeAgo(data.generated_at)}
            </div>
          )}
        </div>

        {/* Generating state */}
        {data?.status === "generating" && (
          <div className="card text-center py-12 space-y-3">
            <div className="text-3xl animate-bounce">🔬</div>
            <p className="text-softly-dark font-semibold">Generating today's newsletter…</p>
            <p className="text-stone-500 text-sm">Our AI is analysing 10,000+ clinical trials.<br />Refresh in about 30 seconds.</p>
          </div>
        )}

        {/* Hero card */}
        {loading ? <HeroSkeleton /> : hero && (
          <HeroCard topic={hero} onReadMore={() => setSelectedTopic(hero)} />
        )}

        {/* 2-col grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[...Array(4)].map((_, i) => <CardSkeleton key={i} />)}
          </div>
        ) : rest.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {rest.map((t) => (
              <TopicCard key={t.rank} topic={t} onReadMore={() => setSelectedTopic(t)} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && !hero && data?.status !== "generating" && (
          <div className="card text-center py-16 space-y-3">
            <div className="text-4xl">🌐</div>
            <p className="text-softly-dark font-semibold">No newsletter yet</p>
            <p className="text-stone-500 text-sm">The pipeline will auto-generate the first edition shortly.</p>
          </div>
        )}

        {/* Footer note */}
        <p className="text-center text-[11px] text-stone-400">
          HealthSignal Newsletter • AI-generated insights from registered clinical trial data.
          Not a substitute for professional medical advice.
        </p>
      </div>

      {/* Article modal */}
      {selectedTopic && (
        <ArticleModal topic={selectedTopic} onClose={() => setSelectedTopic(null)} />
      )}
    </>
  );
}
