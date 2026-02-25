-- Sprint 24: persistência transacional para tokens de reset de senha

CREATE TABLE IF NOT EXISTS auth_reset_tokens (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  token_hash CHAR(64) NOT NULL,
  email VARCHAR(180) NOT NULL,
  expires_at DATETIME NOT NULL,
  created_at DATETIME NOT NULL,
  consumed_at DATETIME NULL,
  PRIMARY KEY (id),
  CONSTRAINT uq_auth_reset_tokens_token_hash UNIQUE (token_hash),
  INDEX idx_auth_reset_tokens_email (email),
  INDEX idx_auth_reset_tokens_expires_at (expires_at),
  INDEX idx_auth_reset_tokens_consumed_at (consumed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
