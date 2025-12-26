.. _plate_simulation_methodology:

Plate Simulation: Methodology
=============================

In order to simulate geophysical data from a physical property model, we
need three things: a computational mesh, a discretization of the model
within that mesh and a means to simulate the data.  Plate simulation
relies on `discretize <https://discretize.simpeg.xyz/en/main/>`_ for
octree mesh creation, and `SimPEG <https://simpeg.xyz/>`_ for finite
volume based forward modeling.  Plate simulation includes a module for
generating a simple two-layer model with embedded plate anomalies within
octree meshes. In this section, we will discuss all three of these
components, their interface exposed by the ui.json file, and the storage
of results.

.. figure:: /images/plate-simulation/methodology/uijson.png
    :align: center
    :width: 80%

    *Merged images of both tabs of the ui.json rendered interface.*

.. contents::

.. toctree::
   :maxdepth: 3

Octree Mesh
-----------

In order to accurately simulate our earth model, we need a mesh
that is refined in key areas, while being coarse enough elsewhere to
efficiently simulate data.  The plate simulation package includes
refinements at the earth-air interface, the transmitter and receiver
sites and on the surface of plates.

.. figure:: /images/plate-simulation/methodology/mesh/refinement.png
    :align: center
    :width: 100%

    *Octree mesh refinement for earth-air interface, receiver sites,
    and within the mesh.*

The meshing can be controlled by options exposed in the ui.json.
Those options are significantly reduced compared with the octree creation from
`grid-app <https://mirageoscience-grid-apps.readthedocs-hosted.com/>`_
since we have tailored many of the parameters to suit the needs of plate simulation.

.. figure:: /images/plate-simulation/methodology/mesh/mesh_options.png
    :align: center

    *Octree mesh parameters exposed in the ui.json.*

Geological Model
----------------

The plate simulation package includes a module for generating
plate(s) embedded in a two-layer Earth model within octree meshes.
There are many permutations of this simple geological scenario
leading to a complex interface. To simplify things, we have
broken the discussion into two sub-sections: background
(basement and overburden) and plates.

Background
~~~~~~~~~~

All model values within plate-simulation are to be provided in
ohm-metres.  The basement resistivity is actually closer to a
halfspace in the sense that it fills the model anywhere outside
of the overburden and plate.  So the basement resistivity should
be chosen as an effective resistivity for the whole geological
section.  This should be quite reasonable for most applications
where the differences in resistivity between layers is much smaller
than the difference between overburden and any anomalous bodies
(plates).

.. figure:: /images/plate-simulation/methodology/model/basement_options.png
    :align: center

    *Basement resistivity option.*

The overburden is discretized by the resistivity and thickness
of the layer.  The thickness is referenced to the earth-air
interface and extends into the earth by the amount specified
in the thickness parameter.

.. figure:: /images/plate-simulation/methodology/model/overburden_options.png
    :align: center

    *Overburden resistivity and thickness options.*

.. figure:: /images/plate-simulation/methodology/model/overburden_and_basement.png
    :align: center
    :width: 100%

    *Model section highlighting the overburden and basement boundary.*

Plates
~~~~~~

In this section we will discuss the various plate options available
through the ui.json and their impact on the resulting discretized
model.

.. figure:: /images/plate-simulation/methodology/model/plate_options.png
    :align: center

    *Plate options available in the ui.json.*

The first set of options allows the user to specify the number of
plates and their spacing.

.. figure:: /images/plate-simulation/methodology/model/n_plates_options.png
    :align: center

    *Number of plates and spacing options.*

For all choices of ``n>1``, the plates will be evenly spaced at the requested
spacing and will share the same resistivity, size and orientation.

.. figure:: /images/plate-simulation/methodology/model/three_plates.png
    :align: center
    :width: 100%

    *Model created by choosing three plates spaced at 200m.*

The plate resistivity is expected to be entered in ohm-metres.

.. figure:: /images/plate-simulation/methodology/model/plate_resistivity_option.png
    :align: center

    *Plate resistivity option.*

The size of the plate is given as a 'thickness', 'strike length', and
'dip length'.

.. figure:: /images/plate-simulation/methodology/model/plate_size_options.png
    :align: center

    *Plate size options.*

The image below shows a dipping plate with annotations showing the size
parameters for that particular plate.

.. figure:: /images/plate-simulation/methodology/model/plate_size.png
    :align: center
    :width: 100%

    *A dipping plate striking northeast with annotations for its thickness,
    strike length and dip length.*

The orientation of the plate is provided in terms of a dip and dip direction.
The dip is defined as the angle between the horizontal projection of the plate
normal and the plate tangent sharing the same origin.  The dip direction is
measured between the horizontal projection of the plate normal and the North
arrow. See the image below for a visual representation of these angles.

.. figure:: /images/plate-simulation/methodology/model/plate_orientation.png
    :align: center
    :width: 100%

    *Plate orientation options.  Plate orientation is given as a dip and dip direction.
    The dip (b) is defined as the angle between the horizontal the projection of the
    plate normal (n\') and the plate tangent sharing the same origin (t).  The dip
    direction (a) is the angle measured between the horizontal projection of the plate
    normal (n\') and due north (N).*

The location of the plate can be provided in both relative and absolute terms.
The position parameters are given as an easting, northing, and elevation.  If the
relative locations checkbox is chosen, then the easting and northing will be
relative to the center of the survey and the elevation will be relative to one of
the available references.  The elevation may either be referenced to the earth-air
interface or the overburden provided by the ``Depth reference`` dropdown.  Either of
these choice can be relative to the minimum, maximum, or mean of the points making
up the reference surface as given by the ``Reference type`` dropdown.  In all of these
cases the distance provided will act as a depth below the reference to the *top of
plate* in the *z negative down* convention.  If the relative locations checkbox is not
chosen, then the easting, northing, and elevation is simply the location of the
center of the plate.

.. figure:: /images/plate-simulation/methodology/model/plate_location_options.png
    :align: center

    *Plate location options in relative mode. Notice the* ``Elevation`` *is given as
    negative to ensure the top of the plate is below the selected min of the
    overburden.*

.. figure:: /images/plate-simulation/methodology/model/plate_location.png
    :align: center
    :width: 100%

    *Example of a relative elevation referenced 100m below the minimum of the
    overburden layer.*

Data Simulation
---------------

.. _simpeg_group_options:

The simulation parameters control the forward modeling of the plate model
discretized within the octree mesh.  Rather than exposing the parameters within
the plate simulation interface all over again, we simply allow the user to
select an existing forward modelling SimPEG group.  It is expected that the
user will have already edited those options and provided at least a topography
and survey object as well as selected one or more components to simulate.  The
user may also provide a name to the new SimPEG group that will be used to store
the results.


.. figure:: /images/plate-simulation/methodology/data/simpeg_group_options.png
    :align: center

    *Selecting the initialized forward modelling SimPEG group and naming the
    group that will store the plate simulation results.*

The required SimPEG group can be created within Geoscience ANALYST through the
``Geophysics`` menu under ``SimPEG Python Interface`` entry.

.. figure:: /images/plate-simulation/methodology/data/simpeg_group_creation.png
    :align: center
    :width: 100%

    *Creating a SimPEG group to be selected within the plate simulation interface.*

Once created, the options can be edited by right-clicking the group and choosing
the 'Edit Options' entry.

.. figure:: /images/plate-simulation/methodology/data/simpeg_group_edit_options.png
    :align: center

    *Editing the SimPEG group options.*

Since plate-simulation will create its own mesh and model, the mesh and
conductivity selections can be ignored.  Selecting a value will not conflict
with the plate-simulation objects and will simply be ignored.  In contrast, the
survey, topography and at least one component must be selected to run the simulation.

.. figure:: /images/plate-simulation/methodology/data/simulation_options.png
    :align: center
    :width: 80%

    *Simulation options with annotations for required and not required components.*

Results
-------

The results of the simulation are stored in the SimPEG group named in the
:ref:`simpeg group option <simpeg_group_options>` section.

.. figure:: /images/plate-simulation/methodology/results.png
    :align: center

    *Results group containing a survey object with all the simulated data channels
    stored in property groups, and an octree mesh containing the model parameterized
    in the interface.*

To iterate on the design of experiment, simply copy the options, edit, and
run again.

.. figure:: /images/plate-simulation/methodology/copy_options.png
    :align: center

    *Copying the options to run a new simulation.*

If the user wishes to sweep one or more of the input parameters to run a large number of
simulations, they can use the ``generate sweep file`` option to write a file used
by the `param-sweeps <https://github.com/MiraGeoscience/param-sweeps>`_ package to do just
that. It is beyond the scope of this document to discuss the use of that package;
refer to its README for further details.

.. figure:: /images/plate-simulation/methodology/sweep_option.png
    :align: center

    *Generating a sweep file to run multiple simulations.*
