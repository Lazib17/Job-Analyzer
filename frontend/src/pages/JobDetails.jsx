import { motion } from 'framer-motion';
import { ArrowLeft, ExternalLink, MapPin, Star } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { analyzeJob, getJob, reanalyzeJob, toggleFavorite } from '../api/axios';
import {
  AppShell,
  FadeInSection,
  PageHeader,
} from '../components/layout/AppShell';
import SkeletonCard from '../components/ui/SkeletonCard';

function platformBadge(platform = '') {
  const key = String(platform).toLowerCase();
  if (key.includes('mynavi')) return 'bg-platform-mynavi/15 text-blue-300 border-platform-mynavi/30';
  if (key.includes('career')) return 'bg-platform-careercross/15 text-amber-300 border-platform-careercross/30';
  if (key.includes('wantedly')) return 'bg-platform-wantedly/15 text-rose-300 border-platform-wantedly/30';
  if (key.includes('gaijin')) return 'bg-platform-gaijinpot/15 text-emerald-300 border-platform-gaijinpot/30';
  return 'bg-white/10 text-white/50 border-white/15';
}

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const item = payload[0];
  return (
    <div className="rounded-xl border border-white/10 bg-[#07070e]/80 px-3 py-2 text-xs text-white shadow-lift backdrop-blur-xl">
      <p className="font-medium text-white/90">{item.payload.name}</p>
      <p className="mt-0.5 text-white/55">{item.value} skill{item.value === 1 ? '' : 's'}</p>
    </div>
  );
}

function SkillsGapChart({ matched = 0, missing = 0 }) {
  const data = [
    { name: 'Matched', value: matched },
    { name: 'Missing', value: missing },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="h-56 w-full"
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} barSize={42}>
          <XAxis dataKey="name" tick={{ fill: 'rgba(255,255,255,0.45)', fontSize: 12 }} axisLine={false} tickLine={false} />
          <YAxis allowDecimals={false} tick={{ fill: 'rgba(255,255,255,0.35)', fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
          <Bar dataKey="value" radius={[10, 10, 0, 0]} isAnimationActive animationDuration={900}>
            <Cell fill="url(#matchedGrad)" />
            <Cell fill="rgba(248,113,113,0.75)" />
          </Bar>
          <defs>
            <linearGradient id="matchedGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#818cf8" />
              <stop offset="50%" stopColor="#60a5fa" />
              <stop offset="100%" stopColor="#7c3aed" />
            </linearGradient>
          </defs>
        </BarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}

function ScoreRing({ score }) {
  const radius = 28;
  const circ = 2 * Math.PI * radius;
  const safe = score == null ? 0 : score;
  const offset = circ - (safe / 100) * circ;

  return (
    <div className="relative h-[72px] w-[72px] shrink-0">
      <svg width="72" height="72" viewBox="0 0 72 72" className="-rotate-90">
        <circle cx="36" cy="36" r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="5" />
        <motion.circle
          cx="36"
          cy="36"
          r={radius}
          fill="none"
          stroke="url(#detailScoreGrad)"
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={circ}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
        />
        <defs>
          <linearGradient id="detailScoreGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#818cf8" />
            <stop offset="50%" stopColor="#60a5fa" />
            <stop offset="100%" stopColor="#c084fc" />
          </linearGradient>
        </defs>
      </svg>
      <span className="absolute inset-0 flex items-center justify-center font-display text-sm font-bold tabular-nums text-white">
        {score == null ? '—' : `${score}`}
      </span>
    </div>
  );
}

export default function JobDetails() {
  const { id } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    loadJob();
  }, [id]);

  const loadJob = async () => {
    setLoading(true);
    try {
      const { data } = await getJob(id);
      setJob(data);
    } catch {
      setJob(null);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      if (job.compatibility_score) {
        await reanalyzeJob(id);
      } else {
        await analyzeJob(id);
      }
      loadJob();
    } catch (err) {
      alert(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleFavorite = async () => {
    try {
      await toggleFavorite(id);
      loadJob();
    } catch {
      alert('Failed to update favorite');
    }
  };

  const matched = job?.matching_skills || [];
  const missing = job?.missing_skills || [];
  const hasAnalysis = job?.compatibility_score != null;

  const chartReady = useMemo(
    () => hasAnalysis && (matched.length > 0 || missing.length > 0),
    [hasAnalysis, matched.length, missing.length]
  );

  if (loading) {
    return (
      <AppShell>
        <div className="mx-auto max-w-3xl space-y-4">
          <SkeletonCard className="h-28" />
          <SkeletonCard className="h-56" />
          <SkeletonCard className="h-40" />
        </div>
      </AppShell>
    );
  }

  if (!job) {
    return (
      <AppShell>
        <div className="mx-auto max-w-2xl py-20 text-center">
          <p className="text-white/40">Job not found.</p>
          <Link
            to="/results"
            className="mt-6 inline-flex rounded-xl border border-white/15 px-4 py-2.5 text-sm text-white/80 hover:bg-white/[0.06]"
          >
            Back to Results
          </Link>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl space-y-8">
        <Link to="/results" className="inline-flex items-center gap-1.5 text-sm text-white/45 hover:text-white">
          <ArrowLeft className="h-4 w-4" /> Back to results
        </Link>

        <PageHeader
          eyebrow="Job details"
          title={job.job_title}
          subtitle={`${job.company}${job.location ? ` · ${job.location}` : ''}`}
          actions={
            <>
              <button
                type="button"
                onClick={handleFavorite}
                className="inline-flex items-center gap-1.5 rounded-xl border border-white/15 px-4 py-2.5 text-sm font-medium text-white/80 hover:bg-white/[0.06]"
              >
                <Star className={`h-3.5 w-3.5 ${job.is_favorite ? 'fill-amber-400 text-amber-400' : ''}`} />
                {job.is_favorite ? 'Unsave' : 'Save Job'}
              </button>
              <button
                type="button"
                onClick={handleAnalyze}
                disabled={analyzing}
                className="inline-flex rounded-xl bg-accent-gradient px-4 py-2.5 text-sm font-semibold text-white shadow-accent-glow disabled:opacity-70"
              >
                {analyzing ? 'Analyzing…' : job.compatibility_score ? 'Re-analyze' : 'Analyze'}
              </button>
            </>
          }
        />

        <FadeInSection>
          <div className="flex flex-col gap-5 rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-soft sm:flex-row sm:items-center">
            <ScoreRing score={job.compatibility_score} />
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                {job.source_platform && (
                  <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-wide ${platformBadge(job.source_platform)}`}>
                    {job.source_platform}
                  </span>
                )}
                {job.location && (
                  <span className="inline-flex items-center gap-1 text-xs text-white/40">
                    <MapPin className="h-3 w-3" /> {job.location}
                  </span>
                )}
              </div>
              <p className="mt-2 font-display text-lg font-semibold text-white">{job.company}</p>
              {job.salary && <p className="mt-1 text-sm text-indigo-300">{job.salary}</p>}
              {job.job_url && (
                <a
                  href={job.job_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 inline-flex items-center gap-1.5 text-sm text-indigo-300 hover:text-indigo-200"
                >
                  View original listing <ExternalLink className="h-3.5 w-3.5" />
                </a>
              )}
            </div>
          </div>
        </FadeInSection>

        {hasAnalysis && (
          <FadeInSection>
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-soft">
              <h2 className="font-display text-lg font-semibold text-white">Why this score</h2>
              {job.ai_reasoning && (
                <p className="mt-3 text-sm leading-relaxed text-white/65">{job.ai_reasoning}</p>
              )}

              {chartReady && (
                <div className="mt-6">
                  <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.14em] text-white/35">Skills gap</p>
                  <SkillsGapChart matched={matched.length} missing={missing.length} />
                </div>
              )}

              <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <p className="mb-3 text-[11px] font-medium uppercase tracking-[0.14em] text-emerald-300/70">
                    Matched skills
                  </p>
                  {matched.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {matched.map((skill) => (
                        <span
                          key={skill}
                          className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-xs text-emerald-300"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-white/35">None listed.</p>
                  )}
                </div>
                <div>
                  <p className="mb-3 text-[11px] font-medium uppercase tracking-[0.14em] text-red-300/70">
                    Missing skills
                  </p>
                  {missing.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {missing.map((skill) => (
                        <span
                          key={skill}
                          className="rounded-full border border-red-500/20 bg-red-500/10 px-2.5 py-1 text-xs text-red-300/80"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-white/35">None listed.</p>
                  )}
                </div>
              </div>

              {job.improvement_suggestions && (
                <p className="mt-6 text-sm leading-relaxed text-white/50">{job.improvement_suggestions}</p>
              )}
            </div>
          </FadeInSection>
        )}

        {job.description && (
          <FadeInSection>
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-soft">
              <h2 className="mb-4 font-display text-lg font-semibold text-white">Job description</h2>
              <p className="whitespace-pre-wrap text-sm leading-7 text-white/60">{job.description}</p>
            </div>
          </FadeInSection>
        )}

        {job.requirements && (
          <FadeInSection>
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-soft">
              <h2 className="mb-4 font-display text-lg font-semibold text-white">Requirements</h2>
              <p className="whitespace-pre-wrap text-sm leading-7 text-white/60">{job.requirements}</p>
            </div>
          </FadeInSection>
        )}
      </div>
    </AppShell>
  );
}
