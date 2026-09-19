import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { MapPin, Star } from 'lucide-react';
import { platformColor } from '@/lib/design-tokens';

function platformBadge(platform = '') {
  const key = String(platform).toLowerCase();
  if (key.includes('mynavi')) return 'bg-platform-mynavi/15 text-blue-300 border-platform-mynavi/30';
  if (key.includes('career')) return 'bg-platform-careercross/15 text-amber-300 border-platform-careercross/30';
  if (key.includes('wantedly')) return 'bg-platform-wantedly/15 text-rose-300 border-platform-wantedly/30';
  if (key.includes('gaijin')) return 'bg-platform-gaijinpot/15 text-emerald-300 border-platform-gaijinpot/30';
  return 'bg-white/10 text-white/50 border-white/15';
}

function ScoreRing({ score, id }) {
  const radius = 18;
  const circ = 2 * Math.PI * radius;
  const safe = score == null ? 0 : score;
  const offset = circ - (safe / 100) * circ;

  return (
    <div className="relative h-12 w-12 shrink-0">
      <svg width="48" height="48" viewBox="0 0 48 48" className="-rotate-90">
        <circle cx="24" cy="24" r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="3.5" />
        <motion.circle
          cx="24"
          cy="24"
          r={radius}
          fill="none"
          stroke={`url(#dashScore-${id})`}
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeDasharray={circ}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
        />
        <defs>
          <linearGradient id={`dashScore-${id}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#818cf8" />
            <stop offset="50%" stopColor="#60a5fa" />
            <stop offset="100%" stopColor="#c084fc" />
          </linearGradient>
        </defs>
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[10px] font-semibold tabular-nums text-white">
        {score == null ? '—' : score}
      </span>
    </div>
  );
}

export default function JobCard({ job, onFavorite, onAnalyze, analyzing }) {
  const platform = job.source_platform || '';

  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.96 }}
      whileHover={{ scale: 1.02, y: -3 }}
      transition={{ duration: 0.22 }}
      className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-4 shadow-soft"
    >
      <div className="flex items-start gap-3">
        <ScoreRing score={job.compatibility_score} id={job.id} />
        <div className="min-w-0 flex-1">
          <div className="mb-1.5 flex flex-wrap items-center gap-2">
            {platform ? (
              <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${platformBadge(platform)}`}>
                {platform}
              </span>
            ) : null}
            {job.is_favorite && <Star className="h-3.5 w-3.5 fill-amber-400/80 text-amber-400/80" />}
          </div>
          <h3 className="truncate font-display text-[15px] font-semibold text-white">{job.job_title}</h3>
          <p className="mt-0.5 truncate text-sm text-white/50">{job.company}</p>
          {job.location && (
            <p className="mt-2 flex items-center gap-1 text-xs text-white/35">
              <MapPin className="h-3 w-3" strokeWidth={1.75} />
              {job.location}
            </p>
          )}
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Link
          to={`/jobs/${job.id}`}
          className="inline-flex rounded-lg border border-white/15 px-3 py-1.5 text-xs font-medium text-white/80 hover:bg-white/[0.06]"
        >
          View details
        </Link>
        {onFavorite && (
          <button
            type="button"
            onClick={() => onFavorite(job.id)}
            className="inline-flex rounded-lg border border-white/15 px-3 py-1.5 text-xs font-medium text-white/80 hover:bg-white/[0.06]"
          >
            {job.is_favorite ? 'Unsave' : 'Save'}
          </button>
        )}
        {onAnalyze && job.compatibility_score == null && (
          <button
            type="button"
            onClick={() => onAnalyze(job.id)}
            disabled={analyzing}
            className="inline-flex rounded-lg bg-accent-gradient px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-60"
          >
            {analyzing ? 'Analyzing…' : 'Analyze'}
          </button>
        )}
      </div>
    </motion.article>
  );
}

export { platformColor };
