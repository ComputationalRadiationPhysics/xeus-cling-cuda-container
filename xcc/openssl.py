"""Function to create build instructions for openssl.
"""

from typing import Union, List, Tuple, List, Dict

from hpccm.templates.wget import wget
from hpccm.templates.tar import tar

import xcc.config


def build_openssl(
    name: str,
    build_prefix: str,
    install_prefix: str,
    threads: int,
    config: xcc.config.XCC_Config,
) -> Tuple[List[str], Dict[str, str]]:
    """install openssl

        :param name: Name of the version (e.g. openssl-1.1.1c). Should be sliced from the official URL.
        :type name: str
        :param build_prefix: path where source code is stored and built
        :type build_prefix: str
        :param install_prefix: CMAKE_INSTAll_PREFIX
        :type install_prefix: str
        :param threads: number of threads for make -j (None for make -j$(nproc))
        :type threads: int
        :param config: Configuration object, which contains different information for the stage
        :type config: xcc.config.XCC_Config
        :returns: list of bash commands and dictionary of environment variables
        :rtype: List[str], {str,str}

        """
    make_threads = "$(nproc)"
    if threads:
        make_threads = str(threads)

    cm = []
    wget_ssl = wget()
    tar_ssl = tar()
    cm.append(
        wget_ssl.download_step(
            url="https://www.openssl.org/source/" + name + ".tar.gz",
            directory=build_prefix,
        )
    )
    cm.append(
        tar_ssl.untar_step(
            tarball=build_prefix + "/" + name + ".tar.gz", directory=build_prefix
        )
    )
    cm.append("cd " + build_prefix + "/" + name)
    cm.append("./config --prefix=" + install_prefix + " -Wl,-rpath=/usr/local/lib")
    cm.append("make -j" + make_threads)
    cm.append("make install -j" + make_threads)
    cm.append("cd -")
    if not config.keep_build:
        config.paths_to_delete.append(build_prefix + "/" + name)
        config.paths_to_delete.append(build_prefix + "/" + name + ".tar.gz")

    return cm, {"OPENSSL_ROOT_DIR": install_prefix}
