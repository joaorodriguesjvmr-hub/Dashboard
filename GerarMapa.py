import pandas as pd
import geopandas as gpd
import folium

# 1. Definição dos caminhos dos arquivos Excel
excel_estacas = r"C:\Users\joaorodrigues\Downloads\Qgis\Sinop\Estacas.xlsx"
excel_emprestimos = r"C:\Users\joaorodrigues\Downloads\Qgis\Sinop\CaixasDeEmprestimo.xlsx"

# ==========================================
# PARTE A: PROCESSAMENTO DAS ESTACAS (EIXO)
# ==========================================
df_estacas = pd.read_excel(excel_estacas).sort_values(by='id')

gdf_estacas = gpd.GeoDataFrame(
    df_estacas, 
    geometry=gpd.points_from_xy(df_estacas['x'], df_estacas['y']), 
    crs="EPSG:31981"
)
gdf_estacas_wgs84 = gdf_estacas.to_crs(epsg=4326)

# ==========================================
# PARTE B: PROCESSAMENTO DAS CAIXAS DE EMPRÉSTIMO
# ==========================================
df_emp = pd.read_excel(excel_emprestimos)

gdf_emp = gpd.GeoDataFrame(
    df_emp, 
    geometry=gpd.points_from_xy(df_emp['x'], df_emp['y']), 
    crs="EPSG:31981"
)
gdf_emp_wgs84 = gdf_emp.to_crs(epsg=4326)

# ==========================================
# PARTE C: CONFIGURAÇÃO DO MAPA BASE
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

# 2. Criar a camada das Caixas de Empréstimo (Polígonos)
camada_caixas = folium.FeatureGroup(name="Caixas de Empréstimo")

# Agrupa os dados pelo 'Name' da caixa para isolar os perímetros
for nome_caixa, grupo in gdf_emp_wgs84.groupby('Name'):
    # Ordena os pontos do grupo pelo 'id' para fechar o polígono na sequência correta
    grupo_ordenado = grupo.sort_values(by='id')
    
    # Extrai a lista de coordenadas [Latitude, Longitude] do perímetro
    coords_perimetro = [[row.geometry.y, row.geometry.x] for _, row in grupo_ordenado.iterrows()]
    
    # Desenha a área se houver pelo menos 3 pontos para formar um polígono
    if len(coords_perimetro) >= 3:
        folium.Polygon(
            locations=coords_perimetro,
            color='#d35400',       # Borda cor de terra (Rust)
            weight=3,
            fill=True,
            fill_color='#e67e22',  # Preenchimento terracota semi-transparente
            fill_opacity=0.4,
            tooltip=f"Caixa de Empréstimo: {nome_caixa}"
        ).add_to(camada_caixas)
    else:
        # Caso tenha apenas 2 pontos, desenha como linha de limite
        folium.PolyLine(
            locations=coords_perimetro,
            color='#d35400',
            weight=3,
            tooltip=f"Limite Caixas: {nome_caixa} (Vértices insuficientes)"
        ).add_to(camada_caixas)

camada_caixas.add_to(mapa)

# 3. Criar a camada das Estacas (Pontos) com controle de escala
camada_pontos = folium.FeatureGroup(name="Estacas (Pontos)")

for _, row in gdf_estacas_wgs84.iterrows():
    lon, lat = row.geometry.x, row.geometry.y
    
    popup_conteudo = f"""
    <div style="font-family: Arial, sans-serif; font-size: 12px; min-width: 160px;">
        <h4 style="margin: 0 0 5px 0; color: #1a365d;">{row['Name']}</h4>
        <b>ID:</b> {row['id']}<br>
        <b>Norte (Y UTM):</b> {row['y']:.2f}<br>
        <b>Este (X UTM):</b> {row['x']:.2f}
    </div>
    """
    
    folium.CircleMarker(
        location=[lat, lon],
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
# PARTE D: CONTROLES E SCRIPTS DE INTERAÇÃO
# ==========================================

# Ativa o menu de ligar/desligar camadas no canto superior direito
folium.LayerControl(position='topright').add_to(mapa)

# Injeta o JavaScript para ocultar as estacas se o zoom for menor que 16 (Escala > 100m)
codigo_js = f"""
window.addEventListener('load', function() {{
    var mapaRef = {mapa.get_name()};
    var camadaRef = {camada_pontos.get_name()};

    function controlarVisibilidade() {{
        if (mapaRef.getZoom() >= 16) {{
            if (!mapaRef.hasLayer(camadaRef)) {{
                mapaRef.addLayer(camadaRef);
            }}
        }} else {{
            if (mapaRef.hasLayer(camadaRef)) {{
                mapaRef.removeLayer(camadaRef);
            }}
        }}
    }}

    mapaRef.on('zoomend', controlarVisibilidade);
    controlarVisibilidade();
}});
"""
mapa.get_root().script.add_child(folium.Element(codigo_js))

# 4. Salvar o arquivo final
mapa.save('index.html')
print("Dashboard completo gerado! Rodovia e Caixas de Empréstimo integradas.")
