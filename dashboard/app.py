import pandas as pd 
import geopandas as gpd 
import matplotlib.pyplot as plt
from shiny import App, render, ui, reactive
from matplotlib.colors import ListedColormap
import numpy as np

#Load and clean datasets
centers_fp = r"C:\Users\12019\OneDrive - The University of Chicago\Documents\GitHub\final_project\dashboard\Data\Cooling_Centers_-_District_of_Columbia\Cooling_Centers_-_District_of_Columbia.shp"
cooling_centers = gpd.read_file(centers_fp)
clean_cc = cooling_centers[(cooling_centers["USER_Open_"] == "All") & (~cooling_centers["USER_Hours"].str.contains('closed', case=False, na=False))]

dc_fp = r"C:\Users\12019\OneDrive - The University of Chicago\Documents\GitHub\final_project\dashboard\Data\Wards_from_2022\Wards_from_2022.shp"
empty_DC = gpd.read_file(dc_fp)

#Clean CC dataset
clean_cc = cooling_centers[(cooling_centers["USER_Open_"] == "All") & (~cooling_centers["USER_Hours"].str.contains('closed', case=False, na=False))]

#Create the CC type options  
cc_types = clean_cc["USER_Type"].unique().tolist()
types_select = ["All"] + cc_types

#Create a color map for each CC type option
color_map = plt.get_cmap("tab10")
type_colors = {c_type: color_map(i / len(cc_types)) for i, c_type in enumerate(cc_types)}

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_checkbox_group(
            id="center_type",
            label="Select cooling center type:",
            choices = types_select,
            selected=["All"],
        ),
        title="Types",
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Environmental Factors"),
            ui.output_plot("environ_plot"),
            full_screen=True,
        ),
        ui.card(
            ui.card_header("Social Factors"),
            ui.output_plot("social_plot"),
            full_screen=True,
        )
    ),
    ui.include_css(r"C:\Users\12019\OneDrive - The University of Chicago\Documents\GitHub\final_project\dashboard\styles.css"),
    title="Cooling Centers in DC Dashboard",
    fillable=True,
)


def server(input, output, session):
    @reactive.calc
    def center_subset(): 
        if "All" in input.center_type(): 
            return clean_cc
        else: 
            return clean_cc[clean_cc["USER_Type"].isin(input.center_type())]

    @render.plot
    def environ_plot():
        fig, ax = plt.subplots(figsize=(12,10))
        empty_DC.plot(ax=ax, edgecolor="black", facecolor="none", label = "Wards")

        #Make sure CRS is aligned 
        center_subset_fix = center_subset().to_crs(empty_DC.crs)

        #Plot with conditional coloring 
        if "All" in input.center_type(): 
            for c_type, color in type_colors.items(): 
                subset = center_subset_fix[center_subset_fix["USER_Type"] == c_type]
                subset.plot(ax=ax, alpha=0.7, color=color, marker="o", label=c_type, legend=True)

        else:
            for c_type in input.center_type(): 
                subset = center_subset_fix[center_subset_fix["USER_Type"] == c_type]
                subset.plot(ax=ax, alpha=0.7, color=type_colors[c_type], marker="o", label=c_type, legend=True)

        ax.set_title(f'Cooling Centers by Type', fontsize=14)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5,-0.1), ncol=1, fontsize="small")

        return fig

    @render.plot
    def social_plot(): 
        return "Empty"

    @render.data_frame
    def centers_prop_table(): 
        return "Test"


app = App(app_ui, server)