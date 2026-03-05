.. _plate_simulation_match:

Plate Matching
==============

The plate matching algorithm searches through a library of pre-computed plate simulations to identify the best-fit conductor geometry for observed electromagnetic data at query locations. The matching process involves spatial and temporal interpolation, data normalization, and correlation-based scoring to rank candidate simulations.

.. figure:: /plate-simulation/images/match_landing.png
    :align: center
    :width: 500pt



Interface
---------

This section describes the parameters controlling the application.

.. figure:: /plate-simulation/images/match_uijson.png
    :align: center
    :width: 300pt

    *Rendered user-interface in Geoscience ANALYST.*


Inputs
^^^^^^

The algorithm operates on the following inputs:

- **Survey**: A geophysical survey object containing the airborne TEM measurements and associated metadata
- **EM data**: Airborne time-domain electromagnetic (TEM) measurements from the survey
- **Query Points**: User-defined positions where plate parameters are to be estimated
- **Query Max Distance**: Maximum distance from the query points along the survey line segments for consideration in the matching process
- **Strike angle**: Optional angle to correct for the strike of the conductor relative to the survey line direction
- **Topography**: Object representing the earth-air interface
- **Elevation channel**: Optional channel containing elevation data for the topography locations. Mainly used for digital elevation models provided on Grid2D objects.
- **Simulation directory**: A directory of pre-computed forward simulations representing various plate geometries and conductivities


Methodology
-----------

For each query location, the application identifies the closest survey line segment, extracts relevant observed data, and compares it against all simulations in the library using a multi-step matching process. To accommodate for variable position, time sampling, it is expected that the simulated library contains sufficient variability in plate parameters and survey geometries to capture the range of possible responses.

.. figure:: /plate-simulation/images/match_template.png
    :align: center
    :width: 500pt

    Template for the simulated data (black) and observed data (red) used in the matching process. The radial pattern centered on the plate allows to tighten sampling around the peak response, which is critical for accurate matching.


The following sections describe the key steps of the matching algorithm.


Spatial Interpolation
^^^^^^^^^^^^^^^^^^^^^

The application performs spatial interpolation to align simulation data with observation points:

1. **Local coordinate transformation**: The application identifies the survey line segment nearest to each query location. It transforms both the observed and simulated receiver locations into a local polar coordinate system (distance, azimuth, height) centered on the line segment.

2. **Strike angle correction**: If strike angles are provided, the application rotates the coordinate system to align the plate orientation with the survey geometry. This accounts for variations in conductor strike relative to the flight line direction.

3. **Inverse distance weighting**: The application constructs a sparse interpolation matrix using the 8 nearest simulation receivers for each observation point. The weights are computed using inverse distance weighting with a power of 2.0 and a minimum distance threshold of 0.1 to prevent singularities.

Temporal Interpolation
^^^^^^^^^^^^^^^^^^^^^^

Time-domain electromagnetic data requires careful handling of the temporal sampling:

1. **Time channel alignment**: The application identifies the overlap between simulated and observed time channels. Only time gates within the simulated range are considered for matching.

2. **Interpolation matrix**: For each observation time within the valid range, the application constructs a sparse interpolation matrix using inverse distance weighting based on the temporal separation between channels. This allows for comparison even when simulated and observed time samplings differ.

Data Normalization
^^^^^^^^^^^^^^^^^^

To enable robust comparison across different conductivity models and survey geometries, the application normalizes both observed and simulated data:

1. **Symlog transformation**: The application applies a symmetric logarithmic transformation to handle the large dynamic range of electromagnetic decay curves. The threshold is set at the 5th percentile of absolute data values.

2. **Median centering**: The application subtracts the median value from each time channel to remove DC offsets.

3. **Amplitude scaling**: The application scales each data profile to unit maximum absolute value, ensuring that shape matching dominates over amplitude matching.

Orientation Detection
^^^^^^^^^^^^^^^^^^^^^

Electromagnetic anomalies are strongly dependent on the direction of approach relative to the conductor dip. Since simulations are only computed in the down-dip direction, the application automatically detects and corrects for orientation reversals:

1. **Spatial integration**: The application computes the integral of positive anomaly values on each half of the survey segment.

2. **Asymmetry test**: If more than 50% of the time channels show stronger anomalies on the left side of the segment, the application infers an up-dip approach and reverses the spatial ordering of the data.

Scoring and Ranking
^^^^^^^^^^^^^^^^^^^

For each simulation file in the library, the application computes a match score:

1. **Cross-correlation**: For each time channel, the application computes the normalized cross-correlation between observed and simulated data. The peak correlation indicates the optimal spatial alignment.

2. **Alignment consistency**: The application records the index of maximum correlation for each time channel and computes the median alignment position across all channels.

3. **Residual norm**: The application computes the L2 norm of the difference between observed and amplitude-scaled simulated data across all time channels and spatial locations. This serves as the primary score metric, with lower values indicating better matches.

4. **Ranking**: The application sorts all simulations by ascending score, with the lowest-scoring simulation representing the best match.

Plate Parameter Extraction
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once the best-matching simulation is identified, the application extracts the plate parameters from the simulation metadata:

1. **Parameter retrieval**: The application reads the conductor geometry (strike length, dip length, width, dip angle, conductivity) from the ui.json metadata stored in the simulation file.

2. **Spatial positioning**: The application positions the plate at the centroid of the matched survey segment, adjusted vertically by the overburden thickness.

3. **Orientation correction**: The application applies strike angle corrections based on the local line azimuth and any user-specified strike angle offsets.

4. **Plate creation**: The application creates a new ``MaxwellPlate`` object in the output workspace with the extracted geometry and stores the full model parameters in the plate metadata.

Parallel Processing
^^^^^^^^^^^^^^^^^^^

The matching algorithm leverages parallel processing to accelerate the comparison of large simulation libraries:

1. **File batching**: The application divides the simulation library into batches, with approximately 10 batches per worker process.

2. **Distributed scoring**: Each batch is submitted to a Dask worker for independent scoring. Workers compute spatial and temporal interpolations, normalize data, and calculate correlation scores without inter-process communication.

3. **Result aggregation**: The main process collects scores from all workers and performs the final ranking to identify the best match for each query location.

This parallel architecture allows efficient processing of libraries containing hundreds to thousands of pre-computed simulations.
