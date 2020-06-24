"""Function to create xeus-cling build instruction.
"""

from typing import List, Union

from hpccm.templates.git import git
from hpccm.templates.CMakeBuild import CMakeBuild

import xcc.config
from xcc.helper import add_libcxx_cmake_arg


def build_xeus_cling(
    url: str, branch: str, config: xcc.config.XCC_Config,
) -> List[str]:
    """Return Cling build instructions.

        :param url: git clone url
        :type url: str
        :param branch: branch or version (git clone --branch)
        :type branch: str
        :param config: Configuration object, which contains different information for the stage
        :type config: xcc.config.XCC_Config
        :returns:  a list of build instructions
        :rtype: List[str]

        """
    cm = [
        "",
        "#///////////////////////////////////////////////////////////",
        "#// Install Xeus-Cling                                    //",
        "#///////////////////////////////////////////////////////////",
    ]
    git_conf = git()
    cm.append(
        git_conf.clone_step(
            repository=url,
            branch=branch,
            path=config.build_prefix,
            directory="xeus-cling",
        )
    )

    # backup PATH
    # xeus-cling requires the llvm-config executable file from the cling installation
    # for dual build different bin paths are necessary
    cm.append("bPATH=$PATH")
    for build in config.get_xeus_cling_build():
        cm += [
            "",
            "#/////////////////////////////",
            "{:<28}".format("#// Build Xeus-Cling " + build.build_type) + "//",
            "#/////////////////////////////",
        ]
        # add path to llvm-config for the xeus-cling build
        cm.append("PATH=$bPATH:/" + build.cling_install_path + "/bin")

        cmake_opts = [
            "-DCMAKE_INSTALL_LIBDIR=" + config.get_miniconda_path() + "/lib",
            "-DCMAKE_LINKER=/usr/bin/gold",
            "-DCMAKE_BUILD_TYPE=" + build.build_type,
            "-DDISABLE_ARCH_NATIVE=ON",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
            "-DCMAKE_PREFIX_PATH=" + build.cling_install_path,
            '-DCMAKE_CXX_FLAGS="-I ' + build.cling_install_path + '/include"',
        ]

        if config.build_libcxx:
            cmake_opts = add_libcxx_cmake_arg(cmake_opts)

        cmake_conf = CMakeBuild(prefix=config.get_miniconda_path())
        cm.append(
            cmake_conf.configure_step(
                build_directory=build.build_path,
                directory=config.build_prefix + "/xeus-cling",
                opts=cmake_opts,
            )
        )
        cm.append(
            cmake_conf.build_step(
                parallel=config.get_cmake_compiler_threads(), target="install"
            )
        )

    if not config.keep_build:
        for build in config.get_xeus_cling_build():
            config.paths_to_delete.append(build.build_path)
        config.paths_to_delete.append(config.build_prefix + "/xeus-cling")

    return cm
