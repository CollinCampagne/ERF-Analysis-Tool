# Name: Collin Campagne
# Contact: collinacampagne@gmail.com // ccampagne@willistonvt.org
# Created: 01/20/2026
# Updated: 02/10/2026
# Purpose: Automate the processes required by the ERF to score parcels. Facilitates the testing of alternative thresholds.
# Trigger: Whenever ERF requires updates, or remodelling of data.  
# Inputs: 
#   1. Parcel Layer (Must contain "MAPID" field as Primary Key), 
#   2. One or more feature classes to be scored against the parcels, 
#   3. Threshold values for scoring.  
# Output: Creates an area/length field, and a scoring field within the Parcel feature class. Overwrites the Total Score Field within Parcel Feature Class. 

# ==========================================================================================================================
# Imports:
# ==========================================================================================================================

import arcpy
import traceback

# ==========================================================================================================================
# Establish environments 
# ==========================================================================================================================

aprx = arcpy.mp.ArcGISProject("CURRENT")

# ==========================================================================================================================
# Create Variables
# ==========================================================================================================================

# User inputs: 
Parcels = arcpy.GetParameterAsText(0)
FeatureClass = arcpy.GetParameterAsText(1)
lowRank = float(arcpy.GetParameterAsText(2))
highRank = float(arcpy.GetParameterAsText(3))

# Split multivalue input into a list
Feature_Class = FeatureClass.split(";")

# Iterate through each Input Feature Class 
for fc in Feature_Class:
# Get name of input feature classes for naming outputs
    desc1 = arcpy.Describe(fc)
    fcName = desc1.name

    # Get name of Parcels layer
    desc2= arcpy.Describe(Parcels)
    parcelName = desc2.name

    # Establish name for score fields
    score = f'{fcName}_SCORE'

# ==========================================================================================================================
# Perform Geoprocessing against parcels with input FC's 
# ==========================================================================================================================
    try:
        # Filter first if the threshold is set. If no threshold is set, then this will perform as an "intersect" tool. 
        if (lowRank == 0 or lowRank is None) and (highRank == 0 or highRank is None):
            Parcels_1 = arcpy.management.SelectLayerByLocation(
            in_layer=Parcels,
            overlap_type="INTERSECT",
            select_features=fc,
            search_distance=None,
            selection_type="NEW_SELECTION",
            invert_spatial_relationship="NOT_INVERT"
            )

            # Score = 1 for intersecting features
            arcpy.management.CalculateField(
                in_table=Parcels_1,
                field=score,
                expression="1",
                expression_type="PYTHON3",
                code_block="",
                field_type="SHORT",
                enforce_domains="NO_ENFORCE_DOMAINS"
            )

            # Invert Selection
            arcpy.management.SelectLayerByAttribute(
                in_layer_or_view=Parcels_1,
                selection_type="NEW_SELECTION",
                where_clause=f"{score} IS NULL",
                invert_where_clause=None
            )

            # Nulls get calculated as "0" 
            arcpy.management.CalculateField(
                in_table=Parcels_1,
                field=score,
                expression="0",
                expression_type="PYTHON3",
                code_block="",
                field_type="SHORT",
                enforce_domains="NO_ENFORCE_DOMAINS"
            )

            # Let 'em know
            arcpy.AddMessage(f'Scores have been created. {score} will be added to {parcelName}.')

            # *** This part should really be a function that is called. If you are reading this, and have the chops, create a function that performs this and email me. ***

            # Create a list of all fields with the text "SCORE" within the Parcels layer. 
            FieldList = arcpy.ListFields(Parcels)

            # Add Total Score Field.
            if "Total_Score" not in [f.name for f in FieldList]:
                arcpy.management.AddField(Parcels, "Total_Score", "SHORT")
            else:
                arcpy.AddMessage("Updating Total Score field...")
                arcpy.management.CalculateField(Parcels,"Total_Score", "0", "PYTHON3")
                    # Calculate Total Score Field
            score_fields = [f.name for f in FieldList if "SCORE" in f.name.upper()]

            arcpy.management.SelectLayerByAttribute(Parcels, "CLEAR_SELECTION")

            # I cheated on this part and used AI because I was not going to land on "[row[i] if isinstance(row[i], (int, float)) else 0 for i in range(len(score_fields))]" on my lonesome. Sue me. 
            with arcpy.da.UpdateCursor(Parcels, [score_fields, "Total_Score"]) as cursor:
                    for row in cursor:
                        count = 0
                        # Handle None values by treating them as 0
                        score_val = sum([row[i] if isinstance(row[i], (int, float)) else 0 for i in range(len(score_fields))])  
                        row[-1] = score_val
                        cursor.updateRow(row)
                        count += 1
            arcpy.AddMessage("Total Score field has been updated.") 
            aprx.save()
            arcpy.SelectLayerByAttribute_management(Parcels_1, "CLEAR_SELECTION")
            arcpy.AddMessage(f"Process Completed Successfully on {fcName}.")
            
        # If there are threshold values, proceed as intended: 
        else:

        # Intersect Parcel and input FC layers
            Intersect = arcpy.analysis.Intersect(in_features=[[Parcels, ""], [fc, ""]], join_attributes="ALL")
            arcpy.AddMessage("Intersecting Layers...")
        # Dissolve output layer using MAPID. *** Note: "MAPID" Serves as the Primary Key for this analysis to be joined back to the parcel layer. If this tool were to be run with other parcel data which does not contain "MAPID", it will fail. A black hole will open, stars will collapse, and all will be lost. *** 
            Dissolve = arcpy.management.Dissolve(in_features=Intersect, dissolve_field=["MAPID"])
            arcpy.AddMessage("Dissolving Layers...")

            # For 'line' FC's, the tool calculates the length of the line in Miles.
            if desc1.shapeType == "Polyline":
                columnName = f'{fcName}_Miles'
                arcpy.AddMessage(f'{columnName} will be added to {parcelName}')
                Parcels_2 = arcpy.management.CalculateGeometryAttributes(
                    in_features=Dissolve,
                    geometry_property=f"{columnName} LENGTH",
                    length_unit="MILES_US",
                    area_unit="",
                    coordinate_system='PROJCRS["NAD_1983_2011_StatePlane_Vermont_FIPS_4400_Ft_US",BASEGEOGCRS["GCS_NAD_1983_2011",DYNAMIC[FRAMEEPOCH[2010.0],MODEL["HTDP"]],DATUM["D_NAD_1983_2011",ELLIPSOID["GRS_1980",6378137.0,298.257222101],ANCHOREPOCH[2010.0]],PRIMEM["Greenwich",0.0],CS[ellipsoidal,2],AXIS["Latitude (lat)",north,ORDER[1]],AXIS["Longitude (lon)",east,ORDER[2]],ANGLEUNIT["Degree",0.0174532925199433]],CONVERSION["Transverse_Mercator",METHOD["Transverse_Mercator"],PARAMETER["False_Easting",1640416.666666667,LENGTHUNIT["Foot_US",0.3048006096012192]],PARAMETER["False_Northing",0.0,LENGTHUNIT["Foot_US",0.3048006096012192]],PARAMETER["Central_Meridian",-72.5],PARAMETER["Scale_Factor",0.9999642857142857],PARAMETER["Latitude_Of_Origin",42.5]],CS[Cartesian,2],AXIS["Easting (X)",east,ORDER[1]],AXIS["Northing (Y)",north,ORDER[2]],LENGTHUNIT["Foot_US",0.3048006096012192],ID["EPSG","6590"]]',
                    coordinate_format="SAME_AS_INPUT"
                    )
                arcpy.AddMessage("Calculating Geometry...")

            # For feature classes that are Polygons,  calculate Acreage. 
            elif desc1.shapeType == 'Polygon': 
                columnName = f'{fcName}_Acres'
                Parcels_2 = arcpy.management.CalculateGeometryAttributes(
                    in_features=Dissolve,
                    geometry_property=f"{columnName} AREA",
                    length_unit="",
                    area_unit="ACRES_US",
                    coordinate_system='PROJCRS["NAD_1983_2011_StatePlane_Vermont_FIPS_4400_Ft_US",BASEGEOGCRS["GCS_NAD_1983_2011",DYNAMIC[FRAMEEPOCH[2010.0],MODEL["HTDP"]],DATUM["D_NAD_1983_2011",ELLIPSOID["GRS_1980",6378137.0,298.257222101],ANCHOREPOCH[2010.0]],PRIMEM["Greenwich",0.0],CS[ellipsoidal,2],AXIS["Latitude (lat)",north,ORDER[1]],AXIS["Longitude (lon)",east,ORDER[2]],ANGLEUNIT["Degree",0.0174532925199433]],CONVERSION["Transverse_Mercator",METHOD["Transverse_Mercator"],PARAMETER["False_Easting",1640416.666666667,LENGTHUNIT["Foot_US",0.3048006096012192]],PARAMETER["False_Northing",0.0,LENGTHUNIT["Foot_US",0.3048006096012192]],PARAMETER["Central_Meridian",-72.5],PARAMETER["Scale_Factor",0.9999642857142857],PARAMETER["Latitude_Of_Origin",42.5]],CS[Cartesian,2],AXIS["Easting (X)",east,ORDER[1]],AXIS["Northing (Y)",north,ORDER[2]],LENGTHUNIT["Foot_US",0.3048006096012192],ID["EPSG","6590"]]',
                    coordinate_format="SAME_AS_INPUT"
                )
                arcpy.AddMessage("Calculating Geometry...")
            else:
                # No points allowed 
                raise ValueError("Unsupported geometry type. Only Line and Polygon feature classes are supported.")

# ==================================================================================================================
# Perform geoprocessing tools to create the necessary data, and calculate area:
# ==================================================================================================================

            # Add field for Area/Length measurement
            arcpy.management.AddField(Parcels, columnName, "FLOAT")

            # Join Parcel 2 table to Parcel table via Map ID
            ParcelsJoin = arcpy.management.AddJoin(
                in_layer_or_view=Parcels,
                in_field="MAPID",
                join_table=Parcels_2,
                join_field="MAPID",
                join_type="KEEP_ALL",
                index_join_fields="NO_INDEX_JOIN_FIELDS",
                rebuild_index="NO_REBUILD_INDEX",
                join_operation="JOIN_ONE_TO_MANY"
            )

            # Let 'em know
            arcpy.AddMessage("Joining Tables...")

            # Use arcpy.Describe to get the naming convention of the joined table field.
            ParcelDesc = arcpy.Describe(Parcels_2)
            parcel2Name = ParcelDesc.name
            fieldName = f"{parcel2Name}.{columnName}"

            # Select all rows with data from the joined table. 
            arcpy.management.SelectLayerByAttribute(ParcelsJoin, "NEW_SELECTION", fieldName + " IS NOT NULL") # This last bit is a SQL statement!

            # Calculate field 

            arcpy.management.CalculateField(
                in_table= ParcelsJoin,
                field= f"{parcelName}.{columnName}",  # Target field in Parcels
                expression= f"!{parcel2Name}.{columnName}!",  # Source field from joined table
                expression_type= "PYTHON3",
                code_block= "",
                field_type= "FLOAT",
                enforce_domains= "NO_ENFORCE_DOMAINS"
            )
            arcpy.AddMessage("Data copied successfully from joined table to original table.")

            # Remove Join
            arcpy.management.RemoveJoin(
                in_layer_or_view=ParcelsJoin,
                join_name=""
            )

            arcpy.AddMessage(f'{columnName} will be added to {parcelName}')

# ==================================================================================================================
# Generate scores using the threshold inputs and calculated areas of dissolved features:
# ==================================================================================================================

            # Add score field to Parcel Layer
            arcpy.management.AddField(Parcels, score)

            # Iterate through each row, assigning a rank in a new column based on user input using UpdateCursor Method.

            with arcpy.da.UpdateCursor(Parcels, [columnName, score]) as cursor:
                count = 0
                for row in cursor:
                    value = row[0]

                    # Low Rank usually is less than High Rank. If this is true, then proceed as normal.
                    if lowRank < highRank:
                    # Handle None or empty values
                        if value is None:
                            row[1] = 0
                        # Compare numerically
                        elif value <= lowRank:
                            row[1] = 0
                        elif lowRank < value < highRank:
                            row[1] = 1
                        elif value >= highRank:
                            row[1] = 2
                        else:
                            row[1] = 0 

                    # If Low Rank is greater than High Rank, reverse the ranking system.
                    else:
                        # Handle None or empty values
                        if value is None:
                            row[1] = 2

                        # Compare numerically
                        elif lowRank > value > highRank:
                            row[1] = 1
                        elif value <= highRank:
                            row[1] = 2
                        else:
                            row[1] = 0 
                    cursor.updateRow(row)
                    count += 1
            arcpy.AddMessage(f'Scores have been created. {score} will be added to {parcelName}.')

# ==================================================================================================================
# Generate and overwrite Total Score field:
# ==================================================================================================================

            # Create a list of all fields within the "Parcels" feature class. We will be using all fields containing the upper case text "SCORE" to calculate the total score. 
            FieldList = arcpy.ListFields(Parcels)

            # Add Total Score Field.
            if "Total_Score" not in [f.name for f in FieldList]:
                arcpy.management.AddField(Parcels, "Total_Score", "SHORT")
            else:
                arcpy.AddMessage("Updating Total Score field...")
                # To prevent scores compounding every time the tool is run, we reset the value of "Total_Score" to zero, then recalculate the field.
                arcpy.management.CalculateField(Parcels,"Total_Score", "0", "PYTHON3")


            # Ensure that no parcels are selected while performing UpdateCursor.
            arcpy.management.SelectLayerByAttribute(Parcels, "CLEAR_SELECTION")

            # Create a list of all fields containing the text "SCORE". This part I used AI to help generate. 
            score_fields = [f.name for f in FieldList if "SCORE" in f.name.upper()]

            # Once again use UpdateCursor to update "Total_Score" Field. 
            with arcpy.da.UpdateCursor(Parcels, [score_fields, "Total_Score"]) as cursor:
                    for row in cursor:
                        count = 0
                        # Handle None values by treating them as 0
                        score_val = sum([row[i] if isinstance(row[i], (int, float)) else 0 for i in range(len(score_fields))])  
                        row[-1] = score_val
                        cursor.updateRow(row)
                        count += 1

            arcpy.AddMessage("Total Score field has been updated.")

    # ==================================================================================================================
    # Clean up temporary data:
    # ==================================================================================================================

            # Clear Selection
            arcpy.management.SelectLayerByAttribute(Parcels, "CLEAR_SELECTION")

            # Clean up temporary feature classes
            arcpy.management.DeleteFeatures(Dissolve)
            arcpy.management.DeleteFeatures(Intersect)
            arcpy.AddMessage("Temporary feature classes deleted.")

            # Save Project
            arcpy.AddMessage("Saving Project...")
            aprx.save()

            arcpy.AddMessage(f"Process Completed Successfully on {fcName}.")

# ====================================================================================================
# Error Handling:
# ====================================================================================================

    except arcpy.ExecuteError:
        arcpy.AddMessage("ArcPy Error: " + arcpy.GetMessages(2))

    except Exception as e:
        tb = traceback.format_exc()
        arcpy.AddMessage(f"Python Error: {tb}")

# ====================================================================================================
# Notes, Known Issues, and Future Improvements:
# ====================================================================================================

# 1: Currently, the multivalue feature is not working. This should be relatively easy to fix, however, I have lost patience trying to debug it and just want to get down to making the damn map. 

    # Update: Resolved 02/10/2026. 

# 2: Future versions of this tool should include adding a weight factor to each score. I currently do not have the time to implement this.

# With love, 
# CC 2026 ;*