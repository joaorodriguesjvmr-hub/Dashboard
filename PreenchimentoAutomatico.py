import pyautogui
import time

# --- CONFIGURAÇÃO DE SEGURANÇA ---
pyautogui.FAILSAFE = True

# --- CONFIGURAÇÃO DAS ESTACAS (Altere aqui quando precisar) ---
KM_INICIAL = 845        # O quilômetro de onde quer começar
METROS_INICIAIS = 0     # O metro de onde quer começar (0, 100, 200...)
REPETICOES = 95         # Quantas estacas você quer preencher no total

# Transforma tudo em metros totais para facilitar a matemática do Python
metros_totais_iniciais = (KM_INICIAL * 1000) + METROS_INICIAIS

print("Prepare a tela! O script começará em 3 segundos...")
time.sleep(3)

for i in range(REPETICOES):
    # 🧮 Lógica Matemática: soma 100 metros a cada repetição (i)
    metros_atuais = metros_totais_iniciais + (i * 100)
    
    km = metros_atuais // 1000  # Pega a parte inteira (o KM)
    m = metros_atuais % 1000   # Pega o resto (os Metros)
    
    # Formata o texto. O ':03d' garante que o metro sempre tenha 3 dígitos (ex: 000, 100)
    texto_estaca = f"{km}+{m:03d}"
    
    print(f"🤖 Ciclo {i + 1} de {REPETICOES} | Preenchendo estaca: {texto_estaca}")

    # --- PASSO 1: Clique no botão para abrir o formulário ---
    pyautogui.click(x=-1987, y=315)
    time.sleep(0.5)

    # --- PASSO 2: Preencha o campo de texto ---
    pyautogui.click(x=-1440, y=573) # Clica no campo
    time.sleep(0.3)
    
    # ⚠️ SEGURANÇA: Seleciona tudo (Ctrl+A) e apaga (Backspace) para o campo ficar limpo
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    time.sleep(0.2)
    
    # Digita a estaca gerada automaticamente
    pyautogui.write(texto_estaca, interval=0.01)
    time.sleep(0.5)

    # --- PASSO 3: Lista suspensa 1 ---
    pyautogui.click(x=-1424, y=658)
    time.sleep(0.5)
    pyautogui.click(x=-1407, y=869)
    time.sleep(0.5)

    # --- PASSO 4: Lista suspensa 2 ---
    pyautogui.click(x=-1429, y=753)
    time.sleep(0.5)
    pyautogui.click(x=-1427, y=631)
    time.sleep(0.5)

    # --- PASSO 5: Clique em salvar ---
    pyautogui.click(x=-967, y=978)
    
    # --- PASSO 6: Pausa antes de reiniciar ---
    time.sleep(0.5)

print("✅ Processo concluído com sucesso!")
