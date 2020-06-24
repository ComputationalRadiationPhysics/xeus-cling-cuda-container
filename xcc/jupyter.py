"""Functions to create build instructions for jupyter notebook and kernels.
"""

from typing import Dict, List, Union
import json

import xcc.config


def build_rel_jupyter_kernel(
    config: xcc.config.XCC_Config, user_install=False,
) -> List[str]:
    """Returns jupyter kernel and instructions to install it

        :param config: Configuration object, which contains different information for the stage
        :type config: xcc.config.XCC_Config
        :param user_install: if true, add flag --user to jupyter-kernelspec install
        :type user_install: bool
        :returns: list of bash commands
        :rtype: List[str]

        """
    user_install_arg = ""
    if user_install:
        user_install_arg = "--user "

    kernel_register: List[str] = []
    # xeus-cling cuda kernel
    for std in [11, 14, 17]:
        kernel_register += [
            "",
            "#/////////////////////////////",
            "{:<28}".format("#// Jupyter Kernel: Xeus " + str(std) + " cuda") + "//",
            "#/////////////////////////////",
        ]
        kernel_path = config.build_prefix + "/xeus-cling-cpp" + str(std) + "-cuda"
        kernel_register.append("mkdir -p " + kernel_path)
        kernel_register.append(
            "echo '"
            + gen_xeus_cling_jupyter_kernel(config.get_miniconda_path(), std)
            + "' > "
            + kernel_path
            + "/kernel.json"
        )
        kernel_register.append(
            "jupyter-kernelspec install " + user_install_arg + kernel_path
        )
        if not config.keep_build:
            config.paths_to_delete.append(kernel_path)

    # cling-cpp kernel
    for std in [11, 14, 17]:
        kernel_register += [
            "",
            "#/////////////////////////////",
            "{:<28}".format("#// Jupyter Kernel: Cling " + str(std)) + "//",
            "#/////////////////////////////",
        ]
        kernel_path = config.build_prefix + "/cling-cpp" + str(std)
        kernel_register.append("mkdir -p " + kernel_path)
        kernel_register.append(
            "echo '"
            + gen_cling_jupyter_kernel(std, False)
            + "' > "
            + kernel_path
            + "/kernel.json"
        )
        kernel_register.append(
            "jupyter-kernelspec install " + user_install_arg + kernel_path
        )
        if not config.keep_build:
            config.paths_to_delete.append(kernel_path)

    # cling-cuda kernel
    for std in [11, 14, 17]:
        kernel_register += [
            "",
            "#/////////////////////////////",
            "{:<28}".format("#// Jupyter Kernel: Cling " + str(std) + " cuda") + "//",
            "#/////////////////////////////",
        ]
        kernel_path = config.build_prefix + "/cling-cpp" + str(std) + "-cuda"
        kernel_register.append("mkdir -p " + kernel_path)
        kernel_register.append(
            "echo '"
            + gen_cling_jupyter_kernel(std, True)
            + "' > "
            + kernel_path
            + "/kernel.json"
        )
        kernel_register.append(
            "jupyter-kernelspec install " + user_install_arg + kernel_path
        )
        if not config.keep_build:
            config.paths_to_delete.append(kernel_path)

    return kernel_register


def build_dev_jupyter_kernel(config: xcc.config.XCC_Config) -> List[str]:
    """Returns jupyter kernel and instructions to install it in the miniconda3 folder. For release builds, please use build_rel_jupyter_kernel().

        :param config: Configuration object, which contains different information for the stage
        :type config: xcc.config.XCC_Config
        :returns: list of bash commands
        :rtype: List[str]

        """
    kernel_prefix = config.build_prefix + "/kernels"

    kernel_register = []
    kernel_register.append(
        "mkdir -p " + config.get_miniconda_path() + "/share/jupyter/kernels/"
    )

    # xeus-cling cuda kernel
    for std in [11, 14, 17]:
        kernel_register += [
            "",
            "#/////////////////////////////",
            "{:<28}".format("#// Jupyter Kernel: Xeus " + str(std) + " cuda") + "//",
            "#/////////////////////////////",
        ]
        kernel_path = kernel_prefix + "/xeus-cling-cpp" + str(std) + "-cuda"
        kernel_register.append("mkdir -p " + kernel_path)
        kernel_register.append(
            "echo '"
            + gen_xeus_cling_jupyter_kernel(config.get_miniconda_path(), std)
            + "' > "
            + kernel_path
            + "/kernel.json"
        )
        kernel_register.append(
            "cp -r "
            + kernel_path
            + " "
            + config.get_miniconda_path()
            + "/share/jupyter/kernels/"
        )
        if not config.keep_build:
            config.paths_to_delete.append(kernel_path)

    # cling-cpp kernel
    for std in [11, 14, 17]:
        kernel_register += [
            "",
            "#/////////////////////////////",
            "{:<28}".format("#// Jupyter Kernel: Cling " + str(std)) + "//",
            "#/////////////////////////////",
        ]
        kernel_path = kernel_prefix + "/cling-cpp" + str(std)
        kernel_register.append("mkdir -p " + kernel_path)
        kernel_register.append(
            "echo '"
            + gen_cling_jupyter_kernel(std, False)
            + "' > "
            + kernel_path
            + "/kernel.json"
        )
        kernel_register.append(
            "cp -r "
            + kernel_path
            + " "
            + config.get_miniconda_path()
            + "/share/jupyter/kernels/"
        )
        if not config.keep_build:
            config.paths_to_delete.append(kernel_path)

    # cling-cuda kernel
    for std in [11, 14, 17]:
        kernel_register += [
            "",
            "#/////////////////////////////",
            "{:<28}".format("#// Jupyter Kernel: Cling " + str(std) + " cuda") + "//",
            "#/////////////////////////////",
        ]
        kernel_path = kernel_prefix + "/cling-cpp" + str(std) + "-cuda"
        kernel_register.append("mkdir -p " + kernel_path)
        kernel_register.append(
            "echo '"
            + gen_cling_jupyter_kernel(std, True)
            + "' > "
            + kernel_path
            + "/kernel.json"
        )
        kernel_register.append(
            "cp -r "
            + kernel_path
            + " "
            + config.get_miniconda_path()
            + "/share/jupyter/kernels/"
        )
        if not config.keep_build:
            config.paths_to_delete.append(kernel_path)

    return kernel_register


def gen_xeus_cling_jupyter_kernel(miniconda_path: str, cxx_std: int) -> str:
    """Generate jupyter kernel description files with cuda support for different C++ standards. The kernels uses xeus-cling.

        :param miniconda_prefix: path to the miniconda installation
        :type miniconda_prefix: str
        :param cxx_std: C++ Standard as number (options: 11, 14, 17)
        :type cxx_std: int
        :returns: json string
        :rtype: str

        """
    return json.dumps(
        {
            "display_name": "Xeus-C++" + str(cxx_std) + "-CUDA",
            "argv": [
                miniconda_path + "/bin/xcpp",
                "-f",
                "{connection_file}",
                "-std=c++" + str(cxx_std),
                "-xcuda",
            ],
            "language": "C++" + str(cxx_std),
        }
    )


def gen_cling_jupyter_kernel(cxx_std: int, cuda: bool) -> str:
    """Generate jupyter kernel description files with cuda support for different C++ standards. The kernels uses the jupyter kernel of the cling project.

        :param cxx_std: C++ Standard as number (options: 11, 14, 17)
        :type cxx_std: int
        :param cuda: if true, create kernel description file with cuda support
        :type cuda: bool
        :returns: json string
        :rtype: str

        """
    kernel_json = {
        "display_name": "Cling-C++" + str(cxx_std) + ("-CUDA" if cuda else ""),
        "argv": [
            "jupyter-cling-kernel",
            "-f",
            "{connection_file}",
            "--std=c++" + str(cxx_std),
        ],
        "language": "C++",
    }

    if cuda:
        kernel_json["env"] = {"CLING_OPTS": "-xcuda"}  # type: ignore

    return json.dumps(kernel_json)
