"""Function to create build instructions for openssl.
"""

from typing import Union, List, Tuple, List, Dict

from hpccm.primitives import shell, comment, environment
from hpccm.templates.wget import wget
from hpccm.templates.tar import tar

import xcc.config
from xcc.helper import add_comment_heading


def build_openssl(
    name: str,
    config: xcc.config.XCC_Config,
) -> List[Union[shell, comment, environment]]:
    """install openssl

    :param name: Name of the version (e.g. openssl-1.1.1c). Should be sliced from the official URL.
    :type name: str
    :param config: Configuration object, which contains different information for the stage
    :type config: xcc.config.XCC_Config
    :returns: list of hpccm.primitives
    :rtype: List[Union[shell, comment, environment]]

    """
    instr: List[Union[shell, comment, environment]] = []
    make_threads = config.get_cmake_compiler_threads()

    instr.append(add_comment_heading("Install OpenSSL"))

    cm: List[str] = []
    wget_ssl = wget()
    tar_ssl = tar()
    cm.append(
        wget_ssl.download_step(
            url="https://www.openssl.org/source/" + name + ".tar.gz",
            directory=config.build_prefix,
        )
    )
    cm.append(
        tar_ssl.untar_step(
            tarball=config.build_prefix + "/" + name + ".tar.gz",
            directory=config.build_prefix,
        )
    )
    cm.append("cd " + config.build_prefix + "/" + name)
    cm.append(
        "./config --prefix=" + config.install_prefix + " -Wl,-rpath=/usr/local/lib"
    )
    cm.append("make -j" + make_threads)
    cm.append("make install -j" + make_threads)
    cm.append("cd -")
    if not config.keep_build:
        config.paths_to_delete.append(config.build_prefix + "/" + name)
        config.paths_to_delete.append(config.build_prefix + "/" + name + ".tar.gz")

    instr.append(shell(commands=cm))
    instr.append(environment(variables={"OPENSSL_ROOT_DIR": config.install_prefix}))

    return instr
