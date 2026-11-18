import os
from datetime import datetime
from importlib.metadata import version as get_version

from packaging.version import Version


def configure_version(app, config):
    full_version = Version(get_version("simpeg-drivers"))
    release = full_version.public
    if full_version.is_postrelease:
        release = release.rsplit(".post", 1)[0]
    config.release = release
    config.version = full_version.base_version
    config.copyright = datetime.now().strftime("%Y, Mira Geoscience Ltd.")
    config.rst_epilog = (
        f"\n.. |copyright_notice| replace:: Copyright {config.copyright}.\n"
    )
    config.googleanalytics_id = os.environ.get("GOOGLE_ANALYTICS_ID", "")
    config.googleanalytics_enabled = bool(config.googleanalytics_id)


def setup(app):
    app.connect("config-inited", configure_version)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
