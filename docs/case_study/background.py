# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# <p style="page-break-after:always;"></p>
#
# # Background
#
# The processing and inversion work focuses on ground and airborne datasets simulated over the Flin Flon model. Extensive drilling has been done over the deposit, as shown in [Figure 2](global_map).
#
# ```{figure} ./images/map_flinflon.png
# ---
# height: 400px
# name: global_map
# ---
# Geological map and drillholes of the Flin Flon deposit. Outline of the main ore body (red) is shown for reference.
# ```
#
# The synthetic block model was generated from open-source data made available by [Natural Resources Canada (NRCan)](https://ostrnrcan-dostrncan.canada.ca/entities/publication/73d767d8-ee1c-4bab-a2da-52dcf83faa06). The VMS deposit is hosted in rhyolite unit as indicated by yellow voxels [Figure 3](ore_body).
#
# ```{figure} ./images/ore_body.png
# ---
# height: 400px
# name: ore_body
# ---
# Discrete geological model of the ore deposit and host units.
# ```
#
#  [Table 1](phys_prop) summarizes the relative physical properties of the main rock units in the area.
# The VMS ore is expected to be more conductive, dense and magnetic than host rhyolite unit. The background mafic rocks are generally non-magnetic and have moderate densities and resistivities. A thick (40 m) overburden layer of relatively low density and  low resistivity covers the survey area.
#
#
# ```{table} Summary of expected physical properties
# :name: phys_prop
# | Unit | Density (g/cc) | Magnetic Susceptibility (SI) | Resistivity (Ohm.m) |
# | :--- | :--- | :---- | :---- |
# | Rhyolite |  low    | low      | high     |
# | Chloritic Schist |  moderate    | low      | moderate     |
# | Mafic Volcanics |  moderate    | low      | moderate     |
# | Mafic Dykes |  moderate    | low      | moderate     |
# | Host Mafic |  moderate    | low      | moderate     |
# | Basalt |  moderate    | moderate      | low     |
# | Ore |  high    | high      | low     |
# | Overburden |  low    | low      | moderate     |
# | Tailings |  low    | low      | low     |
# ```
