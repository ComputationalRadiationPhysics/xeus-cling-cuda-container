"""Function to create build instructions for miniconda.
"""

from typing import Tuple, List, Dict

from hpccm.templates.rm import rm

import xcc.config


def build_miniconda(config: xcc.config.XCC_Config) -> Tuple[List[str], Dict[str, str]]:
    """Return Miniconda 3 installation instructions

        :param config: Configuration object, which contains different information for the stage
        :type config: xcc.config.XCC_Config
        :returns: list of bash commands and dictionary of environment variables
        :rtype: [str], {str,str}

        """
    conda_bin = config.install_prefix + "/miniconda3/bin/"
    conda_exe = conda_bin + "conda"
    cm = [
        "",
        "#///////////////////////////////////////////////////////////",
        "#// Install Miniconda 3                                   //",
        "#///////////////////////////////////////////////////////////",
        "cd /tmp",
        "wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh",
        "chmod u+x Miniconda3-latest-Linux-x86_64.sh",
        "./Miniconda3-latest-Linux-x86_64.sh -b -p "
        + config.install_prefix
        + "/miniconda3",
        "export PATH=$PATH:" + conda_bin,
        conda_exe + " install -y -c conda-forge nodejs",
        conda_exe + " install -y jupyter",
        conda_exe + " install -y -c conda-forge jupyterlab",
        conda_exe + " install -y -c biobuilds libuuid",
        conda_exe + " install -y widgetsnbextension -c conda-forge",
        conda_bin + "jupyter labextension install @jupyter-widgets/jupyterlab-manager",
        "rm /tmp/Miniconda3-latest-Linux-x86_64.sh",
        "cd -",
    ]

    return cm, {"PATH": "$PATH:" + conda_bin}
