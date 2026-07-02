"""
Extrator de dados de Nao Conformidades / Planos de Acao - ChecklistFacil
--------------------------------------------------------------------------
Le uma lista de links (recebidos por e-mail do setor de fiscalizacao),
chama a API publica do ChecklistFacil para cada um, extrai os dados
estruturados e consolida em uma planilha Excel.

Uso:
    python extrair_nc.py            (procura "links.txt" na mesma pasta)
    python extrair_nc.py links.txt  (ou informe outro caminho)
"""

import sys
import time

import requests
import openpyxl
from openpyxl.styles import Font


HEADERS = {"User-Agent": "Mozilla/5.0 (automacao-nc-tripoloni)"}

API_BASE = "https://app.checklistfacil.com.br/api/spa/v1/action-plan/public/"

STATUS_MAP = {
    "approved": "Solucao aprovada",
    "reproved": "Solucao reprovada",
    "pending": "Aguardando analise",
    "review": "Em analise",
}


def construir_url_api(link_email: str) -> str:
    """
    Converte o link recebido por e-mail (dominio spa.checklistfacil.com.br)
    na URL da API publica (dominio app.checklistfacil.com.br), reaproveitando
    o mesmo token que já vem no link.
    """
    token = link_email.strip().rstrip("/").split("/")[-1]
    return API_BASE + token


def mapear_status(status_bruto):
    if not status_bruto:
        return status_bruto
    return STATUS_MAP.get(status_bruto, status_bruto)


def extrair_dados_nc(payload: dict, link: str = "") -> dict:
    """Extrai os dados relevantes a partir do JSON retornado pela API publica."""
    details = payload.get("details") or {}
    solutions = payload.get("solutions") or []

    dados = {
        "link": link,
        "data_criacao": None,
        "status": None,
        "tentativas": len(solutions),
        "solucao": {},
        "plano_acao": {},
    }

    # --- Campos do plano de acao (sempre existem) ---
    plano_acao = {
        "Codigo do Plano de Acao": f"#{payload.get('actionPlanId', '')}",
        "Unidade": (details.get("unit") or {}).get("name"),
        "O que sera feito": details.get("what"),
        "Quando sera feito": details.get("when"),
    }
    # campos opcionais - só inclui se tiverem valor preenchido
    opcionais = {
        "Por que": details.get("why"),
        "Onde": details.get("where"),
        "Quem": details.get("who"),
        "Como": details.get("how"),
        "Quanto custara": details.get("howMuch"),
        "Comentario": details.get("comment"),
    }
    for chave, valor in opcionais.items():
        if valor:
            plano_acao[chave] = valor

    # campos customizados (estrutura pode variar conforme o formulário)
    for cf in details.get("customFields") or []:
        rotulo = cf.get("label") or cf.get("key") or cf.get("name")
        if rotulo:
            plano_acao[rotulo] = cf.get("value")

    dados["plano_acao"] = plano_acao

    # --- Solucao (pode nao existir ainda) ---
    if solutions:
        ultima = solutions[-1]  # solucao mais recente
        acao = ultima.get("solutionAction") or {}
        dados["status"] = mapear_status(ultima.get("status"))
        dados["data_criacao"] = ultima.get("createdAt")
        dados["solucao"] = {
            "Solucao": ultima.get("solutionText") or "",
            "Qtd. Anexos": len(ultima.get("attachments") or []),
            "Enviado por": (ultima.get("user") or {}).get("name") or "",
            "Avaliado em": acao.get("createdAt") or "",
            "Avaliado por": acao.get("user") or "",
            "Motivo/Comentario da avaliacao": acao.get("comment") or "",
        }
    else:
        dados["status"] = "Aguardando solucao"

    return dados


def processar_links(links: list) -> list:
    """Chama a API publica para cada link e retorna os dados extraidos."""
    resultados = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for i, link in enumerate(links, 1):
        link = link.strip()
        if not link:
            continue
        url_api = construir_url_api(link)
        print(f"[{i}/{len(links)}] Processando: {link}")
        try:
            resp = session.get(url_api, timeout=20)
            resp.raise_for_status()
            corpo = resp.json()
            if not corpo.get("success", True):
                raise ValueError(corpo.get("message", "Falha reportada pela API"))
            payload = corpo.get("payload") or {}
            dados = extrair_dados_nc(payload, link)
            resultados.append(dados)
        except Exception as e:
            print(f"  Erro ao processar {link}: {e}")
            resultados.append({
                "link": link, "erro": str(e), "status": "Erro ao processar",
                "solucao": {}, "plano_acao": {},
            })
        time.sleep(0.5)

    return resultados


def exportar_excel(resultados: list, caminho_saida: str = "nao_conformidades.xlsx"):
    """Exporta os resultados extraidos para uma planilha Excel."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Nao Conformidades"

    colunas_fixas = ["Link", "Data da Solucao", "Status", "Tentativas de Solucao"]

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
        linha = [
            r.get("link", ""),
            r.get("data_criacao", ""),
            r.get("status", ""),
            r.get("tentativas", ""),
        ]
        for col in colunas_plano:
            linha.append(r.get("plano_acao", {}).get(col, ""))
        for col in colunas_solucao:
            linha.append(r.get("solucao", {}).get(col, ""))
        ws.append(linha)

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
        print(f"Arquivo nao encontrado: {caminho_links}")
        print("Crie um arquivo .txt com um link por linha, ou informe o caminho:")
        print("  python extrair_nc.py caminho/para/links.txt")
        sys.exit(1)

    if not links:
        print(f"O arquivo {caminho_links} esta vazio.")
        sys.exit(1)

    resultados = processar_links(links)
    exportar_excel(resultados)
