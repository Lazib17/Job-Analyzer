import { useEffect, useState } from 'react';
import { openResumeFile } from '../../api/axios';

export default function CvPreview({ resume, onClose }) {
  const [opening, setOpening] = useState(false);
  const [fileError, setFileError] = useState('');
  const text = resume?.extracted_text?.trim() || '';

  useEffect(() => {
    const onKey = (event) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const handleOpenOriginal = async () => {
    setOpening(true);
    setFileError('');
    try {
      await openResumeFile();
    } catch (err) {
      setFileError(err.message || 'Could not open the original CV file.');
    } finally {
      setOpening(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="cv-preview-title"
        className="flex max-h-[85vh] w-full max-w-3xl flex-col rounded-2xl border border-white/10 bg-[#0c1014] shadow-soft"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b border-white/[0.06] px-6 py-4">
          <div>
            <h2 id="cv-preview-title" className="font-display text-lg font-semibold text-white">
              Your CV
            </h2>
            <p className="mt-1 text-xs text-white/40">
              Uploaded {resume?.uploaded_at ? new Date(resume.uploaded_at).toLocaleString() : 'recently'}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-2 py-1 text-sm text-white/50 hover:bg-white/[0.06] hover:text-white"
          >
            Close
          </button>
        </div>

        <div className="overflow-y-auto px-6 py-5">
          {text ? (
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-white/80">{text}</pre>
          ) : (
            <p className="text-sm text-white/45">No text could be extracted from this CV.</p>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-3 border-t border-white/[0.06] px-6 py-4">
          <button
            type="button"
            onClick={handleOpenOriginal}
            disabled={opening}
            className="rounded-xl bg-accent-gradient px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60"
          >
            {opening ? 'Opening…' : 'Open original file'}
          </button>
          {fileError && <p className="text-sm text-red-400/90">{fileError}</p>}
        </div>
      </div>
    </div>
  );
}
