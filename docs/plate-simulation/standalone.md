#plate_simulation_standalone
# Interface

Simulating geophysical data from a physical property model requires
three things: a computational mesh, a discretization of the model within
that mesh, and a means to simulate the data. Plate simulation includes a
module for generating a simple two-layer model with embedded plate
anomalies within octree meshes. This section discusses all three of
these components, their interface exposed by the ui.json file, and the
storage of results.

<figure class="align-center">
<img src="/plate-simulation/images/methodology/uijson.png"
style="width:300pt"
alt="Merged images of both tabs of the ui.json rendered interface." />
<figcaption aria-hidden="true"><em>Merged images of both tabs of the
ui.json rendered interface.</em></figcaption>
</figure>

## Geological Model

Plate simulation includes a module for generating plates embedded in a
two-layer Earth model within octree meshes. Many permutations of this
simple geological scenario result in a complex interface. To simplify
this, the discussion is organized into two sub-sections: background
(basement and overburden) and plates. All model values within
plate-simulation must be provided in SI units that varies depending on
the chosen forward simulation (g/cc, SI or Ohm.m)

### Background

The basement resistivity is actually closer to a halfspace in the sense
that it fills the model anywhere outside of the overburden and plate.
Therefore, the basement resistivity should be chosen as an effective
resistivity for the whole geological section. This approach is quite
reasonable for most applications where the differences in resistivity
between layers are much smaller than the difference between overburden
and any anomalous bodies (plates).

<figure class="align-center">
<img
src="/plate-simulation/images/methodology/model/basement_options.png"
alt="Basement resistivity option." />
<figcaption aria-hidden="true"><em>Basement resistivity
option.</em></figcaption>
</figure>

The overburden is discretized by the resistivity and thickness of the
layer. The thickness is referenced to the earth-air interface and
extends into the earth by the amount specified in the thickness
parameter.

<figure class="align-center">
<img
src="/plate-simulation/images/methodology/model/overburden_options.png"
alt="Overburden resistivity and thickness options." />
<figcaption aria-hidden="true"><em>Overburden resistivity and thickness
options.</em></figcaption>
</figure>

<figure class="align-center">
<img
src="/plate-simulation/images/methodology/model/overburden_and_basement.png"
style="width:500pt"
alt="Model section highlighting the overburden and basement boundary." />
<figcaption aria-hidden="true"><em>Model section highlighting the
overburden and basement boundary.</em></figcaption>
</figure>

### Plates

This section discusses the various plate options available through the
ui.json and their impact on the resulting discretized model.

<figure class="align-center">
<img src="/plate-simulation/images/methodology/model/plate_options.png"
alt="Plate options available in the ui.json." />
<figcaption aria-hidden="true"><em>Plate options available in the
ui.json.</em></figcaption>
</figure>

The first set of options allows the user to specify the number of plates
and their spacing.

<figure class="align-center">
<img
src="/plate-simulation/images/methodology/model/n_plates_options.png"
alt="Number of plates and spacing options." />
<figcaption aria-hidden="true"><em>Number of plates and spacing
options.</em></figcaption>
</figure>

For all choices of `n>1`, the plates are evenly spaced at the requested
spacing and share the same resistivity, size, and orientation.

<figure class="align-center">
<img src="/plate-simulation/images/methodology/model/three_plates.png"
style="width:500pt"
alt="Model created by choosing three plates spaced at 200m." />
<figcaption aria-hidden="true"><em>Model created by choosing three
plates spaced at 200m.</em></figcaption>
</figure>

The plate resistivity must be entered in SI units (g/cc, SI or Ohm.m).

<figure class="align-center">
<img
src="/plate-simulation/images/methodology/model/plate_resistivity_option.png"
alt="Plate resistivity option." />
<figcaption aria-hidden="true"><em>Plate resistivity
option.</em></figcaption>
</figure>

The size of the plate is defined by three parameters: thickness, strike
length, and dip length.

<figure class="align-center">
<img
src="/plate-simulation/images/methodology/model/plate_size_options.png"
alt="Plate size options." />
<figcaption aria-hidden="true"><em>Plate size options.</em></figcaption>
</figure>

The image below shows a dipping plate with annotations indicating the
size parameters for that particular plate.

<figure class="align-center">
<img src="/plate-simulation/images/methodology/model/plate_size.png"
style="width:500pt"
alt="A dipping plate striking northeast with annotations for its thickness, strike length and dip length." />
<figcaption aria-hidden="true"><em>A dipping plate striking northeast
with annotations for its thickness, strike length and dip
length.</em></figcaption>
</figure>

The plate orientation is defined in terms of dip and dip direction. The
dip is the angle between the horizontal projection of the plate normal
and the plate tangent sharing the same origin. The dip direction is
measured between the horizontal projection of the plate normal and the
North arrow. The image below provides a visual representation of these
angles.

<figure class="align-center">
<img
src="/plate-simulation/images/methodology/model/plate_orientation.png"
style="width:500pt"
alt="Plate orientation options. Plate orientation is given as a dip and dip direction. The dip (b) is defined as the angle between the horizontal the projection of the plate normal (n&#39;) and the plate tangent sharing the same origin (t). The dip direction (a) is the angle measured between the horizontal projection of the plate normal (n&#39;) and due north (N)." />
<figcaption aria-hidden="true"><em>Plate orientation options. Plate
orientation is given as a dip and dip direction. The dip (b) is defined
as the angle between the horizontal the projection of the plate normal
(n') and the plate tangent sharing the same origin (t). The dip
direction (a) is the angle measured between the horizontal projection of
the plate normal (n') and due north (N).</em></figcaption>
</figure>

The plate location is chosen to be centered on the provided survey
object with the depth relative to the topography entered as positive
down.

<figure class="align-center">
<img
src="/plate-simulation/images/methodology/model/plate_location_options.png"
alt="Plate depth option sets the top of the plate n meters below the topography and centered on the survey object." />
<figcaption aria-hidden="true"><em>Plate depth option sets the top of
the plate n meters below the topography and centered on the survey
object.</em></figcaption>
</figure>

<figure class="align-center">
<img src="/plate-simulation/images/methodology/model/plate_location.png"
style="width:500pt"
alt="Example of a relative elevation referenced 100m below the minimum of the overburden layer." />
<figcaption aria-hidden="true"><em>Example of a relative elevation
referenced 100m below the minimum of the overburden
layer.</em></figcaption>
</figure>

## Data Simulation

::: {#simpeg_group_options}
The simulation parameters control the forward modeling of the plate
model discretized within the octree mesh. Rather than exposing
parameters within the plate simulation interface, the application allows
the user to select an existing forward modelling SimPEG group. The user
must ensure that the SimPEG group has been previously edited with
appropriate options, includes at least a topography and survey object,
and has selected one or more components to simulate. The user may also
provide a name for the new SimPEG group to store the results.
:::

<figure class="align-center">
<img
src="/plate-simulation/images/methodology/data/simpeg_group_options.png"
alt="Selecting the initialized forward modelling SimPEG group and naming the group that will store the plate simulation results." />
<figcaption aria-hidden="true"><em>Selecting the initialized forward
modelling SimPEG group and naming the group that will store the plate
simulation results.</em></figcaption>
</figure>

Create the required SimPEG group within Geoscience ANALYST through the
`Geophysics` menu under `SimPEG Python Interface` entry.

<figure class="align-center">
<img
src="/plate-simulation/images/methodology/data/simpeg_group_creation.png"
style="width:300pt"
alt="Creating a SimPEG group to be selected within the plate simulation interface." />
<figcaption aria-hidden="true"><em>Creating a SimPEG group to be
selected within the plate simulation interface.</em></figcaption>
</figure>

Edit the options by right-clicking the group and selecting \'Edit
Options\'.

<figure class="align-center">
<img
src="/plate-simulation/images/methodology/data/simpeg_group_edit_options.png"
style="width:300pt" alt="Editing the SimPEG group options." />
<figcaption aria-hidden="true"><em>Editing the SimPEG group
options.</em></figcaption>
</figure>

Since plate-simulation creates its own mesh and model, the mesh and
conductivity selections can be ignored. Selecting a value does not
conflict with the plate-simulation objects and is simply ignored. In
contrast, the survey, topography, and at least one component must be
selected to run the simulation.

<figure class="align-center">
<img
src="/plate-simulation/images/methodology/data/simulation_options.png"
style="width:300pt"
alt="Simulation options with annotations for required and not required components." />
<figcaption aria-hidden="true"><em>Simulation options with annotations
for required and not required components.</em></figcaption>
</figure>

## Octree Mesh

To accurately simulate the earth model, the mesh must be refined in key
areas while remaining coarse enough elsewhere to efficiently simulate
data. Plate simulation includes refinements at the earth-air interface,
the transmitter and receiver sites, and on the surface of plates.

<figure class="align-center">
<img src="/plate-simulation/images/methodology/mesh/refinement.png"
style="width:500pt"
alt="Octree mesh refinement for earth-air interface, receiver sites, and within the mesh." />
<figcaption aria-hidden="true"><em>Octree mesh refinement for earth-air
interface, receiver sites, and within the mesh.</em></figcaption>
</figure>

The meshing is controlled by options exposed in the ui.json. These
options are significantly reduced compared with octree creation from
[grid-app](https://mirageoscience-grid-apps.readthedocs-hosted.com/), as
many parameters have been tailored to suit the needs of plate
simulation.

<figure class="align-center">
<img src="/plate-simulation/images/methodology/mesh/mesh_options.png"
style="width:300pt"
alt="Octree mesh parameters exposed in the ui.json." />
<figcaption aria-hidden="true"><em>Octree mesh parameters exposed in the
ui.json.</em></figcaption>
</figure>

## Results

The results of the simulation are stored in the SimPEG group named in
the `simpeg group option <simpeg_group_options>`{.interpreted-text
role="ref"} section.

<figure class="align-center">
<img src="/plate-simulation/images/methodology/results.png"
style="width:300pt"
alt="Results group containing a survey object with all the simulated data channels stored in property groups, and an octree mesh containing the model parameterized in the interface." />
<figcaption aria-hidden="true"><em>Results group containing a survey
object with all the simulated data channels stored in property groups,
and an octree mesh containing the model parameterized in the
interface.</em></figcaption>
</figure>

To iterate on the design of experiment, copy the options, edit them, and
run again.

<figure class="align-center">
<img src="/plate-simulation/images/methodology/copy_options.png"
style="width:300pt"
alt="Copying the options to run a new simulation." />
<figcaption aria-hidden="true"><em>Copying the options to run a new
simulation.</em></figcaption>
</figure>
