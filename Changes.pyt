# coding=utf-8
import arcpy
from arcpy.sa import *

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
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
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Input")

        first_field = arcpy.Parameter( #Тут мы выбираем поле
            displayName="Value filed first raster",
            name="first_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")

        first_field.parameterDependencies = [first_raster.name]

        second_raster = arcpy.Parameter(
            displayName="Second raster",
            name="second_raster",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Input")

        resolution = arcpy.Parameter(  # Тут мы задаем число радиуса
            displayName="Resolution output raster",
            name="resolution",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        output_raster = arcpy.Parameter(
            displayName="Output raster",
            name="output_rasterr",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output")

        params = [first_raster, first_field, second_raster, resolution, output_raster]
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
        """The source code of the tool."""
        #[first_raster, first_field, second_raster, second_field]
        first_raster = parameters[0].valueAsText
        first_field = parameters[1].valueAsText
        second_raster = parameters[2].valueAsText
        resolution = float(parameters[3].valueAsText)
        output_raster = parameters[4].valueAsText

        #1. Конвертироавть first_raster в точки (raster to point) в качестве значений передать first_field
        out_points = 'in_memory/out_points'
        arcpy.RasterToPoint_conversion(first_raster, out_points, first_field)

        #2. При помощи инструмента Extract Multi Values to Points извлечь из второго растра информацию в созданные точки 1
        ExtractMultiValuesToPoints(out_points, second_raster)

        #3. Создать поле change (short)
        arcpy.AddField_management(out_points, "Change", 'SHORT')

        fields = arcpy.ListFields(out_points)
        field_names = [str(field.name) for field in fields]

        #4. Заполнить поле change с условием grid_code == название второго слоя (second_raster), то 0, а если отличается, то 1
        cursor = arcpy.da.UpdateCursor(out_points, ['grid_code', field_names[-2], 'Change'])
        for row in cursor:
            if row[0] == row[1]:
                continue
            else:
                row[2] = 1
                cursor.updateRow(row)

        #5. Создать поле change_txt
        arcpy.AddField_management(out_points, "Change_txt", 'TEXT')

        #6. Создать слой выборки в точках
        out_points_lyr = 'out_points_lyr'
        arcpy.MakeFeatureLayer_management(out_points, out_points_lyr)

        #7. Выбрать точки, где значение поля change 1
        arcpy.SelectLayerByAttribute_management(out_points_lyr, 'NEW_SELECTION', '"Change" = 1')

        #8. Заполнить для выбранных точек поле change_txt с следующим запросом "{} --> {}.format(grid_code, название второго слоя)
        rows = arcpy.da.UpdateCursor(out_points_lyr, ['grid_code', field_names[-2], 'Change_txt'])
        for row in rows:
            row[2] = "{} --> {}".format(row[0], row[1])
            rows.updateRow(row)

        #9. Далее не снимая выборку сконвертировать в растр point to raster и указать выходное разрешение
        arcpy.PointToRaster_conversion(out_points_lyr, 'Change_txt', output_raster, "MOST_FREQUENT", "", resolution)

        return
