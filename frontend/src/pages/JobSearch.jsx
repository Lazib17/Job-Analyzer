import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchJobs } from '../api/axios';
import {
  AppShell,
  FadeInSection,
  PageHeader,
} from '../components/layout/AppShell';
import { VetraButton, VetraCard, VetraSelect } from '../components/ui/vetra-ui';

const JOB_TITLES = [
  'Software Engineer',
  'Data Analyst',
  'AI / Machine Learning Engineer',
  'Sales Representative',
  'Marketing Specialist',
  'Business Analyst',
  'Business Development Associate',
  'Human Resources Specialist',
  'Accountant / Financial Analyst',
  'Customer Support Representative',
  'Administrative Assistant',
  'Project Manager',
  'Mechanical Engineer',
  'Electrical Engineer',
  'Civil Engineer',
  'Graphic / UI Designer',
  'Translator / Interpreter',
  'Teacher / English Instructor',
  'Hotel / Hospitality Staff',
  'Supply Chain / Logistics Specialist',
];

const WORK_ARRANGEMENTS = ['Any', 'Remote', 'On-site', 'Hybrid'];

const CITIES = [
  'Any',
  'Tokyo',
  'Osaka',
  'Yokohama',
  'Nagoya',
  'Fukuoka',
  'Sapporo',
  'Kobe',
  'Kyoto',
  'Hiroshima',
  'Sendai',
];

const JAPANESE_LEVELS = [
  'Native',
  'Business level',
  'Intermediate',
  'Daily conversation level',
  'No Japanese',
];

export default function JobSearch() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    job_titles: [],
    location: 'Any',
    city: 'Any',
    experience_level: '',
    japanese_level: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [found, setFound] = useState(null);

  const toggleTitle = (title) => {
    setForm((current) => {
      const selected = current.job_titles.includes(title)
        ? current.job_titles.filter((item) => item !== title)
        : current.job_titles.length >= 4
          ? current.job_titles
          : [...current.job_titles, title];
      return { ...current, job_titles: selected };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.job_titles.length === 0) {
      setError('Choose at least one position.');
      return;
    }
    setLoading(true);
    setError('');
    setFound(null);
    try {
      const { data } = await searchJobs(form);
      if (!data.length) {
        setError('No listings matched those positions.');
        return;
      }
      setFound(data.length);
      setTimeout(() => navigate('/results'), 1500);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Job search failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto">
        <PageHeader
          eyebrow="Discovery"
          title="Search jobs"
          subtitle="Pick one or more positions, then set city, Japanese level, work style, and experience."
        />

        <FadeInSection delay={0.15}>
          <VetraCard>
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <label className="block text-[11px] uppercase tracking-[0.12em] text-white/35 font-medium">
                    Positions
                  </label>
                  <span className="text-xs text-white/35">{form.job_titles.length}/4 selected</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {JOB_TITLES.map((title) => {
                    const selected = form.job_titles.includes(title);
                    return (
                      <button
                        key={title}
                        type="button"
                        aria-pressed={selected}
                        onClick={() => toggleTitle(title)}
                        className={
                          selected
                            ? 'rounded-full border border-violet-300/50 bg-violet-500/20 px-3 py-1.5 text-sm text-white'
                            : 'rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-sm text-white/70 hover:border-white/25 hover:text-white'
                        }
                      >
                        {title}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-[11px] uppercase tracking-[0.12em] text-white/35 font-medium">
                  Location
                </label>
                <div className="flex flex-wrap gap-2">
                  {CITIES.map((city) => {
                    const selected = form.city === city;
                    return (
                      <button
                        key={city}
                        type="button"
                        aria-pressed={selected}
                        onClick={() => setForm({ ...form, city })}
                        className={
                          selected
                            ? 'rounded-full border border-violet-300/50 bg-violet-500/20 px-3 py-1.5 text-sm text-white'
                            : 'rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-sm text-white/70 hover:border-white/25 hover:text-white'
                        }
                      >
                        {city}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <VetraSelect
                  label="Work style"
                  value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                >
                  {WORK_ARRANGEMENTS.map((arrangement) => (
                    <option key={arrangement} value={arrangement}>
                      {arrangement}
                    </option>
                  ))}
                </VetraSelect>

                <VetraSelect
                  label="Japanese level"
                  value={form.japanese_level}
                  onChange={(e) => setForm({ ...form, japanese_level: e.target.value })}
                  required
                >
                  <option value="" disabled>
                    Choose a Japanese level
                  </option>
                  {JAPANESE_LEVELS.map((level) => (
                    <option key={level} value={level}>
                      {level}
                    </option>
                  ))}
                </VetraSelect>

                <VetraSelect
                  label="Experience level"
                  value={form.experience_level}
                  onChange={(e) => setForm({ ...form, experience_level: e.target.value })}
                >
                  <option value="">Any</option>
                  <option value="entry">Entry Level</option>
                  <option value="associate">Associate</option>
                  <option value="mid">Mid-Senior</option>
                  <option value="senior">Senior</option>
                  <option value="director">Director</option>
                </VetraSelect>
              </div>

              {error && (
                <div className="rounded-xl border border-red-500/20 bg-red-500/5 text-red-400/90 text-sm p-4">
                  {error}
                </div>
              )}
              {found !== null && (
                <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 text-emerald-400/90 text-sm p-4">
                  Found {found} jobs! Redirecting to results...
                </div>
              )}

              <VetraButton type="submit" loading={loading} className="w-full py-3">
                {loading ? 'Scraping jobs...' : 'Search Jobs'}
              </VetraButton>
            </form>
          </VetraCard>
        </FadeInSection>

        <FadeInSection delay={0.25}>
          <p className="mt-8 text-center text-xs text-white/30 leading-relaxed max-w-md mx-auto">
            Multi-platform scraping may take 1–3 minutes. Rate limiting is handled automatically.
          </p>
        </FadeInSection>
      </div>
    </AppShell>
  );
}
