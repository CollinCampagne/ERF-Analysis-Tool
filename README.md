# ERF-Analysis-Tool
## Description:

  The Williston Conservation Commission has led the Town's efforts to conserve lands that have valuable natural resources through the use of the Environmental Reserve Fund. Since the program’s inception in 1989, the ERF has helped to conserve 2,252 acres in Williston. The ERF is a powerful leveraging tool resulting in a $2.4 million investment for a total value of $5.2 million over the life of the fund. Here you can find information about publicly accessible conserved lands in Williston.
	
	
To support the ERF, the Town's conservation planner has been tasked with using outlined criteria to generate scores for parcels within Williston. I have been charged with taking over the project. 

The existing methodology contains two main iterations: 
	1. Using "Intersect" spatial relationships to add points to parcels.
	2. Performing "Intersect" -> "Dissolve" ->  "Join" geospatial tools to copy data from the dissolved feature class to the parcel feature class.
	3. Manually calculating scores based on area/length totals

This methodology is applied to over 20 different feature layers. Given the repetition in methodology, and the number of feature classes involved, along with a reasonable risk of human error being introduced, a script tool is the best option of performing the analysis. 

## Scripting:

### Inputs: 
   * The target layer for this project begins with the most recent parcel data layer with up-to-date Grand List boundaries. 
	
	 • The Secondary input layer is the layer that will be intersected, then dissolved, then joined to the parcel layer. This is a multi-value parameter, allowing  for all feature classes with the same thresholds to be inputted. 

	 • The last parameters are thresholds. Please refer to documentation to obtain the established thresholds for each feature class. The tool performs differently depending on the input values within this perimeter:
		○ Low/High thresholds = 0: The tool performs as an "Intersect" tool- features intersecting parcels, eg. Named Streams, obtain a score of 1. 
		○ Low Threshold < High Threshold: The tool scores parcels normally. Parcels with lower area/length receive lower scores than parcels of greater size. 
		○ Low Threshold > High Threshold: The tool scores parcels inversely. Parcels of lower area receive higher scores. For feature classes such as Regulatory Slope, this is key, as parcels with low/no slope are valued higher than parcels with steep slopes.

### Output:

The Parcel layer is overwritten every time the tool is run. With each feature class, two columns are added to the table: an area/length column, and a score column. The "Total_Score" column is either created if it does not exist, or is updated every time the tool runs with the summation of all score fields within the parcel table.
	
Notes:

• This tool requires the parcel layer to contain the "MAPID" field to act as the primary key for the dissolve function to dissolve against. In the future, if the we ever get a cleaned parcel layer, this should be changed to the tax parcel ID. 
• Some layers are special, and should be calculated outside of this tool. For example, the scoring for Acres requires three thresholds: <25 = 0, <100 but >25 = 1, and >100 = 2. Using the "select" and "calculate field" tools will be sufficient for the user to obtain these scores. Please refer to the ERF layer list for help: 


Future Improvements to the tool:

• The base methodology suggests alternative calculation methods. Future versions of this tool should adopt ways to implement these, notably the weighted scoring. 
• It would be helpful to be able to input all feature classes with their thresholds at once, where the tool presents a table with a FC input column and the next column acting as a comma-delimited field for thresholds. 
