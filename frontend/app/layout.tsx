import type { Metadata } from "next";
import { ClerkProvider, SignInButton, SignedIn, SignedOut, UserButton } from '@clerk/nextjs'
import { Outfit, Reenie_Beanie } from "next/font/google";
import "./globals.css";

const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });
const reenie = Reenie_Beanie({ weight: "400", subsets: ["latin"], variable: "--font-reenie" });

export const metadata: Metadata = {
  title: "HealthSignal — Clinical Trial Intelligence",
  description: "Multi-agent AI platform for clinical trial monitoring",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className={`${outfit.variable} ${reenie.variable} font-sans bg-softly-bg text-softly-dark min-h-screen relative selection:bg-softly-coral selection:text-white`}>
        {/* SVG Noise Overlay */}
        <div className="fixed inset-0 z-0 pointer-events-none opacity-[0.35] mix-blend-overlay">
          <svg className="w-full h-full">
            <filter id="noise">
              <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch" />
            </filter>
            <rect width="100%" height="100%" filter="url(#noise)" />
          </svg>
        </div>

        {/* Floating Pill Nav */}
        <div className="fixed top-4 left-0 right-0 z-40 flex justify-center px-4">
          <nav className="bg-white/70 backdrop-blur-[20px] shadow-[0_4px_20px_-2px_rgba(0,0,0,0.05)] rounded-full px-6 py-3 flex items-center gap-6 max-w-full overflow-x-auto no-scrollbar border border-white/40">
            <a href="/" className="flex items-center gap-2 shrink-0">
              <svg className="w-5 h-5 text-softly-coral" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span className="font-semibold tracking-tight text-softly-dark hidden sm:block">
                HealthSignal
              </span>
            </a>
            <div className="flex items-center gap-4 text-[14px] font-medium text-softly-muted shrink-0">
              <a href="/trials" className="hover:text-softly-dark transition-colors">Database</a>
              <a href="/search" className="hover:text-softly-dark transition-colors">Search</a>
              <a href="/ask" className="hover:text-softly-dark transition-colors">Ask AI</a>
              <a href="/evals" className="hover:text-softly-dark transition-colors">Evals</a>
            </div>
            <a href="/ask" className="bg-softly-dark text-white text-[14px] font-medium px-4 py-1.5 rounded-full shrink-0 hover:bg-black transition-colors ml-auto sm:ml-4">
              Try Demo
            </a>
            <div className="shrink-0 flex items-center ml-2">
              <SignedOut>
                <SignInButton mode="modal">
                  <button className="text-[14px] font-medium text-softly-dark hover:text-softly-coral transition-colors">Sign In</button>
                </SignInButton>
              </SignedOut>
              <SignedIn>
                <UserButton afterSignOutUrl="/" />
              </SignedIn>
            </div>
          </nav>
        </div>

        <main className="max-w-6xl mx-auto px-4 sm:px-6 pt-28 pb-12 relative z-10">{children}</main>
      </body>
    </html>
    </ClerkProvider>
  );
}
