# Matriz de compatibilidade Sprint 01

| Domínio | Legado Python | Alvo PHP | Status Sprint 01 |
|---|---|---|---|
| Famílias | rotas SSR + posts form | REST `/api/v1/families` | Parcial (adaptador necessário) |
| Crianças | misto SSR/POST | REST `/api/v1/children` | Parcial (adaptador necessário) |
| Entregas/eventos | `/entregas/eventos/*` | `/api/v1/deliveries/events/*` + rewrite | Parcial (mapeamento com rewrite) |
| Relatórios export | `/relatorios/export.*` | `/api/v1/reports/export.*` | Parcial (header/payload equivalentes) |
| Equipamentos | `/equipamentos/*` | `/api/v1/equipment/*` | Parcial (mapeamento de status/enum) |
| Rua/encaminhamentos | `/rua/*` | `/api/v1/street/*` | Parcial (mapeamento de enums) |
| Fechamentos | `/fechamentos/*` | `/api/v1/closures/*` | Parcial (paridade total de regras pendente) |

## Riscos principais
- Endpoint órfão não mapeado no adaptador de compatibilidade.
- Divergência de shape JSON entre SSR/POST legado e API REST alvo.
- Diferença de enum/status entre módulos críticos (entregas e equipamentos).
