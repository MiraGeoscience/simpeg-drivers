.. _interactive_application:

Interactive Application
=======================

If you are using **peak-finder** through the interactive application you will see
a window with visualizations and ui controls.  The visualization contains both a
section of data along a single line and a plan view to locate the chosen and
adjacent lines and anomaly picks in cartesian space.

.. figure:: /images/interactive/visualizations.png


The ui controls section is divided into three subsections:

- `Detection Parameters`_
- `Visual Parameters`_

.. figure:: /images/interactive/ui_controls.png


Detection Parameters
~~~~~~~~~~~~~~~~~~~~

The detection parameters are those that the peak-finder application uses to
tune the characterization and detection of anomalies within the data.  Most
of these are already described in the :ref:`Methodology` section.  Follow
the links for detailed descriptions of each parameter.

.. figure:: /images/parameters/detection_parameters.png
   :align: left


- :ref:`Smoothing window <Smoothing>`
- :ref:`Minimum Amplitude (%) <Minimum Amplitude>`
- :ref:`Minimum Value <Minimum Data Value>`
- :ref:`Minimum Width (m) <Minimum Width>`
- :ref:`Max Peak Migration (m) <Maximum Peak Migration>`
- :ref:`Minimum # Channels <Minimum number of channels>`
- :ref:`Merge # Peaks <Merge N Peaks>`
- :ref:`Max Separation <Max Group Separation>`


Visual Parameters
~~~~~~~~~~~~~~~~~

This section controls the appearance of the plotting area.

.. figure:: /images/parameters/visual_parameters.png
   :align: left


N Outward Lines
_______________

Number of lines to display on either side of the selected line in the plan view. The ``Survey figure`` option must be
selected to see the effect of this parameter.

.. figure:: /images/parameters/visualization/outward_lines_1.png

    The plan view with 1 outward line on either side of the selected line.


X-axis Label
____________

Updates the label on the data section view x-axis.

.. figure:: /images/parameters/visualization/section_xlabel.png

   The x-axis label is updated to reflect the selection.

Y-axis Scaling
______________

Updates the scaling of the y-axis of the data section view


Linear threshold
________________

When Symlog is chosen for Y-axis scaling, this parameter will set the
region in which linear scaling is used.

.. figure:: /images/parameters/visualization/linthresh_compare.png
   :scale: 60%

   Comparing the data visualization with a symlog linear threshold set to
   10E-3.2 (left) and 10E-5.1 (right).

Plot residuals
______________

Switches on and off the residual visualization that shows the difference
between the raw and smoothed data.  See the :ref:`Smoothing` section for more details.

.. figure:: /images/parameters/visualization/residuals.png
   :scale: 40%

   The residual layer is used to show the effect of the smoothing factor.

Plot markers
____________

Switches on and off the markers outlining the character of each anomaly

.. figure:: /images/parameters/visualization/markers.png
   :scale: 40%

   Markers are used to indicate the left and right edges, the center,
   and the inflection point in curvature of each anomaly.



Output Parameters
~~~~~~~~~~~~~~~~~

Create trend line
__________________

Run a trend line detection algorithm on the result of the Peak Finder algorithm. Results are stored as a curve object in the geoh5 file
with the same group ID as the Peak Finder result.


.. figure:: /images/parameters/visualization/trend_lines.png


Save as
_______

.. autoproperty:: peak_finder.params.PeakFinderParams.ga_group_name

Name of the group in the geoh5 file where the results will be saved.  The default is ``peak_finder``.

Export
______

Run the algorithm with the parameters selected and save the result to geoh5.
