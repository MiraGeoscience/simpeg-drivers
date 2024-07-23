# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# <p style="page-break-after:always;"></p>
#
# # The Set Up
#
# This tutorial on geophysical inversion is framed around a well-known copper-zinc VMS deposit - the Flin Flon mine in northern Manitoba, Canada. Our goal is to provided a step-by-step process to invert data from various geophysical methods and to test their resolving capabilities within a semi-realistic exploration context.
#
# ```{figure} ./images/setup_flinflon.png
# ---
# height: 400px
# name: setup_flinflon
# ---
# Discrete geological and physical properties for the simplified Flin Flon model.
# ```
#
# The local geology of Flin Flon consists mainly of basalt and mafic volcanic formations (green and blue), with discrete occurrences of rhyolite units (yellow) that host the mineralization as shown in [Figure X](setup_flinflon).
# The entire region was later deformed by large tectonic events that over-thursted, folded and faulted the stratigraphy in its current form. The mineralization occurs along thin lences dipping steeply towards the South-East.
#
# The area has been studied extensively over the years, yielding large amount of petrophysical data made available by [Natural Resources Canada (NRCan)](https://ostrnrcan-dostrncan.canada.ca/entities/publication/73d767d8-ee1c-4bab-a2da-52dcf83faa06), as shown in [Figure 3](global_map).
#
# ```{figure} ./images/map_flinflon.png
# ---
# height: 400px
# name: global_map
# ---
# Geological map and drillholes of the Flin Flon deposit. Outline of the main ore body (red) is shown for reference.
# ```
#
# [Table 1](phys_prop) summarizes the physical property contrasts of the main rock units in the area.
# The mineralization is expected to be much more conductive, dense and magnetic than the host rhyolite unit. The background mafic rocks are generally non-magnetic and moderately dense and resistive. We omitted all late-stage intrusives from the modeling for simplicity.
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
# | Ore |  high    | high      | very low     |
# | Overburden |  low    | low      | moderate     |
# | Tailings |  low    | low      | low     |
#
# ```
#
# From this simplified (conceptual) model of Flin Flon, we created a 3D petrophysical model around the mineralization [Figure X](ore_body). We added a thick (40 m) overburden layer (tailings) of relatively low density and low resistivity to test the depth of penetration of the various survey types.
# ```{figure} ./images/ore_body.png
# ---
# height: 400px
# name: ore_body
# ---
# Discrete geological and physical properties for the simplified Flin Flon model [Download here](https://github.com/MiraGeoscience/simpeg-drivers/blob/develop/simpeg_drivers-assets/inversion_demo.geoh5).
# ```
#
# This model was used to generate all the synthetic data used in this tutorial. [Figure X](project_area) shows the layout of the various ground and airborne surveys used in this tutorial.
#
#
# ```{figure} ./images/project_area.png
#
# ---
# scale: 50%
# name: project_area
# ---
# Data coverage for the ground gravity (black), airborne gravity gradiometry (red), airborne magnetics and tipper (green) and direct-current (blue) surveys. Outline of the ore shell (gray) is shown for reference.
# ```
