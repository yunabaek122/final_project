import pandas as pd 
import geopandas as gpd 
import matplotlib.pyplot as plt
from shiny import App, render, ui, reactive
from matplotlib.colors import ListedColormap
import numpy as np
import os

#Load and clean datasets
path = "/Users/yunabaek/Desktop/3. Python II/final_project/Data"

centers_fp = os.path.join(path, "Cooling/Cooling_Centers_-_District_of_Columbia.shp")
cooling_centers = gpd.read_file(centers_fp)
clean_cc = cooling_centers[(cooling_centers["USER_Open_"] == "All") & (~cooling_centers["USER_Hours"].str.contains('closed', case=False, na=False))]

empty_DC = gpd.read_file(os.path.join(path, "Wards_from_2022/Wards_from_2022.shp"))


# poverty, elderly
acs_shp = gpd.read_file(os.path.join(path, "ACS_5-Year_Demographic_Characteristics_DC_Census_Tract/ACS_5-Year_Demographic_Characteristics_DC_Census_Tract.shp"))
acs_shp = acs_shp.to_crs(empty_DC.crs)
acs_shp['poc'] = (acs_shp['DP05_0033E'] - acs_shp['DP05_0079E']) / acs_shp['DP05_0033E']
acs_shp['elderly'] = acs_shp['DP05_0024E'] / acs_shp['DP05_0001E']

# income / poverty, disability
social_shp = gpd.read_file(os.path.join(path,"ACS_5-Year_Social_Characteristics_DC_Census_Tract/ACS_5-Year_Social_Characteristics_DC_Census_Tract.shp"))
social_shp['disability'] = social_shp['DP02_0072E'] / social_shp['DP02_0071E']

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
            choices=types_select,
            selected=["All"],
        ),
        ui.input_radio_buttons(
            id="plot_selector",  # toggle
            label="Select Plot:",
            choices={"poc": "People of Color", 
                     "elderly": "Elderly Population",
                      "disability": "Population with Disabilities"},
            selected="poc"
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
            ui.output_plot("social_plot"),  # Unified plot for all social options
            full_screen=True,
        )
    ),
    ui.include_css(os.path.join(path, "styles.css")),
    title="Cooling Centers in DC Dashboard",
    fillable=True,
)


def server(input, output, session):
    # Reactive calculation for filtering cooling centers
    @reactive.calc
    def center_subset(): 
        if "All" in input.center_type(): 
            return clean_cc
        else: 
            return clean_cc[clean_cc["USER_Type"].isin(input.center_type())]

    # Environmental factors plot (existing logic)
    @render.plot
    def environ_plot():
        fig, ax = plt.subplots(figsize=(12, 10))
        empty_DC.plot(ax=ax, edgecolor="black", facecolor="none", label="Wards")

        # Ensure CRS alignment
        center_subset_fix = center_subset().to_crs(empty_DC.crs)

        # Plot cooling centers with conditional coloring
        if "All" in input.center_type(): 
            for c_type, color in type_colors.items(): 
                subset = center_subset_fix[center_subset_fix["USER_Type"] == c_type]
                subset.plot(ax=ax, alpha=0.7, color=color, marker="o", label=c_type, legend=True)
        else:
            for c_type in input.center_type(): 
                subset = center_subset_fix[center_subset_fix["USER_Type"] == c_type]
                subset.plot(ax=ax, alpha=0.7, color=type_colors[c_type], marker="o", label=c_type, legend=True)

        ax.set_title(f'Cooling Centers by Type', fontsize=14)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=1, fontsize="small")

        return fig

    # Toggle among social plots
    @render.plot
    def social_plot(): 
        selected_plot = input.plot_selector()  # Get the selected plot type
        fig, ax = plt.subplots(figsize=(12, 10))
        
        if selected_plot == "poc":
            # Plot People of Color
            acs_shp.plot(
                column='poc', 
                cmap='YlGnBu',
                legend=True,
                legend_kwds={
                    'label': 'Proportion',
                    'orientation': 'horizontal',
                    'shrink': 0.5,
                    'pad': 0.05
                },
                ax=ax
            )
            ax.set_title('People of Color', fontsize=12, fontweight='bold')
        
        elif selected_plot == "elderly":
            # Plot Elderly Population
            acs_shp.plot(
                column='elderly', 
                cmap='YlGnBu',
                legend=True,
                legend_kwds={
                    'label': 'Proportion',
                    'orientation': 'horizontal',
                    'shrink': 0.5,
                    'pad': 0.05
                },
                ax=ax
            )
            ax.set_title('Population of Older Adults', fontsize=12, fontweight='bold')

        elif selected_plot == "disability":
            # Plot Population with Disabilities
            social_shp.plot(
                column='disability', 
                cmap='YlGnBu',
                legend=True,
                legend_kwds={
                    'label': 'Proportion',
                    'orientation': 'horizontal',
                    'shrink': 0.5,
                    'pad': 0.05
                },
                ax=ax,
                edgecolor='black',
                linewidth=0.2
            )
            ax.set_title('Population with Disabilities', fontsize=12, fontweight='bold')


        # Overlay ward boundaries
        empty_DC.plot(
            ax=ax,
            edgecolor='black',
            facecolor='none',
            linewidth=0.5
        )

        ax.set_axis_off()
        fig.subplots_adjust(top=0.85)

        return fig


app = App(app_ui, server)