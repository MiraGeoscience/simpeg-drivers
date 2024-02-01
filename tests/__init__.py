#  Copyright (c) 2022-2023 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved.
from simpeg_drivers.utils.testing import setup_inversion_workspace

GEOH5, _, model, survey, topography = setup_inversion_workspace(
    work_dir="",  # r"C:\Users\jamieb\Documents\repos\simpeg-drivers\simpeg_drivers-assets",
    background=0.001,
    anomaly=1.0,
    n_electrodes=2,
    n_lines=2,
    refinement=(2,),
    inversion_type="airborne_tem",
    drape_height=10.0,
    padding_distance=400.0,
    flatten=False,
)
