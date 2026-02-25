-- Sprint 12: persistência relacional de pessoas em situação de rua e encaminhamentos
-- Regras: docs/DB_RULES_MYSQL.md

CREATE TABLE IF NOT EXISTS street_residents (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  full_name VARCHAR(150) NOT NULL,
  concluded TINYINT(1) NOT NULL DEFAULT 0,
  consent_accepted TINYINT(1) NOT NULL DEFAULT 0,
  signature_name VARCHAR(150) NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_street_residents_full_name (full_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS street_referrals (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  street_resident_id BIGINT UNSIGNED NOT NULL,
  target VARCHAR(150) NOT NULL,
  status VARCHAR(40) NOT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_street_referrals_street_resident_id (street_resident_id),
  INDEX idx_street_referrals_status (status),
  CONSTRAINT fk_street_referrals_street_residents FOREIGN KEY (street_resident_id) REFERENCES street_residents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
