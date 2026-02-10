ALTER TABLE analysis ADD COLUMN status TEXT NOT NULL DEFAULT 'pending';
UPDATE analysis SET status = 'completed' WHERE status IS NULL;
