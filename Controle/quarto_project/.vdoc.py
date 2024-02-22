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
year=2023

from dotenv import load_dotenv
import matplotlib.pyplot as plt
from intake import open_catalog
import pandas as pd
from IPython.display import display, Latex, Markdown
from tabulate import tabulate
import datetime as dt
import geopandas as gpd
import holoviews as hv
from holoviews import opts
load_dotenv()

#brute
yaml_list=['data_control_incendie.yaml']
rep="N:/Informatique/SIG/Application/Jupyterhub/projets/catalogFiles/"

catfeux = open_catalog(rep+yaml_list[0])
surface_detectees_brutes=catfeux.surfaces_detectees.read()
tile_sentinel=catfeux.tile_sentinel2_line_UTM.read()
nc_limits=catfeux.nc_limits.read()

tile_sentinel=tile_sentinel.to_crs(epsg=4326)
nc_limits=nc_limits.to_crs(epsg=4326)

#
#
#
#| output: false
#| echo: false
#| warning: false

## année en cours
tile_occurence=pd.read_csv('N:/Informatique/SIG/Etudes/2023/2309_QC_feux/Travail/Scripts/CQ_sentinel_surfaces_brulees/Controle/tile_occurence.csv')
tile_occurence['Name'] = [x[-5:] for x in tile_occurence['dalle_names']]
df_concat_year = pd.merge(tile_sentinel, tile_occurence, how='inner',on='Name')

#### total
surface_detectees_brutes['nom'] = [x[-5:] for x in surface_detectees_brutes['nom']]
occurrences_dalles = pd.DataFrame(surface_detectees_brutes["nom"].value_counts())
occurrences_dalles['Name']=occurrences_dalles.index
df_concat_total = pd.merge(tile_sentinel, occurrences_dalles, how='inner',on='Name')

df_concat_year = df_concat_year.to_crs(nc_limits.crs)
#
#
#
#
#
#
#
#| content: valuebox
#| title: "Detected Area"
dict(
    icon = "fire",
    color = "warning",
    value = "3050 ha"
)
#
#
#
#| content: valuebox
#| title: "Pluri-detection"
dict(
    icon = "grid-3x3-gap",
    color = "success",
    value = "5000"
)
#
#
#
#| content: valuebox
#| title: "Mono-detection"
dict(
    icon = "1-square",
    color = "success",
    value = "8000"
)
#
#
#
#
#
#| output: true
#| echo: false
#| warning: false
#| error: false

fig, ax1 = plt.subplots(1, 1, figsize=(10, 6))  

df_concat_year.plot(column=df_concat_year['dalle_names'], cmap='gnuplot', legend=True, ax=ax1)
nc_limits.plot(ax=ax1, color='grey', alpha=0.5)
plt.title('Number of fire detection with Sentinel-2 in ' +str(year))

for idx, row in df_concat_year.iterrows():
    ax1.text(row['geometry'].centroid.x, row['geometry'].centroid.y, str(row['Name']), ha='center', va='center')

ax1.set_xlim(163, 169)
ax1.set_yticks([])
ax1.set_xticks([])
plt.show();
#
#
#
#| output: false
#| echo: false
#| warning: false
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

tile_sentinel['surface']= gdf_intersections['surface']
#
#
#
#| output: true
#| echo: false
#| warning: false

fig, ax = plt.subplots(1, 1, figsize=(10, 6))

tile_sentinel.plot(column=tile_sentinel['surface'], cmap='jet', legend=True, ax=ax)
nc_limits.plot(ax=ax, color='grey', alpha=0.5)

for idx, row in tile_sentinel.iterrows():
    centre = row['geometry'].centroid
    ax.text(centre.x, centre.y, str(row['Name']), ha='center', va='center')

ax.set_title('Land area (ha) for each tile')
ax.set_axis_off()  
ax.set_xlim(163, 169)
plt.show();
#
#
#
#
#| content: valuebox
#| title: "Detected Area"
dict(
    icon = "fire",
    color = "warning",
    value = "3050 ha"
)
#
#
#
#
#
#
#| echo: false
#| warning: false
## time serie of number of burned area detected daily per tiles
hv.extension('bokeh')
hv.output(logo=None)

surface_detectees_brutes['nom'] = [x[-5:] for x in surface_detectees_brutes['nom']]
surface_detectees_brutes['date_'] = pd.to_datetime(surface_detectees_brutes['date_'])

daily_counts = surface_detectees_brutes.groupby(['date_', 'nom']).size().reset_index(name='nombre_occurrences')

daily_counts['date_'] = daily_counts['date_'].dt.strftime('%Y-%m-%d')

date_range = pd.date_range(start=daily_counts['date_'].min(), end=daily_counts['date_'].max())
full_date_series = pd.DataFrame(date_range.strftime('%Y-%m-%d'), columns=['date_'])

daily_counts_gaps = pd.merge(full_date_series, daily_counts, on='date_', how='left')
daily_counts_gaps['nom'] = daily_counts_gaps['nom'].fillna('Inconnu')

key_dimensions   = [('date_', 'Date'),('nom', 'tuile')]
value_dimensions = [('nombre_occurrences', 'Nombre de détection')]
macro1 = hv.Table(daily_counts_gaps, key_dimensions, value_dimensions)

###############

daily_counts_surf = surface_detectees_brutes.groupby(['date_', 'nom']).surface.sum().reset_index(name='surface_totale')

daily_counts_surf['date_'] = pd.to_datetime(daily_counts_surf['date_']).dt.strftime('%Y-%m-%d')

daily_counts_surf_gaps = pd.merge(full_date_series, daily_counts_surf, on='date_', how='left')
daily_counts_surf_gaps['nom'] = daily_counts_surf_gaps['nom'].fillna('Inconnu')

key_dimensions   = [('date_', 'Date'),('nom', 'tuile')]
value_dimensions = [('surface_totale', 'Surface (ha)')]
macro2 = hv.Table(daily_counts_surf_gaps, key_dimensions, value_dimensions)

graph1 = macro1.to.bars(['Date','tuile'], 'Nombre de détection', [])
graph2 = macro2.to.bars(['Date','tuile'], 'Surface (ha)', [])

layout = graph1 + graph2
layout = layout.cols(1)
layout.opts(
        opts.Bars(color=hv.Cycle('Category20'), show_legend=True, legend_position='right', stacked=True, 
        tools=['hover'], responsive=True, height=500, width=1800, xrotation=45,
        title="Burned area (ha) detected per tiles over " + str(year)
))
#
#
#
#
#
#
#| echo: false
#| warning: false

import numpy as np
hv.extension('bokeh')

list_tiles=['58KCC','58KCD','58KDB','58KDC','58KEA','58KEB','58KEC',
            '58KFA','58KFB','58KFC','58KGA','58KGB','58KGC','58KGV','58KHB']

def monthly_tiles(gdf,date_range,tile):
    daily_counts_tile=gdf[gdf['nom']==tile]
    daily_counts_tile_gaps = pd.merge(date_range, daily_counts_tile, on='date_', how='left')
    daily_counts_tile_gaps['nom'] = daily_counts_tile_gaps['nom'].fillna('Inconnu')

    key_dimensions   = [('date_', 'Date'),('nom', 'tuile')]
    value_dimensions = [('nombre_occurrences', 'Occurence')]
    macro1 = hv.Table(daily_counts_tile_gaps, key_dimensions, value_dimensions)
    graph1 = macro1.to.bars(['Date','tuile'], 'Occurence', [],label="Detection over tile : " + tile)

    return(graph1)

graph2=monthly_tiles(daily_counts,full_date_series,list_tiles[0])
graph3=monthly_tiles(daily_counts,full_date_series,list_tiles[1])
graph4=monthly_tiles(daily_counts,full_date_series,list_tiles[2])
graph5=monthly_tiles(daily_counts,full_date_series,list_tiles[3])
graph6=monthly_tiles(daily_counts,full_date_series,list_tiles[4])

graph7=monthly_tiles(daily_counts,full_date_series,list_tiles[5])
graph8=monthly_tiles(daily_counts,full_date_series,list_tiles[6])
graph9=monthly_tiles(daily_counts,full_date_series,list_tiles[7])
graph10=monthly_tiles(daily_counts,full_date_series,list_tiles[8])
graph11=monthly_tiles(daily_counts,full_date_series,list_tiles[9])

graph12=monthly_tiles(daily_counts,full_date_series,list_tiles[10])
graph13=monthly_tiles(daily_counts,full_date_series,list_tiles[11])
graph14=monthly_tiles(daily_counts,full_date_series,list_tiles[12])
graph15=monthly_tiles(daily_counts,full_date_series,list_tiles[13])
graph16=monthly_tiles(daily_counts,full_date_series,list_tiles[14])


layout = (graph2 + graph3 + graph4 + graph5 + graph6+
        graph7 + graph8 + graph9 + graph10 + graph11+
        graph12 + graph13 + graph14 + graph15 + graph16).cols(3)
layout.opts(
        opts.Bars(color='black', show_legend=False, legend_position='right', stacked=True, 
        tools=['hover'], height=300, width=700, xrotation=45
))
#
#
#
#
