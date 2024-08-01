import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine
import geopandas as gpd
import networkx as nx
import datetime as dt
from pystac_client import Client
from holoviews import opts
from intake import open_catalog
import panel as pn
import numpy as np
from bokeh.models import HoverTool, LogColorMapper, ColumnDataSource, DatetimeTickFormatter, GeoJSONDataSource
from bokeh.plotting import figure
from odc.stac import configure_rio, stac_load
import holoviews as hv
from bokeh.models.formatters import DatetimeTickFormatter
import requests
from PIL import Image
from io import BytesIO
import hvplot.pandas 
from functools import reduce
import divers
import math
from pyproj import Transformer

load_dotenv()

catfeux = open_catalog(f'{os.getenv("DATA_CATALOG_DIR")}data_dashboard.yaml')
table_source='vue_sentinel_brute_no_geom'
table_viirs_snpp='incendie_viirs_snpp'
table_viirs_noaa='incendie_viirs_noaa20'
fichier_tiles='list_of_tiles'
catalog_stac="https://earth-search.aws.element84.com/v1"

tile_sentinel=catfeux.tile_sentinel2_line_UTM.read()
tile_sentinel=tile_sentinel.to_crs(epsg=3857)

nc_limits=catfeux.vue_nc_simplifiee.read()
nc_limits=nc_limits.to_crs(epsg=3857)

tile_sentinel['Name']='L2A_T'+tile_sentinel['Name']

tile_centroid=tile_sentinel.copy()
tile_centroid['centroid'] = tile_centroid.geometry.centroid
centroid_tuile = pd.DataFrame({
    'x': tile_centroid['centroid'].x,
    'y': tile_centroid['centroid'].y,
    'nom': tile_centroid['Name']
})

def stac_search(date_start,date_end):

    catalog = Client.open(catalog_stac)
    query = catalog.search(
        collections=["sentinel-2-l2a"],datetime=(date_start).strftime('%Y-%m-%d')+'/'+(date_end).strftime('%Y-%m-%d'), bbox=[163.362, -22.76, 168.223, -19.479],       
        fields={"include": ["properties.grid:code", "properties.datetime", "properties.eo:cloud_cover", "assets.thumbnail.href"], "exclude": []})

    items = list(query.items())
    stac_json = query.item_collection_as_dict()

    gdf = gpd.GeoDataFrame.from_features(stac_json, "epsg:4326")
    thumbnails = [item.assets['thumbnail'].href for item in items]

    df = gdf.rename(columns={
        'grid:code': 'nom',
        'datetime': 'date_',
        'eo:cloud_cover': 'Cloud_Cover',
        'thumbnail.href': 'thumbnail'
    })

    df['nom'] = [x[5:] for x in df['nom']]
    df['nom']='L2A_T'+df['nom'] 

    df=df.reset_index(drop=True)
    date_formats = ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S.%f%z','%Y-%m-%dT%H:%M:%S.%fZ']
    df['date_'] = df['date_'].apply(divers.try_multiple_date_formats, formats=date_formats)
    df['date_'] = df['date_'].dt.strftime('%Y-%m-%d')
    df['date_'] = pd.to_datetime(df['date_'])
    
    df['thumbnail_url'] = thumbnails
    df = df.sort_values(by='date_', ascending=True)

    return(df)

def read_table(date_range):

    sql = f"""SELECT *
    FROM feux_cq.{table_source} si
    WHERE si.date_ >= '{pd.to_datetime(date_range[0]).strftime('%Y-%m-%d')}' AND si.date_ <= '{pd.to_datetime(date_range[1]).strftime('%Y-%m-%d')}'
    """
    dataCatalog = getattr(catfeux, table_source)(sql_expr=sql)
    df = dataCatalog.read()
    
    df['nom']=df['nom'].apply(lambda x: x[20:])
    df['groupe_id'] = np.nan

    return(df)

def prepare_data(df,full_date_series,name,choix):
    df_tiles = df.groupby(['date_', 'nom']).size().reset_index(name=name)
    df_tiles = df_tiles[df_tiles['nom'] == choix]

    df_tiles['date_'] = pd.to_datetime(df_tiles['date_'], errors='coerce')
    df_tiles['date_'] = df_tiles['date_'].dt.strftime('%Y-%m-%d')
    df_tiles['date_']=pd.to_datetime(df_tiles['date_'])

    df_tiles = pd.merge(full_date_series, df_tiles, on='date_', how='left')
    df_tiles['nom'] = df_tiles['nom'].fillna(choix)

    return(df_tiles)

def viirs_data(data,stl2_poly):
    
    dataCatalog = getattr(catfeux, data)
    df = dataCatalog.read()
    df=df.to_crs(epsg=3857)
    df = gpd.sjoin(stl2_poly, df, how='inner')
    df['date_']=pd.to_datetime(df['begDate'])

    df['nom']=df['Name'] 

    return(df)

def create_map(tot_surf_tile, min_size=10, max_size=30, color="orange"):
    tt = pd.merge(centroid_tuile, tot_surf_tile, on='nom', how='left')
    tt = tt.rename(columns={0: 'surface'})
    min_value = np.nanmin(tt['surface'].values)
    max_value = tt['surface'].max()

    if min_value == max_value:
        legend_values = [min_value]
    else:
        Q1 = round(tt['surface'].quantile(0.25))
        median_value = round(tt['surface'].median())
        Q3 = round(tt['surface'].quantile(0.75))
        legend_values = [Q1, median_value, Q3, round(max_value)]

    tt['surface'] = tt['surface'].replace(np.nan, 0)

    legend_sizes = [divers.normalize_size(val, min_size, max_size, min_value, max_value) for val in legend_values]

    tt['normalized_size'] = tt['surface'].apply(divers.normalize_size, args=(min_size, max_size, min_value, max_value))
    tt['color'] = [color if val != 0 else 'black' for val in tt['surface']]

    centroid_data_zero = tt[tt['surface'] == 0]
    centroid_data_nonzero = tt[tt['surface'] != 0]
    source_zero = ColumnDataSource(centroid_data_zero)
    source_nonzero = ColumnDataSource(centroid_data_nonzero)

    geo_source = GeoJSONDataSource(geojson=nc_limits.to_json())

    tile_sentinel_geojson = gpd.GeoDataFrame(tile_sentinel).to_json()
    tile = GeoJSONDataSource(geojson=tile_sentinel_geojson)

    map = figure(width=800, title="Carte des surfaces brûlées estimées par tuiles pour les dates sélectionnées",
                 x_axis_type="mercator", y_axis_type="mercator")

    map.patches('xs', 'ys', source=geo_source,
                fill_alpha=1, fill_color='#d9d9d9', line_color="black", line_width=0.4)  # plot of new caledonia land

    map.multi_line('xs', 'ys', source=tile,
                   line_alpha=1, line_color="black", line_width=1)
    
    circles = map.circle('x', 'y', size='normalized_size', source=source_nonzero, color=color, line_color='black', fill_alpha=0.6)
    squares = map.square('x', 'y', size='normalized_size', source=source_zero, color='black', line_color='black', fill_alpha=0.6)

    hover = HoverTool(renderers=[circles, squares], tooltips=[
        ("Surface (ha)", f"@surface{{0}}"),
        ('Tuile', '@nom')
    ])
    map.add_tools(hover)
    
    lon, lat = 163.75, -23
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    x, y = transformer.transform(lon, lat)

    legend_data = []
    xL, yL = x - 45000, y + 20000
    for i, value in enumerate(legend_values):
        size = divers.normalize_size(value, min_size, max_size, min_value, max_value)
        legend_data.append({'xL': xL, 'yL': yL + i * 40000, 'value': value, 'size': size})
    
    legend_data.append({'xL': xL, 'yL': yL + len(legend_values) * 40000, 'value': 0, 'size': min_size})
    legend_df = pd.DataFrame(legend_data)
    legend_source_nonzero = ColumnDataSource(legend_df[legend_df['value'] != 0])
    legend_source_zero = ColumnDataSource(legend_df[legend_df['value'] == 0])

    legend_squares = map.square('xL', 'yL', size='size', source=legend_source_zero, color='black', line_color='black', fill_alpha=0.6)
    legend_circles = map.circle('xL', 'yL', size='size', source=legend_source_nonzero, color=color, line_color='black', fill_alpha=0.6)

    for idx, row in legend_df.iterrows():
        map.text(x=row['xL'] + 20000, y=row['yL'], text=[str(round(row['value'], 2))], text_align='left', text_baseline='middle', text_font_size='8pt')

    return map

def read_insight_tile(data):
    
    dataCatalog = getattr(catfeux, data)
    tile_insight= dataCatalog.read()

    tile_insight['date_'] = tile_insight[0].str.extract(r'(\d{8})')
    tile_insight['date_']=pd.to_datetime(tile_insight['date_'])
    tile_insight['nom'] = tile_insight[0].str.extract(r'(L2A_T\w+)_D')[0]
    tile_insight['value']=1

    return(tile_insight)

## Start creation of dashboard

pn.extension()
pn.extension('tabulator')

stylesheet = """
.tabulator-cell {
    font-size: 20px;
}
"""
custom_style = {
    'background': '#f89424',
    'border': '1px solid black',
    'padding': '10px',
    'box-shadow': '5px 5px 5px #bcbcbc'
}
    
tile_bouton = pn.widgets.RadioButtonGroup(options=['L2A_T58KCC','L2A_T58KCD','L2A_T58KDB','L2A_T58KDC','L2A_T58KEA','L2A_T58KEB','L2A_T58KEC',
            'L2A_T58KFA','L2A_T58KFB','L2A_T58KFC','L2A_T58KGA','L2A_T58KGB','L2A_T58KGC','L2A_T58KGV','L2A_T58KHB'],align='center',stylesheets=[stylesheet],
            button_type='warning',button_style='outline',name='Choose a tile')

### PAGE 1 #########
############ table

def maj_table(date_range,table_source):
    hv.extension('bokeh')

    global stac_search_results, df
    
    df=read_table(date_range)
    stac_search_results=stac_search(df['date_'].min(),df['date_'].max())
    
    #df['date_'] = pd.to_datetime(df['date_'])

    G = nx.Graph()

    for index, row in df.iterrows():
        intersecting_ids = divers.find_intersecting_id(row, df)
        for id_ in intersecting_ids:
            G.add_edge(row['surface_id_h3'], id_)

    groupes = list(nx.connected_components(G))

    for groupe_id, groupe in enumerate(groupes):
        for id_ in groupe:
            df.loc[df['surface_id_h3'] == id_, 'groupe_id'] = groupe_id

    pluri_tile_surface,pluri_tile_number,pluri_detection_group,pluri_detection_surface=divers.mesure_pluri_detection(df)
    mono_tile_surface,mono_tile_number,mono_detection_group,mono_detection_surface=divers.mesure_mono_detection(df)
    tot_surf,nb_tot,tot_surf_tile=divers.mesure_totale(df)
    print(tot_surf_tile)
    dataframes = [mono_tile_number, mono_tile_surface, pluri_tile_number, pluri_tile_surface]
    info_surfaces = reduce(lambda left, right: pd.merge(left, right, on='nom', how='outer'), dataframes)

    info_surfaces=info_surfaces.rename(columns={'nom':'Tile name','count_x':'Number of mono detection','surface':'Sum of mono detected area','count_y':'Number of pluri detection',0:'Sum of pluri detected area'})
    info_surfaces=info_surfaces.round(2)

    table = pn.widgets.Tabulator(info_surfaces, name="Informations à l'échelle des tuiles Sentinel-2",header_align='center', show_index=False,
                stylesheets=[stylesheet])

#################################    

    map=create_map(tot_surf_tile)

    return(table,map,nb_tot,tot_surf,mono_detection_group,pluri_detection_group,mono_detection_surface,pluri_detection_surface)

############################

def maj_graphic(date_range,choix):
    global stac_search_results, df

    tile_insight=read_insight_tile(fichier_tiles)

    viirs_snpp=viirs_data(table_viirs_snpp,tile_sentinel)
    viirs_noaa=viirs_data(table_viirs_noaa,tile_sentinel)

    viirs_snpp=viirs_snpp[(viirs_snpp['date_'] >= pd.to_datetime(date_range[0]).strftime('%Y-%m-%d')) & (viirs_snpp['date_']<=pd.to_datetime(date_range[1]).strftime('%Y-%m-%d'))]
    viirs_noaa=viirs_noaa[(viirs_noaa['date_'] >= pd.to_datetime(date_range[0]).strftime('%Y-%m-%d')) & (viirs_noaa['date_']<=pd.to_datetime(date_range[1]).strftime('%Y-%m-%d'))]
    tile_insight=tile_insight[(tile_insight['date_'] >= pd.to_datetime(date_range[0]).strftime('%Y-%m-%d')) & (tile_insight['date_']<=pd.to_datetime(date_range[1]).strftime('%Y-%m-%d'))]

    date_range = pd.date_range(start=df['date_'].min(), end=df['date_'].max())
    full_date_series = pd.DataFrame(date_range.strftime('%Y-%m-%d'), columns=['date_'])
    full_date_series['date_']=pd.to_datetime(full_date_series['date_'])
    
    df_tiles=prepare_data(df,full_date_series,"Sentinel-2",choix)
    snpp=prepare_data(viirs_snpp,full_date_series,"Snpp",choix)
    noaa=prepare_data(viirs_noaa,full_date_series,"Noaa-20",choix)
    insight=prepare_data(tile_insight,full_date_series,"INSIGHT",choix)

    df_cloud_cover=stac_search_results[stac_search_results['nom'] == choix]

    dataframes = [df_tiles, df_cloud_cover, noaa, snpp,insight]
    df_tot = reduce(lambda left, right: pd.merge(left, right, on='date_', how='left', suffixes=('', '_y')), dataframes)
    df_tot = df_tot.loc[:, ~df_tot.columns.str.endswith('_y')]

    bar_plot=df_tot.hvplot(x='date_',y=['Sentinel-2', 'Snpp','Noaa-20'], kind='bar', width=800, height=400, title="Nombre de détection par jour", legend='top_left').opts(multi_level=False,
                                                                                                                                            xlabel='Date')
    cc_fig = df_tot.hvplot.scatter(x='date_', y='Cloud_Cover', color=df_tot['INSIGHT'].apply(lambda x: 'green' if x == 1 else 'red'), marker='s', size=300,xlabel='Date')

    combined = hv.Layout([bar_plot, cc_fig]).cols(1)
    combined.opts(
        opts.Scatter(height=400, width=1800, xrotation=45, responsive=True,title='Evolution de la couverture nuageuse (%)',shared_axes=True,show_legend=True),
        opts.Bars(height=600, width=1800, xrotation=45, responsive=True,title="Nombre de détection par jour",shared_axes=True, show_legend=True),
        opts.Layout(shared_axes=True))

    image_elements = []
    for _, row in df_cloud_cover.iterrows():
        url = row['thumbnail_url']
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        img_array = np.array(img)
        image_elements.append(hv.RGB(img_array).opts(title=f"Date: {row['date_'].date()}, Cloud: {row['Cloud_Cover']}%"))

    grid = hv.Layout(image_elements).opts(opts.RGB(width=500, height=500, xaxis=None, yaxis=None)).cols(3)
    grid = hv.Layout(grid).opts(width=1200,height=600)

    return combined,grid

total_detection=pn.indicators.Number(name='Totale détection', value=0, format='{value}',colors=[(0,'blue')])
surface_total=pn.indicators.Number(name='Surface totale estimée (ha)', value=0, format='{value}',colors=[(0,'blue')])
mono_detection_group=pn.indicators.Number(name='Nombre de Mono détection', value=0, format='{value}',colors=[(0,'red')])
pluri_detection_group=pn.indicators.Number(name='Nombre de Pluri détections', value=0, format='{value}',colors=[(0,'green')])
mono_detection_surface=pn.indicators.Number(name='Surface (ha) Mono détection', value=0, format='{value}',colors=[(0,'red')])
pluri_detection_surface=pn.indicators.Number(name='Surface (ha) Pluri détections', value=0, format='{value}',colors=[(0,'green')])

table_map_container = pn.Row()  
graphic_container = pn.Column() 
interface_1_container = pn.Column()

def update_interface_1(event):
    global table_map_container
    
    table, map, nb_tot, tot_surf, mono_nb, pluri_nb, mono_surf, pluri_surf = maj_table(datetime_range_picker.value,table_source) 
    mono_detection_group.value = mono_nb
    pluri_detection_group.value = pluri_nb
    
    mono_detection_surface.value = mono_surf
    pluri_detection_surface.value = pluri_surf

    total_detection.value = nb_tot
    surface_total.value = tot_surf
    
    table_map_container[:] = [table, map]
    interface_1_container[:] = [table_map_container, tile_bouton]
    
    if interface_1_container not in main:
        main.append(interface_1_container)
    if graphic_container not in main:
        main.append(graphic_container)

def update_interface_2(event):
    global graphic_container
    
    choix = event.new
    fig, image = maj_graphic(datetime_range_picker.value, tile_bouton.value)
    graphic_container[:] = [fig, image]    

datetime_range_picker = pn.widgets.DatetimeRangePicker(name='Select your Date Range', start=dt.datetime(2023, 1, 1), end=dt.datetime(2024, 12, 31))
datetime_range_picker.param.watch(update_interface_1, 'value')

tile_bouton.param.watch(update_interface_2, 'value')

sidebar = pn.Column(datetime_range_picker,"# Indicateurs Globaux", total_detection,surface_total,mono_detection_group, mono_detection_surface,pluri_detection_group,pluri_detection_surface)
main = pn.Column("## Step 1 : Selectionner un interval de date pour voir les données et indicateurs globaux. \n ## Step 2 : Choisir une tuile à observer") 

template =pn.template.FastListTemplate(
    site="Panel", header_background ='#f89424',title="Dashboard Contrôle des surfaces brûlées en sortie en chaîne",logo="https://neotech.nc/wp-content/uploads/2023/10/logo_oeil_quadri-254x300.jpeg.webp",sidebar=[sidebar],main=[main])

template.servable()
