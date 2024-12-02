from shiny import App, render, ui, reactive
import geopandas as gpd
import os
import matplotlib.pyplot as plt
import numpy as np
import json
import pandas as pd
path = "/Users/yunabaek/Desktop/3. Python II/final_project/Data"

# poverty, elderly, disability
acs_shp = gpd.read_file(os.path.join(path, "ACS_5-Year_Demographic_Characteristics_DC_Census_Tract/ACS_5-Year_Demographic_Characteristics_DC_Census_Tract.shp"))
acs_shp['poc'] = (acs_shp['DP05_0033E'] - acs_shp['DP05_0079E']) / acs_shp['DP05_0033E']
empty_DC = gpd.read_file(os.path.join(path, "Wards_from_2022/Wards_from_2022.shp"))

# income / poverty
social_shp = gpd.read_file(os.path.join(path,"ACS_5-Year_Social_Characteristics_DC_Census_Tract/ACS_5-Year_Social_Characteristics_DC_Census_Tract.shp"))

app_ui = ui.page_fluid(
    ui.panel_title("DC Plots"),
    ui.output_plot("poc_plot")
)

def server(input, output, session):
    @render.plot
    def poc_plot():
        fig, ax = plt.subplots(figsize=(12, 10))

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

    # Overlay ward boundaries (empty_DC)
        empty_DC.plot(
            ax=ax, 
            edgecolor='black',
            facecolor='none',
            linewidth=0.5
        )

        ax.set_axis_off()
        ax.set_title('People of Color', fontsize=12, fontweight='bold')
        fig.subplots_adjust(top=0.85)

        return fig

app = App(app_ui, server)

