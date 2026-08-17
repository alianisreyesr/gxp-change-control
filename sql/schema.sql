-- GxP Change Control — synthetic portfolio schema
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS changes (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  system_name TEXT NOT NULL,
  change_type TEXT NOT NULL CHECK (change_type IN ('configuration','code','process','infrastructure','documentation')),
  priority TEXT NOT NULL CHECK (priority IN ('low','medium','high','critical')),
  status TEXT NOT NULL CHECK (status IN (
    'draft','submitted','impact_assessment','pending_approval','approved','rejected',
    'implementing','verification','closed','cancelled'
  )),
  requester TEXT NOT NULL,
  business_justification TEXT,
  target_implementation_date TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS impact_assessments (
  id TEXT PRIMARY KEY,
  change_id TEXT NOT NULL REFERENCES changes(id),
  affects_validated_state INTEGER NOT NULL DEFAULT 0,
  affects_part11_controls INTEGER NOT NULL DEFAULT 0,
  affects_data_integrity INTEGER NOT NULL DEFAULT 0,
  affects_training INTEGER NOT NULL DEFAULT 0,
  affects_sops INTEGER NOT NULL DEFAULT 0,
  risk_summary TEXT,
  residual_risk TEXT CHECK (residual_risk IN ('low','medium','high') OR residual_risk IS NULL),
  assessor TEXT,
  assessed_at TEXT,
  UNIQUE(change_id)
);

CREATE TABLE IF NOT EXISTS approvals (
  id TEXT PRIMARY KEY,
  change_id TEXT NOT NULL REFERENCES changes(id),
  role TEXT NOT NULL,
  decision TEXT NOT NULL CHECK (decision IN ('approve','reject','request_info')),
  comment TEXT,
  actor TEXT NOT NULL,
  decided_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activity_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  change_id TEXT NOT NULL REFERENCES changes(id),
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  detail TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_changes_status ON changes(status);
CREATE INDEX IF NOT EXISTS idx_activity_change ON activity_log(change_id);
