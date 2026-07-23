# Release Notes

## Release 0.5.0 (2026-06-05)

### Plate Simulation
* Create UI and Driver for the classification of EM anomalies
* Export best match models as Maxwell plates (w/ GEOPY-2661)
* Finalize Anglo Accelerated Development with synthetic example
* Add documentation for plate sweep and match
* Add summary option for plate sweep
* Change reference of Plate from center-center to top-center
* Plate Match: Attach figure with comparative plot of scaled obs versus simulated data
* Make simpeg group names in plate-simulation more clear in the ui.jsons
### Mag/Grav
* MVI: Add small value to reference amplitude if reference are used
* Implement MVI with PDE inversion
* Use cyclic colormap by default for declination angle model
* Change data groups saved for MVI as requested by users
* Revert legacy behaviour with reference model ON by default
### FEM/TEM
* Implement arbitrary receiver orientations (u-v-w) for airborne EM surveys
* Relabel uijson for TEM using Vertical, inLine, cross-line
* Airborne FEM coaxial do not rotate transmitter, and ppm normalization needs to be adjusted
* Allow rotated receivers for ground EM survey
* Remove dependency on Tx frequency for airborne FEM survey
### Natural Sources
* Incorporate MobileMT inversion with SimPEG (apparent conductivity only) DC/IP
* Parallelize batch 2D inversion
* Improve topography augmentation for DC and MT
* Accept 2D inversion mesh (DrapeModel) in sensitivity_cutoff application
* Add tooltips to missing IP inversion inputs
* DC2D with single line crashes on run with n_workers set
* Investigate edge cells recovered with DC2D inversions
### Joint Inversion
* Joint surveys using mvi crashes with dimension mismatch
* PGI: Add checks for reference model present on inversion groups. Return clean GeoAppsError if not
* Research auto-scaling strategy for cross-gradient regularization terms
* Membership flip between iterations in PGI
* Add PGI documentation
### General Utilities
* Add dip_direction to list of supported variables by plate_sweep
* Micro-management of auto-scaling of misfits with tiles, channels and within joint inversions
* Clip limits of topography extent based on mesh extent
* Add datetime stamp to simpeg.log and simpeg.out file names
* Add validator for negative on NDV values in uncertainties
* Transfer visual parameters Core volume settings from the input mesh to the inversion mesh (if present)
* Add optional out_group to Depth of Investigation app
### Bugs and Maintenance
* Update GravityUIJson with new data forms
* Conductivity/Resistivity switcher doesn't make sense for joint mvi/mag
* Synthetic topography for runtests is overly sampled
* Fix capitalization in labels and tooltips of ui.json files
* Update minimum requirement to python >=3.12, <3.15 and numpy 2.*
* Implement direct run_commands to specific modules for forwards and inversions
* DCIP 2D crash on line ID selection
* PGI failure on petrophysical model with air cells
* Inversion stalls on tiling for large problems during redistribution of clusters
* Refactor extent property calculation for all grid objects
* Consolidate code for plate model definition between different repos
* Update dictionary to choose driver from run_command
* Triangulation crash on input surface
* Regularization parameters of sub-drivers always over-written by joint parameters
* Inversion crash on tile mesh creation transferring data
* Refresh screenshots of UIJsons in docs

## Release 0.4.0 (2026-01-06)

* Support 3D vector property group for orientation of rotated gradients
* Add rotated_gradient to 2D inversions
* Joint inversion: PGI
* Refactor components of inversion options
* single entry point to run any application
* Joint inversion: PGI
* Migrate param-sweeps to geoapps-utils
* Migrate plate-simulation to simpeg-drivers
* Hook up 2D rotated gradients to batch 2D inversions
* Investigate random failure of cross-gradient test
* Amplitude model stuck on upper bound for MVI
* Change default sensitivity threshold for DC inversions
* Fix plate simulation label and tooltip
* Speed up saving directive by keeping the file open during series
* Change units displayed on selector of data type for V/Am^2
* Investigate slow startup time for TEM inversion
* Make pydantic validator issues returns clean GeoAppsError option
* Add case study with Forestania datasets
* Improve rotated gradient on octree change with average cell dim
* Add files via upload
* Add case study with Forestania datasets
* Add docs on rotated gradient options
* Force use of MKL for Blas implementation
* Bad flipping of large loop orientation
* Refactor of the Factory classes
* Migrate octree-creation-app to grid-app
* Investigate double-print of of Geoapps-Error
* Can't handle topography grid with nan
* Parallelize 1D simulations
* Forward simulation of potential fields always form the full J
* Re-order parameters to mimic the order in metadata
* Add check for negative cond/res model values
* Lost control on reference angles for MVI
* Add core depth to the max-min elevation of the survey
* Detect issues with waveform and throw a custom GeoappsError if found
* Add a copy group+object base in input file as it exists uin ui json group
* Failure of directives when using Futures for simulation
* Create custom sweep UIjson for plate-simulation
* Investigate speckly looking MVI models with rotated gradients
* Make start/stop group optional, and use the plate-sim parameter instead if disabled
* Missing grouping of EM data in save directive for joint inversions
* Parallelize the Sweeps
* Explore 2D gridding techniques for EM line data
* Pydantic error on auto-mesh creation with Grid2D topography object
* Crash on Zarr file shape for tiled inversions with disk storage
* Crash on no-upper bound for MVI within a joint process
* Improve parallel creation of 1D simulations
* Parallelize the Sweeps
* Investigate erratic corner cells when using rotated gradients
* Add custom error for topography grid selected without data
* Random failure of sensitivity cutoff app tests
* Workers crash on creating misfits for large problems
* Random failure of sensitivity cutoff app tests
* Remove save directive for petrophysical model
* Adjust target misfit down to account for number of NDV in data
* PGI fails with single simulation selected
* MT predicted channels missing [] indices
* Break edge case for 1D inversion with negative elevation (release 4.7)
* Save sensitivities option ignored (release 4.7)
* Wrong normalization for MT
* Speed up active from topography algorithm
* Bring in doc of plate simulation
* Remove out_group form ui.json. It's redundant, and was currently fai…
* Cannot load results from Batch 2D inversion runs
* DEVOPS-922: adjust or fix text in ui.json
* Check for MVI Simpeg groups and raise error
* Joint surveys fails validation if no starting/reference models chosen

## Release 0.3.0 (2025-06-20)

* Create spatial tiling estimator
* Add a depth of investigation application
* Add auto-meshing option for all inversions with default parameters
* Fix simpeg-drivers pyproject still pointing to octree-creation-app/*
* Auto-meshing: Round cell size to nearest 5 multiplier
* Allow option for percentile cutoff in sensitivity based depth of investigation
* Auto-meshing: Only use depth_code (no vertical pads) for potential fields and DC-IP inversions
* Add UIJson group to hold octree creation parameters and update options
* Octree mesh upside down
* Refactor Params class with BaseData
* Convert all of potential fields to BaseData params class
* Faulty air cells in 2D inversion active
* Reduce tests runtime
* Use MetaSimulations instead of custom misfit mapping towards distributed process
* Convert all DC/IP 3D/2D params to BaseData
* Convert all EM params to BaseData
* Convert both joint params to BaseData
* Export uml from simpeg-drivers and design class structure for inversion parameters.
* Selecting an active model instead of topography with surface survey option crashes
* Update discretize to >=0.11.*
* Cleanup constant files and data classes
* Add version validation and write_default method to update version in …
* Update SimPEG 0.21.2 to 0.23
* Crash running 2D IP
* Add custom Error for problem too large
* Add UIJson class for gravity forward/inversion
* Add option for MUMPS solver
* Duplicated survey object when monitoring_directory is used
* Resolve deprecation warnings with latest simpeg 0.23 and discretize 0.11
* Create documentation for depth of investigation app
* Add UIJson class for gravity forward/inversion
* Fixup dependencies
* Resolve deprecation warnings with latest simpeg 0.23 and discretize 0.11
* Draft uml file for the UIJson/Params design
* Update inversion docs to describe the auto-mesh option
* Phi-d at Iter 0 shows as nan in the *.out file
* Handle extra fields and deprecations in UIJson version validation
* Clean up pydantic warnings
* Implement structural orientation (rotated gradient) option to the inversion UI
* Migrate em_inversion (EM1D) script to simpeg-drivers
* Should update version when writing ui.json from simpeg-drivers options classes
* Migrate FEM-1D from simpeg-drivers
* Make lower bound for MVI visible=False
* Add strike/dip option to the choice list of rotated_gradients.
* Deprecate gradient_type
* Fix warning about differing number of parameters between ui_json and data.
* Relock on latest git dev revisions
* Environment for coming pre-release
* Fix UI json version tests (part of GEOPY-2049)
* Rename params modules to options
* Group models for L2 and LP
* Add version to print screen
* Allow IntegerData for active cell value model type
* Use published dependencies, no git branches
* Correctly declare dask for pip and dask-core for conda
* Fixup dask dependency: do not lock on pypi
* Use dask.distributed with workers as default behaviour
* IP inversion with resistivity option does not convert the model to conductivity
* Name of conductivity_model does not match the selection for resistivity
* Change default auto-scaling to false
* Bring back adjusted ui.json from Analyst to their respective repo
* Bad referencing to transmitter id name
* MVI name change brakes the forward
* Fem1d title
* Outdated inversion_type for 3D FDEM
* Non-zero evaluation of the rotated gradient of a constant model
* Sub-mesh reused on split data
* Ensure backward compatibility of saved ui.json from Analyst 4.5 to 4.6

## Release 0.2.0 (2025-02-07)

* Octree mesh cell definition not update if rec array
* Make the canny add_data optional on get_edges method
* Crash on joint survey with apparent resistivity
* Update simpeg fork to 0.21.2
* Enforce counter-clock wise ordering of EM large loops
* Streamline geoapps-utils
* Generate tutorial for Natural source EM
* Add checks on waveform before sending to SimPEG
* Training material for ATEM
* Always check/closed EM loops and return warning
* Fix handling of UBC ordered Octree cells
* Add docs for validation
* Allow input active cells instead of topography
* Fix formatting of warning for LargeLoop. Use logging instead warning
* Inversion: Allow for model vector to define norms
* Re-order the inversion inputs following users comments
* Add option to export sensitivities for all inversions
* Enable cell/face weights in params
* Fill in default ui.json tooltips for inversion parameters
* Review stitching of predicted data on tipper inversion
* Review log and out for cross-gradient inversion.
* Regression: Crash with no-reference data
* Group vector model orientation parameters as "Dip Direction & Dip"
* Add option for cond/resis for all EM/DC methods
* Flip upper and lower bound value for resistivity style inversions
* Implement rescaling of misfit functions for joint inversion
* Tipper inversion crashes on background_model if not constant
* DC3D inversion reports disconnected cells
* Ram/Disk option not working in simpeg through Analyst
* Save sensitivities fails for MVI inversion in Analyst
* Nan data values not handled by the inversion
* Simpeg-drivers is adding a transmitter id to the transmitter always
* Make the transmitter id name agnostic


## Release 0.1.0 (2024-06-17)

* Copy model to avoid applying double log
* prepare distribution
* Remove factor of half on cpu count for n_cpu=disabled
* Fix reduced set of linter errors on simpeg-drivers
* Regenerate env lock files (for SimPEG rc.1)
* Enforce counter-clock wise loop for TEM large loop
* Move params tests from geoapps to simpeg-drivers
* Deal with negative octree cell dimensions from legacy inversions
* Improve tiling strategy for large loop EM
* Improve scaling of cross-gradient regularization
* Build distribution files for geology and geophysics modules for Analyst
* Use new dev script to create lock files
* Fix tile ID on save directive
* New RC distribution for Analyst 4.4
* Import of simpeg-drivers too slow
* Merge Release/0.1.0 to main
* Use octree-creation-app v0.1.1

 Copyright (c) 2023-2026 Mira Geoscience Ltd.
