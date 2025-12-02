.. _standalone_application:

Standalone Application
======================

The standalone application contains no visualization and operates on the entire
data object provided in the :ref:`General Parameters <General Parameters>` section of the ui.json.
For this reason we will limit the discussion here to the :ref:`detection parameters <detection parameters>`
as well as the :ref:`grouping parameters <grouping parameters>` that affect not only the visual representation
in the interactive application, but also the grouping for detection within the
standalone application.

.. _detection parameters:

.. figure:: /images/standalone/ui.png

   Detection parameters section of the peak finder ui.json.

- :ref:`Smoothing window <Smoothing>`
- :ref:`Minimum Amplitude (%) <Minimum Amplitude>`
- :ref:`Minimum Value <Minimum Data Value>`
- :ref:`Minimum Width (m) <Minimum Width>`
- :ref:`Max Peak Migration (m) <Maximum Peak Migration>`
- :ref:`Minimum # Channels <Minimum number of channels>`
- :ref:`Merge # Peaks <Merge N Peaks>`
- :ref:`Max Separation <Max Group Separation>`

Masking Data
____________

Provide an Mask (boolean) data object to focus the peak finder process on an area
of interest.
