# Release Notes

## Release 0.5.0 (2026-06-05)

### Plate Simulation
* GEOPY-2449: Create UI and Driver for the classification of EM anomalies
* GEOPY-2701: Export best match models as Maxwell plates (w/ GEOPY-2661)
* GEOPY-2708: Finalize Anglo Accelerated Development with synthetic example
* GEOPY-2726: Add documentation for plate sweep and match
* GEOPY-2715: Add summary option for plate sweep
* GEOPY-2794: Change reference of Plate from center-center to top-center
* GEOPY-2800: Plate Match: Attach figure with comparative plot of scaled obs versus simulated data
* GEOPY-2852: Make simpeg group names in plate-simulation more clear in the ui.jsons
### Mag/Grav
* GEOPY-2659: MVI: Add small value to reference amplitude if reference are used
* GEOPY-2799: Implement MVI with PDE inversion
* GEOPY-2874: Use cyclic colormap by default for declination angle model
* GEOPY-2884: Change data groups saved for MVI as requested by users
* GEOPY-2903: Revert legacy behaviour with reference model ON by default
### FEM/TEM
* GEOPY-1406: Implement arbitrary receiver orientations (u-v-w) for airborne EM surveys
* GEOPY-2776: Relabel uijson for TEM using Vertical, inLine, cross-line
* GEOPY-2773: Airborne FEM coaxial do not rotate transmitter, and ppm normalization needs to be adjusted
* GEOPY-2879: Allow rotated receivers for ground EM survey
* GEOPY-2883: Remove dependency on Tx frequency for airborne FEM survey
### Natural Sources
* GEOPY-1383: Incorporate MobileMT inversion with SimPEG (apparent conductivity only)
DC/IP
* GEOPY-2490: Parallelize batch 2D inversion
* GEOPY-2686: Improve topography augmentation for DC and MT
* GEOPY-2665: Accept 2D inversion mesh (DrapeModel) in sensitivity_cutoff application
* GEOPY-2015: Add tooltips to missing IP inversion inputs
* GEOPY-2897: DC2D with single line crashes on run with n_workers set
* GEOPY-2898: Investigate edge cells recovered with DC2D inversions
### Joint Inversion
* GEOPY-2620: Joint surveys using mvi crashes with dimension mismatch
* GEOPY-2801: PGI: Add checks for reference model present on inversion groups. Return clean GeoAppsError if not
* GEOPY-2866: Research auto-scaling strategy for cross-gradient regularization terms
* GEOPY-2905: Membership flip between iterations in PGI
* GEOPY-2641: Add PGI documentation
### General Utilities
* GEOPY-2587: Add dip_direction to list of supported variables by plate_sweep
* GEOPY-2683: Micro-management of auto-scaling of misfits with tiles, channels and within joint inversions
* GEOPY-2622: Clip limits of topography extent based on mesh extent
* GEOPY-1029: Add datetime stamp to simpeg.log and simpeg.out file names
* GEOPY-2590: Add validator for negative on NDV values in uncertainties
* GEOPY-2684: Transfer visual parameters Core volume settings from the input mesh to the inversion mesh (if present)
* GEOPY-2865: Add optional out_group to Depth of Investigation app
### Bugs and Maintenance
* GEOPY-2508: Update GravityUIJson with new data forms
* GEOPY-2618: Conductivity/Resistivity switcher doesn't make sense for joint mvi/mag
* GEOPY-2519: Synthetic topography for runtests is overly sampled
* GEOPY-2704: Fix capitalization in labels and tooltips of ui.json files
* GEOPY-2661: Update minimum requirement to python >=3.12, <3.15 and numpy 2.*
* GEOPY-2758: Implement direct run_commands to specific modules for forwards and inversions
* GEOPY-2775: DCIP 2D crash on line ID selection
* GEOPY-2594: PGI failure on petrophysical model with air cells
* GEOPY-2781: Inversion stalls on tiling for large problems during redistribution of clusters
* GEOPY-2714: Refactor extent property calculation for all grid objects
* GEOPY-2770: Consolidate code for plate model definition between different repos
* GEOPY-2795: Update dictionary to choose driver from run_command
* GEOPY-2813: Triangulation crash on input surface
* GEOPY-2833: Regularization parameters of sub-drivers always over-written by joint parameters
* GEOPY-2862: Inversion crash on tile mesh creation transferring data
* GEOPY-2745: Refresh screenshots of UIJsons in docs

## Release 0.4.0 (2026-01-06)

* GEOPY-2108: Support 3D vector property group for orientation of rotated gradients
* GEOPY-2110: Add rotated_gradient to 2D inversions
* GEOPY-789: Joint inversion: PGI
* GEOPY-2232: Refactor components of inversion options
* GEOPY-2188: single entry point to run any application
* GEOPY-789: Joint inversion: PGI
* GEOPY-2276: Migrate param-sweeps to geoapps-utils
* GEOPY-2264: Migrate plate-simulation to simpeg-drivers
* GEOPY-2173: Hook up 2D rotated gradients to batch 2D inversions
* GEOPY-2124: Investigate random failure of cross-gradient test
* GEOPY-2291: Amplitude model stuck on upper bound for MVI
* GEOPY-2285: Change default sensitivity threshold for DC inversions
* GEOPY-2310: Fix plate simulation label and tooltip
* GEOPY-2314: Speed up saving directive by keeping the file open during series
* GEOPY-2303: Change units displayed on selector of data type for V/Am^2
* GEOPY-2320: Investigate slow startup time for TEM inversion
* GEOPY-2329: Make pydantic validator issues returns clean GeoAppsError option
* GEOPY-2297: Add case study with Forestania datasets
* GEOPY-2362: Improve rotated gradient on octree change with average cell dim
* GEOPY-2297: Add files via upload
* GEOPY-2297: Add case study with Forestania datasets
* GEOPY-2111: Add docs on rotated gradient options
* GEOPY-2387: force use of MKL for Blas implementation
* GEOPY-2404: Bad flipping of large loop orientation
* GEOPY-2389: Refactor of the Factory classes
* GEOPY-2157: Migrate octree-creation-app to grid-app
* GEOPY-2376: Investigate double-print of of Geoapps-Error
* GEOPY-2405: Can't handle topography grid with nan
* GEOPY-2182: Parallelize 1D simulations
* GEOPY-2365: Forward simulation of potential fields always form the full J
* GEOPY-2393: Re-order parameters to mimic the order in metadata
* GEOPY-2395: Add check for negative cond/res model values
* GEOPY-2357: Lost control on reference angles for MVI
* GEOPY-2386: Add core depth to the max-min elevation of the survey
* GEOPY-2364: Detect issues with waveform and throw a custom GeoappsError if found
* GEOPY-2440: add a copy group+object base in input file as it exists uin ui json group
* GEOPY-2461: Failure of directives when using Futures for simulation
* GEOPY-2058: Create custom sweep UIjson for plate-simulation
* GEOPY-2467: Investigate speckly looking MVI models with rotated gradients
* GEOPY-2457: Make start/stop group optional, and use the plate-sim parameter instead if disabled
* GEOPY-2482: Missing grouping of EM data in save directive for joint inversions
* GEOPY-2466: Parallelize the Sweeps
* GEOPY-2447: Explore 2D gridding techniques for EM line data
* GEOPY-2156: Pydantic error on auto-mesh creation with Grid2D topography object
* GEOPY-425: Crash on Zarr file shape for tiled inversions with disk storage
* GEOPY-2518: Crash on no-upper bound for MVI within a joint process
* GEOPY-2526: Improve parallel creation of 1D simulations
* GEOPY-2466: Parallelize the Sweeps
* GEOPY-2542: Investigate erratic corner cells when using rotated gradients
* GEOPY-2421: Add custom error for topography grid selected without data
* GEOPY-2549: Random failure of sensitivity cutoff app tests
* GEOPY-2546: Workers crash on creating misfits for large problems
* GEOPY-2549: Random failure of sensitivity cutoff app tests
* GEOPY-2550: Remove save directive for petrophysical model
* GEOPY-2538: Adjust target misfit down to account for number of NDV in data
* GEOPY-2551: PGI fails with single simulation selected
* GEOPY-2568: MT predicted channels missing [] indices
* GEOPY-2556: Break edge case for 1D inversion with negative elevation (release 4.7)
* GEOPY-2557: Save sensitivities option ignored (release 4.7)
* GEOPY-2569: Wrong normalization for MT
* GEOPY-2574: Speed up active from topography algorithm
* GEOPY-2613: bring in doc of plate simulation
* GEOPY-2621: Remove out_group form ui.json. It's redundant, and was currently fai…
* GEOPY-2605: Cannot load results from Batch 2D inversion runs
* DEVOPS-922: adjust or fix text in ui.json
* GEOPY-2624: check for MVI Simpeg groups and raise error
* GEOPY-2619: Joint surveys fails validation if no starting/reference models chosen

## Release 0.3.0 (2025-06-20)

* GEOPY-760: Create spatial tiling estimator
* GEOPY-1820: Add a depth of investigation application
* GEOPY-1788: Add auto-meshing option for all inversions with default parameters
* GEOPY-1874: Fix simpeg-drivers pyproject still pointing to octree-creation-app/* GEOPY-1788
* GEOPY-1871: Auto-meshing: Round cell size to nearest 5 multiplier
* GEOPY-1865: Allow option for percentile cutoff in sensitivity based depth of investigation
* GEOPY-1880: Auto-meshing: Only use depth_code (no vertical pads) for potential fields and DC-IP inversions
* GEOPY-1864: Add UIJson group to hold octree creation parameters and update options
* GEOPY-1946: Octree mesh upside down
* GEOPY-1842: Refactor Params class with BaseData
* GEOPY-1962: Convert all of potential fields to BaseData params class
* GEOPY-1980: Faulty air cells in 2D inversion active
* GEOPY-1499: Reduce tests runtime
* GEOPY-1879: Use MetaSimulations instead of custom misfit mapping towards distributed process
* GEOPY-1963: Convert all DC/IP 3D/2D params to BaseData
* GEOPY-1965: Convert all EM params to BaseData
* GEOPY-1966: Convert both joint params to BaseData
* GEOPY-2001: Export uml from simpeg-drivers and design class structure for inversion parameters.
* GEOPY-1944: Selecting an active model instead of topography with surface survey option crashes
* GEOPY-2023: Update discretize to >=0.11.*
* GEOPY-2032: Cleanup constant files and data classes
* GEOPY-2002: Add version validation and write_default method to update version in …
* GEOPY-2029: Update SimPEG 0.21.2 to 0.23
* GEOPY-1997: Crash running 2D IP
* GEOPY-1912: Add custom Error for problem too large
* GEOPY-2003: Add UIJson class for gravity forward/inversion
* GEOPY-1729: Add option for MUMPS solver
* GEOPY-2025: Duplicated survey object when monitoring_directory is used
* GEOPY-2048: Resolve deprecation warnings with latest simpeg 0.23 and discretize 0.11
* GEOPY-1866: Create documentation for depth of investigation app
* GEOPY-2003: Add UIJson class for gravity forward/inversion
* GEOPY-2029: fixup dependencies
* GEOPY-2048: Resolve deprecation warnings with latest simpeg 0.23 and discretize 0.11
* GEOPY-2004: Draft uml file for the UIJson/Params design
* GEOPY-1867: Update inversion docs to describe the auto-mesh option
* GEOPY-2045: Phi-d at Iter 0 shows as nan in the *.out file
* GEOPY-2056: Handle extra fields and deprecations in UIJson version validation
* GEOPY-2068: Clean up pydantic warnings
* GEOPY-2075: Implement structural orientation (rotated gradient) option to the inversion UI
* GEOPY-95: Migrate em_inversion (EM1D) script to simpeg-drivers
* GEOPY-2097: Should update version when writing ui.json from simpeg-drivers options classes
* GEOPY-2103: Migrate FEM-1D from simpeg-drivers
* GEOPY-2105: Make lower bound for MVI visible=False
* GEOPY-2115: Add strike/dip option to the choice list of rotated_gradients.
* GEOPY-2109: Deprecate gradient_type
* GEOPY-2046: Fix warning about differing number of parameters between ui_json and data.
* GEOPY-2049: relock on latest git dev revisions
* GEOPY-2049: environment for coming pre-release
* GEOPY-2128: fix UI json version tests (part of GEOPY-2049)
* GEOPY-2127: Rename params modules to options
* GEOPY-1827: Group models for L2 and LP
* GEOPY-2134: Add version to print screen
* GEOPY-2133: Allow IntegerData for active cell value model type
* GEOPY-2049: use published dependencies, no git branches
* GEOPY-2141: correctly declare dask for pip and dask-core for conda
* GEOPY-2141: fixup dask dependency: do not lock on pypi
* GEOPY-2137: Use dask.distributed with workers as default behaviour
* GEOPY-2144: IP inversion with resistivity option does not convert the model to conductivity
* GEOPY-2147: Name of conductivity_model does not match the selection for resistivity
* GEOPY-2150: Change default auto-scaling to false
* GEOPY-2142: bring back adjusted ui.json from Analyst to their respective repo
* GEOPY-2152: Bad referencing to transmitter id name
* GEOPY-2154: MVI name change brakes the forward
* GEOPY-2049: fem1d title
* GEOPY-2183: Outdated inversion_type for 3D FDEM
* GEOPY-2190: Non-zero evaluation of the rotated gradient of a constant model
* GEOPY-2194: Sub-mesh reused on split data
* GEOPY-2143: ensure backward compatibility of saved ui.json from Analyst 4.5 to 4.6

## Release 0.2.0 (2025-02-07)

* GEOPY-1503: Octree mesh cell definition not update if rec array
* GEOPY-1527: Make the canny add_data optional on get_edges method
* GEOPY-1552: Crash on joint survey with apparent resistivity
* GEOPY-1573: Update simpeg fork to 0.21.2
* GEOPY-1255: Enforce counter-clock wise ordering of EM large loops
* GEOPY-1681: Streamline geoapps-utils
* GEOPY-1663: Generate tutorial for Natural source EM
* GEOPY-1684: Add checks on waveform before sending to SimPEG
* GEOPY-1704: Training material for ATEM
* GEOPY-1656: Always check/closed EM loops and return warning
* GEOPY-1730: Fix handling of UBC ordered Octree cells
* GEOPY-1717: Add docs for validation
* GEOPY-1719: allow input active cells instead of topography
* GEOPY-1727: Fix formatting of warning for LargeLoop. Use logging instead warning
* GEOPY-421: Inversion: Allow for model vector to define norms
* GEOPY-1774: Re-order the inversion inputs following users comments
* GEOPY-1448: Add option to export sensitivities for all inversions
* GEOPY-496: Enable cell/face weights in params
* GEOPY-415: Fill in default ui.json tooltips for inversion parameters
* GEOPY-1734: Review stitching of predicted data on tipper inversion
* GEOPY-1746: Review log and out for cross-gradient inversion.
* GEOPY-1792: Regression: Crash with no-reference data
* GEOPY-1787: Group vector model orientation parameters as "Dip Direction & Dip"
* GEOPY-1791: Add option for cond/resis for all EM/DC methods
* GEOPY-1818: Flip upper and lower bound value for resistivity style inversions
* GEOPY-1531: Implement rescaling of misfit functions for joint inversion
* GEOPY-1824: Tipper inversion crashes on background_model if not constant
* GEOPY-1825: DC3D inversion reports disconnected cells
* GEOPY-1896: Ram/Disk option not working in simpeg through Analyst
* GEOPY-1897: Save sensitivities fails for MVI inversion in Analyst
* GEOPY-1888: Nan data values not handled by the inversion
* GEOPY-1901: Simpeg-drivers is adding a transmitter id to the transmitter always
* GEOPY-1914: Make the transmitter id name agnostic


## Release 0.1.0 (2024-06-17)

* GEOPY-1265: Copy model to avoid applying double log
* GEOPY-1472: prepare distribution
* GEOPY-1477: Remove factor of half on cpu count for n_cpu=disabled
* GEOPY-1497: fix reduced set of linter errors on simpeg-drivers
* GEOPY-1472: regenerate env lock files (for SimPEG rc.1)
* GEOPY-1476: Enforce counter-clock wise loop for TEM large loop
* GEOPY-1495: Move params tests from geoapps to simpeg-drivers
* GEOPY-1478: Deal with negative octree cell dimensions from legacy inversions
* GEOPY-1500: Improve tiling strategy for large loop EM
* GEOPY-1516: Improve scaling of cross-gradient regularization
* GEOPY-1472: build distribution files for geology and geophysics modules for Analyst
* GEOPY-863: use new dev script to create lock files
* GEOPY-1556: Fix tile ID on save directive
* GEOPY-1566: new RC distribution for Analyst 4.4
* GEOPY-1584: import of simpeg-drivers too slow
* GEOPY-1489: merge Release/0.1.0 to main
* GEOPY-1489: use octree-creation-app v0.1.1

 Copyright (c) 2023-2026 Mira Geoscience Ltd.
