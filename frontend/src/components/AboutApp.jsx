import React from 'react';
import { motion } from 'framer-motion';
import { Globe, Headphones, Equalizer, Lightning, ShieldCheck, Sparkle, ArrowsLeftRight } from '@phosphor-icons/react';
import ScrollFrameBackground from './ScrollFrameBackground';

export default function AboutApp() {
  return (
    <div className="min-h-[100dvh] flex flex-col bg-bgBase text-textPrimary selection:bg-accentPrimary/30 selection:text-accentPrimary relative">
      
      {/* Dynamic 180-Frame Scroll Background */}
      <ScrollFrameBackground />

      {/* Transparent Sticky Navbar */}
      <nav className="sticky top-0 flex items-center justify-between py-5 px-6 md:px-12 bg-transparent z-50 pointer-events-auto">
        
        {/* Brand Name Only */}
        <div className="flex items-center">
          <a href="/" className="font-display font-bold text-2xl tracking-tight text-textPrimary hover:opacity-90 transition-opacity">
            Acoustic<span className="text-accentPrimary">Search.</span>
          </a>
        </div>
        
        {/* Centered Glassmorphism Floating Pill Container */}
        <div className="hidden md:flex items-center gap-1 bg-[#0F141C]/60 backdrop-blur-2xl border border-white/10 rounded-full px-3 py-1.5 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
          <a href="/#how-it-works" className="px-5 py-2 rounded-full text-xs font-mono uppercase tracking-wider text-textMuted hover:text-textPrimary hover:bg-white/10 transition-all">
            How It Works
          </a>
          <a href="/#advanced-eq" className="px-5 py-2 rounded-full text-xs font-mono uppercase tracking-wider text-textMuted hover:text-textPrimary hover:bg-white/10 transition-all">
            Advanced EQ
          </a>
          <a href="/#faq" className="px-5 py-2 rounded-full text-xs font-mono uppercase tracking-wider text-textMuted hover:text-textPrimary hover:bg-white/10 transition-all">
            FAQ
          </a>
          <a href="/about" className="px-5 py-2 rounded-full text-xs font-mono uppercase tracking-wider bg-white/10 text-accentPrimary font-bold transition-all">
            About IEMs
          </a>
        </div>

        {/* Right CTA Button */}
        <div className="flex items-center gap-4">
          <button className="hidden lg:flex items-center gap-2 text-xs font-mono uppercase text-textMuted hover:text-textPrimary transition-colors">
            <Globe weight="bold" size={16} /> EN
          </button>
          
          <motion.a 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            href="/"
            className="bg-accentPrimary text-black px-6 py-2.5 rounded-full text-xs font-mono font-bold uppercase tracking-wider hover:brightness-110 transition-all shadow-[0_0_20px_rgba(210,248,91,0.35)] flex items-center gap-2"
          >
            <ArrowsLeftRight size={16} weight="bold" /> Compare
          </motion.a>
        </div>
      </nav>

      {/* Hero Header */}
      <header className="relative z-10 pt-16 md:pt-24 pb-16 px-6 md:px-12 max-w-[1200px] mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accentPrimary/10 border border-accentPrimary/30 text-accentPrimary font-mono text-xs uppercase tracking-widest mb-6 backdrop-blur-xl">
          <Sparkle weight="bold" size={14} /> Audiophile 101 Guide
        </div>
        <h1 className="font-display text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight text-textPrimary mb-6 leading-[1.1] drop-shadow-lg">
          What Are IEMs (In-Ear Monitors) & How Are They Different From Earphones?
        </h1>
        <p className="font-body text-textMuted text-lg md:text-xl max-w-3xl mx-auto leading-relaxed drop-shadow">
          You are probably coming across the term "In-Ear Monitor" for the first time while searching for audio gear. Here is everything you need to know about what IEMs are, why they sound so incredible, and how they differ from regular earphones.
        </p>
      </header>

      {/* Main Content Sections / Translucent Bento Grid Layout */}
      <main className="relative z-10 flex-1 max-w-[1200px] mx-auto px-6 md:px-12 pb-24 space-y-16">
        
        {/* Section 1: The Difference */}
        <section className="bg-[#0F141C]/50 border border-white/10 rounded-[2.5rem] p-8 md:p-12 backdrop-blur-2xl relative overflow-hidden shadow-2xl">
          <div className="absolute -top-24 -right-24 w-96 h-96 bg-accentPrimary/10 rounded-full blur-3xl pointer-events-none"></div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center">
            <div>
              <span className="font-mono text-xs uppercase tracking-widest text-accentPrimary block mb-3">01. The Anatomy</span>
              <h2 className="font-display text-3xl md:text-4xl font-bold text-textPrimary mb-6">
                Earphones vs In-Ear Monitors
              </h2>
              <p className="font-body text-textMuted text-base md:text-lg leading-relaxed mb-4">
                Most of us are familiar with canal-type in-ear earphones. They feature a silicone earbud that sits inside the ear canal, giving a snug fit and blocking out surrounding noise. 
              </p>
              <p className="font-body text-textMuted text-base md:text-lg leading-relaxed">
                However, standard earphones on their own are fundamentally different from <strong>In-Ear Monitors (IEMs)</strong>, which are precision acoustic instruments engineered strictly for fidelity and accuracy.
              </p>
            </div>
            
            <div className="bg-black/30 border border-white/10 rounded-2xl p-6 space-y-4">
              <div className="flex items-start gap-4 p-4 rounded-xl bg-white/5 border border-white/5">
                <Headphones size={32} className="text-textMuted shrink-0" />
                <div>
                  <h4 className="font-display font-semibold text-textPrimary text-base">Standard Earphones</h4>
                  <p className="font-body text-xs text-textMuted mt-1">Built for basic consumer listening. Single dynamic driver, non-detachable cables, and generic sound signatures.</p>
                </div>
              </div>
              <div className="flex items-start gap-4 p-4 rounded-xl bg-accentPrimary/10 border border-accentPrimary/30">
                <Equalizer size={32} className="text-accentPrimary shrink-0" />
                <div>
                  <h4 className="font-display font-semibold text-accentPrimary text-base">In-Ear Monitors (IEMs)</h4>
                  <p className="font-body text-xs text-textPrimary/80 mt-1">Engineered for studio detail. Multi-driver arrays, detachable cables, noise isolation, and lifelike acoustic realism.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Section 2: Born on the Stage */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-2 bg-[#0F141C]/50 border border-white/10 rounded-[2.5rem] p-8 md:p-10 backdrop-blur-2xl flex flex-col justify-between shadow-2xl">
            <div>
              <span className="font-mono text-xs uppercase tracking-widest text-accentPrimary block mb-3">02. The Heritage</span>
              <h2 className="font-display text-3xl font-bold text-textPrimary mb-4">
                Designed by Professionals for Live Performers
              </h2>
              <p className="font-body text-textMuted text-base leading-relaxed mb-4">
                In-Ear Monitors were originally designed by professional musicians and mix engineers for artists, singers, and drummers on stage.
              </p>
              <p className="font-body text-textMuted text-base leading-relaxed">
                Traditionally, musicians used massive monitor speakers on stage pointed at them. IEMs replaced those speakers by blocking out crowd noise completely, allowing artists to hear themselves and each bandmate with perfect clarity at controlled, safe volumes.
              </p>
            </div>
          </div>

          <div className="bg-[#0F141C]/50 border border-white/10 rounded-[2.5rem] p-8 md:p-10 backdrop-blur-2xl flex flex-col justify-between shadow-2xl">
            <div className="w-12 h-12 rounded-2xl bg-accentPrimary/20 flex items-center justify-center text-accentPrimary mb-6">
              <Lightning size={24} weight="bold" />
            </div>
            <div>
              <h3 className="font-display text-xl font-bold text-textPrimary mb-3">Multi-Driver Architecture</h3>
              <p className="font-body text-textMuted text-sm leading-relaxed">
                IEMs can pack multiple drivers (Dynamic, Balanced Armatures, Planar Magnetics) into a single tiny ear shell to handle sub-bass, vocals, and treble independently.
              </p>
            </div>
          </div>
        </section>

        {/* Section 3: Ergonomics & Sound Resolution */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-8">
          
          <div className="bg-[#0F141C]/50 border border-white/10 rounded-[2.5rem] p-8 md:p-10 backdrop-blur-2xl shadow-2xl">
            <span className="font-mono text-xs uppercase tracking-widest text-accentPrimary block mb-3">03. Ergonomics</span>
            <h3 className="font-display text-2xl font-bold text-textPrimary mb-4">
              The Over-Ear Cable Design
            </h3>
            <p className="font-body text-textMuted text-base leading-relaxed mb-4">
              With traditional earphones, heavy earbuds pull down on your ear canal, causing fatigue and pain during long listening sessions.
            </p>
            <p className="font-body text-textMuted text-base leading-relaxed">
              IEMs feature an ergonomic shell worn with cables looped over your ear pinna. This distributes weight evenly across your earlobe—similar to wearing a pair of glasses—allowing for hours of comfortable, fatigue-free music enjoyment.
            </p>
          </div>

          <div className="bg-[#0F141C]/50 border border-white/10 rounded-[2.5rem] p-8 md:p-10 backdrop-blur-2xl shadow-2xl">
            <span className="font-mono text-xs uppercase tracking-widest text-accentPrimary block mb-3">04. Sound Quality</span>
            <h3 className="font-display text-2xl font-bold text-textPrimary mb-4">
              Built Solely to Sound Incredible
            </h3>
            <p className="font-body text-textMuted text-base leading-relaxed mb-4">
              Until recently, high-end IEMs were expensive stage tools used exclusively by touring artists.
            </p>
            <p className="font-body text-textMuted text-base leading-relaxed">
              Today, driver technology has trickled down. Audiophiles and music lovers can experience lifelike soundstage, rich sub-bass, and crystal-clear acoustic separation at every budget tier.
            </p>
          </div>

        </section>

        {/* Source Attribution Box */}
        <div className="p-6 rounded-2xl bg-[#0F141C]/60 backdrop-blur-2xl border border-white/10 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <ShieldCheck size={32} className="text-accentPrimary shrink-0" />
            <div>
              <p className="font-mono text-xs text-textMuted uppercase tracking-wider">Source Attribution</p>
              <p className="font-body text-sm text-textPrimary">Guide content adapted from <strong>Headphone Zone's Audiophile 101</strong> guide.</p>
            </div>
          </div>
          <a 
            href="https://www.headphonezone.in/blogs/audiophile-101/what-are-iems-or-in-ears-monitors-and-how-are-they-different-from-earphones" 
            target="_blank" 
            rel="noopener noreferrer"
            className="font-mono text-xs text-accentPrimary hover:underline uppercase tracking-wider shrink-0"
          >
            Read Original Article →
          </a>
        </div>

      </main>

      {/* Footer */}
      <footer className="w-full bg-black/60 backdrop-blur-2xl border-t border-white/10 px-6 md:px-12 py-16 relative z-10 text-textMuted">
        <div className="max-w-[1400px] mx-auto grid grid-cols-1 md:grid-cols-4 gap-10 mb-12">
          <div className="md:col-span-2">
            <a href="/" className="font-display font-bold text-2xl tracking-tight text-textPrimary block mb-4">
              Acoustic<span className="text-accentPrimary">Search.</span>
            </a>
            <p className="font-body text-sm text-textMuted max-w-sm leading-relaxed mb-6">
              AI-powered In-Ear Monitor recommendation engine combining natural language processing, vector embeddings, and acoustic curve math.
            </p>
          </div>

          <div>
            <h4 className="font-mono text-xs text-textPrimary uppercase tracking-widest mb-4">Navigation</h4>
            <ul className="space-y-2.5 text-sm">
              <li><a href="/" className="hover:text-accentPrimary transition-colors">Search Engine</a></li>
              <li><a href="/#how-it-works" className="hover:text-accentPrimary transition-colors">How It Works</a></li>
              <li><a href="/#faq" className="hover:text-accentPrimary transition-colors">FAQs</a></li>
              <li><a href="/about" className="hover:text-accentPrimary transition-colors">About IEMs</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-mono text-xs text-textPrimary uppercase tracking-widest mb-4">Acoustic Traits</h4>
            <div className="flex flex-wrap gap-1.5 text-xs font-mono">
              <span className="px-2 py-1 bg-white/5 rounded text-textMuted">Sub-bass</span>
              <span className="px-2 py-1 bg-white/5 rounded text-textMuted">Warm Mids</span>
              <span className="px-2 py-1 bg-white/5 rounded text-textMuted">Airy Treble</span>
            </div>
          </div>
        </div>

        <div className="max-w-[1400px] mx-auto border-t border-white/5 pt-8 flex flex-col md:flex-row items-center justify-between gap-4 text-xs font-mono">
          <p>© {new Date().getFullYear()} AcousticSearch. All rights reserved.</p>
          <p className="text-textMuted/60">Crafted for Audiophiles & Music Enthusiasts</p>
        </div>
      </footer>

    </div>
  );
}
