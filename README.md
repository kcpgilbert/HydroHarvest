# HydroHarvest
HydroHarvest is a tool to calculate the volume of water that can be collected and stored from the runoff of a site in Los Angeles County. The tool utilizes various GIS maps to find the necessary inputs required to use the Rational Method to calculate a reasonable design volume according to the 85th percentile rainfall depth. HydroHarvest also provides an estimation of the volume of runoff based on projected climate data. HydroHarvest has the potential to save engineers the time and energy to collect the rational method site inputs themselves. 

The link to the live HydroHarvest website is: https://kcpgilbert-hydroharvest-hydroharvest-qzavle.streamlit.app/

The inputs and outputs of the HydroHarvest system are summarized below.
![image](https://user-images.githubusercontent.com/120534381/235779675-135c596d-f628-4aa3-93e3-7acb7f2626ab.png)
![image](https://user-images.githubusercontent.com/120534381/235779738-3b480ec1-1333-4085-967d-594443bd6d1a.png)
![image](https://user-images.githubusercontent.com/120534381/235779792-a534cc4e-922e-4078-83c1-d3dc042d3feb.png)

HyrdoHarvest is not yet complete and suggests the following improvements to its algorithm before being used to design runoff capture volumes.
![image](https://user-images.githubusercontent.com/120534381/235780538-e3735614-cd80-4b84-b048-37ce232a42ba.png)

HydroHarvest used the following sources of data and design guidance for LA County in its algorithm:
- https://dpw.lacounty.gov/wrd/publication/engineering/2006_Hydrology_Manual/2006%20Hydrology%20Manual-Divided.pdf
- https://open-meteo.com/en/docs/climate-api
- https://geohub.lacity.org/datasets/0eeb8e59bd194c3a97d03ea6dfe2cfea/explore?location=34.077914%2C-118.224051%2C10.81
- https://www.openstreetmap.org/#map=4/38.01/-95.84
- https://agsite.missouri.edu/slope-and-landscape-features/
- https://www.usgs.gov/centers/eros/science/national-land-cover-database 
