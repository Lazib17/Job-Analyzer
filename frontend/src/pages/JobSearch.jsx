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

const WORK_ARRANGEMENTS = ['Remote', 'On-site', 'Hybrid'];

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
    job_title: '',
    location: 'Remote',
    experience_level: '',
    japanese_level: '',
    remote_only: true,
    max_results: 25,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [found, setFound] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setFound(null);
    try {
      const { data } = await searchJobs(form);
      setFound(data.length);
      setTimeout(() => navigate('/results'), 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Job search failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-xl mx-auto">
        <PageHeader
          eyebrow="Discovery"
          title="Search jobs"
          subtitle="Scrape entry-level listings from Mynavi, CareerCross, Wantedly, and GaijinPot."
        />

        <FadeInSection delay={0.15}>
          <VetraCard>
            <form onSubmit={handleSubmit} className="space-y-5">
              <VetraSelect
                label="Job title"
                value={form.job_title}
                onChange={(e) => setForm({ ...form, job_title: e.target.value })}
                required
              >
                <option value="" disabled>
                  Choose a job title
                </option>
                {JOB_TITLES.map((title) => (
                  <option key={title} value={title}>
                    {title}
                  </option>
                ))}
              </VetraSelect>

              <VetraSelect
                label="Location"
                value={form.location}
                onChange={(e) =>
                  setForm({
                    ...form,
                    location: e.target.value,
                    remote_only: e.target.value === 'Remote',
                  })
                }
                required
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

              <div className="space-y-2">
                <label className="label">Max results: {form.max_results}</label>
                <input
                  type="range"
                  min="5"
                  max="50"
                  step="5"
                  value={form.max_results}
                  onChange={(e) => setForm({ ...form, max_results: Number(e.target.value) })}
                  className="w-full accent-violet-500/80"
                />
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
