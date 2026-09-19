export default function ScoreBadge({ score }) {
  if (score === null || score === undefined) {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium tracking-wide border border-white/[0.08] bg-white/[0.03] text-white/40">
        Unrated
      </span>
    );
  }

  let colorClass = 'bg-red-500/10 text-red-300/80 border-red-500/10';
  if (score >= 80) colorClass = 'bg-emerald-500/10 text-emerald-300/80 border-emerald-500/10';
  else if (score >= 60) colorClass = 'bg-violet-500/10 text-violet-300/80 border-violet-500/10';
  else if (score >= 40) colorClass = 'bg-amber-500/10 text-amber-300/80 border-amber-500/10';

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide border ${colorClass}`}
    >
      {score}%
    </span>
  );
}
