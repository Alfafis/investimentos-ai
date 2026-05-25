# Claude Desktop Scheduled — Investimentos AI

Referência das 6 rotinas. **Mecanismo principal: Windows Task Scheduler** via `run_rotina.ps1` + `setup_scheduler.ps1`.

Esta configuração serve como alternativa caso o Task Scheduler não esteja disponível.

---

## Rotinas

| # | Arquivo | Nome | Horário |
|---|---------|------|---------|
| 0 | [rotina-00-radar.md](rotina-00-radar.md) | Investimentos AI — Radar de Mercado | 08h00 BRT |
| 1 | [rotina-01-investing-abertura.md](rotina-01-investing-abertura.md) | Investimentos AI — Pipeline Diário | 10h00 BRT |
| 2 | [rotina-02-investing-fechamento.md](rotina-02-investing-fechamento.md) | Investimentos AI — Fechamento Diário | 17h00 BRT |
| 3 | [rotina-03-trader-pre.md](rotina-03-trader-pre.md) | Trader — Pré-Mercado | 09h00 BRT |
| 4 | [rotina-04-trader-mid.md](rotina-04-trader-mid.md) | Trader — Monitoramento Meio-Dia | 13h00 BRT |
| 5 | [rotina-05-trader-fechamento.md](rotina-05-trader-fechamento.md) | Trader — Fechamento e Relatório | 17h30 BRT |

---

## Logs gerados por execução

```
logs/
├── radar-YYYY-MM-DD-08h.md
├── trader-pre-YYYY-MM-DD-09h.md
├── investing-YYYY-MM-DD-10h.md
├── trader-mid-YYYY-MM-DD-13h.md
├── fechamento-YYYY-MM-DD-17h.md          (sexta: -semanal.md)
└── trader-fechamento-YYYY-MM-DD-17h30.md  (sexta: -semanal.md)
```

Cada execução gera um arquivo único (timestamp no nome — sem sobrescrita).
Persistência estruturada: SQLite via `save_decision` / `save_paper_trade` (MCP).
