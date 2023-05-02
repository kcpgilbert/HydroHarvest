# Set up streamlit in file
import streamlit as st

#Set up folium in streamlit
import folium
from folium.plugins import Draw
from folium.plugins import Geocoder
from streamlit_folium import st_folium

#Set up other packages
import math
import geopandas as gpd
import pyflo
import pandas as pd
import numpy as np
from matplotlib import pyplot
from pyflo import system
from pyflo.rational import hydrology
from shapely.geometry import Point, LineString
import osmnx as ox

#Define function to calculate the longest line path within a polygon
def find_longest_line_path(polygon_gdf):
    """
    Finds the longest line path inside a polygon.

    Args:
        polygon_gdf (GeoDataFrame): A GeoDataFrame with a polygon geometry column.

    Returns:
        float: The length of the longest line path inside the polygon.
    """

    #Calculate the distance between two points
    def distance(point1, point2):
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    #Get the polygon geometry
    polygon = polygon_gdf.geometry[0]

    #Initialize the longest line path to zero
    longest_line_path = 0

    #Loop through each pair of points in the polygon
    for i in range(len(polygon.exterior.coords)):
        for j in range(i+1, len(polygon.exterior.coords)):
            # Calculate the length of the line between the two points
            line_length = distance(polygon.exterior.coords[i], polygon.exterior.coords[j])

            #Check if the line is inside the polygon
            is_inside_polygon = True
            for k in range(len(polygon.exterior.coords)):
                if k != i and k != j:
                    if (polygon.exterior.coords[k][0] - polygon.exterior.coords[i][0]) * (polygon.exterior.coords[j][1] - polygon.exterior.coords[i][1]) \
                    > (polygon.exterior.coords[k][1] - polygon.exterior.coords[i][1]) * (polygon.exterior.coords[j][0] - polygon.exterior.coords[i][0]):
                        is_inside_polygon = False
                        break

            #If the line is inside the polygon and longer than the current longest line path, update the longest line path
            if is_inside_polygon and line_length > longest_line_path:
                longest_line_path = line_length

    return longest_line_path

#Start creating app contents

#Create a title
st.title('HYDROHARVEST')

with st.form(key='my_form'):
    #Create a box for user to select flow area
    volume = st.selectbox('Select if you are interested in collecting rainwater from roofs only or from your whole site:',('Roofs only','Entire site'))

    #Create a box for user to select site slope
    slope_input = st.selectbox('Select the slope of your site:',("Nearly Level","Gently Sloping","Strongly Sloping","Moderately Steep","Steep","Very Steep"))

    #Create caption for map
    st.caption('Draw your polygon on the map below:')

    #Create folium map with polygon drawing and address searching added
    Map = folium.Map(location=[34, -118], tiles = 'cartodbpositron', zoom_start=10, control_scale=True)
    Draw(export=True).add_to(Map)
    Geocoder().add_to(Map)

    #Display map using integrated streamlit and folium command
    st_folium(Map, width = 675)

    #Create a location to upload GeoJSON file if polygon
    uploaded_file = st.file_uploader('Export your polygon then upload your geojson file below:', type=["geojson"])

    #Create a buttom to start the program
    submit_button = st.form_submit_button(label='Calculate')

#If the user uploads a file perform the following
if submit_button == 1 and uploaded_file is not None:
    #Read the GeoJSON file and convert it into a GeoDataFrame
    gdf = gpd.read_file(uploaded_file)

    #Update to an appropriate PCS for LA County
    gdf_pcs = gdf.to_crs(epsg=3857)
    
    #Calculate the area of the polygon in m^2 
    area_m = gdf_pcs['geometry'].area[0]

    #Convert the area to acres
    area_acres = area_m*0.00024711

    #Calculate the longest line path using defined function and converting from meters to ft
    L = find_longest_line_path(gdf_pcs)*3.2808399
    
    #Determine the roof area in the site
    #Set boundary to look for buildings within as the orginal gdf in a GCS
    boundary_geojson = gdf
    #Get building geometries from open street maps within the polygon
    building_geoms = ox.geometries.geometries_from_polygon(boundary_geojson.geometry.values[0], tags={'building': True})
    #Reproject building geometry to the PCS
    buidling_geoms = building_geoms.to_crs(epsg=3857)
    #Find the area of the building geometry
    building_geoms['area (m^2)'] = buidling_geoms['geometry'].area
    #Find total building area for all buildings in polygon
    total_building_area = building_geoms['area (m^2)'].sum()
    #Find percentage of site area that is roof
    roofs = total_building_area/area_m 

    #Determine the flow path slope
    #Create a lookup table for slope of site based on the input options the user is given
    lookup_table = {
    "Nearly Level": 0.015,
    "Gently Sloping": 0.045,
    "Strongly Sloping": 0.1,
    "Moderately Steep": 0.20,
    "Steep": "0.40",
    "Very Steep": 0.60}
    #Retrieve a value from the lookup table for the slope using the user input
    value = lookup_table[slope_input]
    S = value

    #Set the total impervious area equal to the roof area as a place holder for finding the total impervious area percentage
    imp = roofs

    #Determine the 85th percentile 24 hour rainfall intensity in inches for LA County
    #Add a centroid column in PCS gdf for the selected polygon
    gdf_pcs['centroid'] = gdf_pcs['geometry'].centroid
    #Retrieve the centroid data
    centroid = gdf_pcs['centroid'][0]
    #Load the rain contour data
    rain_contours = gpd.read_file("https://raw.githubusercontent.com/kristinhernandez/Geospatial-Data-Analytics/Week-1/85th_and_95th_Percentile_Rainfall.geojson")
    #Create a Shapely Point from the centroid coordinates
    point = Point(centroid.x, centroid.y)  
    #Create a new gdf of the centroid point alone
    gdf_p = gpd.GeoDataFrame(index=[0], crs='epsg:3857', geometry=[point])
    #Perform the spatial join and merge with the rain_contours GeoDataFrame
    df_n = gpd.sjoin_nearest(gdf_p, rain_contours).merge(rain_contours, left_on="index_right", right_index=True)
    #Extract the point and line string geometries from the joined dataframe
    point_new = df_n.iloc[0]['geometry_x']
    line = df_n.iloc[0]['geometry_y']
    #Extract the value of the 'CONTOUR_x' column
    contour = df_n.loc[0, 'CONTOUR_x']
    #Set the 85th percentile equal to the contour
    pctl_85 = contour
    #Determine the intensity in in/hr by dividing by 24 hours
    i = pctl_85/24

    #Set the assumed undeveloped runoff coefficient
    c_u = 0.1

    #Calculate the developed runoff coefficient
    c_d = (0.9 * imp) + (1.0 - imp) * c_u

    #Set the assumed the roof runoff coefficient
    c_roof = 0.9

    #Calculate time of concentration and peak intensity
    tc_guess = 15
    while True:
      i_peak = i * np.power((1440/tc_guess),0.47)
      tc_new = (0.31 * np.power(L,0.483))/((np.power((c_d*i_peak),0.519))*np.power(S,0.135))
      if tc_guess == tc_new:
        break
      tc_guess = tc_new

    #Calculate peak flow rate
    Q_peak = c_d * i_peak * area_acres
    
    #Calculate design runoff in gallons based on the selection of whole site or roofs only
    if volume == "Entire site":
      Q_cfs = c_d * i * area_acres
      Q_cfh = Q_cfs * 60 * 60
      V_design = Q_cfh * 24 * 7.48
    elif volume == "Roofs only":
      Q_cfs = c_roof * i * (area_acres * roofs)
      Q_cfh = Q_cfs * 60 * 60
      V_design = Q_cfh * 24 * 7.48
    
    #Create and display outputs dataframe
    data = {'Output': {'Modeled (85th percentile storm) Rainfall Depth (in)': "%.2f" % pctl_85,
                  'Peak Rainfall Intensity (in/hr)': "%.4f" % i_peak,
                  'Undeveloped Runoff Coefficient (Cu)': "%.1f" % c_u,
                  'Developed Runoff Coefficient (Cd)': "%.4f" % c_d,
                  'Time of Concentration (min)': "%.1f" % tc_new,
                  'Clear Peak Flow Rate (cfs)': "%.4f" % Q_peak,
                  'Burned Peak Flow Rate (cfs)': "%.4f" % Q_peak,
                  '24-Hr Clear Runoff Volume (ac-ft)': "%.4f" % (V_design/325900),
                  '24-Hr Clear Runoff Volume (cu-ft)' : "%.2f" % (V_design/7.48)}}
    df_outputs = pd.DataFrame(data={'Output': list(data['Output'].values())}, index=list(data['Output'].keys()))
    st.table(df_outputs)

    #Make the hydrograph using design storm
    design_storm = np.array([
      (0.1, 0.0),
      (5.0, 0.5),
      (10, 1.5),
      (15, 2.0),
      (20, 2.25),
      (25, 2.5),
      (30, 2.5),
      (35, 2.5),
      (40, 2.5),
      (45, 2.5),
      (50, 2.5),
      (55, 2.5),
      (60, 2.5)])
    basin = hydrology.Basin(tc=tc_new, area=area_acres, c=c_d)
    rainfall_depths = design_storm * [24, tc_new]  # Scale array to 24 hour and peak duration
    flood_hydrograph = basin.flood_hydrograph(rainfall_depths, interval=1)
    x = flood_hydrograph[:, 0]
    y = flood_hydrograph[:, 1]
    
    #Plot the hydrograph
    pyplot.plot(x, y, 'c')
    pyplot.plot(x, y, 'lightsteelblue')
    pyplot.title(r'Site Hydrograph')
    pyplot.xlabel(r'Time ($minutes$)')
    pyplot.ylabel(r'Discharge ($cfs$)')
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot(pyplot.show())

    #Calculate new design volume due to climate change factor
    #Load climate data
    historical_data = pd.read_csv("https://raw.githubusercontent.com/kristinhernandez/Geospatial-Data-Analytics/Week-1/historical.csv")
    future_data = pd.read_csv("https://raw.githubusercontent.com/kristinhernandez/Geospatial-Data-Analytics/Week-1/future.csv")
    #Rename climate data columns
    future_data = future_data.rename(columns={'precipitation_sum_CMCC_CM2_VHR4 (mm)': 'future rainfall'})
    historical_data = historical_data.rename(columns={'precipitation_sum_CMCC_CM2_VHR4 (mm)': 'historical rainfall'})
    #Add year columns to climate data dataframes
    historical_data['YEAR'] = historical_data['time'].astype(str).str.slice(start=0,stop=4)
    future_data['YEAR'] = future_data['time'].astype(str).str.slice(start=0,stop=4)
    #Group climate dataframes by year
    historical_grouped = historical_data.groupby('YEAR').sum().reset_index()
    future_grouped = future_data.groupby('YEAR').sum().reset_index()
    #Determine average percent difference
    avg_historical = historical_grouped['historical rainfall'].mean()
    avg_future = future_grouped['future rainfall'].mean()
    percent_difference = (avg_future - avg_historical)/avg_future
    
    #Set climate change factor equal to the average percent difference
    cc_factor = percent_difference 
    cc_percent = cc_factor * 100

    #Calculate the design volume adjusted for cliamte change
    V_new = (1 + cc_factor) * V_design
    
    #Display a sentence summarizing the current and future design volumes for the site
    st.write("The current design volume is","%0.1f" % V_design,"and with a climate change increase factor of", "%0.1f" % cc_percent, "percent, the new design volume is", "%0.1f" % V_new, "gallons.")
else:
    st.write("Please upload a file and select calculate")