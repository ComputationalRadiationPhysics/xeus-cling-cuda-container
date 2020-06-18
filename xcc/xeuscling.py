"""Function to create xeus-cling build instruction.
"""

from typing import List, Union

from hpccm.templates.git import git
from hpccm.templates.CMakeBuild import CMakeBuild

import xcc.config


def build_xeus_cling(
    build_prefix: str,
    build_type: str,
    url: str,
    branch: str,
    threads: int,
    config: xcc.config.XCC_Config,
    miniconda_path: str,
    cling_path: List[str],
    force_keep_build: bool = None,
    second_build=None,
    build_libcxx=None,
) -> List[str]:
    """Return Cling build instructions.

        :param build_prefix: path where source code is cloned and built
        :type build_prefix: str
        :param build_type: CMAKE_BUILD_TYPE
        :type build_type: str
        :param url: git clone url
        :type url: str
        :param branch: branch or version (git clone --branch)
        :type branch: str
        :param threads: number of threads for make -j (None for make -j$(nproc))
        :type threads: int
        :param config: Configuration object, which contains different information for the stage
        :type config: xcc.config.XCC_Config
        :param miniconda_path: Path to the Miniconda installation. Set it as CMAKE_INSTALL_PREFIX
        :type miniconda_path: str
        :param cling_path: Paths to the cling installations. Dual build uses the first path for the first build and the second path for the second build.
        :type cling_path: List[str]
        :param force_keep_build: Overwrite keep_build of config object
        :type force_keep_build: bool
        :param second_build: Set a CMAKE_BUILD_TYPE to build xeus-cling a second time, e.g. if you want to have a debug and a release build of xeus-cling at the same time. The name of the build folder and CMAKE_INSTALL_PREFIX is extended by the CMAKE_BUILD_TYPE.
        :type second_build: str
        :param build_libcxx: Build the whole stack with libc++.
        :type build_libcxx: bool
        :returns:  a list of build instructions
        :rtype: List[str]

        """
    cm = []
    git_conf = git()
    cm.append(
        git_conf.clone_step(
            repository=url, branch=branch, path=build_prefix, directory="xeus-cling"
        )
    )

    # build_directories
    xeus_cling_builds = []

    if not second_build:
        xeus_cling_builds.append(build_prefix + "/xeus-cling_build")
    else:
        xeus_cling_builds.append(
            build_prefix + "/xeus-cling_build_" + build_type.lower()
        )
        xeus_cling_builds.append(
            build_prefix + "/xeus-cling_build_" + second_build.lower()
        )

    # backup PATH
    # xeus-cling requires the llvm-config executable file from the cling installation
    # for dual build different bin paths are necessary
    cm.append("bPATH=$PATH")
    # index
    i = 0
    for build_dir in xeus_cling_builds:
        # add path to llvm-config for the xeus-cling build
        cm.append("PATH=$bPATH:/" + cling_path[i] + "/bin")
        cmake_opts = [
            "-DCMAKE_INSTALL_LIBDIR=" + miniconda_path + "/lib",
            "-DCMAKE_LINKER=/usr/bin/gold",
            "-DCMAKE_BUILD_TYPE=" + build_type,
            "-DDISABLE_ARCH_NATIVE=ON",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
            "-DCMAKE_PREFIX_PATH=" + cling_path[i],
            '-DCMAKE_CXX_FLAGS="-I ' + cling_path[i] + '/include"',
        ]

        if build_libcxx:
            cmake_opts.append('-DCMAKE_CXX_FLAGS="-stdlib=libc++"')

        cmake_conf = CMakeBuild(prefix=miniconda_path)
        cm.append(
            cmake_conf.configure_step(
                build_directory=build_dir,
                directory=build_prefix + "/xeus-cling",
                opts=cmake_opts,
            )
        )
        cm.append(cmake_conf.build_step(parallel=threads, target="install"))
        i += 1

    if force_keep_build != None:
        keep_build = force_keep_build
    else:
        keep_build = config.keep_build

    if not keep_build:
        for build_dir in xeus_cling_builds:
            config.paths_to_delete.append(build_dir)
        config.paths_to_delete.append(build_prefix + "/xeus-cling")

    return cm
