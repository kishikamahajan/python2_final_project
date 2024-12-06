import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import altair as alt
from shiny import App, render, ui, reactive
from shinywidgets import render_altair, output_widget

# Data for forest cover analysis (Page 1)
vcf_india = pd.read_csv("/Users/kishikamahajan/Desktop/python2_final_project/shrug-vcf-csv/vcf_shrid.csv")
location_shrid = pd.read_csv("/Users/kishikamahajan/Desktop/python2_final_project/shrug-shrid-keys-csv/shrid_loc_names.csv")
coordinates_shrid = pd.read_csv("/Users/kishikamahajan/Desktop/python2_final_project/shrug-shrid-keys-csv/shrid2_spatial_stats.csv")

vcf_india_master = pd.merge(vcf_india, location_shrid, on="shrid2")
vcf_india_master = pd.merge(vcf_india_master, coordinates_shrid, on="shrid2")
vcf_india_master_gdf = gpd.GeoDataFrame(
    vcf_india_master,
    geometry=gpd.points_from_xy(vcf_india_master["longitude"], vcf_india_master["latitude"]),
    crs="EPSG:4326"
)

# Data for tourism analysis (Page 2)
visitor_data = pd.read_excel("/Users/kishikamahajan/Desktop/python2_final_project/National Park Visit Data.xlsx")
visitor_data_long = visitor_data.melt(id_vars="Year", var_name="Park", value_name="Visitors")

# Forest cover page UI
forest_cover_page = ui.page_fluid(
    ui.panel_title("Forest Cover in India"),
    ui.input_slider(
        id="year_slider",
        label="Select Year",
        min=2001,
        max=2020,
        step=1,
        value=2001
    ),
    ui.output_plot("final_map_chart")
)

# Tourism analysis page UI
tourism_page = ui.page_fluid(
    ui.h2("National Park Visitor Trend"),
    ui.input_switch("switch_button", "Toggle to see comparative chart", value=False),
    ui.output_ui("park_selector"),
    output_widget("visitor_plot")
)
# Main app UI
app_ui = ui.page_navbar(
    ui.nav_panel("Forest Cover", forest_cover_page),
    ui.nav_panel("Tourism Analysis", tourism_page),
    title="National Park Data Explorer"
)

# Server function
def server(input, output, session):
    # Forest cover server logic
    @reactive.Calc
    def filtered_data():
        selected_year = input.year_slider()
        return vcf_india_master_gdf[vcf_india_master_gdf["year"] == selected_year]

    @render.plot(alt="Forest cover map of India")
    def final_map_chart():
        data = filtered_data()
        fig, ax = plt.subplots(figsize=(20, 20))
        ax.set_aspect('equal')
        ax.scatter(
            data["longitude"], 
            data["latitude"],
            c=data["vcf_mean"],
            cmap='Greens',
            alpha=0.6,
            s=50
        )
        ax.set_xlim(65, 98)  # Longitude limits
        ax.set_ylim(8, 37)   # Latitude limits
        plt.tight_layout()
        return fig

    # Tourism analysis server logic
    @reactive.Calc
    def tourism_filtered_data():
        if input.switch_button():
            return visitor_data_long
        else:
            return visitor_data_long[visitor_data_long['Park'] == input.Park()]
    
    @output
    @render_altair
    def visitor_plot():
        selected_data = tourism_filtered_data()
        if input.switch_button():
            chart = (
                alt.Chart(selected_data)
                .mark_line(point=True)
                .encode(
                    x='Year:O',
                    y='Visitors:Q',
                    color='Park:N',
                    tooltip=['Year', 'Park', 'Visitors']
                )
                .properties(
                    title="Comparative Visitor Trends",
                    width=600,
                    height=400
                )
            )
        else:
            chart = (
                alt.Chart(selected_data)
                .mark_line(point=True)
                .encode(
                    x='Year:O',
                    y='Visitors:Q',
                    tooltip=['Year', 'Visitors'],
                    color=alt.value('blue')
                )
                .properties(
                    title=f"Visitor Trends for {input.Park()}",
                    width=600,
                    height=400
                )
            )
        return chart

    @output
    @render.ui
    def park_selector():
        if not input.switch_button():
            return ui.input_select(
                "Park",
                "Select National Park:",
                choices=list(visitor_data_long['Park'].unique())
            )
        else:
            return ui.div()  # Return an empty div when the switch is on

# Create app
app = App(app_ui, server)
