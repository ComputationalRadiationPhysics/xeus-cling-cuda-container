"""Function to create build instructions for miniconda.
"""

from typing import List, Union

from hpccm.templates.rm import rm
from hpccm.primitives import shell, comment, environment

import xcc.config
from xcc.helper import add_comment_heading


def build_miniconda(
    config: xcc.config.XCC_Config,
) -> List[Union[shell, comment, environment]]:
    """Return Miniconda 3 installation instructions

    :param config: Configuration object, which contains different information for the stage
    :type config: xcc.config.XCC_Config
    :returns: list of hpccm.primitives
    :rtype: List[Union[shell, comment, environment]]

    """
    instr: List[Union[shell, comment, environment]] = []

    instr.append(add_comment_heading("Install Miniconda 3"))

    conda_bin = config.install_prefix + "/miniconda3/bin/"
    conda_exe = conda_bin + "conda"
    instr.append(
        shell(
            commands=[
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
                conda_bin
                + "jupyter labextension install @jupyter-widgets/jupyterlab-manager",
                "rm /tmp/Miniconda3-latest-Linux-x86_64.sh",
                "cd -",
            ]
        )
    )

    instr.append(environment(variables={"PATH": "$PATH:" + conda_bin}))

    return instr
