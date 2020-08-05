# LST_Plugin
QGIS plugin to estimate Land Surface Temperature (LST) from Landsat 5 and 8 data.
This follows the algorithm outlined in the paper by Avdan and Jovanovska, 2016 - Algorithm for Automated Mapping of Land Surface Temperature Using LANDSAT 8 Satellite Data.

This plugin opens a GUI, offering options for file selection and choice of outputs. By default, outputs are stored in a folder in the input directory. Results are displayed on screen as new layers for further use.

Landsat 5 option requires bands 3, 4 and 6 for LST, and variations of these for other outputs. Instead, the landsat 8 option uses bands 4, 5 and 10. This is due to the same data being assigned different band numbers in the two cases.
