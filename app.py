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

def calculate_new_column(gdf, ovl, bomen, water, monumenten, wegen, parken, colum_name = 'Score'): 
    # Add your calculation logic here, e.g., using min_value and max_value
	# Score op basis van gewichten ingevuld op streamlit
	gdf[colum_name] = (gdf['score_ovl']*ovl + 
					gdf['score_bomen']*bomen + 
					gdf['score_water']*water + 
					gdf['score_monumenten']*monumenten + 
					gdf['score_wegen']*wegen + 
					gdf['score_park']*parken)

	return gdf	

#@st.cache_resource
def create_map(_gdf, _nodes, _df_route = None, route = False, distance = 0, score_origineel = 0, score_2 = 0):
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
		st.markdown('**Er is een route gevonden van '+str(round(distance/1000,2))+'km en een gemiddelde score van '+str(round(score_origineel,2))
			  		+ ' (' +str(round(score_2,2)) + ')'+'**' )

	return m

def calculate_route(gdf, start, end, min, max):
	a = gdf.sort_values(['u','v']).pivot(index = 'u', columns = 'v', values = 'length').fillna(100000).values # lengte van de edges
	s = gdf.sort_values(['u','v']).pivot(index = 'u', columns = 'v', values = 'Score').fillna(0).values # score afhankelijke van selectie
	s=s*a

	s_norm = s.copy()
	s_norm -= np.min(s_norm)
	s_norm /= np.max(s_norm)
 
	best_solution, distance, score, runtime = looproutes_ant_colony_optimization(a,s,s_norm,start,end,min,max)
	
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
	score_ori = 0
	score_2 = 0
	calculate_triggered = False
	
	with st.sidebar.form("Score input"):	
		ovl = st.number_input("Score openbare verlichting", -10,10,0,1,  key="ovl")
		bomen = st.number_input("Score bomen", -10,10,0,1, key="bomen")
		water = st.number_input("Score water", -10,10,0,1, key="water")
		monumenten = st.number_input("Score monumenten", -10,10,0,1, key="monumenten")
		wegen = st.number_input("Score drukke wegen", -10,10,0,1, key="wegen")
		parken = st.number_input("Score parken", -10,10,0,1, key="parken")
		calculate_button = st.form_submit_button("Calculate")
	
	with st.sidebar.form("Route"):	
		start = st.number_input("Start knooppunt", 0,3100,0,1,  key="start")
		end = st.number_input("Eind knooppunt", 0,3100,0,1,  key="end")
		min_dist = st.number_input("Minimale afstand", 500,10000,500,100,  key="min_dist")
		max_dist = st.number_input("Maximale afstand", 500,10000,500,100,  key="max_dist")
		add_route = st.form_submit_button("Add route")
			
	if calculate_button:
		gdf = calculate_new_column(gdf, ovl, bomen, water, monumenten, wegen, parken)

	if add_route:
		gdf = calculate_new_column(gdf, ovl, bomen, water, monumenten, wegen, parken)
		i = 0
		# Ook bij negatieve scores een route vinden door scores te verhogen.
		while len(df_route) == 0:
			df_route, distance, score_ori = calculate_route(gdf.assign(Score=lambda d: d.Score+i), start, end, min_dist, max_dist)
			i += 1
		route = True

		# Bij verhoogde scores willen we de score weten die bij de ingevoerde scores hoort -> score 2
		df_route = calculate_new_column(df_route, ovl, bomen, water, monumenten, wegen, parken, colum_name = 'Score2')
		score_2 = np.average(df_route.Score2, weights=df_route.length)

	folium_static(create_map(gdf, nodes, df_route, route, distance, score_ori, score_2), width=1000, height=700)

	route = False
	
# Run the app
if __name__ == '__main__':
	main()
