-- Add multi-platform job fields (run in Supabase SQL Editor)
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source_platform TEXT DEFAULT 'linkedin';
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS visa_sponsorship BOOLEAN DEFAULT FALSE;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS japanese_level TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS remote_option BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_jobs_source_platform ON jobs(source_platform);
