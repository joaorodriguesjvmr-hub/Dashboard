import pandas as pd
import geopandas as gpd
import folium
from branca.element import Element

# ==========================================
# FUNÇÃO DA ROTINA GEOESPACIAL (REUTILIZÁVEL)
# ==========================================
def carregar_pontos_excel(caminho_excel, crs_origem="EPSG:31981", crs_destino=4326):
    """Lê planilha Excel com x/y, converte em GeoDataFrame e reprojeta."""
    df = pd.read_excel(caminho_excel)
    if 'id' in df.columns:
        df = df.sort_values(by='id')
    gdf = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df['x'], df['y']), 
        crs=crs_origem
    )
    return gdf.to_crs(epsg=crs_destino)

# ==========================================
# CONFIGURAÇÃO DE DADOS E CAMINHOS
# ==========================================
prefixo_icones = r"C:\Users\joaorodrigues\Downloads\Maquinas\Convertido\sem bg\\" 

excel_estacas = r"C:\Users\joaorodrigues\Downloads\Qgis\Sinop\Estacas.xlsx"
excel_emprestimos = r"C:\Users\joaorodrigues\Downloads\Qgis\Sinop\CaixasDeEmprestimo.xlsx"
excel_frota = r"C:\Users\joaorodrigues\Downloads\Qgis\Sinop\Equipamentos.xlsx"

# Carrega os dados geográficos e analíticos
gdf_estacas_wgs84 = carregar_pontos_excel(excel_estacas)
gdf_emp_wgs84 = carregar_pontos_excel(excel_emprestimos)

# Lê a planilha de frota (2 colunas: 'imagem' e 'Name')
df_frota = pd.read_excel(excel_frota)

# ==========================================
# CONFIGURAÇÃO DO MAPA BASE
# ==========================================
centro = gdf_estacas_wgs84.geometry.unary_union.centroid
mapa = folium.Map(
    location=[centro.y, centro.x], 
    zoom_start=14, 
    tiles='OpenStreetMap',
    control_scale=True
)

# 1. Desenhar os segmentos do Eixo da Rodovia
estacas_lista = list(gdf_estacas_wgs84.iterrows())
for i in range(len(estacas_lista) - 1):
    _, estaca_atual = estacas_lista[i]
    _, estaca_proxima = estacas_lista[i+1]
    
    coords_segmento = [
        [estaca_atual.geometry.y, estaca_atual.geometry.x],
        [estaca_proxima.geometry.y, estaca_proxima.geometry.x]
    ]
    
    folium.PolyLine(
        coords_segmento,
        color='#1a365d',
        weight=4,
        opacity=0.8,
        tooltip=f"Segmento: {estaca_atual['Name']}"
    ).add_to(mapa)

# 2. Desenhar as Caixas de Empréstimo (Polígonos)
camada_caixas = folium.FeatureGroup(name="Caixas de Empréstimo")
for nome_caixa, grupo in gdf_emp_wgs84.groupby('Name'):
    coords_perimetro = [[row.geometry.y, row.geometry.x] for _, row in grupo.iterrows()]
    
    if len(coords_perimetro) >= 3:
        folium.Polygon(
            locations=coords_perimetro,
            color='#d35400',
            weight=3,
            fill=True,
            fill_color='#e67e22',
            fill_opacity=0.4,
            tooltip=f"Caixa de Empréstimo: {nome_caixa}"
        ).add_to(camada_caixas)
    else:
        folium.PolyLine(
            locations=coords_perimetro,
            color='#d35400',
            weight=3,
            tooltip=f"Limite Caixas: {nome_caixa}"
        ).add_to(camada_caixas)
camada_caixas.add_to(mapa)

# 3. Criar a camada de Pontos de Estaca
camada_pontos = folium.FeatureGroup(name="Estacas (Pontos)")
for _, row in gdf_estacas_wgs84.iterrows():
    popup_conteudo = f"""
    <div style="font-family: Arial, sans-serif; font-size: 12px; min-width: 160px;">
        <h4 style="margin: 0 0 5px 0; color: #1a365d;">{row['Name']}</h4>
        <b>ID:</b> {row['id']}<br>
        <b>Norte (Y UTM):</b> {row['y']:.2f}<br>
        <b>Este (X UTM):</b> {row['x']:.2f}
    </div>
    """
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=6,
        color='blue',
        fill=True,
        fill_color='white',
        fill_opacity=0.8,
        weight=2,
        popup=folium.Popup(popup_conteudo, max_width=250),
        tooltip=str(row['Name'])
    ).add_to(camada_pontos)
camada_pontos.add_to(mapa)

# ==========================================
# LÓGICA DE FROTA ATUALIZADA: POSICIONAMENTO NO PONTO MÉDIO
# ==========================================
camada_frota = folium.FeatureGroup(name="Equipamento Ativo (Teste)")

for _, row_frota in df_frota.iterrows():
    arquivo_icone = row_frota['imagem']
    nome_estaca_alvo = row_frota['Name']
    
    # 1. Encontrar o índice da estaca informada na lista ordenada
    estaca_index_list = gdf_estacas_wgs84[gdf_estacas_wgs84['Name'] == nome_estaca_alvo].index
    
    if not estaca_index_list.empty:
        idx_atual = estaca_index_list[0]
        
        # Encontra a posição numérica dessa estaca dentro da nossa lista sequencial de tuplas
        posicao_na_lista = None
        for k, (original_idx, _) in enumerate(estacas_lista):
            if original_idx == idx_atual:
                posicao_na_lista = k
                break
        
        # Se houver uma estaca seguinte na sequência, calcula o ponto médio do segmento
        if posicao_na_lista is not None and posicao_na_lista < len(estacas_lista) - 1:
            _, estaca_atual = estacas_lista[posicao_na_lista]
            _, estaca_proxima = estacas_lista[posicao_na_lista + 1]
            
            # Interpolação matemática para achar o ponto central do trecho
            lat_equip = (estaca_atual.geometry.y + estaca_proxima.geometry.y) / 2
            lon_equip = (estaca_atual.geometry.x + estaca_proxima.geometry.x) / 2
            nome_segmento = f"{estaca_atual['Name']} → {estaca_proxima['Name']}"
        else:
            # Caso seja a última estaca da rodovia (não tem próxima), plota em cima dela mesma
            _, estaca_atual = estacas_lista[posicao_na_lista]
            lat_equip = estaca_atual.geometry.y
            lon_equip = estaca_atual.geometry.x
            nome_segmento = f"Final da linha ({estaca_atual['Name']})"
        
        caminho_completo_icone = prefixo_icones + arquivo_icone
        
        popup_frota = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px; min-width: 160px;">
            <h4 style="margin: 0 0 5px 0; color: #1a365d;">Ativo em Frente de Serviço</h4>
            <b>Equipamento:</b> {arquivo_icone.split('.')[0].upper()}<br>
            <b>Segmento Alvo:</b> {nome_segmento}<br>
        </div>
        """
        
        # Modificado icon_anchor para (32, 32) para alinhar pelo CENTRO geométrico do PNG
        # Isso faz com que a máquina "sente" perfeitamente centralizada sobre o meio da linha
        custom_icon = folium.CustomIcon(
            caminho_completo_icone,
            icon_size=(64, 64),
            icon_anchor=(32, 32)
        )
        
        folium.Marker(
            location=[lat_equip, lon_equip],
            icon=custom_icon,
            popup=folium.Popup(popup_frota, max_width=250),
            tooltip=f"{arquivo_icone.split('.')[0].capitalize()} no segmento {nome_segmento}"
        ).add_to(camada_frota)

camada_frota.add_to(mapa)

# ==========================================
# CONTROLES E SCRIPTS DE INTERAÇÃO
# ==========================================
folium.LayerControl(position='topright').add_to(mapa)

codigo_js = f"""
window.addEventListener('load', function() {{
    var mapaRef = {mapa.get_name()};
    var camadaPontosRef = {camada_pontos.get_name()};
    var camadaFrotaRef = {camada_frota.get_name()};

    function controlarVisibilidade() {{
        var zoomAtual = mapaRef.getZoom();

        // Regra 1: Ícones dos Equipamentos aparecem a partir de 1km (Zoom >= 14)
        if (zoomAtual >= 14) {{
            if (!mapaRef.hasLayer(camadaFrotaRef)) {{
                mapaRef.addLayer(camadaFrotaRef);
            }}
        }} else {{
            if (mapaRef.hasLayer(camadaFrotaRef)) {{
                mapaRef.removeLayer(camadaFrotaRef);
            }}
        }}

        // Regra 2: Pontos das Estacas aparecem apenas a partir de 100m (Zoom >= 16)
        if (zoomAtual >= 16) {{
            if (!mapaRef.hasLayer(camadaPontosRef)) {{
                mapaRef.addLayer(camadaPontosRef);
            }}
        }} else {{
            if (mapaRef.hasLayer(camadaPontosRef)) {{
                mapaRef.removeLayer(camadaPontosRef);
            }}
        }}
    }}

    mapaRef.on('zoomend', controlarVisibilidade);
    controlarVisibilidade();
}});
"""
mapa.get_root().script.add_child(folium.Element(codigo_js))

mapa.save('index.html')
print("Dashboard atualizado com os ícones centralizados nos segmentos de linha!")
