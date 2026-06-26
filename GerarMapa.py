import geopandas as gpd
import folium

# 1. Definir o caminho do seu Geopackage
gpkg_path = r"C:\Users\joaorodrigues\Downloads\Qgis\Sinop\Estacas.gpkg"

# --- DICA DE ENGENHARIA ---
# Um Geopackage pode ter várias camadas internas (layers). 
# Caso você precise descobrir o nome exato das camadas dentro do seu arquivo, 
# descomente as duas linhas abaixo para listá-las no terminal antes de rodar o resto:
# import fiona
# print("Camadas no arquivo:", fiona.listlayers(gpkg_path))


# 2. Carregar as camadas do Geopackage
# (Substitua 'eixo_rodovia' e 'pontos_estacas' pelos nomes reais das suas camadas no GPKG)
gdf_eixo = gpd.read_file(gpkg_path, layer='eixo_rodovia')
gdf_estacas = gpd.read_file(gpkg_path, layer='pontos_estacas')


# 3. Reprojetar de UTM 21S (EPSG:31981) para Geográficas WGS84 (EPSG:4326)
# Essencial para que o mapa web saiba plotar os elementos no local correto do globo
gdf_eixo_wgs84 = gdf_eixo.to_crs(epsg=4326)
gdf_estacas_wgs84 = gdf_estacas.to_crs(epsg=4326)


# 4. Encontrar o centro geográfico do alinhamento para focar o mapa nele
centro = gdf_eixo_wgs84.geometry.unary_union.centroid
mapa = folium.Map(location=[centro.y, centro.x], zoom_start=13, tiles='OpenStreetMap')


# 5. Adicionar o Alinhamento da Rodovia (Linha) ao mapa
# Usamos o estilo azul escuro com espessura de 4 pixels para representar o eixo
folium.GeoJson(
    gdf_eixo_wgs84,
    name="Eixo da Rodovia",
    style_function=lambda x: {
        'color': '#1a365d',
        'weight': 4,
        'opacity': 0.8
    }
).add_to(mapa)


# 6. Adicionar as Estacas (Pontos) ao mapa
for _, linha in gdf_estacas_wgs84.iterrows():
    # Extrair as coordenadas reprojetadas (X=Longitude, Y=Latitude)
    lon, lat = linha.geometry.x, linha.geometry.y
    
    # Extrair os atributos textuais da tabela do Geopackage
    # (Substitua 'nome_estaca' e 'status_obra' pelas colunas reais da sua tabela)
    numero_estaca = linha.get('nome_estaca', 'N/A')
    status_atual = linha.get('status_obra', 'Planejado')
    
    # Definir uma lógica simples de cores para o avanço físico das estacas
    cor_marcador = 'green' if status_atual == 'Concluído' else 'orange' if status_atual == 'Em Andamento' else 'red'
    
    # Montar o balão de informações (Popup) formatado em HTML simples
    popup_conteudo = f"""
    <div style="font-family: Arial, sans-serif; font-size: 12px; min-width: 140px;">
        <h4 style="margin: 0 0 5px 0; color: #1a365d;">Estaca: {numero_estaca}</h4>
        <b>Status:</b> <span style="color: {cor_marcador}; font-weight: bold;">{status_atual}</span><br>
        <b>Norte (UTM):</b> {linha.geometry.y:.2f}<br>
        <b>Este (UTM):</b> {linha.geometry.x:.2f}
    </div>
    """
    
    # Inserir um círculo interativo para cada estaca no mapa
    folium.CircleMarker(
        location=[lat, lon],
        radius=5,
        color=cor_marcador,
        fill=True,
        fill_color='white',
        fill_opacity=0.9,
        weight=2,
        popup=folium.Popup(popup_conteudo, max_width=250),
        tooltip=f"Estaca {numero_estaca}" # Texto rápido ao passar o mouse por cima
    ).add_to(mapa)


# 7. Adicionar controle de camadas no canto superior direito do mapa
folium.LayerControl().add_to(mapa)

# 8. Salvar o mapa final como map.html para o seu GitHub Pages
mapa.save('map.html')
print("Dashboard Geospacial gerado com sucesso!")