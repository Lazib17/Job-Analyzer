import { Link } from 'react-router-dom';
import { MapPin, Star } from 'lucide-react';
import ScoreBadge from './ScoreBadge';
import { VetraButton, VetraCard } from '@/components/ui/vetra-ui';

export default function JobCard({ job, onFavorite, onAnalyze, analyzing }) {
  return (
    <VetraCard hover className="group">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <ScoreBadge score={job.compatibility_score} />
            {job.is_favorite && <Star className="w-3.5 h-3.5 text-amber-400/80 fill-amber-400/80" />}
            {job.source_platform && (
              <span className="vetra-tag capitalize">{job.source_platform}</span>
            )}
          </div>
          <h3 className="text-base font-medium text-white truncate group-hover:text-white/90 transition-colors">
            {job.job_title}
          </h3>
          <p className="text-white/45 text-sm mt-1">{job.company}</p>
          {job.location && (
            <p className="text-white/30 text-xs mt-2 flex items-center gap-1.5">
              <MapPin className="w-3 h-3" />
              {job.location}
            </p>
          )}
          {job.salary && (
            <p className="text-emerald-400/70 text-xs mt-1">{job.salary}</p>
          )}
        </div>

        <div className="flex flex-col gap-2 shrink-0">
          <Link to={`/jobs/${job.id}`}>
            <VetraButton variant="secondary" className="text-xs py-2 px-3 w-full">
              Details
            </VetraButton>
          </Link>
          <VetraButton
            variant="secondary"
            className="text-xs py-2 px-3"
            onClick={() => onFavorite?.(job.id)}
          >
            {job.is_favorite ? 'Unsave' : 'Save'}
          </VetraButton>
          {!job.compatibility_score && (
            <VetraButton
              className="text-xs py-2 px-3"
              onClick={() => onAnalyze?.(job.id)}
              loading={analyzing}
            >
              Analyze
            </VetraButton>
          )}
        </div>
      </div>

      {job.missing_skills?.length > 0 && (
        <div className="mt-4 pt-4 border-t border-white/[0.05]">
          <p className="text-[11px] uppercase tracking-wider text-white/30 mb-2">Missing skills</p>
          <div className="flex flex-wrap gap-1.5">
            {job.missing_skills.slice(0, 4).map((skill) => (
              <span
                key={skill}
                className="text-xs bg-red-500/10 text-red-300/80 px-2 py-0.5 rounded-full border border-red-500/10"
              >
                {skill}
              </span>
            ))}
            {job.missing_skills.length > 4 && (
              <span className="text-xs text-white/30">+{job.missing_skills.length - 4}</span>
            )}
          </div>
        </div>
      )}
    </VetraCard>
  );
}
