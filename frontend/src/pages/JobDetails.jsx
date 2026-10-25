import { motion } from 'framer-motion';
import { ArrowLeft, ExternalLink, MapPin, Star } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { analyzeJob, getJob, reanalyzeJob, toggleFavorite, translateJobPage } from '../api/axios';
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

const COPY = {
  en: {
    back: 'Back to results',
    eyebrow: 'Job details',
    save: 'Save Job',
    unsave: 'Unsave',
    analyze: 'Analyze',
    reanalyze: 'Re-analyze',
    analyzing: 'Analyzing…',
    why: 'Why this score',
    gap: 'Skills gap',
    matched: 'Matched',
    missing: 'Missing',
    matchedSkills: 'Matched skills',
    missingSkills: 'Missing skills',
    none: 'None listed.',
    description: 'Job description',
    requirements: 'Requirements',
    original: 'View original listing',
    notFound: 'Job not found.',
    oneSkill: 'skill',
    manySkills: 'skills',
    translating: 'Translating…',
    translateError: 'Could not translate this page.',
    languageLabel: 'Read this page in',
  },
  ja: {
    back: '結果に戻る',
    eyebrow: '求人の詳細',
    save: '保存する',
    unsave: '保存を解除',
    analyze: '分析する',
    reanalyze: '再分析',
    analyzing: '分析中…',
    why: 'このスコアの理由',
    gap: 'スキルの差',
    matched: '一致',
    missing: '不足',
    matchedSkills: '一致したスキル',
    missingSkills: '不足しているスキル',
    none: 'なし',
    description: '仕事内容',
    requirements: '応募条件',
    original: '元の求人を見る',
    notFound: '求人が見つかりません。',
    oneSkill: '件',
    manySkills: '件',
    translating: '翻訳中…',
    translateError: 'このページを翻訳できませんでした。',
    languageLabel: '表示言語',
  },
};

function textValue(value) {
  if (Array.isArray(value)) return value.filter(Boolean).join('\n');
  return value || '';
}

function ChartTooltip({ active, payload, copy }) {
  if (!active || !payload?.length) return null;
  const item = payload[0];
  const unit = item.value === 1 ? copy.oneSkill : copy.manySkills;
  return (
    <div className="rounded-xl border border-white/10 bg-[#07070e]/80 px-3 py-2 text-xs text-white shadow-lift backdrop-blur-xl">
      <p className="font-medium text-white/90">{item.payload.name}</p>
      <p className="mt-0.5 text-white/55">{item.value} {unit}</p>
    </div>
  );
}

function SkillsGapChart({ matched = 0, missing = 0, copy }) {
  const data = [
    { name: copy.matched, value: matched },
    { name: copy.missing, value: missing },
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
          <Tooltip content={<ChartTooltip copy={copy} />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
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
  const [language, setLanguage] = useState(() => {
    const stored = sessionStorage.getItem('jobPageLanguage');
    return stored === 'en' || stored === 'ja' ? stored : 'source';
  });
  const [translations, setTranslations] = useState({});
  const [translating, setTranslating] = useState(false);
  const [translateError, setTranslateError] = useState('');

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

  useEffect(() => {
    if (!job || (language !== 'en' && language !== 'ja')) return undefined;
    const cacheKey = `${id}:${language}`;
    if (translations[cacheKey]) return undefined;
    let cancelled = false;
    setTranslating(true);
    setTranslateError('');
    translateJobPage(id, language)
      .then(({ data }) => {
        if (!cancelled) {
          setTranslations((current) => ({ ...current, [cacheKey]: data }));
        }
      })
      .catch((err) => {
        if (!cancelled) {
          const detail = err?.response?.data?.detail;
          setTranslateError(typeof detail === 'string' ? detail : COPY[language].translateError);
        }
      })
      .finally(() => {
        if (!cancelled) setTranslating(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id, job, language, translations]);

  const copy = COPY[language] || COPY.en;
  const translated = translations[`${id}:${language}`];
  const view = translated ? { ...job, ...translated } : job;
  const matched = view?.matching_skills || [];
  const missing = view?.missing_skills || [];

  const chooseLanguage = (next) => {
    setLanguage(next);
    setTranslateError('');
    sessionStorage.setItem('jobPageLanguage', next);
  };
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
          <p className="text-white/40">{copy.notFound}</p>
          <Link
            to="/results"
            className="mt-6 inline-flex rounded-xl border border-white/15 px-4 py-2.5 text-sm text-white/80 hover:bg-white/[0.06]"
          >
            {copy.back}
          </Link>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl space-y-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <Link to="/results" className="inline-flex items-center gap-1.5 text-sm text-white/45 hover:text-white">
            <ArrowLeft className="h-4 w-4" /> {copy.back}
          </Link>
          <div className="flex items-center gap-2" role="group" aria-label={copy.languageLabel}>
            {[
              ['en', 'English'],
              ['ja', '日本語'],
            ].map(([value, label]) => {
              const selected = language === value;
              return (
                <button
                  key={value}
                  type="button"
                  aria-pressed={selected}
                  onClick={() => chooseLanguage(value)}
                  className={`rounded-full px-3.5 py-1.5 text-xs font-medium ${
                    selected
                      ? 'bg-gradient-to-r from-indigo-400 to-violet-400 text-white'
                      : 'border border-white/15 text-white/60 hover:text-white'
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>
        {translating && <p className="text-sm text-white/45">{copy.translating}</p>}
        {translateError && <p className="text-sm text-red-400/90">{translateError}</p>}

        <PageHeader
          eyebrow={copy.eyebrow}
          title={view.job_title}
          subtitle={`${view.company}${view.location ? ` · ${view.location}` : ''}`}
          actions={
            <>
              <button
                type="button"
                onClick={handleFavorite}
                className="inline-flex items-center gap-1.5 rounded-xl border border-white/15 px-4 py-2.5 text-sm font-medium text-white/80 hover:bg-white/[0.06]"
              >
                <Star className={`h-3.5 w-3.5 ${job.is_favorite ? 'fill-amber-400 text-amber-400' : ''}`} />
                {job.is_favorite ? copy.unsave : copy.save}
              </button>
              <button
                type="button"
                onClick={handleAnalyze}
                disabled={analyzing}
                className="inline-flex rounded-xl bg-accent-gradient px-4 py-2.5 text-sm font-semibold text-white shadow-accent-glow disabled:opacity-70"
              >
                {analyzing ? copy.analyzing : job.compatibility_score ? copy.reanalyze : copy.analyze}
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
                {view.location && (
                  <span className="inline-flex items-center gap-1 text-xs text-white/40">
                    <MapPin className="h-3 w-3" /> {view.location}
                  </span>
                )}
              </div>
              <p className="mt-2 font-display text-lg font-semibold text-white">{view.company}</p>
              {view.salary && <p className="mt-1 text-sm text-indigo-300">{view.salary}</p>}
              {job.job_url && (
                <a
                  href={job.job_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 inline-flex items-center gap-1.5 text-sm text-indigo-300 hover:text-indigo-200"
                >
                  {copy.original} <ExternalLink className="h-3.5 w-3.5" />
                </a>
              )}
            </div>
          </div>
        </FadeInSection>

        {hasAnalysis && (
          <FadeInSection>
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-soft">
              <h2 className="font-display text-lg font-semibold text-white">{copy.why}</h2>
              {view.ai_reasoning && (
                <p className="mt-3 text-sm leading-relaxed text-white/65">{view.ai_reasoning}</p>
              )}

              {chartReady && (
                <div className="mt-6">
                  <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.14em] text-white/35">{copy.gap}</p>
                  <SkillsGapChart matched={matched.length} missing={missing.length} copy={copy} />
                </div>
              )}

              <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <p className="mb-3 text-[11px] font-medium uppercase tracking-[0.14em] text-emerald-300/70">
                    {copy.matchedSkills}
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
                    <p className="text-sm text-white/35">{copy.none}</p>
                  )}
                </div>
                <div>
                  <p className="mb-3 text-[11px] font-medium uppercase tracking-[0.14em] text-red-300/70">
                    {copy.missingSkills}
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
                    <p className="text-sm text-white/35">{copy.none}</p>
                  )}
                </div>
              </div>

              {view.improvement_suggestions && (
                <p className="mt-6 text-sm leading-relaxed text-white/50">{view.improvement_suggestions}</p>
              )}
            </div>
          </FadeInSection>
        )}

        {textValue(view.description) && (
          <FadeInSection>
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-soft">
              <h2 className="mb-4 font-display text-lg font-semibold text-white">{copy.description}</h2>
              <p className="whitespace-pre-wrap text-sm leading-7 text-white/60">{textValue(view.description)}</p>
            </div>
          </FadeInSection>
        )}

        {textValue(view.requirements) && (
          <FadeInSection>
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-soft">
              <h2 className="mb-4 font-display text-lg font-semibold text-white">{copy.requirements}</h2>
              <p className="whitespace-pre-wrap text-sm leading-7 text-white/60">{textValue(view.requirements)}</p>
            </div>
          </FadeInSection>
        )}
      </div>
    </AppShell>
  );
}
