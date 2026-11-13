import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { ScanFace, CheckCircle2, ShieldCheck, Zap, Sparkles } from 'lucide-react';
import { useTheme } from '../stores/themeStore';
import { Sun, Moon } from 'lucide-react';

export const AuthLayout: React.FC = () => {
  const { isDark, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen flex flex-col justify-between bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Top Bar with Logo & Theme Switcher */}
      <header className="flex items-center justify-between px-6 py-4 lg:px-12">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-700 to-brand-500 shadow-md shadow-brand-500/25 text-white group-hover:scale-105 transition-transform">
            <ScanFace className="h-6 w-6" />
          </div>
          <span className="text-xl font-extrabold tracking-tight">
            ATTENDORA
          </span>
        </Link>

        <button
          onClick={toggleTheme}
          className="rounded-xl p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-slate-200 transition-colors"
          title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        >
          {isDark ? <Sun className="h-5 w-5 text-amber-400" /> : <Moon className="h-5 w-5" />}
        </button>
      </header>

      {/* Main Centered Content */}
      <main className="flex-1 flex items-center justify-center p-4 sm:p-6 lg:p-8">
        <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Left Hero / Brand showcase (visible on desktop) */}
          <div className="hidden lg:flex lg:col-span-5 flex-col justify-center space-y-6 pr-4">
            <div className="inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50/80 px-3 py-1 text-xs font-semibold text-brand-700 dark:border-brand-800 dark:bg-brand-950/60 dark:text-brand-300 w-fit">
              <Sparkles className="h-3.5 w-3.5 text-brand-600 dark:text-brand-400" />
              <span>Next-Gen Facial AI Platform</span>
            </div>

            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-tight">
              Enterprise Attendance Powered by Precision Vision AI
            </h1>

            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
              Eliminate buddy punching and time theft with millisecond face verification, multi-camera live feeds, and automated shift scheduling.
            </p>

            <div className="space-y-3 pt-2">
              <div className="flex items-center gap-2.5 text-xs text-slate-700 dark:text-slate-300">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                <span>99.8% recognition accuracy with anti-spoofing liveness</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-slate-700 dark:text-slate-300">
                <ShieldCheck className="h-4 w-4 text-brand-600 dark:text-brand-400 shrink-0" />
                <span>Multi-tenant data isolation & GDPR/HIPAA compliant</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-slate-700 dark:text-slate-300">
                <Zap className="h-4 w-4 text-amber-500 shrink-0" />
                <span>Plug-and-play RTSP IP cameras and USB webcams</span>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200/80 bg-white/70 p-4 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/60">
              <p className="text-xs italic text-slate-600 dark:text-slate-400">
                &ldquo;Attendora eliminated attendance queues completely across our 3 campus locations in under 48 hours.&rdquo;
              </p>
              <div className="mt-2 text-[11px] font-semibold text-slate-900 dark:text-slate-200">
                — Director of Operations, Nexus Corp
              </div>
            </div>
          </div>

          {/* Right Card / Form Container */}
          <div className="w-full lg:col-span-7 flex justify-center">
            <div className="w-full max-w-md rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-xl shadow-slate-200/40 dark:border-slate-800 dark:bg-slate-900 dark:shadow-slate-950/60">
              <Outlet />
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-4 text-center text-xs text-slate-500 dark:text-slate-500">
        &copy; {new Date().getFullYear()} Attendora Inc. Enterprise AI Attendance SaaS. All rights reserved.
      </footer>
    </div>
  );
};

export default AuthLayout;
