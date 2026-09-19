import { useEffect, useState } from 'react';
import {
  analyzeAllJobs,
  analyzeJob,
  getRankedJobs,
  reanalyzeJob,
  toggleFavorite,
} from '../api/axios';
import JobCard from '../components/JobCard';
import {
  AppShell,
  FadeInSection,
  LoadingState,
  PageHeader,
} from '../components/layout/AppShell';
import { VetraButton, VetraCard, VetraInput, VetraSelect } from '../components/ui/vetra-ui';

export default function JobResults() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzingId, setAnalyzingId] = useState(null);
  const [filters, setFilters] = useState({
    min_score: '',
    favorites_only: false,
    search_query: '',
  });

  useEffect(() => {
    loadJobs();
  }, [filters]);

  const loadJobs = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.min_score) params.min_score = Number(filters.min_score);
      if (filters.favorites_only) params.favorites_only = true;
      if (filters.search_query) params.search_query = filters.search_query;

      const { data } = await getRankedJobs(params);
      setJobs(data);
    } catch (err) {
      console.error('Failed to load jobs', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFavorite = async (id) => {
    try {
      await toggleFavorite(id);
      loadJobs();
    } catch {
      alert('Failed to update favorite');
    }
  };

  const handleAnalyze = async (id) => {
    setAnalyzingId(id);
    try {
      await analyzeJob(id);
      loadJobs();
    } catch (err) {
      alert(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setAnalyzingId(null);
    }
  };

  const handleAnalyzeAll = async () => {
    setLoading(true);
    try {
      const { data } = await analyzeAllJobs();
      if (data.errors?.length) {
        alert(`Analyzed ${data.analyzed} jobs. ${data.errors.length} failed.`);
      } else if (data.analyzed === 0) {
        alert('No jobs to analyze. Search for jobs first.');
      }
      loadJobs();
    } catch (err) {
      alert(err.response?.data?.detail || 'Bulk analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const handleReanalyze = async (id) => {
    setAnalyzingId(id);
    try {
      await reanalyzeJob(id);
      loadJobs();
    } catch (err) {
      alert(err.response?.data?.detail || 'Re-analysis failed');
    } finally {
      setAnalyzingId(null);
    }
  };

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto">
        <PageHeader
          eyebrow="Rankings"
          title="Job results"
          subtitle={`${jobs.length} jobs ranked by AI compatibility score.`}
          actions={
            <VetraButton onClick={handleAnalyzeAll}>Analyze All</VetraButton>
          }
        />

        <FadeInSection delay={0.1}>
          <VetraCard className="mb-8 flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
              <VetraInput
                label="Search"
                placeholder="Filter by title, company..."
                value={filters.search_query}
                onChange={(e) => setFilters({ ...filters, search_query: e.target.value })}
              />
            </div>
            <div className="w-full sm:w-40">
              <VetraSelect
                label="Min score"
                value={filters.min_score}
                onChange={(e) => setFilters({ ...filters, min_score: e.target.value })}
              >
                <option value="">Any</option>
                <option value="40">40%+</option>
                <option value="60">60%+</option>
                <option value="80">80%+</option>
              </VetraSelect>
            </div>
            <div className="flex items-center gap-2 pb-1">
              <input
                type="checkbox"
                id="fav"
                checked={filters.favorites_only}
                onChange={(e) => setFilters({ ...filters, favorites_only: e.target.checked })}
                className="w-4 h-4 accent-violet-500"
              />
              <label htmlFor="fav" className="text-sm text-white/50">
                Favorites only
              </label>
            </div>
          </VetraCard>
        </FadeInSection>

        {loading ? (
          <LoadingState message="Loading jobs..." />
        ) : jobs.length === 0 ? (
          <VetraCard className="text-center py-20">
            <p className="text-white/40">No jobs found. Try searching for jobs first.</p>
          </VetraCard>
        ) : (
          <FadeInSection delay={0.15}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {jobs.map((job) => (
                <div key={job.id} className="relative">
                  <JobCard
                    job={job}
                    onFavorite={handleFavorite}
                    onAnalyze={handleAnalyze}
                    analyzing={analyzingId === job.id}
                  />
                  {job.compatibility_score && (
                    <button
                      onClick={() => handleReanalyze(job.id)}
                      className="absolute top-4 right-4 text-xs text-white/25 hover:text-white/60 transition-colors"
                      title="Re-run analysis"
                    >
                      ↻
                    </button>
                  )}
                </div>
              ))}
            </div>
          </FadeInSection>
        )}
      </div>
    </AppShell>
  );
}
