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
heat_dc = gpd.read_file(os.path.join(path, "Heat_Sensitivity_Exposure_Index.shp"))
cc_dc = gpd.read_file(os.path.join(path, "Cooling_Centers_-_District_of_Columbia.shp"))
wards_dc = gpd.read_file(os.path.join(path, "Wards_from_2022.shp"))
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

# Disability
social_shp = gpd.read_file(os.path.join(path,"ACS_5-Year_Social_Characteristics_DC_Census_Tract/ACS_5-Year_Social_Characteristics_DC_Census_Tract.shp"))
social_shp['disability'] = social_shp['DP02_0072E'] / social_shp['DP02_0071E']

# Poverty
poverty_shp = gpd.read_file(os.path.join(path, "ACS_5-Year_Economic_Characteristics_DC_Ward/ACS_5-Year_Economic_Characteristics_DC_Ward.shp"))
poverty_shp = poverty_shp.rename(columns={'DP03_0119P': 'poverty'})


#Clean CC dataset
clean_cc = cooling_centers[(cooling_centers["USER_Open_"] == "All") & (~cooling_centers["USER_Hours"].str.contains('closed', case=False, na=False))]

#Create the CC type options  
cc_types = clean_cc["USER_Type"].unique().tolist()
types_select = cc_types

#Create a color map for each CC type option
color_map = plt.get_cmap("tab10")
type_colors = {c_type: color_map(i / len(cc_types)) for i, c_type in enumerate(cc_types)}


# ========================================================
# Creating Shiny App
# ========================================================

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_radio_buttons(
            id="social_plot_selector",
            label="Select Social Plot:",
            choices={
                "poc": "People of Color",
                "elderly": "Elderly Population",
                "poverty" : "Poverty",
                "disability": "Population with Disabilities",
                "asthma": "Asthma"
            },
            selected="poc"
        ),
        ui.input_radio_buttons(
            id="environmental_plot_selector",
            label="Select Environmental Plot:",
            choices={
                "HEI": "Heat Exposure Index",
                "HSI": "Heat Sensitivity Index",
                "P_TREECOVE": "Tree Cover"
            },
            selected="HEI"
        ),
        ui.input_checkbox_group(
            id="center_type",
            label="Select type of center (multiple allowed):",
            choices=types_select,
            selected=types_select,
        ),
        ui.input_switch(
            id="toggle_ward",
            label="Show Ward Information",
            value=False
        ),
        title="Plot Layers",
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
        ),
    ),
    ui.include_css(os.path.join(path, "styles.css")),
    title="Cooling Centers in DC Dashboard",
    fillable=True,
)


def server(input, output, session):
    @reactive.calc
    def center_subset(): 
        """Filter cooling centers based on user selection."""
        if "All" in input.center_type(): 
            return clean_cc
        return clean_cc[clean_cc["USER_Type"].isin(input.center_type())]

    def add_borders_and_labels(ax):
        """Add ward borders and labels if toggle is enabled."""
        if input.toggle_ward(): 
            # Add ward borders
            empty_DC.plot(ax=ax, edgecolor="black", facecolor="none", linewidth=0.5)

            # Add ward labels
            empty_DC["centroid"] = empty_DC.geometry.centroid
            for idx, row in empty_DC.iterrows():
                ax.text(
                    row["centroid"].x,
                    row["centroid"].y,
                    str(row["WARD"]),
                    fontsize=10,
                    ha="center",
                    color="black",
                    fontweight="bold",
                )
    
    def add_cooling_centers(ax):
        """Add cooling center points on top of the map."""
        selected_df = center_subset()
        if selected_df.empty: 
            return  # Do nothing if there are no selected cooling centers

        # Align CRS
        selected_df = selected_df.to_crs(empty_DC.crs)

        # Plot cooling center points by type using type_colors
        for c_type, color in type_colors.items():
            subset = selected_df[selected_df["USER_Type"] == c_type]
            if not subset.empty:
                subset.plot(
                    ax=ax,
                    color="white",
                    markersize=55,
                    alpha=1.0,
                    label=None
                )
                # Plot actual dot
                subset.plot(
                    ax=ax,
                    color=color,  # Use color from type_colors
                    markersize=40,  # Original size for the dot
                    alpha=1.0,
                    label=c_type  # Exclude from the legend
                )
                
    def add_legend(ax, selected_df):
        """Add legend at the bottom center of the plot."""
        unique_types = selected_df["USER_Type"].unique()
        legend_patches = [
            Patch(color=type_colors[type_], label=type_)
            for type_ in unique_types if type_ in type_colors
        ]
        ax.legend(
            handles=legend_patches,
            title="Cooling Center Types",
            loc="lower center",
            bbox_to_anchor=(0.5, -0.2),
            ncol=2,
            fontsize="small",
            title_fontsize="small",
            frameon=False,
        )

    # def customize_colorbar(cbar, vmin, vmax, label):
    #     """
    #     Customize color bar by setting ticks, labels, and title.
    #     """
    #     cbar.ax.set_title(label, loc="center", fontsize=10, fontweight="bold", pad=10)  # Title for the color bar
    #     cbar.set_ticks([vmin, vmax])  # Set min and max ticks
    #     cbar.ax.set_yticklabels([f"{vmin:.1f}", f"{vmax:.1f}"], fontsize=9)  # Adjust tick labels


    @render.plot
    def environ_plot():
        selected_env_plot = input.environmental_plot_selector()
        fig, ax = plt.subplots(figsize=(10, 8))

        if selected_env_plot == "HEI":
            heat_dc.plot(column="HEI", cmap="viridis", alpha=0.8, legend=True, ax=ax, edgecolor="0.8", linewidth=0.5)
            ax.set_title("Heat Exposure Index", fontsize=14, fontweight="bold")

        elif selected_env_plot == "HSI":
            heat_dc.plot(column="HSI", cmap="coolwarm", legend=True, ax=ax, edgecolor="0.8", linewidth=0.5)
            ax.set_title("Heat Sensitivity Index", fontsize=14, fontweight="bold")

        elif selected_env_plot == "P_TREECOVE":
            heat_dc.plot(column="P_TREECOVE", cmap="Greens", legend=True, ax=ax, edgecolor="0.8", linewidth=0.5)
            ax.set_title("Tree Cover", fontsize=14, fontweight="bold")

        add_borders_and_labels(ax)
        add_cooling_centers(ax) 

        selected_df = center_subset()
        if not selected_df.empty:
            add_legend(ax, selected_df)

        ax.set_axis_off()
        plt.tight_layout()
        return fig

    @render.plot
    def social_plot():
        selected_social_plot = input.social_plot_selector()
        fig, ax = plt.subplots(figsize=(10, 8))

        if selected_social_plot == "poc":
            acs_shp.plot(column="poc", cmap="YlGnBu", alpha=0.8, legend=True, ax=ax, edgecolor="0.8", linewidth=0.2)
            ax.set_title("People of Color", fontsize=14, fontweight="bold")

        elif selected_social_plot == "poverty":
            poverty_shp.plot(column='poverty', cmap="YlGnBu", legend=True, ax=ax, edgecolor="0.8", linewidth=0.2)
            ax.set_title("Poverty", fontsize=14, fontweight="bold")


        elif selected_social_plot == "elderly":
            acs_shp.plot(column="elderly", cmap="YlGnBu", legend=True, ax=ax, edgecolor="0.8", linewidth=0.2)
            ax.set_title("Population of Older Adults", fontsize=14, fontweight="bold")

        elif selected_social_plot == "disability":
            social_shp.plot(column="disability", cmap="YlGnBu", legend=True, ax=ax, edgecolor="0.8", linewidth=0.2)
            ax.set_title("Population with Disabilities", fontsize=14, fontweight="bold")

        elif selected_social_plot == "asthma":
            heat_dc.plot(column="ASTHMA", cmap="Reds", legend=True, ax=ax, edgecolor="0.8", linewidth=0.5)
            ax.set_title("Asthma", fontsize=14, fontweight="bold")

        add_borders_and_labels(ax)
        add_cooling_centers(ax) 

        selected_df = center_subset()
        if not selected_df.empty:
            add_legend(ax, selected_df)

        ax.set_axis_off()
        plt.tight_layout()
        return fig



app = App(app_ui, server)