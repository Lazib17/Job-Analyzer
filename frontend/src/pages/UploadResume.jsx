import { useEffect, useState } from 'react';
import { getResume, uploadResume } from '../api/axios';
import {
  AppShell,
  FadeInSection,
  PageHeader,
} from '../components/layout/AppShell';
import { VetraButton, VetraCard } from '../components/ui/vetra-ui';

export default function UploadResume() {
  const [file, setFile] = useState(null);
  const [existing, setExisting] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    getResume()
      .then((res) => setExisting(res.data))
      .catch(() => setExisting(null));
  }, []);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      const ext = selected.name.split('.').pop().toLowerCase();
      if (!['pdf', 'docx', 'doc'].includes(ext)) {
        setError('Only PDF and DOCX files are supported.');
        return;
      }
      setFile(selected);
      setError('');
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError('');
    setMessage('');
    try {
      const { data } = await uploadResume(file);
      setExisting(data.resume);
      setMessage('Resume uploaded and parsed successfully.');
      setFile(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-xl mx-auto">
        <PageHeader
          eyebrow="Profile"
          title="Upload resume"
          subtitle="Upload your CV in PDF or DOCX format for AI-powered job analysis."
        />

        {existing && (
          <FadeInSection delay={0.1}>
            <VetraCard className="mb-6 border-emerald-500/10 bg-emerald-500/[0.03]">
              <p className="text-white/80 font-medium">Resume on file</p>
              <p className="text-white/40 text-sm mt-2">
                Uploaded {new Date(existing.uploaded_at).toLocaleDateString()}
              </p>
              {existing.extracted_text && (
                <p className="text-white/30 text-xs mt-3 leading-relaxed line-clamp-3">
                  {existing.extracted_text.slice(0, 200)}...
                </p>
              )}
            </VetraCard>
          </FadeInSection>
        )}

        <FadeInSection delay={0.15}>
          <VetraCard>
            <form onSubmit={handleUpload}>
              <div
                className="border border-dashed border-white/[0.08] rounded-2xl p-12 sm:p-16 text-center hover:border-white/[0.15] hover:bg-white/[0.02] transition-all duration-300 cursor-pointer"
                onClick={() => document.getElementById('file-input').click()}
              >
                <p className="text-white/70 font-medium">
                  {file ? file.name : 'Click to select your resume'}
                </p>
                <p className="text-white/30 text-sm mt-2">PDF or DOCX, max 10MB</p>
                <input
                  id="file-input"
                  type="file"
                  accept=".pdf,.docx,.doc"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </div>

              {error && (
                <div className="rounded-xl border border-red-500/20 bg-red-500/5 text-red-400/90 text-sm p-4 mt-5">
                  {error}
                </div>
              )}
              {message && (
                <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 text-emerald-400/90 text-sm p-4 mt-5">
                  {message}
                </div>
              )}

              <VetraButton
                type="submit"
                disabled={!file}
                loading={loading}
                className="w-full mt-6 py-3"
              >
                {loading ? 'Uploading...' : 'Upload Resume'}
              </VetraButton>
            </form>
          </VetraCard>
        </FadeInSection>
      </div>
    </AppShell>
  );
}
