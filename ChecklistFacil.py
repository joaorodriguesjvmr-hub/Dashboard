import json
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def extrair_dados_html(html_content, url_origem):
    soup = BeautifulSoup(html_content, 'html.parser')
    dados_extraidos = {
        "url": url_origem,
        "historico_solucoes": [],
        "detalhes_plano_acao": {}
    }
    
    cards = soup.find_all(class_="action-plan-card")[cite: 1]
    
    for card in cards:
        header_solucao = card.find(class_="card-solution-header")[cite: 1]
        if header_solucao:
            solucao_info = {}
            
            data_elem = header_solucao.find(class_="solution-info__date")[cite: 1]
            solucao_info["data_criacao"] = data_elem.text.strip() if data_elem else "Não encontrada"
            
            status_elem = header_solucao.find(class_="solution-status")[cite: 1]
            solucao_info["status"] = status_elem.text.strip() if status_elem else "Não encontrado"
            
            campos_solucao = {}
            fields = card.find_all(class_="solution-field")[cite: 1]
            for field in fields:
                key_elem = field.find(class_="solution-field__key")[cite: 1]
                value_elem = field.find(class_="solution-field__value")[cite: 1]
                if key_elem and value_elem:
                    key = key_elem.text.replace(":", "").strip()
                    value = value_elem.text.strip()
                    campos_solucao[key] = value
            
            solucao_info["campos"] = campos_solucao
            dados_extraidos["historico_solucoes"].append(solucao_info)
            
        elif "action-plan-detail-card" in card.get("class", []):
            fields_plano = card.find_all(class_="action-plan-field")[cite: 1]
            for field in fields_plano:
                key_elem = field.find(class_="action-plan-field__key")[cite: 1]
                value_elem = field.find(class_="action-plan-field__value")[cite: 1]
                if key_elem and value_elem:
                    key = key_elem.text.replace(":", "").strip()
                    value = value_elem.text.strip()
                    dados_extraidos["detalhes_plano_acao"][key] = value
                    
    return dados_extraidos

def processar_links_com_navegador(links):
    resultados = []
    
    with sync_playwright() as p:
        # Lança o navegador em segundo plano (headless=True)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for link in links:
            print(f"Navegando até: {link}...")
            try:
                # Acessa a URL e aguarda até a rede sossegar
                page.goto(link, wait_until="networkidle", timeout=30000)
                
                # Aguarda explicitamente até que o componente do Plano de Ação apareça no DOM
                page.wait_for_selector(".action-plan-card", timeout=15000)[cite: 1]
                
                # Coleta o HTML completo e renderizado pelo Angular
                html_renderizado = page.content()
                
                # Faz o parse com o BeautifulSoup
                dados = extrair_dados_html(html_renderizado, link)
                resultados.append(dados)
                print("Reflexão do DOM obtida com sucesso!")
                
            except Exception as e:
                print(f"❌ Erro ao processar o link (Timeout ou Elemento não carregou): {str(e)}")
                resultados.append({"url": link, "erro": "A página demorou para responder ou o plano de ação não existe."})
                
        browser.close()
        
    return resultados

if __name__ == "__main__":
    # Cole aqui a sua lista de links reais para teste
    lista_urls = [
        "https://spa.checklistfacil.com.br/action-plan/solution-by-link/YTozOntzOjEzOiJpZF9wbGFub19hY2FvIjtpOjE1MzYyNTYwO3M6NToiZW1haWwiO2E6MTp7aTowO2E6Mjp7czo0OiJuYW1lIjtOO3M6NzoiYWRkcmVzcyI7czoyNToiZWRsZW5lc291emFAdHJpcG9sb25pLmNvbSI7fX1zOjEwOiJpZF9lbXByZXNhIjtpOjMzMTA4O30%3D"
    ]
    
    relatorio = processar_links_com_navegador(lista_urls)
    
    print("\n" + "="*50 + "\nRELATÓRIO DE EXTRAÇÃO:\n" + "="*50)
    print(json.dumps(relatorio, indent=4, ensure_ascii=False))
