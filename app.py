import streamlit as st
import pandas as pd
import geopandas as gpd
from streamlit_folium import folium_static
import folium
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from functions import * 
import numpy as np

st.set_page_config(layout = 'wide')

@st.cache_data
def load_data():
	gdf = gpd.read_feather('./data/df_full.feather').to_crs('EPSG:4326')
	gdf = gdf.reset_index(drop = True)
	gdf = calculate_new_column(gdf, ovl = 0, bomen = 0, water = 1, monumenten = 0, wegen = -1, parken = 1, toiletten = 0, verkeerslichten = 0, wegdekkwaliteit = 0, horeca = 0, kerk = 0, winkels = 0 ,ov = 0)
	
	nodes = gpd.read_feather('./data/nodes.feather').to_crs('EPSG:4326')
	nodes = nodes.reset_index().rename(columns = {'osmid' : 'knooppunt'})
	return (gdf, nodes)

def style_function(feature):
	cmap = cm.RdYlGn  # Choose a continuous colormap (11 colors)
	value = feature['properties']['Score']  # Get the value from your column
	normalized_value = (0.5*value)+0.5
	color = mcolors.rgb2hex(cmap(normalized_value))  # Map the value to a color
	return {'color': color}
	
def style_function_route(feature):
	return {'weight': 5}

def calculate_new_column(gdf, ovl, bomen, water, monumenten, wegen, parken, toiletten, verkeerslichten, wegdekkwaliteit, horeca, kerk, winkels, ov, colum_name = 'Score'): 
    # Add your calculation logic here, e.g., using min_value and max_value
	# Score op basis van gewichten ingevuld op streamlit
	gdf[colum_name] = (gdf['score_ovl']*ovl + 
					gdf['score_bomen']*bomen + 
					gdf['score_water']*water + 
					gdf['score_monumenten']*monumenten + 
					gdf['score_wegen']*wegen + 
					gdf['score_park']*parken + 
					gdf['score_openbare_toiletten']*toiletten + 
					gdf['score_verkeerslichten']*verkeerslichten + 
					gdf['score_wegdekkwaliteit']*wegdekkwaliteit + 
					gdf['score_horeca']*horeca +
					gdf['score_kerk']*kerk +
					gdf['score_winkels']*winkels +
					gdf['score_OV']*ov)

	return gdf	

#@st.cache_resource
def create_map(_gdf, _nodes, _df_route = None, route = False, distance = 0, score = 0):
	m = folium.Map(location=[_gdf['geometry'].centroid.y.mean(), _gdf['geometry'].centroid.x.mean()], zoom_start=14)

	folium.GeoJson(
		_gdf,
		name='Score',
		style_function=style_function).add_to(m)	
	
	folium.GeoJson(
		_nodes,
		name='Nodes',
		marker = folium.CircleMarker(radius = 2, # Radius in metres
                                           weight = 0, #outline weight
                                           fill_color = '#000000', 
                                           fill_opacity = 1),
		tooltip=folium.GeoJsonTooltip(fields=['knooppunt'], labels=True, sticky=True)
		).add_to(m)	
	
	if route: 
		folium.GeoJson(
			_df_route, style_function=style_function_route,
			name='Route').add_to(m)	
		st.markdown('**Er is een route gevonden van '+str(round(distance/1000,2))+'km en een gemiddelde score van '+str(round(score,2))
			  		+ '**' )
		if score == -10: ###
			st.markdown("Niet mogelijk om alle waypoints te bezoeken") ###
    

	return m

def calculate_route(gdf, start, end, g_min, g_max, waypoints):
    a = gdf.sort_values(['u','v']).pivot(index = 'u', columns = 'v', values = 'length').fillna(100000).values # lengte van de edges
    s = gdf.sort_values(['u','v']).pivot(index = 'u', columns = 'v', values = 'Score').fillna(0).values # score afhankelijke van selectie
    s=s*a
    
    a_final,s_final,start_final,end_final,indices = smallMatrices(a,s,g_max,start,end)
    
    best_solution_temp, distance, score, runtime = looproutes_ant_colony_optimization(a_final,s_final,start_final,end_final,waypoints,g_min,g_max)
    
    best_solution = indices[best_solution_temp]
    
    df_route = pd.DataFrame({'u' : best_solution})
    df_route['v'] = df_route.u.shift(-1)
    df_route = df_route.dropna()
    df_route = gdf.merge(df_route)
    
    return df_route, distance, score

def main():
	# Title and description
	
	st.title("Loopplezierkaart")
	st.write("Welkom bij de loopplezierkaart van de Hogeschool van Amsterdam. Kies in het menu links welke omgevingsfactoren je wil laten meewegen in de loopbaarheidsscore. Klik op 'Calculate' en bekijk de kaart (groen is aantrekkelijk, geel is neutraal en rood is minder aantrekkelijk).")
	st.write("De zwarte punten zijn knooppunten met een id. Als je twee knooppunten kiest en de id's invult in het menu kan je ook de meest aantrekkelijke route bereken tussen de twee punten a.d.v. de eerder gekozen score. Klik op 'Add route' om jouw gepersonaliseerde route te tonen")
	
	(gdf, nodes) = load_data()
	
	# Sidebar with sliders
	st.sidebar.header("Map Settings")

	# df_route = None
	df_route = []
	route = False
	distance = 0
	score = 0
	calculate_triggered = False
	
	with st.sidebar.form("Score input"):	
		ovl = st.number_input("Score openbare verlichting", -10,10,0,1,  key="ovl")
		bomen = st.number_input("Score bomen", -10,10,0,1, key="bomen")
		water = st.number_input("Score water", -10,10,1,1, key="water")
		monumenten = st.number_input("Score monumenten", -10,10,0,1, key="monumenten")
		wegen = st.number_input("Score drukke wegen", -10,10,-1,1, key="wegen")
		parken = st.number_input("Score parken", -10,10,1,1, key="parken")
		#toiletten = st.number_input("Score toiletten", -10,10,0,1, key="toiletten")
		verkeerslichten = st.number_input("Score verkeerslichten", -10,10,0,1, key="verkeerslichten")
		#wegdekkwaliteit = st.number_input("Score wegdekkwaliteit", -10,10,0,1, key="wegdekkwaliteit")
		horeca = st.number_input("Score horeca", -10,10,0,1, key="horeca")
		#kerk = st.number_input("Score kerken", -10,10,0,1, key="kerk")
		winkels = st.number_input("Sco3re winkels", -10,10,0,1, key="winkels")
		#ov = st.number_input("Score OV", -10,10,0,1, key="ov")
		calculate_button = st.form_submit_button("Calculate")
	
	with st.sidebar.form("Route"):	
		start = st.number_input("Start knooppunt", 0,3100,2913,1,  key="start")
		end = st.number_input("Eind knooppunt", 0,3100,3045,1,  key="end")
		min_dist = st.number_input("Minimale afstand", 500,10000,500,100,  key="min_dist")
		max_dist = st.number_input("Maximale afstand", 500,10000,3000,100,  key="max_dist")
		waypoints_text = st.text_input("Voeg waypoints toe (gescheiden met komma)",value = '')
		waypoints = eval(f"[{waypoints_text}]")

		add_route = st.form_submit_button("Add route")
			
	if calculate_button:
		gdf = calculate_new_column(gdf, ovl = ovl, bomen = bomen, water = water, monumenten = monumenten, wegen = wegen, parken = parken, toiletten = 0, verkeerslichten = verkeerslichten, wegdekkwaliteit = 0, horeca = horeca, kerk = 0, winkels = winkels ,ov = 0)

	if add_route:
		gdf = calculate_new_column(gdf, ovl = ovl, bomen = bomen, water = water, monumenten = monumenten, wegen = wegen, parken = parken, toiletten = 0, verkeerslichten = verkeerslichten, wegdekkwaliteit = 0, horeca = horeca, kerk = 0, winkels = winkels ,ov = 0)
		i = 0
		# Ook bij negatieve scores een route vinden door scores te verhogen.
		df_route, distance, score = calculate_route(gdf, start, end, min_dist, max_dist, waypoints)
		route = True

	folium_static(create_map(gdf, nodes, df_route, route, distance, score), width=1000, height=700)

	route = False
	
# Run the app
if __name__ == '__main__':
	main()
