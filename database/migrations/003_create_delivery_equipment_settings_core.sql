-- Sprint 13: persistência relacional de entregas, equipamentos e configurações
-- Regras: docs/DB_RULES_MYSQL.md

CREATE TABLE IF NOT EXISTS delivery_events (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(150) NOT NULL,
  event_date DATE NOT NULL,
  status VARCHAR(40) NOT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_delivery_events_event_date (event_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS delivery_invites (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  delivery_event_id BIGINT UNSIGNED NOT NULL,
  family_id BIGINT UNSIGNED NOT NULL,
  withdrawal_code VARCHAR(12) NOT NULL,
  status VARCHAR(40) NOT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT uq_delivery_invites_event_family UNIQUE (delivery_event_id, family_id),
  INDEX idx_delivery_invites_family_id (family_id),
  CONSTRAINT fk_delivery_invites_events FOREIGN KEY (delivery_event_id) REFERENCES delivery_events(id) ON DELETE CASCADE,
  CONSTRAINT fk_delivery_invites_families FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS delivery_withdrawals (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  delivery_event_id BIGINT UNSIGNED NOT NULL,
  family_id BIGINT UNSIGNED NOT NULL,
  signature_accepted TINYINT(1) NOT NULL DEFAULT 0,
  signature_name VARCHAR(150) NULL,
  status VARCHAR(40) NOT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_delivery_withdrawals_family_id (family_id),
  CONSTRAINT fk_delivery_withdrawals_events FOREIGN KEY (delivery_event_id) REFERENCES delivery_events(id) ON DELETE CASCADE,
  CONSTRAINT fk_delivery_withdrawals_families FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS equipments (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(20) NOT NULL,
  type VARCHAR(120) NOT NULL,
  status VARCHAR(40) NOT NULL,
  `condition` VARCHAR(120) NULL,
  notes VARCHAR(255) NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT uq_equipments_code UNIQUE (code),
  INDEX idx_equipments_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS equipment_loans (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  equipment_id BIGINT UNSIGNED NOT NULL,
  family_id BIGINT UNSIGNED NOT NULL,
  due_date DATE NOT NULL,
  status VARCHAR(40) NOT NULL,
  return_condition VARCHAR(120) NULL,
  return_notes VARCHAR(255) NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_equipment_loans_equipment_id (equipment_id),
  INDEX idx_equipment_loans_family_id (family_id),
  CONSTRAINT fk_equipment_loans_equipment FOREIGN KEY (equipment_id) REFERENCES equipments(id) ON DELETE CASCADE,
  CONSTRAINT fk_equipment_loans_family FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS eligibility_settings (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  max_deliveries_per_month INT UNSIGNED NOT NULL,
  min_months_since_last_delivery INT UNSIGNED NOT NULL,
  min_vulnerability_score INT UNSIGNED NOT NULL,
  require_documentation TINYINT(1) NOT NULL DEFAULT 0,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
