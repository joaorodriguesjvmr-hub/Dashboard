import os
from PIL import Image
import pillow_avif 
from rembg import remove  # Biblioteca para remoção de fundo

def converter_imagem_para_png(caminho_imagem, pasta_saida, tirar_fundo=False):
    try:
        with Image.open(caminho_imagem) as img:
            nome_base = os.path.splitext(os.path.basename(caminho_imagem))[0]
            caminho_saida = os.path.join(pasta_saida, f"{nome_base}.png")
            
            # Força o modo RGBA para suportar transparência
            img_convertida = img.convert('RGBA')
            
            # Aplica a remoção de fundo se a opção estiver ativa
            if tirar_fundo:
                print(f"⏳ Removendo fundo de: {os.path.basename(caminho_imagem)}...")
                img_convertida = remove(img_convertida)
            
            # Salva no formato PNG
            img_convertida.save(caminho_saida, 'PNG')
            print(f"✓ Processado: {os.path.basename(caminho_imagem)} -> {nome_base}.png")
            
    except Exception as e:
        print(f"❌ Erro ao processar {os.path.basename(caminho_imagem)}: {e}")

def converter_pasta(pasta_origem, pasta_destino, tirar_fundo=False):
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
        
    extensoes_suportadas = ('.avif', '.webp', '.jpg', '.jpeg')
    
    print("Iniciando o processamento...")
    arquivos = os.listdir(pasta_origem)
    
    for arquivo in arquivos:
        if arquivo.lower().endswith(extensoes_suportadas):
            caminho_completo = os.path.join(pasta_origem, arquivo)
            converter_imagem_para_png(caminho_completo, pasta_destino, tirar_fundo)
            
    print("\nProcesso concluído!")

# --- Configuração ---
if __name__ == "__main__":
    PASTA_ORIGEM = r"C:\Users\joaorodrigues\Downloads\Maquinas\Reduzido"
    PASTA_DESTINO = r"C:\Users\joaorodrigues\Downloads\Maquinas\Convertido"
    
    # 💡 MUDE PARA True SE QUISER REMOVER O FUNDO AUTOMATICAMENTE
    REMOVER_FUNDO = False 
    
    if not os.path.exists(PASTA_ORIGEM):
        os.makedirs(PASTA_ORIGEM)
        print(f"Pasta '{PASTA_ORIGEM}' criada. Coloque suas imagens nela.")
    else:
        converter_pasta(PASTA_ORIGEM, PASTA_DESTINO, tirar_fundo=REMOVER_FUNDO)
