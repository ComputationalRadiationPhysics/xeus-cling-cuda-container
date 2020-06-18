"""Function to create build instructions for miniconda.
"""

from typing import Tuple, List, Dict

import xcc.config


def build_miniconda(
    build_prefix: str, install_prefix: str, config: xcc.config.XCC_Config
) -> Tuple[List[str], Dict[str, str]]:
    """Return Miniconda 3 installation instructions

        :param build_prefix: path which the installation script is stored
        :type build_prefix: str
        :param install_prefix: path which miniconda is installed
        :type install_prefix: str
        :param config: Configuration object, which contains different information for the stage
        :type config: xcc.config.XCC_Config
        :returns: list of bash commands and dictionary of environment variables
        :rtype: [str], {str,str}

        """
    cm = [
        "cd " + build_prefix,
        "wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh",
        "chmod u+x Miniconda3-latest-Linux-x86_64.sh",
        "./Miniconda3-latest-Linux-x86_64.sh -b -p " + install_prefix + "/miniconda3",
        "export PATH=$PATH:" + install_prefix + "/miniconda3/bin/",
        install_prefix + "/miniconda3/bin/conda install -y -c conda-forge nodejs",
        install_prefix + "/miniconda3/bin/conda install -y jupyter",
        install_prefix + "/miniconda3/bin/conda install -y -c conda-forge jupyterlab",
        install_prefix + "/miniconda3/bin/conda install -y -c biobuilds libuuid",
        install_prefix
        + "/miniconda3/bin/conda install -y widgetsnbextension -c conda-forge",
        install_prefix
        + "/miniconda3/bin/jupyter labextension install @jupyter-widgets/jupyterlab-manager",
        "cd -",
    ]

    if not config.keep_build:
        config.paths_to_delete.append(
            build_prefix + "/Miniconda3-latest-Linux-x86_64.sh"
        )

    return cm, {"PATH": "$PATH:" + install_prefix + "/miniconda3/bin/"}
