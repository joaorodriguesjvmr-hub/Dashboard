import pyautogui
import time

print("Posicione o mouse sobre o elemento... Você tem 5 segundos.")
time.sleep(2)
print(f"Coordenada atual: {pyautogui.position()}")
