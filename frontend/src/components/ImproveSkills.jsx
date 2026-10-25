import { motion, useReducedMotion } from 'framer-motion';
import { useEffect, useState } from 'react';
import {
  createLearningPlan,
  getJapaneseLevel,
  getLearningPlan,
  getLearningPlans,
  getLearningSkills,
  updateJapaneseLevel,
  updateLearningTask,
} from '../api/axios';
import { SectionTitle } from './layout/AppShell';
import PlanBuilder from './learning/PlanBuilder';
import PlanView from './learning/PlanView';

const LEVELS = ['None', 'N5', 'N4', 'N3', 'N2', 'N1', 'Native/Fluent', 'Not sure'];

const TIER_CLASS = {
  High: 'border-emerald-400/30 bg-emerald-400/10 text-emerald-300',
  Medium: 'border-cyan-400/30 bg-cyan-400/10 text-cyan-200',
  Low: 'border-white/15 bg-white/[0.04] text-white/55',
};

function errorText(err, fallback) {
  const detail = err?.response?.data?.detail;
  return typeof detail === 'string' ? detail : fallback;
}

export default function ImproveSkills({ hasResume = false }) {
  const reduce = useReducedMotion();
  const [level, setLevel] = useState(null);
  const [skills, setSkills] = useState([]);
  const [totalJobs, setTotalJobs] = useState(0);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savingLevel, setSavingLevel] = useState(false);
  const [error, setError] = useState('');
  const [planNotice, setPlanNotice] = useState('');
  const [builderSkill, setBuilderSkill] = useState(null);
  const [builderSeed, setBuilderSeed] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [builderError, setBuilderError] = useState('');
  const [activePlan, setActivePlan] = useState(null);
  const [pendingTaskId, setPendingTaskId] = useState(null);

  const loadSkills = async () => {
    const { data } = await getLearningSkills();
    setSkills(data.skills || []);
    setTotalJobs(data.total_jobs || 0);
    if (data.japanese_level) setLevel(data.japanese_level);
  };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError('');
      try {
        const [levelRes, skillsRes] = await Promise.all([
          getJapaneseLevel(),
          getLearningSkills(),
        ]);
        if (cancelled) return;
        setLevel(levelRes.data.japanese_level);
        setSkills(skillsRes.data.skills || []);
        setTotalJobs(skillsRes.data.total_jobs || 0);
        try {
          const plansRes = await getLearningPlans();
          if (!cancelled) {
            setPlans(plansRes.data || []);
            setPlanNotice('');
          }
        } catch (planErr) {
          if (!cancelled) setPlanNotice(errorText(planErr, 'Saved plans are unavailable until the plans table exists.'));
        }
      } catch (err) {
        if (!cancelled) setError(errorText(err, 'Could not load skill priorities.'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const chooseLevel = async (next) => {
    const previous = level;
    setLevel(next);
    setSavingLevel(true);
    setError('');
    try {
      await updateJapaneseLevel(next);
      await loadSkills();
    } catch (err) {
      setLevel(previous);
      setError(errorText(err, 'Could not save your Japanese level.'));
    } finally {
      setSavingLevel(false);
    }
  };

  const openBuilder = (skill, seed = null) => {
    setBuilderError('');
    setBuilderSeed(seed);
    setBuilderSkill(skill);
  };

  const generate = async (payload) => {
    setGenerating(true);
    setBuilderError('');
    try {
      const { data } = await createLearningPlan(payload);
      setActivePlan(data);
      setBuilderSkill(null);
      setPlanNotice('');
      const { data: saved } = await getLearningPlans();
      setPlans(saved || []);
    } catch (err) {
      setBuilderError(errorText(err, 'Could not build a plan.'));
    } finally {
      setGenerating(false);
    }
  };

  const openPlan = async (id) => {
    setError('');
    try {
      const { data } = await getLearningPlan(id);
      setActivePlan(data);
    } catch (err) {
      setError(errorText(err, 'Could not open that plan.'));
    }
  };

  const toggleTask = async (task, done) => {
    if (!activePlan) return;
    setPendingTaskId(task.id);
    try {
      const { data } = await updateLearningTask(activePlan.id, task.id, done);
      setActivePlan(data);
      setPlans((current) =>
        current.map((plan) => (plan.id === data.id ? { ...plan, progress: data.progress } : plan))
      );
    } catch (err) {
      setError(errorText(err, 'Could not update that task.'));
    } finally {
      setPendingTaskId(null);
    }
  };

  return (
    <section aria-labelledby="improve-skills-heading">
      <SectionTitle>
        <span id="improve-skills-heading">Improve Your Skills</span>
      </SectionTitle>

      <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-5 shadow-soft sm:p-6">
        <p className="text-sm font-medium text-white/80">Your Japanese level</p>
        <p className="mt-1 max-w-xl text-xs leading-relaxed text-white/40">
          Why we ask: many Japan tech jobs require a Japanese level. We use yours to decide whether Japanese belongs on this list.
        </p>
        <div className="mt-4 flex flex-wrap gap-2" role="radiogroup" aria-label="Japanese level">
          {LEVELS.map((item) => {
            const selected = level === item;
            return (
              <button
                key={item}
                type="button"
                role="radio"
                aria-checked={selected}
                disabled={savingLevel}
                onClick={() => chooseLevel(item)}
                className={`rounded-full px-3.5 py-1.5 text-xs font-medium transition-colors ${
                  selected
                    ? 'bg-gradient-to-r from-emerald-400 to-cyan-400 text-slate-950'
                    : 'border border-white/10 bg-white/[0.04] text-white/55 hover:text-white/80'
                }`}
              >
                {item}
              </button>
            );
          })}
        </div>

        {error && <p className="mt-4 text-sm text-red-400/90">{error}</p>}
        {planNotice && <p className="mt-4 text-sm text-amber-200/80">{planNotice}</p>}

        {plans.length > 0 && (
          <div className="mt-5 flex flex-wrap gap-2">
            {plans.map((plan) => (
              <button
                key={plan.id}
                type="button"
                onClick={() => openPlan(plan.id)}
                className="rounded-full border border-emerald-300/20 px-3 py-1.5 text-xs text-emerald-100 hover:bg-emerald-400/10"
              >
                {plan.skill} · {plan.progress?.done || 0}/{plan.progress?.total || 0}
              </button>
            ))}
          </div>
        )}

        <div className="mt-6 space-y-3">
          {loading &&
            [1, 2, 3].map((item) => (
              <div key={item} className="h-24 animate-pulse rounded-2xl bg-white/[0.04]" />
            ))}

          {!loading && skills.length === 0 && (
            <p className="text-sm text-white/45">
              {!hasResume
                ? 'Upload a resume and analyze jobs to build a learning list.'
                : totalJobs === 0
                  ? 'Analyze your matches to see which skills to learn first.'
                  : 'No skill gaps in your current matches.'}
            </p>
          )}

          {!loading &&
            skills.map((item) => (
              <motion.article
                key={item.skill}
                whileHover={reduce ? undefined : { scale: 1.02, y: -3 }}
                transition={reduce ? { duration: 0 } : { duration: 0.22 }}
                className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4"
              >
                <div className="flex items-start gap-4">
                  <span className="font-display text-lg font-semibold tabular-nums text-white/30">
                    {String(item.rank).padStart(2, '0')}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-display text-base font-semibold text-white">{item.skill}</h3>
                      <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${TIER_CLASS[item.tier] || TIER_CLASS.Low}`}>
                        {item.tier}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-white/50">
                      Appears in {item.jobs_missing_count} of {item.total_jobs} matched jobs
                    </p>
                    <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10">
                      <motion.div
                        className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400"
                        initial={reduce ? false : { width: 0 }}
                        animate={{ width: `${item.demand_percent}%` }}
                        transition={reduce ? { duration: 0 } : { duration: 0.6 }}
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() => openBuilder(item.skill)}
                      className="mt-4 rounded-xl bg-gradient-to-r from-emerald-400 to-cyan-400 px-3.5 py-2 text-xs font-semibold text-slate-950"
                    >
                      Build my plan
                    </button>
                  </div>
                </div>
              </motion.article>
            ))}
        </div>

        {activePlan && (
          <PlanView
            plan={activePlan}
            pendingTaskId={pendingTaskId}
            regenerating={generating && builderSkill === activePlan.skill}
            onClose={() => setActivePlan(null)}
            onToggle={toggleTask}
            onRegenerate={() =>
              openBuilder(activePlan.skill, {
                duration_weeks: activePlan.duration_weeks,
                hours_per_week: activePlan.hours_per_week,
                start_date: activePlan.start_date,
                study_days: activePlan.study_days,
              })
            }
          />
        )}
      </div>

      {builderSkill && (
        <PlanBuilder
          skill={builderSkill}
          initial={builderSeed}
          generating={generating}
          error={builderError}
          onClose={() => {
            if (!generating) setBuilderSkill(null);
          }}
          onGenerate={generate}
        />
      )}
    </section>
  );
}
