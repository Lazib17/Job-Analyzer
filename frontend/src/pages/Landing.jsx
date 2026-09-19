import { animate, motion, useInView, useMotionValue, useTransform } from 'framer-motion';
import { ChartNoAxesColumn, FileUp, Globe2, GraduationCap, MapPin, Search, Sparkles } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '@/components/Navbar';

const PREVIEW_JOBS = [
  {
    title: 'Junior Frontend Engineer',
    company: 'Mercari',
    location: 'Tokyo',
    platform: 'Wantedly',
    score: 92,
    platformClass: 'bg-platform-wantedly/15 text-rose-300 border-platform-wantedly/30',
  },
  {
    title: 'New Grad iOS Engineer',
    company: 'Rakuten',
    location: 'Tokyo',
    platform: 'Mynavi',
    score: 86,
    platformClass: 'bg-platform-mynavi/15 text-blue-300 border-platform-mynavi/30',
  },
  {
    title: 'Backend Engineer (Junior)',
    company: 'SmartHR',
    location: 'Remote · Japan',
    platform: 'CareerCross',
    score: 81,
    platformClass: 'bg-platform-careercross/15 text-amber-300 border-platform-careercross/30',
  },
  {
    title: 'Data Analyst — Entry Level',
    company: 'GaijinPot Jobs',
    location: 'Osaka',
    platform: 'GaijinPot',
    score: 74,
    platformClass: 'bg-platform-gaijinpot/15 text-emerald-300 border-platform-gaijinpot/30',
  },
];

function scoreTone(score) {
  if (score >= 85) return 'text-emerald-300';
  if (score >= 75) return 'text-indigo-300';
  return 'text-violet-300';
}

function PreviewJobCard({ job, index }) {
  const radius = 18;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (job.score / 100) * circ;

  return (
    <motion.article
      initial={{ opacity: 0, y: 22 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.45 + index * 0.12, duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ scale: 1.02, y: -4 }}
      className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-4 shadow-soft backdrop-blur-sm"
    >
      <div className="flex items-start gap-3">
        <svg width="48" height="48" viewBox="0 0 48 48" className="shrink-0 -rotate-90">
          <circle cx="24" cy="24" r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="3.5" />
          <circle
            cx="24"
            cy="24"
            r={radius}
            fill="none"
            stroke={`url(#scoreGrad-${index})`}
            strokeWidth="3.5"
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
          />
          <defs>
            <linearGradient id={`scoreGrad-${index}`} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#818cf8" />
              <stop offset="50%" stopColor="#60a5fa" />
              <stop offset="100%" stopColor="#c084fc" />
            </linearGradient>
          </defs>
        </svg>
        <div className="min-w-0 flex-1">
          <div className="mb-1.5 flex items-center justify-between gap-2">
            <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${job.platformClass}`}>
              {job.platform}
            </span>
            <span className={`text-sm font-semibold tabular-nums ${scoreTone(job.score)}`}>{job.score}%</span>
          </div>
          <h3 className="truncate font-display text-[15px] font-semibold text-white">{job.title}</h3>
          <p className="mt-0.5 truncate text-sm text-white/50">{job.company}</p>
          <p className="mt-2 flex items-center gap-1 text-xs text-white/35">
            <MapPin className="h-3 w-3" strokeWidth={1.75} />
            {job.location}
          </p>
        </div>
      </div>
    </motion.article>
  );
}

const STATS = [
  { value: 4, label: 'Job Boards Scanned' },
  { value: 12400, label: 'AI-Scored Matches' },
  { value: 3200, label: 'Resumes Analyzed' },
  { value: 86, label: 'Avg. Top Match Score', suffix: '%' },
];

function AnimatedCounter({ value, suffix = '' }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-60px' });
  const motionVal = useMotionValue(0);
  const rounded = useTransform(motionVal, (latest) => Math.round(latest));
  const [display, setDisplay] = useState(0);

  useEffect(() => rounded.on('change', (v) => setDisplay(v)), [rounded]);

  useEffect(() => {
    if (!isInView) return undefined;
    const controls = animate(motionVal, value, {
      duration: 1.45,
      ease: [0.22, 1, 0.36, 1],
    });
    return () => controls.stop();
  }, [isInView, motionVal, value]);

  return (
    <span ref={ref} className="tabular-nums">
      {display.toLocaleString()}
      {suffix}
    </span>
  );
}

const FEATURES = [
  {
    icon: Globe2,
    title: 'Four boards, one search',
    description:
      'We scrape Mynavi, CareerCross, Wantedly, and GaijinPot in parallel so you are not hopping between Japan job sites.',
    featured: true,
  },
  {
    icon: Sparkles,
    title: 'Gemini resume scoring',
    description: 'Each listing is scored against your CV so the strongest fits rise to the top.',
  },
  {
    icon: ChartNoAxesColumn,
    title: 'Skills-gap breakdown',
    description: 'See matching skills, missing skills, and what to improve before you apply.',
  },
  {
    icon: GraduationCap,
    title: 'Junior & visa-friendly',
    description: 'Built for new grads and foreigner-friendly tech roles, not senior-only listings.',
  },
];

function FeatureCard({ feature, index, className }) {
  const Icon = feature.icon;
  return (
    <motion.article
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ delay: index * 0.1, duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ scale: 1.02, y: -4 }}
      className={`rounded-3xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-soft sm:p-8 ${className ?? ''}`}
    >
      <div className="mb-5 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-accent-gradient text-white shadow-accent-glow">
        <Icon className="h-5 w-5" strokeWidth={1.75} />
      </div>
      <h3 className="font-display text-xl font-semibold tracking-tight text-white sm:text-2xl">{feature.title}</h3>
      <p className="mt-3 max-w-md text-sm leading-relaxed text-white/50 sm:text-base">{feature.description}</p>
    </motion.article>
  );
}

export default function Landing() {
  return (
    <div className="relative min-h-screen overflow-x-hidden bg-[#07070e] font-sans text-white">
      <Navbar />

      <section className="relative mx-auto flex min-h-screen max-w-[1280px] flex-col items-center px-4 pb-20 pt-28 text-center sm:px-6 sm:pt-32 lg:px-8 lg:pt-36">
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute -left-24 top-16 h-72 w-72 rounded-full bg-indigo-700/25 blur-[100px]" />
          <div className="absolute right-0 top-32 h-80 w-80 rounded-full bg-violet-600/20 blur-[110px]" />
          <div className="absolute bottom-10 left-1/3 h-56 w-56 rounded-full bg-blue-600/15 blur-[90px]" />
        </div>
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mb-6 inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 text-xs font-medium text-white/70"
        >
          <Sparkles className="h-3.5 w-3.5 text-violet-300" strokeWidth={1.75} />
          AI-Powered Job Matching for Japan
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.08, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="font-display text-[2.35rem] font-bold leading-[1.08] tracking-tight text-white sm:text-6xl lg:text-7xl xl:text-[5.25rem]"
        >
          <span className="block">Welcome to Job Analyzer</span>
          <span className="mt-2 block sm:mt-3">Find your next tech job in Japan, ranked by AI.</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.18, duration: 0.45 }}
          className="mt-6 max-w-2xl text-base leading-relaxed text-white/50 sm:text-lg"
        >
          We scan Mynavi, CareerCross, Wantedly, and GaijinPot for entry-level and visa-friendly tech roles, then score every listing against your resume with Gemini so the best matches rise to the top.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.28, duration: 0.4 }}
          className="mt-8 flex flex-col items-center gap-3 sm:flex-row"
        >
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Link
              to="/register"
              className="inline-flex items-center justify-center rounded-xl bg-accent-gradient px-6 py-3 text-sm font-semibold text-white shadow-accent-glow sm:text-base"
            >
              Get Started Free
            </Link>
          </motion.div>
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <a
              href="#how-it-works"
              className="inline-flex items-center justify-center rounded-xl border border-white/20 bg-transparent px-6 py-3 text-sm font-medium text-white/90 transition-colors duration-soft hover:border-white/40 hover:bg-white/[0.06] sm:text-base"
            >
              See How It Works
            </a>
          </motion.div>
        </motion.div>

        <div className="relative mt-14 grid w-full max-w-5xl grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {PREVIEW_JOBS.map((job, index) => (
            <PreviewJobCard key={job.title} job={job} index={index} />
          ))}
        </div>
      </section>

      <section className="relative z-10 bg-[#f4f6fb]">
        <div className="mx-auto grid max-w-[1280px] grid-cols-4 divide-x divide-black/[0.08]">
          {STATS.map((stat) => (
            <div key={stat.label} className="px-2 py-10 text-center sm:px-6 sm:py-14">
              <p className="font-display text-xl font-bold tracking-tight text-[#07070e] sm:text-4xl lg:text-5xl">
                <AnimatedCounter value={stat.value} suffix={stat.suffix} />
              </p>
              <p className="mt-2 text-[10px] font-medium leading-snug text-[#07070e]/50 sm:text-sm">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="features" className="relative z-10 scroll-mt-24 bg-[#101018] px-4 py-20 sm:px-6 sm:py-24 lg:px-8">
        <div className="mx-auto max-w-[1280px]">
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-[11px] font-medium uppercase tracking-[0.2em] text-white/40"
          >
            Why Job Analyzer
          </motion.p>
          <motion.h2
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.06 }}
            className="mt-3 max-w-xl font-display text-3xl font-bold tracking-tight text-white sm:text-4xl"
          >
            Built for finding tech work in Japan — not scrolling four sites by hand.
          </motion.h2>

          <div className="mt-12 grid grid-cols-1 gap-4 lg:grid-cols-4 lg:grid-rows-2">
            <FeatureCard feature={FEATURES[0]} index={0} className="lg:col-span-2 lg:row-span-2 lg:min-h-[340px] lg:p-10" />
            <FeatureCard feature={FEATURES[1]} index={1} className="lg:col-span-2" />
            <FeatureCard feature={FEATURES[2]} index={2} />
            <FeatureCard feature={FEATURES[3]} index={3} />
          </div>
        </div>
      </section>

      <section id="how-it-works" className="relative z-10 scroll-mt-24 bg-[#f4f6fb] px-4 py-20 sm:px-6 sm:py-24 lg:px-8">
        <div className="mx-auto max-w-[1280px]">
          <p className="text-center text-[11px] font-medium uppercase tracking-[0.2em] text-[#07070e]/40">
            How it works
          </p>
          <h2 className="mt-3 text-center font-display text-3xl font-bold tracking-tight text-[#07070e] sm:text-4xl">
            Three steps from resume to ranked matches
          </h2>

          <div className="relative mt-16 grid grid-cols-1 gap-10 md:grid-cols-3 md:gap-8">
            <div className="pointer-events-none absolute left-7 top-8 bottom-8 w-px bg-[#07070e]/10 md:left-[16%] md:right-[16%] md:top-8 md:bottom-auto md:h-px md:w-auto" />

            {[
              {
                icon: FileUp,
                step: '01',
                title: 'Upload Resume',
                body: 'Drop in your CV. We extract skills, experience, and education so scoring has a real baseline.',
              },
              {
                icon: Search,
                step: '02',
                title: 'We Scan Mynavi, CareerCross, Wantedly & GaijinPot',
                body: 'Four Japan job boards, searched in parallel for entry-level and foreigner-friendly tech roles.',
              },
              {
                icon: Sparkles,
                step: '03',
                title: 'Get Ranked AI Matches',
                body: 'Gemini scores every listing against your resume so the best fits show up first.',
              },
            ].map((item, index) => {
              const Icon = item.icon;
              return (
                <motion.div
                  key={item.step}
                  initial={{ opacity: 0, x: -28 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: '-80px' }}
                  transition={{ delay: index * 0.16, duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
                  className="relative flex gap-5 md:flex-col md:items-center md:text-center"
                >
                  <div className="relative z-10 flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-accent-gradient text-white shadow-accent-glow">
                    <Icon className="h-6 w-6" strokeWidth={1.75} />
                  </div>
                  <div>
                    <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-[#07070e]/40">{item.step}</p>
                    <h3 className="mt-1 font-display text-lg font-semibold tracking-tight text-[#07070e] sm:text-xl">
                      {item.title}
                    </h3>
                    <p className="mt-2 max-w-sm text-sm leading-relaxed text-[#07070e]/55 md:mx-auto">{item.body}</p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="relative z-10 bg-accent-gradient px-4 py-20 text-center sm:px-6 sm:py-24 lg:px-8">
        <h2 className="font-display text-3xl font-bold tracking-tight text-white sm:text-5xl">
          Start finding your job in Japan today
        </h2>
        <p className="mx-auto mt-4 max-w-lg text-base text-white/80">
          Upload a resume, scan four boards, and get Gemini-ranked matches in one place.
        </p>
        <Link
          to="/register"
          className="mt-8 inline-flex items-center justify-center rounded-xl bg-white px-6 py-3 text-sm font-semibold text-[#07070e] transition-transform duration-soft hover:scale-[1.02] active:scale-[0.98] sm:text-base"
        >
          Get Started Free
        </Link>
      </section>

      <footer className="relative z-10 bg-[#07070e] px-4 py-10 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-[1280px] flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
          <Link to="/" className="font-display text-sm font-semibold tracking-tight text-white">
            Job Analyzer
          </Link>
          <nav className="flex flex-wrap gap-6 text-sm text-white/45">
            <a href="#features" className="hover:text-white/80">About</a>
            <a href="mailto:hello@jobanalyzer.app" className="hover:text-white/80">Contact</a>
            <a href="#privacy" className="hover:text-white/80">Privacy</a>
          </nav>
          <p className="text-xs text-white/30">© {new Date().getFullYear()} Job Analyzer. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
