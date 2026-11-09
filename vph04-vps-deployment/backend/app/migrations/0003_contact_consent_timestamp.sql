ALTER TABLE applications ADD COLUMN IF NOT EXISTS contact_consent_at TIMESTAMPTZ;
UPDATE applications SET contact_consent_at = created_at WHERE contact_consent = TRUE AND contact_consent_at IS NULL;
