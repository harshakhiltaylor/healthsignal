"use client";
import { useState } from "react";
import Link from "next/link";
import { ChevronDown, Plus } from "lucide-react";

const SCENARIOS = [
  { time: "09:41 AM", text: "New Phase 3 obesity trial announced." },
  { time: "11:20 AM", text: "FDA approved novel gene therapy." },
  { time: "02:15 PM", text: "Updated protocol for oncology study." },
  { time: "04:30 PM", text: "Pediatric enrollment completed." },
  { time: "06:00 PM", text: "AI evaluation scored 98% faithfulness." },
];

const TESTIMONIALS = [
  {
    quote: "HealthSignal transformed how we monitor competitor pipelines. The AI insights are incredibly accurate and save us hours of manual reading.",
    author: "Dr. Sarah Jenkins",
    role: "Clinical Strategist",
    rotate: "rotate-1",
  },
  {
    quote: "Finally, a platform that makes clinical trial data feel accessible. The interface is calming, and the search capabilities are unmatched.",
    author: "Michael Chang",
    role: "Lead Researcher",
    rotate: "-rotate-1",
  },
];

const FAQS = [
  { q: "How often is the database updated?", a: "We run a nightly ingestion pipeline directly from ClinicalTrials.gov to ensure you always have the latest data." },
  { q: "Can I use natural language to search?", a: "Yes, our semantic search allows you to type queries naturally, powered by PubMedBERT and PGVector." },
  { q: "How accurate are the AI evaluations?", a: "We use an advanced RAG pipeline with Ragas evaluation, consistently scoring above our 0.85 faithfulness threshold." },
];

export default function LandingPage() {
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  return (
    <div className="flex flex-col items-center overflow-x-hidden pt-10">
      {/* Background Blobs */}
      <div className="fixed top-20 left-1/2 -translate-x-1/2 w-full max-w-5xl h-full pointer-events-none z-[-1]">
        <div className="absolute top-0 left-10 w-[500px] h-[500px] bg-[#FFE4E1] rounded-full mix-blend-multiply filter blur-[100px] opacity-60 animate-blob"></div>
        <div className="absolute top-20 right-10 w-[400px] h-[400px] bg-[#E6E6FA] rounded-full mix-blend-multiply filter blur-[120px] opacity-60 animate-blob" style={{ animationDelay: "2s" }}></div>
      </div>

      {/* Hero Section */}
      <section className="w-full flex flex-col items-center text-center px-4 mb-32 animate-reveal">
        <h1 className="text-[48px] md:text-[72px] font-semibold text-softly-dark tracking-tight leading-[1.1] max-w-3xl">
          Clinical trial intelligence, <span className="font-cursive text-softly-coral font-normal text-[64px] md:text-[96px] leading-[0.5] align-bottom inline-block -mb-4">simplified</span>
        </h1>
        <p className="mt-8 text-softly-muted text-lg max-w-[500px] leading-relaxed">
          HealthSignal aggregates millions of clinical trials into an actionable, beautifully designed digital living room for researchers and strategists.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 mt-10">
          <Link href="/ask" className="bg-softly-coral text-white font-medium px-8 py-4 rounded-full shadow-[0_8px_30px_rgba(255,183,178,0.4)] hover:scale-105 transition-transform">
            Start Exploring
          </Link>
          <Link href="/trials" className="bg-white text-softly-dark font-medium px-8 py-4 rounded-full border border-stone-200 hover:bg-stone-50 transition-colors">
            View Database
          </Link>
        </div>
      </section>

      {/* Horizontal Scenario Scroll */}
      <section className="w-full mb-32 relative">
        <div className="flex gap-6 overflow-x-auto pb-8 px-4 sm:px-10 no-scrollbar snap-x">
          {SCENARIOS.map((s, i) => (
            <div key={i} className="shrink-0 w-[288px] h-[160px] bg-white rounded-[24px] p-6 shadow-sm border border-stone-100 flex flex-col justify-between group hover:border-softly-coral transition-colors snap-center">
              <div className="text-[14px] text-stone-400 font-medium">{s.time}</div>
              <div className="text-[20px] text-stone-800 font-medium leading-snug group-hover:text-softly-coral transition-colors">
                {s.text}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* App Experience Preview */}
      <section className="w-full mb-40 flex justify-center items-center px-4">
        <div className="relative flex justify-center items-center h-[700px] w-full max-w-4xl">
          {/* Left Phone */}
          <div className="absolute left-0 md:left-[10%] w-[280px] h-[580px] bg-softly-sage rounded-[40px] shadow-xl opacity-80 translate-y-[48px] border-8 border-white hidden sm:block overflow-hidden">
            <div className="p-6">
              <div className="w-1/2 h-4 bg-white/50 rounded-full mb-8"></div>
              <div className="space-y-4">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="w-full h-20 bg-white/40 rounded-2xl"></div>
                ))}
              </div>
            </div>
          </div>
          
          {/* Right Phone */}
          <div className="absolute right-0 md:right-[10%] w-[280px] h-[580px] bg-softly-lavender rounded-[40px] shadow-xl opacity-80 translate-y-[96px] border-8 border-white hidden sm:block overflow-hidden">
            <div className="p-6">
              <div className="w-2/3 h-4 bg-white/50 rounded-full mb-8"></div>
              <div className="w-full h-40 bg-white/40 rounded-2xl mb-4"></div>
              <div className="w-full h-40 bg-white/40 rounded-2xl"></div>
            </div>
          </div>

          {/* Center Phone */}
          <div className="relative z-10 w-[300px] h-[620px] bg-white rounded-[40px] shadow-2xl border-8 border-stone-100 flex flex-col justify-between overflow-hidden">
            <div className="p-6 pt-10">
              <h3 className="text-2xl font-semibold text-softly-dark leading-tight">Patient Search <br/> & Analysis</h3>
              <div className="mt-6 space-y-4">
                <div className="p-4 bg-stone-50 rounded-2xl">
                  <div className="text-xs text-stone-400 mb-1">Query</div>
                  <div className="text-sm font-medium text-stone-700">GLP-1 phase 3 trials</div>
                </div>
                <div className="p-4 bg-softly-bg rounded-2xl border border-stone-100">
                  <div className="text-sm text-stone-600 leading-relaxed">Found 24 matching studies. The primary completion date for the leading study is expected in Q4 2026.</div>
                </div>
              </div>
            </div>
            <div className="p-6 pb-10 flex justify-center">
              <Link href="/search">
                <button className="w-24 h-24 rounded-full bg-softly-coral shadow-[0_0_0_8px_rgba(255,183,178,0.2)] flex items-center justify-center text-white font-medium hover:scale-105 transition-transform animate-pulse">
                  Analyze
                </button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Diary Entry Testimonials */}
      <section className="w-full max-w-4xl px-4 mb-32">
        <h2 className="text-3xl font-semibold text-center mb-16">What our researchers say</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          {TESTIMONIALS.map((t, i) => (
            <div key={i} className={`bg-white p-8 rounded-[2rem] shadow-sm border border-stone-100 ${t.rotate}`}>
              <p className="text-lg text-softly-dark leading-relaxed mb-10">"{t.quote}"</p>
              <div>
                <div className="w-8 h-[1px] bg-stone-300 mb-4"></div>
                <div className="font-cursive text-2xl text-stone-500">{t.author}</div>
                <div className="text-xs text-stone-400 mt-1 uppercase tracking-widest">{t.role}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Interactive FAQ Accordion */}
      <section className="w-full max-w-2xl px-4 mb-32">
        <h2 className="text-3xl font-semibold text-center mb-10">Common Questions</h2>
        <div className="bg-white rounded-[16px] border border-stone-100 overflow-hidden">
          {FAQS.map((faq, i) => (
            <div key={i} className="border-b border-stone-100 last:border-0">
              <button
                onClick={() => setOpenFaq(openFaq === i ? null : i)}
                className="w-full flex items-center justify-between p-6 text-left"
              >
                <span className="text-lg font-medium text-softly-dark">{faq.q}</span>
                <Plus className={`w-5 h-5 text-stone-400 transition-transform duration-300 ${openFaq === i ? "rotate-45" : ""}`} />
              </button>
              <div
                className={`overflow-hidden transition-all duration-500 ease-in-out ${openFaq === i ? "max-h-40" : "max-h-0"}`}
              >
                <div className="px-6 pb-6 text-stone-500 leading-relaxed">
                  {faq.a}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Waitlist Conversion */}
      <section className="w-full relative py-32 flex flex-col items-center text-center px-4 overflow-hidden rounded-[3rem] mb-20">
        <div className="absolute inset-0 bg-softly-sage/30 pointer-events-none"></div>
        <div className="absolute top-0 left-1/4 w-[300px] h-[300px] bg-softly-coral/20 rounded-full filter blur-[80px] pointer-events-none"></div>
        <div className="absolute bottom-0 right-1/4 w-[300px] h-[300px] bg-softly-lavender/40 rounded-full filter blur-[80px] pointer-events-none"></div>
        
        <div className="relative z-10">
          <div className="w-16 h-16 bg-softly-dark rounded-2xl mx-auto mb-8 flex items-center justify-center">
            <div className="w-4 h-4 bg-softly-coral rounded-full"></div>
          </div>
          <h2 className="text-4xl md:text-5xl font-semibold text-softly-dark mb-6 tracking-tight">Stay in the loop</h2>
          <p className="text-stone-500 mb-10 max-w-md mx-auto">
            Join our waitlist to get early access to advanced AI pipeline features and custom evaluation models.
          </p>
          <form className="flex flex-col sm:flex-row gap-3 justify-center max-w-md mx-auto" onSubmit={(e) => e.preventDefault()}>
            <input 
              type="email" 
              placeholder="Enter your email" 
              className="w-full sm:w-auto flex-1 bg-white border border-stone-200 rounded-full px-6 py-4 text-stone-700 placeholder-stone-400 focus:outline-none focus:border-softly-coral shadow-sm"
              required
            />
            <button type="submit" className="bg-softly-dark text-white font-medium rounded-full px-8 py-4 hover:scale-105 transition-transform whitespace-nowrap">
              Join Waitlist
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}
