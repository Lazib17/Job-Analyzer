import { useEffect, useId, useState } from 'react';

const PRESETS = [2, 4, 8, 12];
const DAYS = [
  { id: 'mon', label: 'Mon' },
  { id: 'tue', label: 'Tue' },
  { id: 'wed', label: 'Wed' },
  { id: 'thu', label: 'Thu' },
  { id: 'fri', label: 'Fri' },
  { id: 'sat', label: 'Sat' },
  { id: 'sun', label: 'Sun' },
];

export default function PlanBuilder({ skill, initial, generating, error, onClose, onGenerate }) {
  const titleId = useId();
  const [weeks, setWeeks] = useState(initial?.duration_weeks || 4);
  const [custom, setCustom] = useState(
    initial?.duration_weeks ? !PRESETS.includes(initial.duration_weeks) : false
  );
  const [hours, setHours] = useState(initial?.hours_per_week || 4);
  const [startDate, setStartDate] = useState(initial?.start_date || '');
  const [days, setDays] = useState(initial?.study_days || []);

  useEffect(() => {
    const onKey = (event) => {
      if (event.key === 'Escape' && !generating) onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [generating, onClose]);

  const toggleDay = (id) => {
    setDays((current) => (current.includes(id) ? current.filter((day) => day !== id) : [...current, id]));
  };

  const submit = (event) => {
    event.preventDefault();
    const duration = Math.min(24, Math.max(1, Number(weeks) || 1));
    onGenerate({
      skill,
      duration_weeks: duration,
      hours_per_week: Number(hours),
      start_date: startDate || null,
      study_days: days.length ? days : null,
    });
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-end justify-center bg-black/70 p-4 sm:items-center" onClick={generating ? undefined : onClose}>
      <form
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(event) => event.stopPropagation()}
        onSubmit={submit}
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-white/10 bg-[#0c1014] p-5 shadow-soft sm:p-6"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id={titleId} className="font-display text-lg font-semibold text-white">
              Build a plan
            </h2>
            <p className="mt-1 text-sm text-white/50">{skill}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={generating}
            className="rounded-lg px-2 py-1 text-sm text-white/50 hover:bg-white/[0.06] hover:text-white disabled:opacity-40"
          >
            Close
          </button>
        </div>

        <fieldset className="mt-5">
          <legend className="text-xs font-medium uppercase tracking-[0.12em] text-white/40">Duration</legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {PRESETS.map((preset) => {
              const selected = !custom && weeks === preset;
              return (
                <button
                  key={preset}
                  type="button"
                  aria-pressed={selected}
                  onClick={() => {
                    setCustom(false);
                    setWeeks(preset);
                  }}
                  className={`rounded-full px-3.5 py-1.5 text-xs font-medium ${
                    selected
                      ? 'bg-gradient-to-r from-emerald-400 to-cyan-400 text-slate-950'
                      : 'border border-white/10 bg-white/[0.04] text-white/60 hover:text-white'
                  }`}
                >
                  {preset} weeks
                </button>
              );
            })}
            <button
              type="button"
              aria-pressed={custom}
              onClick={() => setCustom(true)}
              className={`rounded-full px-3.5 py-1.5 text-xs font-medium ${
                custom
                  ? 'bg-gradient-to-r from-emerald-400 to-cyan-400 text-slate-950'
                  : 'border border-white/10 bg-white/[0.04] text-white/60 hover:text-white'
              }`}
            >
              Custom
            </button>
          </div>
          {custom && (
            <label className="mt-3 block text-sm text-white/60">
              Weeks (1–24)
              <input
                type="number"
                min="1"
                max="24"
                value={weeks}
                onChange={(event) => setWeeks(Number(event.target.value))}
                className="mt-1 w-full rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-white"
              />
            </label>
          )}
        </fieldset>

        <label className="mt-5 block text-xs font-medium uppercase tracking-[0.12em] text-white/40">
          Hours per week: {hours}
          <input
            type="range"
            min="1"
            max="20"
            value={hours}
            onChange={(event) => setHours(Number(event.target.value))}
            className="mt-3 w-full accent-emerald-400"
          />
        </label>
        <p className="mt-2 text-sm text-emerald-200/80">About {weeks * hours} hours total</p>

        <label className="mt-5 block text-sm text-white/60">
          Start date <span className="text-white/35">(optional)</span>
          <input
            type="date"
            value={startDate || ''}
            onChange={(event) => setStartDate(event.target.value)}
            className="mt-1 w-full rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-white"
          />
        </label>

        <fieldset className="mt-5">
          <legend className="text-sm text-white/60">
            Study days <span className="text-white/35">(optional)</span>
          </legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {DAYS.map((day) => {
              const selected = days.includes(day.id);
              return (
                <button
                  key={day.id}
                  type="button"
                  aria-pressed={selected}
                  onClick={() => toggleDay(day.id)}
                  className={`rounded-full px-3 py-1.5 text-xs font-medium ${
                    selected
                      ? 'bg-gradient-to-r from-emerald-400 to-cyan-400 text-slate-950'
                      : 'border border-white/10 text-white/55 hover:text-white'
                  }`}
                >
                  {day.label}
                </button>
              );
            })}
          </div>
        </fieldset>

        {error && <p className="mt-4 text-sm text-red-400/90">{error}</p>}

        <button
          type="submit"
          disabled={generating}
          className="mt-6 w-full rounded-xl bg-gradient-to-r from-emerald-400 to-cyan-400 py-3 text-sm font-semibold text-slate-950 disabled:opacity-60"
        >
          {generating ? 'Building your plan…' : 'Generate plan'}
        </button>
      </form>
    </div>
  );
}
