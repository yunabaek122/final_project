import pandas as pd 
import geopandas as gpd 
import matplotlib.pyplot as plt
from shiny import App, render, ui, reactive
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
import numpy as np
import os

# ========================================================
# Loading Datasets & Cleaning
# ========================================================
# Yuna
path = "/Users/yunabaek/Desktop/3. Python II/final_project/Data"
# Sumner
# path = r"C:\Users\12019\OneDrive - The University of Chicago\Documents\GitHub\final_project\Data\"
# Mithila
# path = "/Users/mithilaiyer/Documents/GitHub/final_project/shp"

# Cooling center
centers_fp = os.path.join(path, "Cooling/Cooling_Centers_-_District_of_Columbia.shp")
cooling_centers = gpd.read_file(centers_fp)
clean_cc = cooling_centers[(cooling_centers["USER_Open_"] == "All") & (~cooling_centers["USER_Hours"].str.contains('closed', case=False, na=False))]
empty_DC = gpd.read_file(os.path.join(path, "Wards_from_2022/Wards_from_2022.shp"))

# Heat data + cooling centers data + ward data 
heat_dc = os.path.join(path, "Heat_Sensitivity_Exposure_Index.shp")
cc_dc = os.path.join(path, "Cooling_Centers_-_District_of_Columbia.shp")
wards_dc = os.path.join(path, "Wards_from_2022.shp")
heat_dc['ASTHMA'] = heat_dc['ASTHMA'].round(1)
cc_dc.plot(marker='o', color = "green", figsize=(10,8), alpha=0.5)
cc_dc = cc_dc.to_crs(heat_dc.crs)
#Variable cleaning
heat_dc['HSI'] = heat_dc['HSI'].apply(lambda x: x if str(x).startswith('0') else np.nan)
heat_dc['ASTHMA'] = heat_dc['ASTHMA'].round(1)

# POC, elderly
acs_shp = gpd.read_file(os.path.join(path, "ACS_5-Year_Demographic_Characteristics_DC_Census_Tract/ACS_5-Year_Demographic_Characteristics_DC_Census_Tract.shp"))
acs_shp = acs_shp.to_crs(empty_DC.crs)
acs_shp['poc'] = (acs_shp['DP05_0033E'] - acs_shp['DP05_0079E']) / acs_shp['DP05_0033E']
acs_shp['elderly'] = acs_shp['DP05_0024E'] / acs_shp['DP05_0001E']

# Income, disability
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


# ========================================================
# Creating Shiny App
# ========================================================

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_radio_buttons(
            id="plot_selector",
            label="Select Social Plot:",
            choices={
                "poc": "People of Color",
                "elderly": "Elderly Population",
                "disability": "Population with Disabilities",
                "asthma": "Asthma"
            },
            selected="poc"
        ),
        ui.input_checkbox_group(
            id="center_type",
            label="Overlay Cooling Center Type:",
            choices=types_select,
            selected=[],  # Default: nothing selected
        ),
        title="Layers",
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Layered Map"),
            ui.output_plot("layered_plot"),  # Unified layered plot
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
        if not input.center_type():  # If no selection, return an empty GeoDataFrame
            return clean_cc.iloc[0:0]
        else: 
            return clean_cc[clean_cc["USER_Type"].isin(input.center_type())]

    # @render.plot
    # def environ_plot():
    #     fig, ax = plt.subplots(figsize=(12, 10))
    #     empty_DC.plot(ax=ax, edgecolor="black", facecolor="none", label="Wards")

    #     # Ensure CRS alignment
    #     center_subset_fix = center_subset().to_crs(empty_DC.crs)

    #     # Plot cooling centers with conditional coloring
    #     if "All" in input.center_type(): 
    #         for c_type, color in type_colors.items(): 
    #             subset = center_subset_fix[center_subset_fix["USER_Type"] == c_type]
    #             subset.plot(ax=ax, alpha=0.7, color=color, marker="o", label=c_type, legend=True)
    #     else:
    #         for c_type in input.center_type(): 
    #             subset = center_subset_fix[center_subset_fix["USER_Type"] == c_type]
    #             subset.plot(ax=ax, alpha=0.7, color=type_colors[c_type], marker="o", label=c_type, legend=True)

    #     ax.set_title(f'Cooling Centers by Type', fontsize=14)
    #     ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=1, fontsize="small")

    #     return fig

    # Unified layered plot
    @render.plot
    def layered_plot():
        selected_plot = input.plot_selector()  # Get the selected social plot
        fig, ax = plt.subplots(figsize=(12, 10))

        # Plot the selected social graph
        if selected_plot == "poc":
            acs_shp.plot(
                column='poc', 
                cmap='YlGnBu',
                legend=True,
                legend_kwds={
                    'shrink': 0.5,
                    'pad': 0.05
                },
                ax=ax,
                edgecolor='black',
                linewidth=0.2
            )
            ax.set_title('People of Color', fontsize=12, fontweight='bold')

        elif selected_plot == "elderly":
            acs_shp.plot(
                column='elderly', 
                cmap='YlGnBu',
                legend=True,
                legend_kwds={
                    'shrink': 0.5,
                    'pad': 0.05
                },
                ax=ax,
                edgecolor='black',
                linewidth=0.2
            )
            ax.set_title('Population of Older Adults', fontsize=12, fontweight='bold')

        elif selected_plot == "disability":
            social_shp.plot(
                column='disability', 
                cmap='YlGnBu',
                legend=True,
                legend_kwds={
                    'shrink': 0.5,
                    'pad': 0.05
                },
                ax=ax,
                edgecolor='black',
                linewidth=0.2
            )
            ax.set_title('Population with Disabilities', fontsize=12, fontweight='bold')

        elif selected_plot == "asthma":
            #Asthma with ward numbers 
            heat_dc.plot(column='ASTHMA', ax=ax, legend=True,
                        cmap='Reds',
                        linewidth=0.8, edgecolor='0.8', alpha=0.7)

            cc_dc.plot(marker='o', color='red', ax=ax, alpha=0.5, markersize=50)
            wards_dc.plot(edgecolor="black", facecolor="none", ax=ax, linewidth=1)

            wards_dc['centroid'] = wards_dc.geometry.centroid

            for idx, row in wards_dc.iterrows():
                centroid_x, centroid_y = row['centroid'].x, row['centroid'].y
                ax.text(centroid_x, centroid_y, str(row['WARD']), fontsize=14, ha='center', color='black', fontweight='bold')

            ax.set_title("Asthma and Cooling Centers Accessibility by Ward", fontsize=16)

        # Overlay ward boundaries
        empty_DC.plot(
            ax=ax,
            edgecolor='black',
            facecolor='none',
            linewidth=0.5
        )

        # Overlay cooling centers (if any are selected)
        if not center_subset().empty:
            center_subset_fix = center_subset().to_crs(empty_DC.crs)
            cooling_centers_plot = center_subset_fix.plot(
                ax=ax,
                column="USER_Type",
                alpha=0.7,
                cmap="tab10",
                legend=False  # Disable automatic legend for GeoPandas
            )

            # Create a manual legend
            unique_types = center_subset_fix["USER_Type"].unique()
            colors = plt.cm.tab10(range(len(unique_types)))
            legend_patches = [
                Patch(color=colors[i], label=type_) for i, type_ in enumerate(unique_types)
            ]

            # Add the legend
            ax.legend(
                handles=legend_patches,
                title="Cooling Center Types",
                loc="upper right",  # Adjust legend location
                bbox_to_anchor=(1, 0.9)  # Place the legend at the desired position
            )

        # Final adjustments
        ax.set_axis_off()
        plt.tight_layout()
        return fig


app = App(app_ui, server)