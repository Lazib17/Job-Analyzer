import { AnimatePresence } from 'framer-motion';
import { BarChart3, Briefcase, FileText, Search, Star } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import {
  analyzeAllJobs,
  exportReport,
  getRankedJobs,
  getResume,
  getSearchHistory,
  getSkillsGap,
  uploadResume,
} from '../api/axios';
import {
  AppShell,
  FadeInSection,
  PageHeader,
  SectionTitle,
} from '../components/layout/AppShell';
import JobCard from '../components/ui/JobCard';
import ResumeDropZone from '../components/ui/ResumeDropZone';
import SkeletonCard from '../components/ui/SkeletonCard';
import StatCard from '../components/ui/StatCard';

const PLATFORM_FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'mynavi', label: 'Mynavi' },
  { id: 'careercross', label: 'CareerCross' },
  { id: 'wantedly', label: 'Wantedly' },
  { id: 'gaijinpot', label: 'GaijinPot' },
  { id: 'favorites', label: 'Favorites' },
];

function matchesPlatform(job, filter) {
  if (filter === 'all') return true;
  if (filter === 'favorites') return Boolean(job.is_favorite);
  const key = String(job.source_platform || '').toLowerCase().replace(/\s+/g, '');
  if (filter === 'careercross') return key.includes('career');
  if (filter === 'gaijinpot') return key.includes('gaijin');
  return key.includes(filter);
}

export default function Dashboard() {
  const [jobs, setJobs] = useState([]);
  const [skillsGap, setSkillsGap] = useState([]);
  const [history, setHistory] = useState([]);
  const [resume, setResume] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const [jobsRes, skillsRes, historyRes] = await Promise.allSettled([
        getRankedJobs(),
        getSkillsGap(),
        getSearchHistory(),
      ]);

      if (jobsRes.status === 'fulfilled') setJobs(jobsRes.value.data);
      if (skillsRes.status === 'fulfilled') setSkillsGap(skillsRes.value.data);
      if (historyRes.status === 'fulfilled') setHistory(historyRes.value.data.slice(0, 5));

      try {
        const { data } = await getResume();
        setResume(data);
      } catch {
        setResume(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeAll = async () => {
    setAnalyzing(true);
    try {
      await analyzeAllJobs();
      await loadDashboard();
    } catch (err) {
      alert(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleExport = async () => {
    try {
      const { data } = await exportReport();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'job-analysis-report.json';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert('Export failed');
    }
  };

  const handleResumeFile = async (file) => {
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx', 'doc'].includes(ext)) {
      alert('Only PDF and DOCX files are supported.');
      return;
    }
    setUploading(true);
    setProgress(12);
    const tick = setInterval(() => {
      setProgress((p) => (p < 88 ? p + 8 : p));
    }, 180);
    try {
      const { data } = await uploadResume(file);
      setProgress(100);
      setResume(data.resume);
    } catch (err) {
      alert(err.response?.data?.detail || 'Upload failed');
    } finally {
      clearInterval(tick);
      setUploading(false);
      setProgress(0);
    }
  };

  const scoredJobs = jobs.filter((j) => j.compatibility_score != null);
  const avgScore = scoredJobs.length
    ? Math.round(scoredJobs.reduce((s, j) => s + j.compatibility_score, 0) / scoredJobs.length)
    : 0;
  const topScore = scoredJobs.length ? Math.max(...scoredJobs.map((j) => j.compatibility_score)) : 0;

  const chartData = scoredJobs.slice(0, 8).map((j) => ({
    name: j.job_title.slice(0, 20),
    score: j.compatibility_score,
  }));

  const filteredJobs = useMemo(() => {
    const next = jobs.filter((job) => matchesPlatform(job, filter));
    return [...next].sort((a, b) => (b.compatibility_score || 0) - (a.compatibility_score || 0));
  }, [filter, jobs]);

  if (loading) {
    return (
      <AppShell>
        <div className="mx-auto max-w-6xl space-y-8">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <SkeletonCard key={i} className="h-28" />
            ))}
          </div>
          <SkeletonCard className="h-40" />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {[1, 2, 3, 4].map((i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl space-y-12">
        <PageHeader
          eyebrow="Overview"
          title="Dashboard"
          subtitle="Your AI-powered job matching overview — track compatibility, skills gaps, and top opportunities."
          actions={
            <>
              <button
                type="button"
                onClick={handleExport}
                className="inline-flex rounded-xl border border-white/15 px-4 py-2.5 text-sm font-medium text-white/80 hover:bg-white/[0.06]"
              >
                Export Report
              </button>
              <button
                type="button"
                onClick={handleAnalyzeAll}
                disabled={analyzing}
                className="inline-flex rounded-xl bg-accent-gradient px-4 py-2.5 text-sm font-semibold text-white shadow-accent-glow disabled:opacity-70"
              >
                {analyzing ? 'Analyzing…' : 'Analyze All Jobs'}
              </button>
            </>
          }
        />

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard icon={Briefcase} label="Total matches" value={jobs.length} />
          <StatCard icon={BarChart3} label="Top score" value={topScore} suffix="%" />
          <StatCard icon={Star} label="Avg. score" value={avgScore} suffix="%" />
          <StatCard icon={FileText} label="Resume" value={resume ? 'Uploaded' : 'Missing'} isText />
        </div>

        <FadeInSection>
          <SectionTitle>Resume</SectionTitle>
          <ResumeDropZone
            resume={resume}
            uploading={uploading}
            progress={progress}
            onFile={handleResumeFile}
          />
        </FadeInSection>

        <FadeInSection>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-soft">
              <SectionTitle>Compatibility Scores</SectionTitle>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={chartData}>
                    <XAxis dataKey="name" tick={{ fill: 'rgba(255,255,255,0.35)', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,0.35)', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: 'rgba(10,10,18,0.95)',
                        border: '1px solid rgba(255,255,255,0.08)',
                        borderRadius: '12px',
                        fontSize: '12px',
                      }}
                      labelStyle={{ color: 'rgba(255,255,255,0.7)' }}
                    />
                    <Bar dataKey="score" fill="#818cf8" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-sm text-white/40">No analyzed jobs yet. Search and analyze jobs to see scores.</p>
              )}
            </div>
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-soft">
              <SectionTitle>Top Missing Skills</SectionTitle>
              {skillsGap.length > 0 ? (
                <div className="space-y-3">
                  {skillsGap.map((item) => (
                    <div key={item.skill} className="flex items-center justify-between py-1">
                      <span className="text-sm text-white/70">{item.skill}</span>
                      <span className="vetra-tag">{item.count} jobs</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-white/40">Analyze jobs to see skill gaps.</p>
              )}
            </div>
          </div>
        </FadeInSection>

        <FadeInSection>
          <SectionTitle
            action={
              <Link to="/results" className="text-xs text-white/45 hover:text-white">
                View all →
              </Link>
            }
          >
            Ranked matches
          </SectionTitle>

          <div className="mb-5 flex flex-wrap gap-2">
            {PLATFORM_FILTERS.map((chip) => {
              const active = filter === chip.id;
              return (
                <button
                  key={chip.id}
                  type="button"
                  onClick={() => setFilter(chip.id)}
                  className={`rounded-full px-3.5 py-1.5 text-xs font-medium transition-colors ${
                    active
                      ? 'bg-accent-gradient text-white shadow-accent-glow'
                      : 'border border-white/10 bg-white/[0.04] text-white/50 hover:text-white/80'
                  }`}
                >
                  {chip.label}
                </button>
              );
            })}
          </div>

          {filteredJobs.length > 0 ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <AnimatePresence mode="popLayout">
                {filteredJobs.map((job) => (
                  <JobCard key={job.id} job={job} />
                ))}
              </AnimatePresence>
            </div>
          ) : (
            <div className="flex flex-col items-center rounded-2xl border border-white/[0.08] bg-white/[0.03] px-6 py-16 text-center">
              <Search className="mb-4 h-8 w-8 text-indigo-300" strokeWidth={1.5} />
              <p className="font-display text-lg font-semibold text-white">No matches yet</p>
              <p className="mt-1 max-w-sm text-sm text-white/45">
                {jobs.length === 0
                  ? 'Run a search to scan Mynavi, CareerCross, Wantedly, and GaijinPot.'
                  : 'Nothing in this filter. Try All or another platform.'}
              </p>
              {jobs.length === 0 && (
                <Link
                  to="/search"
                  className="mt-5 inline-flex rounded-xl bg-accent-gradient px-4 py-2.5 text-sm font-semibold text-white shadow-accent-glow"
                >
                  Search Jobs
                </Link>
              )}
            </div>
          )}
        </FadeInSection>

        {history.length > 0 && (
          <FadeInSection>
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-soft">
              <SectionTitle>Recent Searches</SectionTitle>
              <div className="space-y-3">
                {history.map((h) => (
                  <div key={h.id} className="flex justify-between border-b border-white/[0.04] py-1 text-sm last:border-0">
                    <span className="text-white/60">
                      {h.job_title} — {h.location}
                    </span>
                    <span className="text-white/30">{h.results_count} results</span>
                  </div>
                ))}
              </div>
            </div>
          </FadeInSection>
        )}
      </div>
    </AppShell>
  );
}
