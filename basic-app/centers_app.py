import pandas as pd 
import geopandas as gpd 
import matplotlib.pyplot as plt
from shiny import App, render, ui, reactive
from matplotlib.colors import ListedColormap
import numpy as np

#Load clean datasets
centers_fp = r"C:\Users\12019\OneDrive - The University of Chicago\Documents\GitHub\final_project\basic-app\Cooling_Centers_-_District_of_Columbia\Cooling_Centers_-_District_of_Columbia.shp"
cooling_centers = gpd.read_file(centers_fp)
clean_cc = cooling_centers[(cooling_centers["USER_Open_"] == "All") & (~cooling_centers["USER_Hours"].str.contains('closed', case=False, na=False))]

dc_fp = r"C:\Users\12019\OneDrive - The University of Chicago\Documents\GitHub\final_project\basic-app\Wards_from_2022\Wards_from_2022.shp"
empty_DC = gpd.read_file(dc_fp)

#Create the proportions table 
counts = clean_cc["USER_Type"].value_counts()
percentages = counts / counts.sum() * 100
centers_table = pd.DataFrame({"Type": counts.index, "Counts": counts, "Percentage": percentages.round(2)})

#Get the dropdown options 
cc_types = clean_cc["USER_Type"].unique().tolist()
types_dropdown = ["All"] + cc_types

#Create a color map 
color_map = plt.get_cmap("tab10")
type_colors = {c_type: color_map(i / len(cc_types)) for i, c_type in enumerate(cc_types)}

#UI section
app_ui = ui.page_fluid(
    ui.panel_title("Cooling Centers in DC"),
    ui.input_select(
        id="center_type", 
        label="Select center type:",
        choices = types_dropdown, 
        selected = "All"
        ), 
    ui.output_plot("centers_plot"),
    ui.output_table("centers_prop_table")
)

#Server section 
def server(input, output, session):
    @reactive.calc 
    def center_subset(): 
        if input.center_type() == "All": 
            return clean_cc
        return clean_cc[clean_cc["USER_Type"] == input.center_type()]
    
    @render.plot
    def centers_plot(): 
        fig, ax = plt.subplots(figsize=(10,8))
        empty_DC.plot(ax=ax, edgecolor="black", facecolor="none", label = "Wards")

        #Make sure CRS is aligned 
        center_subset_fix = center_subset().to_crs(empty_DC.crs)

        #Plot with conditional coloring 
        if input.center_type() == "All": 
            for c_type, color in type_colors.items(): 
                subset = center_subset_fix[center_subset_fix["USER_Type"] == c_type]
                subset.plot(ax=ax, alpha=0.7, color=color, marker="o", label=c_type, legend=True)

            ax.legend(loc="upper center", bbox_to_anchor=(0.5,-0.1), ncol=2, fontsize="small")

        else:
            selected_type = input.center_type()
            center_subset_fix.plot(ax=ax, alpha=0.7, color=type_colors[selected_type], marker="o", label=selected_type)

        ax.set_title(f'Cooling Centers by Type: {input.center_type()}', fontsize=14)
        return fig

    @render.table
    def centers_prop_table(): 
        selected_type = input.center_type()

        #Filter based on the type that's selected
        if selected_type == "All": 
            return centers_table
        else: 
            return centers_table.loc[[selected_type]]

app = App(app_ui, server)
