import pandas as pd
import geopandas as gpd
import folium

# 1. Definir o caminho da planilha Excel
excel_path = r"C:\Users\joaorodrigues\Downloads\Qgis\Sinop\Estacas.xlsx"

# 2. Carregar os dados do Excel usando o Pandas
df = pd.read_excel(excel_path)

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
mapa = folium.Map(location=[centro.y, centro.x], zoom_start=14, tiles='OpenStreetMap')

# 6. Adicionar as Estacas (Pontos) ao mapa
for _, linha in gdf_estacas_wgs84.iterrows():
    # Coordenadas em graus decimais obtidas após a reprojeção
    lon, lat = linha.geometry.x, linha.geometry.y
    
    # Extrair os atributos das colunas exatas da sua planilha
    descricao = linha['descrição da estaca']
    id_estaca = linha['id']
    cota_z = linha['z']
    x_utm = linha['x']
    y_utm = linha['y']
    
    # Cor padrão para visualização (azul). 
    # Se futuramente adicionar uma coluna de status, pode reativar a lógica de cores aqui.
    cor_marcador = 'blue'
    
    # Montar o balão de informações (Popup) formatado em HTML
    popup_conteudo = f"""
    <div style="font-family: Arial, sans-serif; font-size: 12px; min-width: 160px;">
        <h4 style="margin: 0 0 5px 0; color: #1a365d;">{descricao}</h4>
        <b>ID:</b> {id_estaca}<br>
        <b>Cota (Z):</b> {cota_z:.2f} m<br>
        <b>Norte (Y UTM):</b> {y_utm:.2f}<br>
        <b>Este (X UTM):</b> {x_utm:.2f}
    </div>
    """
    
    # Inserir o marcador circular no mapa
    folium.CircleMarker(
        location=[lat, lon],
        radius=6,
        color=cor_marcador,
        fill=True,
        fill_color='white',
        fill_opacity=0.8,
        weight=2,
        popup=folium.Popup(popup_conteudo, max_width=250),
        tooltip=str(descricao)
    ).add_to(mapa)

# 7. Salvar o mapa final como index.html (pronto para o fluxo do GitHub Pages)
mapa.save('index.html')
print("Dashboard gerado com sucesso a partir da planilha Excel!")
