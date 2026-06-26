import pandas as pd
import geopandas as gpd
import folium

# ==========================================
# FUNÇÃO DA ROTINA GEOESPACIAL (REUTILIZÁVEL)
# ==========================================
def carregar_pontos_excel(caminho_excel, crs_origem="EPSG:31981", crs_destino=4326):
    """Lê uma planilha Excel com colunas x/y, converte em GeoDataFrame e reprojeta."""
    df = pd.read_excel(caminho_excel)
    
    # Ordena pelo ID se a coluna existir (garante sequência para linhas/polígonos)
    if 'id' in df.columns:
        df = df.sort_values(by='id')
        
    gdf = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df['x'], df['y']), 
        crs=crs_origem
    )
    return gdf.to_crs(epsg=crs_destino)

# ==========================================
# CONFIGURAÇÃO DE CAMINHOS E DADOS
# ==========================================
excel_estacas = r"C:\Users\joaorodrigues\Downloads\Qgis\Sinop\Estacas.xlsx"
excel_emprestimos = r"C:\Users\joaorodrigues\Downloads\Qgis\Sinop\Caixas_Emprestimo.xlsx"

# Chamadas limpas da função criada
gdf_estacas_wgs84 = carregar_pontos_excel(excel_estacas)
gdf_emp_wgs84 = carregar_pontos_excel(excel_emprestimos)

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

# 2. Criar a camada das Caixas de Empréstimo (Polígonos)
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
# CONTROLES E SCRIPTS DE INTERAÇÃO
# ==========================================
folium.LayerControl(position='topright').add_to(mapa)

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

mapa.save('index.html')
print("Dashboard otimizado gerado com sucesso!")
