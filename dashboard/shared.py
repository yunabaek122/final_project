from pathlib import Path

import geopandas as gpd

app_dir = Path(__file__).parent

cooling_centers = gpd.read_file(app_dir / "Cooling_Centers_-_District_of_Columbia\Cooling_Centers_-_District_of_Columbia.shp")
empty_DC=gpd.read_file(app_dir/ "Wards_from_2022\Wards_from_2022.shp")
