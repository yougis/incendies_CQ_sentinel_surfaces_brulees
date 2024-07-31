from shapely.geometry import Polygon, LineString, shape, mapping
import geopandas as gpd
import pandas as pd
import math

def linestring_to_polygon(gdf):
    polygons = []
    
    for index, row in gdf.iterrows():
        all_coords = mapping(row['geometry'])['coordinates']
        lats = [x[1] for x in all_coords]
        lons = [x[0] for x in all_coords]
        
        polyg = Polygon(zip(lons, lats))
        polygons.append(polyg)
    new_gdf = gpd.GeoDataFrame(geometry=polygons, crs=gdf.crs)
    
    return new_gdf

def getPolyCoords(row, geom, coord_type):
    """Returns the coordinates ('x' or 'y') of edges of a Polygon exterior"""
    exterior = row[geom].exterior

    if coord_type == 'x':
        return list( exterior.coords.xy[0] )
    elif coord_type == 'y':
        return list( exterior.coords.xy[1] )
    
def find_intersecting_id(row, gdf):

    possible_matches_index = list(gdf.sindex.intersection(row['geometry'].bounds))
    possible_matches = gdf.iloc[possible_matches_index]
    precise_matches = possible_matches[possible_matches.geometry.intersects(row['geometry'])]
    intersecting_ids = precise_matches['surface_id_h3'].tolist()
    intersecting_ids = [id_ for id_ in intersecting_ids if id_ != row['surface_id_h3']]
    return intersecting_ids


def mesure_totale(df):
    """
    tot_surf : total number of detected area (ha)
    tot_surf_tile: total sum of detected area per tile (ha)
    """
    tot_nb = len(df)
    tot_surf = df.dissolve().area.sum() / 10000
    tot_surf_tile = df.dissolve(by='nom').area / 10000
    tot_surf_tile = tot_surf_tile.reset_index()
    
    return(tot_surf,tot_nb,tot_surf_tile)

def mesure_pluri_detection(df):
    """
    pluri_detection_surface : number of pluri detected detected area (ha)
    pluri_detection_group: number of group
    pluri_tile_number : number of detection per tile
    pluri_tile_surface : sum of detected area per tile (ha)
    """
    pluri_detection_list = df[df['groupe_id'].notna()]
    pluri_detection_surface = pluri_detection_list.dissolve().area.sum() / 10000
    pluri_detection_group = pluri_detection_list['groupe_id'].nunique()
    pluri_tile_number = pluri_detection_list['nom'].value_counts().reset_index()
    pluri_tile_surface = pluri_detection_list.dissolve(by='nom').area / 10000
    pluri_tile_surface = pluri_tile_surface.reset_index()

    return(pluri_tile_surface,pluri_tile_number,pluri_detection_group,pluri_detection_surface)

def mesure_mono_detection(df):
    """
    mono_detection_surface : number of mono detected detected area (ha)
    mono_detection_group: number of group
    mono_tile_number : number of detection per tile
    mono_tile_surface : sum of detected area per tile (ha)
    """
    mono_detection_list=df[df['groupe_id'].isna()]
    mono_detection_surface=mono_detection_list['surface'].sum() 
    mono_detection_group=mono_detection_list['groupe_id'].isna().sum() 
    mono_tile_number = pd.DataFrame(mono_detection_list["nom"].value_counts()) 
    mono_tile_surface = mono_detection_list.groupby('nom')['surface'].sum().reset_index() 
    
    return(mono_tile_surface,mono_tile_number,mono_detection_group,mono_detection_surface)

def try_multiple_date_formats(date_str, formats):
    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except ValueError:
            continue
    return pd.NaT 

def normalize_size(value, min_size, max_size, min_value, max_value):
    """Normalize the size based on the given range using a logarithmic scale."""
    if value == 0:
        return min_size
    log_min_value = math.log1p(min_value)
    log_max_value = math.log1p(max_value)
    log_value = math.log1p(value)
    return min_size + (log_value - log_min_value) * (max_size - min_size) / (log_max_value - log_min_value)
