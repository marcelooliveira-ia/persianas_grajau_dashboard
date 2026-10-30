#!/usr/bin/env python3
"""Monta o painel do cliente: src/ (molde) + config.json + data/AAAA-MM/ -> index.html.

Uso:
  python3 build.py              # mês mais recente em data/ (gera index.html e meses/AAAA-MM/index.html)
  python3 build.py --mes 2026-10
"""
import argparse, csv, html, io, json, os, re, sys, urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
ARQUIVOS = ['campanhas', 'leads_conta', 'pedido', 'sugestao', 'acoes']


def ler(p):
    with open(os.path.join(ROOT, p), encoding='utf-8') as f:
        return f.read()


def escrever(p, t):
    full = os.path.join(ROOT, p)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(t)


def linhas(texto):
    return list(csv.DictReader(io.StringIO(texto)))


def meses_disponiveis():
    d = os.path.join(ROOT, 'data')
    return sorted(x for x in os.listdir(d) if re.fullmatch(r'\d{4}-\d{2}', x))


def validar(cfg, dados, meta, mes, imprimir=True):
    erros = []
    camp = linhas(dados['campanhas'])
    ped = linhas(dados['pedido'])
    sug = linhas(dados['sugestao'])
    conta = linhas(dados['leads_conta'])
    plats = []
    for r in camp:
        if r['plataforma'] not in plats:
            plats.append(r['plataforma'])
    for p in plats:
        if p not in cfg['cores']['plataformas']:
            erros.append(f'plataforma sem cor em config.json: {p}')
        if p not in cfg['canais']:
            erros.append(f'plataforma sem canais em config.json: {p}')
    for r in ped:
        if r['plataforma'] not in plats:
            erros.append(f'pedido para plataforma sem campanha: {r["plataforma"]}')
    for p in plats:
        if p not in [r['plataforma'] for r in ped]:
            erros.append(f'plataforma sem verba combinada (pedido.csv): {p}')
    for r in conta:
        if r['plataforma'] not in plats:
            erros.append(f'leads_conta de plataforma sem campanha: {r["plataforma"]}')
    soma = sum(float(r['percentual']) for r in sug)
    if abs(soma - 1) > 0.001:
        erros.append(f'sugestao.csv soma {soma:.3f}, deveria somar 1.0')
    grupos = {r['grupo'] for r in camp}
    for r in sug:
        if r['grupo'] not in grupos and r['grupo'] not in ('Remarketing',):
            erros.append(f'sugestao com grupo sem campanha: {r["grupo"]}')
    if int(meta['dias_passados']) > int(meta['dias_total']):
        erros.append('dias_passados maior que dias_total')
    if not imprimir:
        return erros
    # resumo para conferência humana
    inv = {}
    leads = {}
    for r in camp:
        inv[r['plataforma']] = inv.get(r['plataforma'], 0) + float(r['investimento'])
        if r['leads'] != '':
            leads[r['plataforma']] = leads.get(r['plataforma'], 0) + float(r['leads'])
    for r in conta:
        leads[r['plataforma']] = float(r['leads'])
    print(f'== {cfg["cliente"]} - {mes} ==')
    tot_i = sum(inv.values())
    tot_l = sum(leads.values())
    for p in plats:
        l = leads.get(p)
        cpl = f'{inv[p] / l:.2f}' if l else 'sem lead'
        print(f'  {p:<12} investido {inv[p]:>10.2f}  leads {l if l is not None else "-"}  CPL {cpl}')
    print(f'  TOTAL        investido {tot_i:>10.2f}  leads {tot_l:.0f}  CPL {tot_i / tot_l:.2f}' if tot_l else f'  TOTAL investido {tot_i:.2f}')
    return erros


def montar(cfg, mes, prefixo, imprimir=True):
    pasta = f'data/{mes}'
    meta = json.loads(ler(f'{pasta}/meta.json'))
    dados = {n: ler(f'{pasta}/{n}.csv') for n in ARQUIVOS}
    erros = validar(cfg, dados, meta, mes, imprimir)
    if erros:
        print('ERROS DE VALIDAÇÃO:')
        for e in erros:
            print(' -', e)
        sys.exit(1)
    dados['periodo'] = f'dias_total,dias_passados\n{meta["dias_total"]},{meta["dias_passados"]}\n'
    ordem = ['campanhas', 'leads_conta', 'pedido', 'periodo', 'acoes', 'sugestao']
    csv_json = json.dumps({k: dados[k] for k in ordem}, ensure_ascii=False).replace('</', '<\\/')
    cfg_js = json.dumps({'cores': {'series': cfg['cores']['series'], 'plataformas': cfg['cores']['plataformas']},
                         'canais': cfg['canais']}, ensure_ascii=False).replace('</', '<\\/')
    wa_texto = (f'Olá, Marcelo! Estou acessando o painel de desempenho da {cfg["cliente"]} '
                f'({meta["mes_extenso"].lower()}) e gostaria de conversar sobre ele.')
    como = '\n'.join('<li>' + html.escape(t, quote=False) + '</li>' for t in cfg['como_ler'])
    vals = {
        'CLIENTE': html.escape(cfg['cliente'], quote=False),
        'MES_EXTENSO': meta['mes_extenso'], 'MES_NOME': meta['mes_nome'],
        'INTERVALO': meta['intervalo'], 'LIDO_EM': meta['lido_em'],
        'PLATAFORMAS_TXT': cfg['plataformas_txt'], 'OBJETIVO': cfg['objetivo'], 'REGIAO': cfg['regiao'],
        'LOGO_CAB': prefixo + cfg['logo_cabecalho'], 'LOGO_ROD': prefixo + cfg['logo_rodape'],
        'WA_NUM': cfg['whatsapp_marcelo'], 'WA_TEXT': urllib.parse.quote(wa_texto, safe=''),
        'COMO_LER': como, 'COR_DESTAQUE': cfg['cores']['destaque'], 'COR_DOURADO': cfg['cores']['dourado'],
        'CFG_JSON': cfg_js, 'CSV_JSON': csv_json,
    }
    out = ''.join(ler('src/' + n) for n in ['head.html', 'page.html', 'shim.html', 'app.html', 'tail.html'])
    for k, v in vals.items():
        out = out.replace('{{' + k + '}}', v)
    sobra = re.findall(r'\{\{[A-Z_]+\}\}', out)
    if sobra:
        print('Placeholders sem valor:', sorted(set(sobra)))
        sys.exit(1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mes')
    a = ap.parse_args()
    cfg = json.loads(ler('config.json'))
    meses = meses_disponiveis()
    if not meses:
        sys.exit('Nenhuma pasta data/AAAA-MM encontrada')
    mes = a.mes or meses[-1]
    if mes not in meses:
        sys.exit(f'Mês {mes} não existe em data/')
    arquivo = montar(cfg, mes, '../../')
    escrever(f'meses/{mes}/index.html', arquivo)
    if mes == meses[-1]:
        escrever('index.html', montar(cfg, mes, '', False))
        print('Gerado: index.html e meses/%s/index.html' % mes)
    else:
        print('Gerado: meses/%s/index.html' % mes)
    escrever('.nojekyll', '')


if __name__ == '__main__':
    main()
