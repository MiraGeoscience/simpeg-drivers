# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.14.6
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# <p style="page-break-after:always;"></p>
#
# # Background
#
# The processing and inversion work focuses on airborne datasets acquired over the Carajas - Block 3 area ([Figure 3](global_map)). The region contains several iron-ore deposits currently exploited by Vale. This case study focuses on the southern portion of Block 3, over a known ore body currently under investigation by the exploration team.
#
# ```{figure} ./images/map_carajas.png
# ---
# height: 400px
# name: global_map
# ---
# Satellite image over the Carajas - Block 3 area. Flight lines (black) of the HeliTEM survey and outline of the expected jaspelite (blue) and hematite (red) ore bodies are shown for reference.
# ```
#
# Limited drilling has been done over the Western half of the deposit, as shown in [Figure 4](ore_body).
# The iron formation is made up of units ranging from jaspelite (JP) in variable degree of alteration (supergene alteration) to compact hematite (HC) and friable hematite (HF) units. On the top of it, there is the occurrence of the extreme alteration product of the iron body, forming an iron crust, called "structural canga" (CE). For Vale, the iron ore is composed by HF and CE units. The whole iron formation is hosted in a mafic unit, also with variable degree of supergene alteration, which is composed by the non-alterated mafic (MS), semi-decomposed mafic (MSD) and decomposed mafic (MD).
#
# ```{figure} ./images/ore_body.png
# ---
# height: 400px
# name: ore_body
# ---
# Close-up view of the expected ore shell with respect to the drilling data.
# ```
#
#  [Table 1](phys_prop) summarizes the relative physical properties of the main rock units in the area.
# The iron formation is expected to be more resistive and dense than the host rocks. Although non-alterated mafic rocks are generally magnetic, petrophysical data show that the iron formation in this region is more magnetic than the host rocks. In fact, jaspelite has a higher concentration of magnetite than any other lithology in this area.
#
#
#
# ```{table} Summary of expected physical properties
# :name: phys_prop
# | Unit | Susceptibility | Density | Resistivity |
# | :--- | :--- | :---- | :---- |
# | Jaspelite (JP) |  high    | high      | high     |
# | Hematite (HC) |  high    | high      | high     |
# | Mafic (MS, MSD) |  moderate    | moderate      | moderate     |
# ```
#
