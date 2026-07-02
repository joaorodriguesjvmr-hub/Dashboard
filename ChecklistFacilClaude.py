"""
Extrator de dados de Não Conformidades / Planos de Ação - ChecklistFacil
--------------------------------------------------------------------------
Lê uma lista de links (recebidos por e-mail do setor de fiscalização),
acessa cada página, extrai os dados estruturados e consolida em uma
planilha Excel.

Uso:
    python extrair_nc.py links.txt
    (arquivo .txt com um link por linha)

    ou edite a lista `links` no bloco __main__ abaixo.
"""

import sys
import time

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import openpyxl
from openpyxl.styles import Font


def extrair_dados_nc(html: str, link: str = "") -> dict:
    """Extrai os dados de uma página de solução/plano de ação do ChecklistFacil."""
    soup = BeautifulSoup(html, "html.parser")

    dados = {
        "link": link,
        "data_criacao": None,
        "status": None,
        "solucao": {},   # key/value dos campos da solução enviada
        "plano_acao": {},  # key/value dos campos do plano de ação (NC)
    }

    # --- Data de criação da solução ---
    date_el = soup.find(class_="solution-info__date")
    if date_el:
        texto = date_el.get_text(strip=True)
        # remove o rótulo "Data de criação:" e deixa só o valor
        dados["data_criacao"] = texto.split(":", 1)[-1].strip() if ":" in texto else texto

    # --- Status da solução (Aprovada / Reprovada / Em análise) ---
    # Quando a NC ainda não recebeu nenhuma solução, o bloco
    # "solution-status" simplesmente não existe na página (só aparece
    # o formulário "Nova solução"). Nesse caso, classificamos manualmente.
    status_el = soup.find(class_="solution-status")
    if status_el:
        span = status_el.find("span")
        dados["status"] = span.get_text(strip=True) if span else status_el.get_text(strip=True)
    else:
        dados["status"] = "Aguardando solução"

    # --- Campos da solução (dentro do card de solução enviada) ---
    # Nota: no HTML real a classe é "solution-field" (chave: solution-field__key /
    # valor: solution-field__value), agrupados dentro do componente
    # <cl-action-plan-solution-card>.
    solution_card = soup.find("cl-action-plan-solution-card")
    if solution_card:
        for field in solution_card.find_all(class_="solution-field"):
            key_el = field.find(class_="solution-field__key")
            val_el = field.find(class_="solution-field__value")
            if key_el:
                key = key_el.get_text(strip=True)
                value = val_el.get_text(strip=True) if val_el else ""
                dados["solucao"][key] = value

    # --- Campos do plano de ação (card "Detalhes do Plano de Ação") ---
    action_card = soup.find(class_="action-plan-detail-card")
    if action_card:
        for field in action_card.find_all(class_="action-plan-field"):
            key_el = field.find(class_="action-plan-field__key")
            val_el = field.find(class_="action-plan-field__value")
            if key_el:
                key = key_el.get_text(strip=True)
                value = val_el.get_text(strip=True) if val_el else ""
                dados["plano_acao"][key] = value

    return dados


def processar_links(links: list) -> list:
    """
    Abre cada link em um navegador headless (Chromium via Playwright),
    espera o Angular renderizar o conteúdo e então extrai os dados.

    Necessário: pip install playwright && playwright install chromium
    """
    resultados = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (automacao-nc-tripoloni)")

        for i, link in enumerate(links, 1):
            link = link.strip()
            if not link:
                continue
            print(f"[{i}/{len(links)}] Processando: {link}")
            try:
                page.goto(link, wait_until="networkidle", timeout=30000)
                # Os detalhes do plano de ação sempre existem na página,
                # com ou sem solução enviada — é um indicador seguro de
                # que o Angular terminou de renderizar.
                page.wait_for_selector(".action-plan-field", timeout=15000)
                html = page.content()
                dados = extrair_dados_nc(html, link)
                resultados.append(dados)
            except Exception as e:
                print(f"  Erro ao processar {link}: {e}")
                resultados.append({"link": link, "erro": str(e), "solucao": {}, "plano_acao": {}})
            time.sleep(1)  # evita sobrecarregar o servidor

        browser.close()

    return resultados


def exportar_excel(resultados: list, caminho_saida: str = "nao_conformidades.xlsx"):
    """Exporta os resultados extraídos para uma planilha Excel."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Não Conformidades"

    colunas_fixas = ["Link", "Data de Criação", "Status"]

    # Colunas dinâmicas: descobertas a partir dos dados reais (evita perder
    # campos que variem de uma NC para outra)
    colunas_plano = set()
    colunas_solucao = set()
    for r in resultados:
        colunas_plano.update(r.get("plano_acao", {}).keys())
        colunas_solucao.update(r.get("solucao", {}).keys())

    colunas_plano = sorted(colunas_plano)
    colunas_solucao = sorted(colunas_solucao)
    cabecalho = colunas_fixas + colunas_plano + colunas_solucao

    ws.append(cabecalho)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for r in resultados:
        linha = [r.get("link", ""), r.get("data_criacao", ""), r.get("status", "")]
        for col in colunas_plano:
            linha.append(r.get("plano_acao", {}).get(col, ""))
        for col in colunas_solucao:
            linha.append(r.get("solucao", {}).get(col, ""))
        ws.append(linha)

    # Ajuste simples de largura de coluna
    for col_cells in ws.columns:
        max_len = max((len(str(c.value)) if c.value else 0) for c in col_cells)
        ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 2, 60)

    wb.save(caminho_saida)
    print(f"\nArquivo salvo em: {caminho_saida}")


if __name__ == "__main__":
    caminho_links = sys.argv[1] if len(sys.argv) > 1 else "links.txt"

    try:
        with open(caminho_links, encoding="utf-8") as f:
            links = [l.strip() for l in f if l.strip()]
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {caminho_links}")
        print("Crie um arquivo .txt com um link por linha, ou informe o caminho:")
        print("  python extrair_nc.py caminho/para/links.txt")
        sys.exit(1)

    if not links:
        print(f"O arquivo {caminho_links} está vazio.")
        sys.exit(1)

    resultados = processar_links(links)
    exportar_excel(resultados)
