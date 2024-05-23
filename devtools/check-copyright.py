#!/usr/bin/env python3

# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#  All rights reserved.
#
#  This file is part of simpeg-drivers.
#
#  The software and information contained herein are proprietary to, and
#  comprise valuable trade secrets of, Mira Geoscience, which
#  intend to preserve as trade secrets such software and information.
#  This software is furnished pursuant to a written license agreement and
#  may be used, copied, transmitted, and stored only in accordance with
#  the terms of such license and with the inclusion of the above copyright
#  notice.  This software and information or any other copies thereof may
#  not be provided or otherwise made available to any other person.
#
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved.

from __future__ import annotations

import re
import sys
from datetime import date

if __name__ == "__main__":
    current_year = date.today().year
    copyright_re = re.compile(
        rf"\bcopyright \(c\) (:?\d{{4}}-|)\b{current_year}\b", re.IGNORECASE
    )
    files = sys.argv[1:]
    max_lines = 10
    report_files = []
    for f in files:
        with open(f, encoding="utf-8") as file:
            count = 0
            has_dated_copyright = False
            for line in file:
                count += 1
                if count >= max_lines and not (
                    f.endswith("README.rst") or f.endswith("README-dev.rst")
                ):
                    break
                if re.search(copyright_re, line):
                    has_dated_copyright = True
                    break

            if not has_dated_copyright:
                report_files.append(f)

    if len(report_files) > 0:
        for f in report_files:
            sys.stderr.write(f"{f}: No copyright or invalid year\n")
        sys.exit(1)

# readonly CURRENT_YEAR=$(date +"%Y")

# if ! grep -e "Copyright (c) .*$CURRENT_YEAR" $(head -10 $f) 2>&1 1>/dev/null; then
#    echo "File '$f' has no copyright or an invalid year"
#    exit 1
# fi
