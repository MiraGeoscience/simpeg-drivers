(plate_simulation_standalone)=

# Interface

Simulating geophysical data from a physical property model requires
three things: a computational mesh, a discretization of the model within
that mesh, and a means to simulate the data. Plate simulation includes a
module for generating a simple two-layer model with embedded plate
anomalies within octree meshes. This section discusses all three of
these components, their interface exposed by the ui.json file, and the
storage of results.

```{figure} images/methodology/uijson.png
---
width: 500pt
align: center
---
Merged images of **main** and **advanced** parameter tabs.
```

(simpeg_group_options)=

## Forward group

The parameters controlling the forward simulation are defined through a SimPEG forward modelling group. The user
must ensure that the SimPEG group has been previously edited with appropriate options, including a topography object,
a survey object and data components to simulate.

```{figure} images/methodology/data/simpeg_group_options.png
---
width: 300pt
align: center
---
Selecting the initialized forward modelling SimPEG group and naming the group that will store the plate
simulation results.
```

- Create the required SimPEG group within Geoscience ANALYST through the
`Geophysics` menu under `SimPEG Python Interface` entry.

```{figure} images/methodology/data/simpeg_group_creation.png
---
width: 300pt
align: center
---
Creating a SimPEG group to be selected within the plate simulation interface.
```

- Edit the options by right-clicking the group and selecting ``Edit Options``.

```{figure} images/methodology/data/simpeg_group_edit_options.png
---
width: 300pt
align: center
---
Editing the SimPEG group options.
```

Since plate-simulation creates its own mesh and model, the mesh and
conductivity selections can be ignored. Selecting a value does not
conflict with the plate-simulation objects and is simply ignored.

```{figure} images/methodology/data/simulation_options.png
---
width: 300pt
align: center
---
Simulation options with annotations for required and not required components.
```

### Label
The user may also provide a name for the new SimPEG group to store the results.

## Geological Model

Plate simulation includes a module for generating plates embedded in a
two-layer Earth model within octree meshes. Many permutations of this
simple geological scenario result in a complex interface. To simplify
this, the discussion is organized into two subsections: background
(basement and overburden) and plates. All model values within
plate-simulation must be provided in SI units that varies depending on
the chosen forward simulation (g/cc, SI or Ohm.m)

### Basement

The basement physical property fills the model below the overburden layer.

```{figure} images/methodology/model/basement_options.png
---
width: 300pt
align: center
---
Basement physical property option.
```

### Overburden

The overburden is discretized by a physical property value and a thickness.

```{figure} images/methodology/model/overburden_options.png
---
width: 300pt
align: center
---
Overburden physical property and thickness options.
```

```{figure} images/methodology/model/overburden_and_basement.png
---
width: 300pt
align: center
---
Model section highlighting the overburden and basement boundary.
```

### Plates

This section discusses the various options to define the plate(s) embedded in the basement, below the overburden layer.

```{figure} images/methodology/model/plate_options.png
---
width: 300pt
align: center
---
```

Users can specify the number of plates and the spacing between them.

```{figure} images/methodology/model/n_plates_options.png
---
width: 300pt
align: center
---
Number of plates and spacing options.
```

For all choices of `n>1`, the plates are evenly spaced at the requested
spacing. All plates share the same physical property, size, and orientation.

```{figure} images/methodology/model/three_plates.png
---
width: 300pt
align: center
---
Model created by choosing three plates spaced at 200m.
```

The plate physical property must be entered in SI units (g/cc, SI or Ohm.m).

```{figure} images/methodology/model/plate_resistivity_option.png
---
width: 300pt
align: center
---
```

The size of the plate is defined by three parameters: thickness, strike
length, and dip length.

```{figure} images/methodology/model/plate_size_options.png
---
width: 300pt
align: center
---
```

The image below shows a dipping plate with annotations indicating the
size parameters for that particular plate.

```{figure} images/methodology/model/plate_size.png
---
width: 300pt
align: center
---
A dipping plate striking northeast with annotations for its thickness, strike length and dip
length.
```


The plate orientation is defined in terms of dip and dip direction. The
dip is the angle between the horizontal projection of the plate normal
and the plate tangent sharing the same origin. The dip direction is
measured between the horizontal projection of the plate normal and the
North arrow. The image below provides a visual representation of these
angles.

```{figure} images/methodology/model/plate_orientation.png
---
width: 300pt
align: center
---
Plate orientation options. Plate orientation is given as a dip and dip direction. The dip (b) is defined
as the angle between the horizontal the projection of the plate normal
(n') and the plate tangent sharing the same origin (t). The dip
direction (a) is the angle measured between the horizontal projection of
the plate normal (n') and due north (N).
```


The plate location is chosen to be centered on the provided survey
object with the depth relative to the topography entered as positive
down.

```{figure} images/methodology/model/plate_location_options.png
---
width: 300pt
align: center
---
Plate depth option sets the top of the plate n meters below the topography and centered on the survey
object.
```


```{figure} images/methodology/model/plate_location.png
---
width: 300pt
align: center
---
Example of a relative elevation referenced 100m below the minimum of the overburden
layer.
```


## Octree Mesh

To accurately simulate the earth model, the mesh must be refined in key
areas while remaining coarse enough elsewhere to efficiently simulate
data. Plate simulation includes refinements at the earth-air interface,
the transmitter and receiver sites, and on the surface of plates.

```{figure} images/methodology/mesh/refinement.png
---
width: 300pt
align: center
---
Octree mesh refinement for earth-air interface, receiver sites, and within the mesh.
```


The meshing is controlled by options exposed in the ui.json. These
options are significantly reduced compared with octree creation from
[grid-app](https://mirageoscience-grid-apps.readthedocs-hosted.com/), as
many parameters have been tailored to suit the needs of plate
simulation.

```{figure} images/methodology/mesh/mesh_options.png
---
width: 300pt
align: center
---
Octree mesh parameters exposed in the ui.json file.
```

## Results

The results of the simulation are stored in the SimPEG group named in
the [](simpeg_group_options) section.

```{figure} images/methodology/results.png
---
width: 300pt
align: center
---
Results group containing a survey object with all the simulated data channels stored in property groups,
and an octree mesh containing the model parameterized in the
interface.
```


To iterate on the design of experiment, copy the options, edit them, and
run again.

```{figure} images/methodology/copy_options.png
---
width: 300pt
align: center
---
Copying the options to run a new simulation.
```
