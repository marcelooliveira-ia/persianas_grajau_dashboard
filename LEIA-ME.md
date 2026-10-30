# Painel de desempenho por plataforma — Persianas Grajaú

Página pública: https://marcelooliveira-ia.github.io/persianas_grajau_dashboard/
Arquivo dos meses: https://marcelooliveira-ia.github.io/persianas_grajau_dashboard/meses/AAAA-MM/

## Estrutura
- `src/` molde do painel (igual para todos os clientes)
- `config.json` marca, plataformas, canais, contas de anúncio e textos fixos deste cliente
- `data/AAAA-MM/` dados do mês: `campanhas.csv`, `leads_conta.csv`, `pedido.csv`, `sugestao.csv`, `acoes.csv`, `meta.json`
- `assets/` logos
- `build.py` gera `index.html` (mês mais recente) e `meses/AAAA-MM/index.html`
- `tests/check.js` teste automático (computador, tablet, celular, tela pequena)

## Relatório do mês (resumo)
1. Criar `data/AAAA-MM/` com os 6 arquivos (ler os painéis; conferir que os totais fecham).
2. `python3 build.py` (valida os dados e gera as páginas).
3. `node tests/check.js index.html` (tem que terminar sem PROBLEMAS).
4. `git add -A && git commit && git push` e conferir o link no Chrome.

## Novo cliente
Copiar `src/`, `build.py`, `tests/` e `LEIA-ME.md` para o repositório `<cliente>_dashboard`, criar `config.json`, `assets/` e a primeira pasta `data/AAAA-MM/`.

Aviso: repositório público, link previsível, `noindex`. Não incluir dados sensíveis. Remover após a reunião, se o cliente preferir.
