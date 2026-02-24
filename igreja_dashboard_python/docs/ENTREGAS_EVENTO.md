# Entregas por Evento

## Fluxo (alto nível)

1. Criar evento (`OPEN`).
2. Convidar famílias (manual ou automático).
3. Gerar código de retirada por família/evento.
4. Registrar retirada com assinatura aceita.
5. Exportar consolidado CSV/XLSX.
6. Registrar auditoria persistente das ações críticas.

## Endpoints

- `POST /entregas/eventos`
- `POST /entregas/eventos/{id}/convidar`
- `POST /entregas/eventos/{id}/retirada/{family_id}`
- `GET /entregas/eventos/{id}/export.csv`
- `GET /entregas/eventos/{id}/export.xlsx`

## Validações principais

- Apenas `Admin` ou `Operador` podem operar.
- Convite não permite família inativa.
- Evento fechado não permite retirada.
- Assinatura (`signature_accepted`) deve ser `true`.
- Uma retirada por família por evento (constraint + validação).
- `withdrawal_code` único por evento (índice único + gerador dedicado).

## Convite automático

Critérios aplicados em conjunto:

- Vulnerabilidade em níveis críticos (HIGH/EXTREME).
- Sem cesta entregue nos últimos 2 meses.
- Família ativa.

## Exportação

Colunas exportadas:

- Família
- CPF responsável
- Bairro
- Código retirada
- Status
- Confirmado por
- Data confirmação

## Auditoria persistente

Eventos auditados em `audit_logs`:

- criação de evento (`CREATE_EVENT`)
- convite de famílias (`INVITE_FAMILIES`)
- confirmação de retirada (`CONFIRM_WITHDRAWAL`)

## Teste manual rápido

1. Criar evento.
2. Convidar famílias (manual e automático).
3. Confirmar retirada com assinatura aceita.
4. Tentar retirada duplicada (deve bloquear).
5. Baixar CSV e XLSX do evento.

