import { motion } from 'framer-motion';
import { Check, FileUp, LoaderCircle } from 'lucide-react';
import { useCallback, useState } from 'react';
import { cn } from '@/lib/utils';

export default function ResumeDropZone({ resume, uploading, progress, onFile }) {
  const [dragOver, setDragOver] = useState(false);

  const handleFiles = useCallback(
    (file) => {
      if (!file || !onFile) return;
      onFile(file);
    },
    [onFile]
  );

  if (resume && !uploading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-indigo-400/25 bg-indigo-500/[0.08] p-5"
      >
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-gradient text-white">
            <Check className="h-5 w-5" strokeWidth={2} />
          </div>
          <div className="min-w-0">
            <p className="font-display text-sm font-semibold text-white">Resume parsed</p>
            <p className="mt-1 text-xs text-white/45">
              Uploaded {resume.uploaded_at ? new Date(resume.uploaded_at).toLocaleDateString() : 'recently'}
            </p>
            {resume.extracted_text && (
              <p className="mt-3 line-clamp-3 text-sm leading-relaxed text-white/55">
                {resume.extracted_text.slice(0, 220)}
                {resume.extracted_text.length > 220 ? '…' : ''}
              </p>
            )}
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <label
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        handleFiles(e.dataTransfer.files?.[0]);
      }}
      className={cn(
        'flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-colors duration-soft',
        dragOver || uploading ? 'border-indigo-400/60 bg-indigo-500/10' : 'border-white/15 bg-white/[0.03] hover:border-indigo-400/40'
      )}
    >
      <motion.div
        animate={uploading ? { rotate: 0 } : { rotate: [0, 0] }}
        className={cn(
          'mb-3 flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04]',
          uploading && 'border-indigo-400/40'
        )}
      >
        {uploading ? (
          <LoaderCircle className="h-5 w-5 animate-spin text-indigo-300" />
        ) : (
          <FileUp className="h-5 w-5 text-indigo-300" strokeWidth={1.75} />
        )}
      </motion.div>
      <p className="font-display text-sm font-semibold text-white">
        {uploading ? 'Uploading & parsing…' : 'Drop your resume here'}
      </p>
      <p className="mt-1 text-xs text-white/40">PDF or DOCX — or click to browse</p>
      {uploading && (
        <div className="mt-4 h-1.5 w-48 overflow-hidden rounded-full bg-white/10">
          <motion.div
            className="h-full bg-accent-gradient"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.2 }}
          />
        </div>
      )}
      <input
        type="file"
        accept=".pdf,.doc,.docx"
        className="hidden"
        disabled={uploading}
        onChange={(e) => handleFiles(e.target.files?.[0])}
      />
    </label>
  );
}
