import { Calendar, Languages, Sparkles } from 'lucide-react';
import { buildJobBrief } from '@/lib/jobBrief';

function Block({ title, children }) {
  if (!children) return null;
  return (
    <div>
      <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.14em] text-white/35">{title}</p>
      {children}
    </div>
  );
}

export default function JobBrief({ job, language }) {
  const brief = buildJobBrief(job, language);
  const hasWindow = brief.starts || brief.deadline;

  return (
    <div className="space-y-5">
      {brief.chips.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {brief.chips.map((chip) => (
            <span
              key={chip}
              className="rounded-full border border-indigo-300/30 bg-indigo-400/10 px-3 py-1 text-xs text-indigo-100"
            >
              {chip}
            </span>
          ))}
        </div>
      )}

      <Block title={brief.labels.summary}>
        {brief.summary ? (
          <p className="flex gap-2 text-sm leading-relaxed text-white/75">
            <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-violet-300" strokeWidth={1.75} />
            <span>{brief.summary}</span>
          </p>
        ) : (
          <p className="text-sm text-white/40">{brief.labels.notStated}</p>
        )}
      </Block>

      <div className="grid gap-4 sm:grid-cols-2">
        <Block title={brief.labels.japanese}>
          <p className="flex items-center gap-2 text-sm text-white/75">
            <Languages className="h-4 w-4 text-sky-300" strokeWidth={1.75} />
            {brief.japanese || brief.labels.notStated}
          </p>
        </Block>
        <Block title={brief.labels.window}>
          {hasWindow ? (
            <div className="space-y-1 text-sm text-white/75">
              {brief.starts && (
                <p className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-emerald-300" strokeWidth={1.75} />
                  {brief.labels.starts}: {brief.starts}
                </p>
              )}
              {brief.deadline && (
                <p className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-amber-300" strokeWidth={1.75} />
                  {brief.labels.deadline}: {brief.deadline}
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-white/40">{brief.labels.notStated}</p>
          )}
        </Block>
      </div>

      <Block title={brief.labels.skills}>
        {brief.skills.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {brief.skills.map((skill) => (
              <span
                key={skill}
                className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-white/75"
              >
                {skill}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-white/40">{brief.labels.notStated}</p>
        )}
      </Block>

      {brief.other.length > 0 && (
        <Block title={brief.labels.other}>
          <ul className="space-y-2">
            {brief.other.map((item) => (
              <li key={item} className="flex gap-2 text-sm leading-relaxed text-white/70">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-300" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </Block>
      )}

      {brief.fullText && (
        <details className="rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3">
          <summary className="cursor-pointer text-sm text-white/55">{brief.labels.full}</summary>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-white/50">{brief.fullText}</p>
        </details>
      )}
    </div>
  );
}
