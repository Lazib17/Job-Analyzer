import { motion, useReducedMotion } from 'framer-motion';
import { useState } from 'react';

function formatViews(views) {
  if (views == null || views === '') return null;
  const count = Number(views);
  if (!Number.isFinite(count)) return null;
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M views`;
  if (count >= 1_000) return `${Math.round(count / 1000)}K views`;
  return `${count} views`;
}

function ProgressRing({ done, total }) {
  const reduce = useReducedMotion();
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const progress = total ? done / total : 0;
  return (
    <div className="relative h-20 w-20 shrink-0">
      <svg viewBox="0 0 72 72" className="h-20 w-20 -rotate-90" aria-hidden="true">
        <circle cx="36" cy="36" r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="6" />
        <motion.circle
          cx="36"
          cy="36"
          r={radius}
          fill="none"
          stroke="url(#plan-progress)"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={reduce ? false : { strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference - circumference * progress }}
          transition={reduce ? { duration: 0 } : { duration: 0.7 }}
        />
        <defs>
          <linearGradient id="plan-progress" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#34d399" />
            <stop offset="100%" stopColor="#22d3ee" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex items-center justify-center text-sm font-semibold text-white">
        {total ? Math.round(progress * 100) : 0}%
      </div>
    </div>
  );
}

function VideoCard({ resource }) {
  const [open, setOpen] = useState(false);
  const isSearch = resource.kind === 'search_link' || !resource.videoId;
  if (isSearch) {
    return (
      <a
        href={resource.url}
        target="_blank"
        rel="noreferrer"
        className="mt-3 block rounded-xl border border-dashed border-cyan-300/30 bg-cyan-400/[0.04] p-3 text-sm text-cyan-100 hover:border-cyan-300/60"
      >
        <span className="mb-1 inline-block rounded-full border border-cyan-300/30 px-2 py-0.5 text-[10px] uppercase tracking-wide text-cyan-200">
          Search link
        </span>
        <span className="mt-2 block">{resource.title || 'Search YouTube for this lesson'}</span>
      </a>
    );
  }

  if (open) {
    return (
      <div className="mt-3 overflow-hidden rounded-xl border border-white/10">
        <iframe
          title={resource.title || 'Lesson video'}
          src={`https://www.youtube-nocookie.com/embed/${resource.videoId}`}
          className="aspect-video w-full"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={() => setOpen(true)}
      className="mt-3 flex w-full gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-2 text-left hover:border-emerald-300/40"
    >
      {resource.thumbnail ? (
        <img src={resource.thumbnail} alt="" className="h-16 w-28 shrink-0 rounded-lg object-cover" />
      ) : (
        <span className="flex h-16 w-28 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-400/30 to-cyan-400/20 text-xs text-white">
          Play
        </span>
      )}
      <span className="min-w-0">
        <span className="block truncate text-sm font-medium text-white">{resource.title}</span>
        <span className="mt-1 block text-xs text-white/45">
          {[resource.channel, resource.duration, formatViews(resource.views)].filter(Boolean).join(' · ')}
        </span>
      </span>
    </button>
  );
}

function ReadingCard({ task, resource }) {
  const isSearch = !resource || resource.kind === 'search_link';
  const body = (
    <>
      <span className="mb-2 inline-flex items-center gap-2">
        <span className="rounded-full border border-white/15 px-2 py-0.5 text-[10px] uppercase tracking-wide text-white/55">
          {isSearch ? 'Search link' : resource.source || 'Reading'}
        </span>
        <span className="text-xs text-white/40">{task.estimated_minutes} min</span>
      </span>
      <span className="block text-sm text-white/80">{resource?.title || task.title}</span>
    </>
  );
  if (!resource?.url) {
    return <div className="mt-3 rounded-xl border border-dashed border-white/15 p-3">{body}</div>;
  }
  return (
    <a
      href={resource.url}
      target="_blank"
      rel="noreferrer"
      className={`mt-3 block rounded-xl p-3 ${
        isSearch
          ? 'border border-dashed border-cyan-300/30 bg-cyan-400/[0.04] hover:border-cyan-300/60'
          : 'border border-white/10 bg-white/[0.03] hover:border-emerald-300/40'
      }`}
    >
      {body}
    </a>
  );
}

export default function PlanView({ plan, onClose, onRegenerate, regenerating, onToggle, pendingTaskId }) {
  const reduce = useReducedMotion();
  const progress = plan.progress || { done: 0, total: 0 };

  return (
    <div className="mt-6 rounded-2xl border border-emerald-400/15 bg-emerald-400/[0.03] p-4 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <ProgressRing done={progress.done} total={progress.total} />
          <div>
            <h3 className="font-display text-lg font-semibold text-white">{plan.skill}</h3>
            <p className="mt-1 text-sm text-white/50">
              {progress.done} of {progress.total} tasks · {plan.duration_weeks} weeks · {plan.hours_per_week} h/week
            </p>
            {plan.source === 'template' && (
              <p className="mt-1 text-xs text-white/40">Built from the standard study template.</p>
            )}
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={onRegenerate}
            disabled={regenerating}
            className="rounded-xl border border-white/15 px-3.5 py-2 text-xs font-medium text-white/80 hover:bg-white/[0.06] disabled:opacity-50"
          >
            {regenerating ? 'Regenerating…' : 'Regenerate plan'}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl px-3.5 py-2 text-xs font-medium text-white/50 hover:text-white"
          >
            Close
          </button>
        </div>
      </div>

      <ol className="mt-6 space-y-4">
        {(plan.weeks || []).map((week, index) => {
          const weekDone = week.tasks.filter((task) => task.done).length;
          const weekProgress = week.tasks.length ? Math.round((weekDone / week.tasks.length) * 100) : 0;
          return (
            <motion.li
              key={week.week_number}
              initial={reduce ? false : { opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={reduce ? { duration: 0 } : { delay: index * 0.06, duration: 0.35 }}
              className="rounded-2xl border border-white/[0.08] bg-[#0c1014]/80 p-4"
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.14em] text-emerald-200/70">Week {week.week_number}</p>
                  <h4 className="mt-1 font-display text-base font-semibold text-white">{week.goal}</h4>
                </div>
                <p className="text-xs text-white/45">{weekDone}/{week.tasks.length}</p>
              </div>
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10">
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400"
                  initial={reduce ? false : { width: 0 }}
                  animate={{ width: `${weekProgress}%` }}
                  transition={reduce ? { duration: 0 } : { duration: 0.45 }}
                />
              </div>
              <ul className="mt-3 space-y-3">
                {week.tasks.map((task) => (
                  <li key={task.id} className="rounded-xl border border-white/[0.06] p-3">
                    <label className="flex items-start gap-3">
                      <input
                        type="checkbox"
                        checked={Boolean(task.done)}
                        disabled={pendingTaskId === task.id}
                        onChange={(event) => onToggle(task, event.target.checked)}
                        className="mt-1 h-4 w-4 accent-emerald-400"
                      />
                      <span className={task.done ? 'text-white/40 line-through' : 'text-sm text-white/85'}>
                        {task.title}
                        <span className="ml-2 text-xs uppercase tracking-wide text-white/35">{task.type}</span>
                      </span>
                    </label>
                    {task.type === 'watch' && task.resource && <VideoCard resource={task.resource} />}
                    {task.type === 'read' && <ReadingCard task={task} resource={task.resource} />}
                  </li>
                ))}
              </ul>
            </motion.li>
          );
        })}
      </ol>
    </div>
  );
}
