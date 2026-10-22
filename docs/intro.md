# About

This module documents the use of [SimPEG](https://simpeg.xyz/) for geophysical data inversion with user-interface (UIjson) made available through the [Mira Geoscience-geoapps](https://mirageoscience-geoapps.readthedocs-hosted.com/) project.

```{image} ./images/ore_body.png
:width: 500px
```

 While the code itself has its own documentation, there is a need to demonstrate the effect of parameters controlling the inversion. This document is meant to be a reference guide with practical examples to help practitioners with their inversion work.

# Table of contents

```{tableofcontents}
```


# Running the applications

The main entry point to the various modules are the [*.ui.json](https://github.com/MiraGeoscience/simpeg-drivers/blob/develop/simpeg_drivers-assets/uijson)
files. The ``ui.json`` serves a dual purpose:

(1) rendering a user-interface in Geoscience ANALYST

(2) storing the input parameters chosen by the user for the program to run. See the [UIJson documentation](https://mirageoscience-geoh5py.readthedocs-hosted.com/en/latest/content/uijson_format/usage.html)
for more information about the ui.json interface.

The various user-interfaces can be accessed from the Geoscience ANALYST Pro Geophysics menu.

```{image} ./images/analyst_geophysics_menu.png
:width: 500px
```

The application can also be run from command line if all required fields in
the ui.json are provided. This approach is useful for advanced users who want to
automate the mesh creation process or re-run an existing mesh with different parameters.

To run any of the applications, assuming a valid Conda environment, use the following command:

``conda activate simpeg-drivers``

``python -m simpeg-drivers.driver [YOUR.ui.json]``

where ``[YOUR.ui.json]`` is the path to the input ui.json file on disk.


# References

```{bibliography}
```

 Copyright (c) 2023-2026 Mira Geoscience Ltd.
