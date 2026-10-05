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

O agente não tem a ferramenta Write (ver "Permissões do agente" no README). O relatório é a
resposta final do `claude -p`, gravada pelo `run_rotina.ps1`:

```
logs/
├── 00-radar-YYYY-MM-DD-08h00.md
├── 03-trader-pre-YYYY-MM-DD-09h00.md
├── 01-investing-abertura-YYYY-MM-DD-10h00.md
├── 04-trader-mid-YYYY-MM-DD-13h00.md
├── 02-investing-fechamento-YYYY-MM-DD-17h00.md
└── 05-trader-fechamento-YYYY-MM-DD-17h30.md
```

Se o arquivo já existir (reexecução no mesmo minuto), o runner acrescenta `-2`, `-3`… — nunca sobrescreve.

Persistência estruturada: SQLite via `save_decision` / `save_paper_trade` (MCP).
