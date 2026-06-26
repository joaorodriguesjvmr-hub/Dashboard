import pandas as pd
import geopandas as gpd
import folium

# 1. Definir o caminho da planilha Excel
excel_path = r"C:\Users\joaorodrigues\Downloads\Qgis\Sinop\Estacas.xlsx"

# 2. Carregar os dados do Excel e ORDENAR em sequência pelo ID
df = pd.read_excel(excel_path)
df = df.sort_values(by='id')

# 3. Criar o GeoDataFrame a partir das colunas X e Y (UTM 21S / SIRGAS 2000 -> EPSG:31981)
gdf_estacas = gpd.GeoDataFrame(
    df, 
    geometry=gpd.points_from_xy(df['x'], df['y']), 
    crs="EPSG:31981"
)

# 4. Reprojetar para Geográficas WGS84 (EPSG:4326) exigido pelo Folium
gdf_estacas_wgs84 = gdf_estacas.to_crs(epsg=4326)

# 5. Encontrar o centro geográfico dos pontos para focar o mapa
centro = gdf_estacas_wgs84.geometry.unary_union.centroid

mapa = folium.Map(
    location=[centro.y, centro.x], 
    zoom_start=14, 
    tiles='OpenStreetMap',
    control_scale=True
)

# 6. Criar Linhas quebradas em segmentos entre estacas consecutivas
# Convertemos para lista para conseguir acessar o elemento atual (i) e o próximo (i+1)
estacas_lista = list(gdf_estacas_wgs84.iterrows())

for i in range(len(estacas_lista) - 1):
    _, estaca_atual = estacas_lista[i]
    _, estaca_proxima = estacas_lista[i+1]
    
    # Coordenadas do segmento (Início e Fim)
    coord_inicio = [estaca_atual.geometry.y, estaca_atual.geometry.x]
    coord_fim = [estaca_proxima.geometry.y, estaca_proxima.geometry.x]
    coords_segmento = [coord_inicio, coord_fim]
    
    # Define o nome do segmento baseado no Name da estaca de menor id (estaca_atual)
    nome_segmento = estaca_atual['Name']
    
    # Plota o segmento individual no mapa
    folium.PolyLine(
        coords_segmento,
        color='#1a365d',
        weight=4,
        opacity=0.8,
        tooltip=f"Segmento: {nome_segmento}" # Exibe o nome ao passar o mouse sobre a linha
    ).add_to(mapa)

# 7. Criar uma camada separada para os pontos
camada_pontos = folium.FeatureGroup(name="Estacas (Pontos)")

# 8. Adicionar as Estacas (Pontos) à sua camada específica
for _, row in gdf_estacas_wgs84.iterrows():
    lon, lat = row.geometry.x, row.geometry.y
    
    descricao = row['Name']
    id_estaca = row['id']
    x_utm = row['x']
    y_utm = row['y']
    
    popup_conteudo = f"""
    <div style="font-family: Arial, sans-serif; font-size: 12px; min-width: 160px;">
        <h4 style="margin: 0 0 5px 0; color: #1a365d;">{descricao}</h4>
        <b>ID:</b> {id_estaca}<br>
        <b>Norte (Y UTM):</b> {y_utm:.2f}<br>
        <b>Este (X UTM):</b> {x_utm:.2f}
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
        tooltip=str(descricao)
    ).add_to(camada_pontos)

# Adiciona a camada de pontos ao mapa principal
camada_pontos.add_to(mapa)

# 9. Injetar JavaScript SEGURO para controlar a visibilidade por escala (Zoom >= 16)
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

# 10. Salvar o mapa final como index.html
mapa.save('index.html')
print("Dashboard atualizado com sucesso com segmentos individuais por ID!")
