# coding=utf-8
import arcpy
from arcpy.sa import *

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = ""
        self.tools = [Changes]


class Changes(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Changes"
        self.description = ""
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""
        first_raster = arcpy.Parameter(
            displayName="First raster",
            name="first_raster",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        second_raster = arcpy.Parameter(
            displayName="Second raster",
            name="second_raster",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        output_raster = arcpy.Parameter(
            displayName="Output raster",
            name="output_rasterr",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output")

        params = [first_raster, second_raster, output_raster]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        first_raster = parameters[0].valueAsText
        second_raster = parameters[1].valueAsText
        output_raster = parameters[2].valueAsText

        scale = 10000
        combined = Raster(first_raster) * scale + Raster(second_raster)

        first_calc  = Int(combined // scale)
        second_calc = Int(combined % scale)

        filtered = SetNull(first_calc == second_calc, Int(combined))
        filtered.save(output_raster)

        tbl = arcpy.management.CreateTable("in_memory/", "ras_attrs").getOutput(0)
        vat_view = arcpy.management.MakeTableView(filtered, "vat_view")
        arcpy.management.CopyRows(vat_view, tbl)

        arcpy.management.AddField(tbl, "First",  "LONG")
        arcpy.management.AddField(tbl, "Second", "LONG")
        arcpy.management.AddField(tbl, "Change", "TEXT", field_length=64)

        arcpy.management.CalculateField(tbl, "First",  "int(!VALUE! / 10000)", "PYTHON_9.3")
        arcpy.management.CalculateField(tbl, "Second", "!VALUE! % 10000",      "PYTHON_9.3")
        arcpy.management.CalculateField(tbl, "Change", "str(!First!) + ' -> ' + str(!Second!)",
                                        "PYTHON_9.3")

        arcpy.management.JoinField(in_data=filtered, in_field="VALUE",
                                   join_table=tbl, join_field="VALUE",
                                   fields=["First","Second","Change"])

        return

