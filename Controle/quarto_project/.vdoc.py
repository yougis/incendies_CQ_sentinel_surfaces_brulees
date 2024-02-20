# type: ignore
# flake8: noqa
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#| output: false
#| echo: false
#| warning: false

year=2023
from dotenv import load_dotenv
load_dotenv()
import matplotlib.pyplot as plt
from intake import open_catalog
import pandas as pd
from IPython.display import display, Latex, Markdown
from tabulate import tabulate
import datetime as dt
import geopandas as gpd

#brute
yaml_list=['data_control_incendie.yaml']
rep="N:/Informatique/SIG/Application/Jupyterhub/projets/catalogFiles/"

catfeux = open_catalog(rep+yaml_list[0])
surface_detectees_brutes=catfeux.surfaces_detectees.read()
tile_sentinel=catfeux.tile_sentinel2_line_UTM.read()
nc_limits=catfeux.nc_limits.read()
#
#
#
#| output: true
#| echo: false
#| warning: false

## année en cours
tile_occurence=pd.read_csv('N:/Informatique/SIG/Etudes/2023/2309_QC_feux/Travail/Scripts/CQ_sentinel_surfaces_brulees/Controle/tile_occurence.csv')
tile_occurence['Name'] = [x[-5:] for x in tile_occurence['Unnamed: 0']]
df_concat_year = pd.merge(tile_sentinel, tile_occurence, how='inner',on='Name')

#### total
surface_detectees_brutes['nom'] = [x[-5:] for x in surface_detectees_brutes['nom']]
occurrences_dalles = pd.DataFrame(surface_detectees_brutes["nom"].value_counts())
occurrences_dalles['Name']=occurrences_dalles.index
df_concat_total = pd.merge(tile_sentinel, occurrences_dalles, how='inner',on='Name')

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))  # Ajuste figsize au besoin

nc_limits = nc_limits.to_crs(df_concat_year.crs)

df_concat_year.plot(column=df_concat_year['dalle_names'], cmap='gnuplot', legend=True, ax=ax1)
nc_limits.plot(ax=ax1, color='grey', alpha=0.5)
ax1.set_title('Number of fire detection with Sentinel-2 in' +str(year))

for idx, row in df_concat_year.iterrows():
    centre = row['geometry'].centroid
    ax1.text(centre.x, centre.y, str(row['Name']), ha='center', va='center')

df_concat_total.plot(column=df_concat_total['nom'], cmap='gnuplot', legend=True, ax=ax2)
ax2.set_title('Number of fire detection with Sentinel-2 before' +str(year))
nc_limits.plot(ax=ax2, color='grey', alpha=0.5)

for idx, row in df_concat_total.iterrows():
    centre = row['geometry'].centroid
    ax2.text(centre.x, centre.y, str(row['Name']), ha='center', va='center')

for ax in [ax1, ax2]:
    ax.set_xlim(50000, 9.5**6)
    ax.set_yticks([])
    ax.set_xticks([])
#
#
#
tile_geom_path = 'N:/Informatique/SIG/Etudes/2023/2309_QC_feux/Travail/Scripts/CQ_sentinel_surfaces_brulees/Controle/shp/tiles_sentinel2_UTM.shp'
tile_geom = gpd.read_file(tile_geom_path)

polygone_unique = nc_limits.unary_union
gdf_union = gpd.GeoDataFrame(geometry=[polygone_unique], crs=nc_limits.crs)

if gdf_union.crs != tile_geom.crs:
    gdf_union = gdf_union.to_crs(tile_geom.crs)
    
intersections = []

geom1 = gdf_union.geometry.iloc[0]
for geom2 in tile_geom.geometry:
    intersection = geom1.intersection(geom2)
    if not intersection.is_empty:
        intersections.append(intersection)

gdf_intersections = gpd.GeoDataFrame(geometry=intersections, crs=tile_sentinel.crs)
gdf_intersections['Name']=tile_geom['Name']
gdf_intersections['surface']=gdf_intersections.area/10000
#
#
#
#| output: false
#| echo: false
#| warning: false

tile_sentinel['surface']= gdf_intersections['surface']

fig, ax = plt.subplots(1, 1, figsize=(10, 6))

# Tracez les polygones avec une coloration basée sur les données statistiques
tile_sentinel.plot(column=tile_sentinel['surface'], cmap='jet', legend=True, ax=ax)
nc_limits.plot(ax=ax, color='grey', alpha=0.5)

for idx, row in tile_sentinel.iterrows():
    centre = row['geometry'].centroid
    ax.text(centre.x, centre.y, str(row['Name']), ha='center', va='center')

# Ajustements optionnels
ax.set_title('Titre de ma cartographie statistique')
ax.set_axis_off()  # Cache les axes pour une visualisation épurée
ax.set_xlim(50000, 9.5**6)

#
#
#
