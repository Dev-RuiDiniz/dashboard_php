-- Sprint 26: ticket sequencial por evento e imutabilidade pós-publicação

ALTER TABLE delivery_events
  ADD COLUMN published_at DATETIME NULL AFTER status;

ALTER TABLE delivery_invites
  ADD COLUMN ticket_number INT UNSIGNED NULL AFTER family_id;

ALTER TABLE delivery_invites
  ADD CONSTRAINT uq_delivery_invites_event_ticket UNIQUE (delivery_event_id, ticket_number);
