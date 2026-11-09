ALTER TABLE services ADD COLUMN IF NOT EXISTS category VARCHAR(60) NOT NULL DEFAULT 'Other';
ALTER TABLE services ADD COLUMN IF NOT EXISTS name_en VARCHAR(120);
ALTER TABLE services ADD COLUMN IF NOT EXISTS name_ru VARCHAR(120);
ALTER TABLE services ADD COLUMN IF NOT EXISTS description_en TEXT;
ALTER TABLE services ADD COLUMN IF NOT EXISTS description_ru TEXT;
CREATE INDEX IF NOT EXISTS ix_services_category ON services (category);

ALTER TABLE applications ADD COLUMN IF NOT EXISTS language VARCHAR(5) NOT NULL DEFAULT 'de';
ALTER TABLE applications ADD COLUMN IF NOT EXISTS client_id INTEGER REFERENCES clients(id) ON DELETE SET NULL;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS location VARCHAR(180);
ALTER TABLE applications ADD COLUMN IF NOT EXISTS person_type VARCHAR(40);
ALTER TABLE applications ADD COLUMN IF NOT EXISTS preferred_contact VARCHAR(30);
ALTER TABLE applications ADD COLUMN IF NOT EXISTS reference_url VARCHAR(500);
ALTER TABLE applications ADD COLUMN IF NOT EXISTS priority_score INTEGER NOT NULL DEFAULT 0;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS priority_label VARCHAR(12) NOT NULL DEFAULT 'cold';
ALTER TABLE applications ADD COLUMN IF NOT EXISTS priority_reasons TEXT NOT NULL DEFAULT '[]';
CREATE INDEX IF NOT EXISTS ix_applications_client_id ON applications (client_id);
CREATE INDEX IF NOT EXISTS ix_applications_priority_score ON applications (priority_score);
CREATE INDEX IF NOT EXISTS ix_applications_priority_label ON applications (priority_label);
