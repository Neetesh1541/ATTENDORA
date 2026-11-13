import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ScanFace,
  ShieldCheck,
  Video,
  BarChart3,
  CalendarCheck,
  Sparkles,
  Zap,
  Building2,
  GraduationCap,
  Factory,
  HeartPulse,
  ShoppingBag,
  Dumbbell,
  CheckCircle,
  ArrowRight,
  Sun,
  Moon,
  ChevronRight,
  Users,
  Clock,
  Layers,
  Lock,
} from 'lucide-react';
import { useTheme } from '../stores/themeStore';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';

export const LandingPage: React.FC = () => {
  const { isDark, toggleTheme } = useTheme();
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly');

  const features = [
    {
      icon: ScanFace,
      title: 'Precision Face Recognition',
      description:
        'State-of-the-art 128-d deep facial embeddings deliver 99.8% verification accuracy with sub-500ms matching time.',
      tag: 'Core AI',
    },
    {
      icon: Video,
      title: 'Universal Camera Support',
      description:
        'Connect any RTSP/IP security camera, USB webcam, or tablet kiosk without expensive proprietary hardware.',
      tag: 'Hardware-Agnostic',
    },
    {
      icon: ShieldCheck,
      title: 'Multi-Tenant Security',
      description:
        'Complete data isolation per organization, encrypted facial vectors, and zero raw biometric image exposure.',
      tag: 'Enterprise Ready',
    },
    {
      icon: Clock,
      title: 'Dynamic Shift Engine',
      description:
        'Customizable grace periods, automated overnight shifts, overtime calculation, and seamless holiday calendars.',
      tag: 'Automation',
    },
    {
      icon: BarChart3,
      title: 'Real-time Intelligence',
      description:
        'Interactive dashboards, attendance heatmaps, absence trends, and automated export to Excel, CSV, and PDF.',
      tag: 'Analytics',
    },
    {
      icon: Lock,
      title: 'Liveness & Anti-Spoofing',
      description:
        'AI protection against printed photos, mobile screen replays, and mask attacks ensures 100% genuine presence.',
      tag: 'Fraud Proof',
    },
  ];

  const workflowSteps = [
    {
      step: '01',
      title: 'Enroll Members & Capture Vectors',
      description:
        'Bulk import employees or students with a single click, or capture 3-second self-registration face samples via webcam.',
    },
    {
      step: '02',
      title: 'Deploy Cameras & Assign Schedules',
      description:
        'Link lobby IP cameras or tablet devices at entry points. Configure department shifts, grace periods, and weekly offs.',
    },
    {
      step: '03',
      title: 'Automate Attendance & Reporting',
      description:
        'Members walk past cameras naturally. Attendance logs instantly, alerts trigger for late arrivals, and reports generate automatically.',
    },
  ];

  const orgTypes = [
    { name: 'Corporate Tech Parks', icon: Building2, count: '5,000+ staff' },
    { name: 'Colleges & Universities', icon: GraduationCap, count: '20,000+ students' },
    { name: 'Factories & Industrial', icon: Factory, count: '3-shift operations' },
    { name: 'Hospitals & Clinics', icon: HeartPulse, count: '24/7 staff coverage' },
    { name: 'Retail Store Chains', icon: ShoppingBag, count: 'Multi-store sync' },
    { name: 'Fitness & Gym Centers', icon: Dumbbell, count: 'Member check-ins' },
  ];

  const pricingTiers = [
    {
      name: 'Starter',
      price: billingPeriod === 'monthly' ? '$49' : '$39',
      period: '/mo',
      description: 'Ideal for small offices, studios, and single branch setups.',
      features: [
        'Up to 50 active members',
        '2 camera / webcam streams',
        '2 organization admins',
        'Standard shifts & grace times',
        'Excel & CSV export',
        'Email notifications',
      ],
      popular: false,
      cta: 'Start Free Trial',
    },
    {
      name: 'Professional',
      price: billingPeriod === 'monthly' ? '$129' : '$99',
      period: '/mo',
      description: 'Engineered for growing organizations with multi-department rosters.',
      features: [
        'Up to 300 active members',
        '8 camera / RTSP streams',
        'Unlimited managers & admins',
        'Multi-shift & overnight schedules',
        'Attendance correction workflows',
        'Advanced analytics & heatmaps',
        'Priority email & Slack support',
      ],
      popular: true,
      cta: 'Start Free Trial',
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      description: 'For large campuses, universities, factories, and multi-location companies.',
      features: [
        'Unlimited members & cameras',
        'Dedicated on-premise AI relay option',
        'Custom HRMS / ERP webhooks & API',
        'Full audit logging & compliance reports',
        'Custom SLA & 99.99% uptime guarantee',
        'Dedicated account manager',
      ],
      popular: false,
      cta: 'Contact Sales',
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 transition-colors duration-200 dark:bg-slate-950 dark:text-slate-100">
      {/* ─── Navigation Bar ─── */}
      <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/80 backdrop-blur-md dark:border-slate-800/80 dark:bg-slate-950/80">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-700 to-brand-500 shadow-md shadow-brand-500/25 text-white group-hover:scale-105 transition-transform">
              <ScanFace className="h-6 w-6" />
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-xl font-extrabold tracking-tight">ATTENDORA</span>
              <span className="text-xs font-semibold text-brand-600 dark:text-brand-400">AI</span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600 dark:text-slate-300">
            <a href="#features" className="hover:text-brand-600 dark:hover:text-white transition-colors">
              Features
            </a>
            <a href="#how-it-works" className="hover:text-brand-600 dark:hover:text-white transition-colors">
              How It Works
            </a>
            <a href="#solutions" className="hover:text-brand-600 dark:hover:text-white transition-colors">
              Industries
            </a>
            <a href="#pricing" className="hover:text-brand-600 dark:hover:text-white transition-colors">
              Pricing
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <button
              onClick={toggleTheme}
              className="rounded-xl p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-slate-200 transition-colors"
              title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {isDark ? <Sun className="h-5 w-5 text-amber-400" /> : <Moon className="h-5 w-5" />}
            </button>

            <Link to="/login">
              <Button variant="ghost" size="sm">
                Log In
              </Button>
            </Link>

            <Link to="/register">
              <Button variant="primary" size="sm" rightIcon={<ArrowRight className="h-3.5 w-3.5" />}>
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* ─── Hero Section ─── */}
      <section className="relative overflow-hidden pt-12 pb-20 sm:pt-20 sm:pb-28">
        {/* Ambient background glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 bg-gradient-to-b from-brand-500/15 via-transparent to-transparent blur-3xl pointer-events-none" />

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50/80 px-4 py-1.5 text-xs font-semibold text-brand-700 dark:border-brand-800 dark:bg-brand-950/60 dark:text-brand-300 shadow-sm"
          >
            <Sparkles className="h-3.5 w-3.5 text-brand-600 dark:text-brand-400" />
            <span>Attendora AI Face Recognition Engine v3.0 Live</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mt-6 text-4xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl"
          >
            Touchless Attendance.{' '}
            <span className="bg-gradient-to-r from-brand-600 via-indigo-500 to-sky-500 bg-clip-text text-transparent">
              Zero Queues.
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mx-auto mt-6 max-w-2xl text-base sm:text-lg text-slate-600 dark:text-slate-400"
          >
            Replace outdated biometric thumb scanners and manual paper logs with instant AI facial recognition. Works with any standard camera, tablet, or existing RTSP security stream.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link to="/register">
              <Button size="lg" variant="primary" rightIcon={<ArrowRight className="h-4 w-4" />}>
                Start 14-Day Free Trial
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="outline">
                Explore Live Demo
              </Button>
            </Link>
          </motion.div>

          {/* Interactive Simulated Vision AI Preview */}
          <motion.div
            initial={{ opacity: 0, y: 35 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.4 }}
            className="relative mx-auto mt-16 max-w-4xl rounded-2xl border border-slate-200/80 bg-white p-3 shadow-2xl dark:border-slate-800 dark:bg-slate-900 shadow-brand-500/10"
          >
            <div className="relative aspect-video w-full overflow-hidden rounded-xl bg-slate-950 flex items-center justify-center border border-slate-800">
              {/* Simulated camera feed scan animation */}
              <div className="absolute inset-0 bg-radial-gradient opacity-30" />
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-brand-500 to-transparent animate-scan" />

              {/* Grid overlay */}
              <div
                className="absolute inset-0 opacity-15"
                style={{
                  backgroundImage: 'radial-gradient(circle, #6366f1 1px, transparent 1px)',
                  backgroundSize: '24px 24px',
                }}
              />

              {/* Simulated bounding boxes for detected faces */}
              <div className="relative z-10 flex flex-col items-center">
                <div className="relative flex flex-col items-center justify-center p-6 border-2 border-dashed border-brand-500/80 rounded-2xl bg-brand-950/30 backdrop-blur-xs animate-pulse-subtle">
                  <div className="flex h-20 w-20 items-center justify-center rounded-full bg-slate-800/80 ring-4 ring-brand-500/40 text-brand-400">
                    <ScanFace className="h-10 w-10" />
                  </div>
                  <div className="mt-3 flex items-center gap-2 rounded-lg bg-emerald-500/20 px-2.5 py-1 text-xs font-semibold text-emerald-400 border border-emerald-500/40">
                    <CheckCircle className="h-3.5 w-3.5" />
                    <span>Sarah Jenkins (UID: EMP-1042) • Conf: 99.4%</span>
                  </div>
                  <span className="mt-1 text-[11px] text-slate-400">
                    Shift: Morning Core (09:00 - 17:00) • Status: Present (On Time)
                  </span>
                </div>
              </div>

              {/* Live HUD info overlay */}
              <div className="absolute top-4 left-4 flex items-center gap-2 rounded-lg bg-slate-900/80 px-2.5 py-1 text-[11px] font-mono text-emerald-400 border border-slate-800 backdrop-blur-md">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
                <span>CAMERA 01 [LOBBY MAIN] • 30 FPS • 1080P</span>
              </div>

              <div className="absolute bottom-4 right-4 flex items-center gap-2 rounded-lg bg-slate-900/80 px-2.5 py-1 text-[11px] font-mono text-slate-300 border border-slate-800 backdrop-blur-md">
                <span>LATENCY: 42ms • DETECTIONS: 1</span>
              </div>
            </div>
          </motion.div>

          {/* Social Proof Metric Bar */}
          <div className="mt-16 grid grid-cols-2 gap-4 md:grid-cols-4 border-y border-slate-200/80 py-8 dark:border-slate-800/80">
            <div>
              <div className="text-3xl font-extrabold text-slate-900 dark:text-white">99.8%</div>
              <div className="mt-1 text-xs text-slate-500">Recognition Accuracy</div>
            </div>
            <div>
              <div className="text-3xl font-extrabold text-brand-600 dark:text-brand-400">&lt;500ms</div>
              <div className="mt-1 text-xs text-slate-500">Verification Speed</div>
            </div>
            <div>
              <div className="text-3xl font-extrabold text-slate-900 dark:text-white">500,000+</div>
              <div className="mt-1 text-xs text-slate-500">Daily Attendances Verified</div>
            </div>
            <div>
              <div className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">99.99%</div>
              <div className="mt-1 text-xs text-slate-500">Service SLA Uptime</div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Features Grid ─── */}
      <section id="features" className="py-20 sm:py-28 bg-white dark:bg-slate-900/50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto">
            <h2 className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
              Enterprise AI Capabilities
            </h2>
            <h3 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl text-slate-900 dark:text-white">
              Engineered for Speed, Scale, and Reliability
            </h3>
            <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">
              From biometric verification to automated payroll-ready reporting, Attendora gives HR and Ops leaders complete control.
            </p>
          </div>

          <div className="mt-14 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feat) => (
              <div
                key={feat.title}
                className="group relative rounded-2xl border border-slate-200/80 bg-white p-7 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-xl dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700"
              >
                <div className="flex items-center justify-between mb-5">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-950/60 dark:text-brand-400 group-hover:scale-110 transition-transform">
                    <feat.icon className="h-6 w-6" />
                  </div>
                  <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                    {feat.tag}
                  </span>
                </div>

                <h4 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  {feat.title}
                </h4>
                <p className="mt-2 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
                  {feat.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── How It Works ─── */}
      <section id="how-it-works" className="py-20 sm:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto">
            <h2 className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
              Frictionless Setup
            </h2>
            <h3 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl text-slate-900 dark:text-white">
              Up and Running in 3 Simple Steps
            </h3>
          </div>

          <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            {workflowSteps.map((ws, i) => (
              <div
                key={ws.step}
                className="relative rounded-2xl border border-slate-200/80 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900"
              >
                <div className="text-4xl font-extrabold text-brand-600/20 dark:text-brand-400/20">
                  {ws.step}
                </div>
                <h4 className="mt-3 text-lg font-bold text-slate-900 dark:text-white">
                  {ws.title}
                </h4>
                <p className="mt-2 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
                  {ws.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Industries Supported ─── */}
      <section id="solutions" className="py-20 sm:py-28 bg-white dark:bg-slate-900/50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto">
            <h2 className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
              Versatile Deployments
            </h2>
            <h3 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl text-slate-900 dark:text-white">
              Tailored for Every Industry Environment
            </h3>
          </div>

          <div className="mt-14 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {orgTypes.map((item) => (
              <div
                key={item.name}
                className="flex flex-col items-center justify-center rounded-2xl border border-slate-200/80 bg-white p-5 text-center shadow-xs dark:border-slate-800 dark:bg-slate-900"
              >
                <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                  <item.icon className="h-6 w-6" />
                </div>
                <h5 className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                  {item.name}
                </h5>
                <span className="mt-1 text-[10px] text-slate-500">{item.count}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Pricing Section ─── */}
      <section id="pricing" className="py-20 sm:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto">
            <h2 className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
              Simple, Transparent Pricing
            </h2>
            <h3 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl text-slate-900 dark:text-white">
              Invest in Accuracy, Not Bulky Hardware
            </h3>

            {/* Toggle Billing Period */}
            <div className="mt-6 inline-flex items-center rounded-xl bg-slate-100 p-1 dark:bg-slate-800">
              <button
                type="button"
                onClick={() => setBillingPeriod('monthly')}
                className={`rounded-lg px-4 py-1.5 text-xs font-semibold transition-all ${
                  billingPeriod === 'monthly'
                    ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white'
                    : 'text-slate-600 dark:text-slate-400'
                }`}
              >
                Monthly Billing
              </button>
              <button
                type="button"
                onClick={() => setBillingPeriod('yearly')}
                className={`rounded-lg px-4 py-1.5 text-xs font-semibold transition-all flex items-center gap-1 ${
                  billingPeriod === 'yearly'
                    ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white'
                    : 'text-slate-600 dark:text-slate-400'
                }`}
              >
                <span>Annual Billing</span>
                <span className="rounded-md bg-emerald-100 px-1.5 py-0.2 text-[10px] font-bold text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                  Save 20%
                </span>
              </button>
            </div>
          </div>

          <div className="mt-14 grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch">
            {pricingTiers.map((tier) => (
              <div
                key={tier.name}
                className={`relative flex flex-col justify-between rounded-2xl border p-8 transition-all ${
                  tier.popular
                    ? 'border-brand-600 bg-white shadow-xl ring-2 ring-brand-600 dark:border-brand-500 dark:bg-slate-900 dark:ring-brand-500'
                    : 'border-slate-200/80 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900'
                }`}
              >
                {tier.popular && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full bg-brand-600 px-3 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white shadow-md">
                    Most Popular
                  </div>
                )}

                <div>
                  <h4 className="text-lg font-bold text-slate-900 dark:text-white">
                    {tier.name}
                  </h4>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    {tier.description}
                  </p>

                  <div className="mt-6 flex items-baseline gap-1">
                    <span className="text-4xl font-extrabold text-slate-900 dark:text-white">
                      {tier.price}
                    </span>
                    <span className="text-xs text-slate-500">{tier.period}</span>
                  </div>

                  <ul className="mt-8 space-y-3 border-t border-slate-100 pt-6 dark:border-slate-800">
                    {tier.features.map((feat) => (
                      <li key={feat} className="flex items-center gap-2.5 text-xs text-slate-700 dark:text-slate-300">
                        <CheckCircle className="h-4 w-4 text-emerald-500 shrink-0" />
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="mt-8 pt-6">
                  <Link to="/register" className="w-full">
                    <Button
                      variant={tier.popular ? 'primary' : 'outline'}
                      fullWidth
                    >
                      {tier.cta}
                    </Button>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="border-t border-slate-200/80 bg-white py-12 dark:border-slate-800 dark:bg-slate-950">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white shadow-sm">
                <ScanFace className="h-5 w-5" />
              </div>
              <span className="text-base font-bold tracking-tight">ATTENDORA</span>
            </div>

            <div className="flex items-center gap-6 text-xs text-slate-500 dark:text-slate-400">
              <a href="#" className="hover:text-slate-900 dark:hover:text-white">Privacy Policy</a>
              <a href="#" className="hover:text-slate-900 dark:hover:text-white">Terms of Service</a>
              <a href="#" className="hover:text-slate-900 dark:hover:text-white">Security & GDPR</a>
              <a href="#" className="hover:text-slate-900 dark:hover:text-white">API Documentation</a>
            </div>

            <p className="text-xs text-slate-400">
              &copy; {new Date().getFullYear()} Attendora Inc. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
