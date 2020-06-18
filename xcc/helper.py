"""Different helper functions for generating container recipe
"""

from typing import List, Union

from hpccm.templates.git import git
from hpccm.templates.CMakeBuild import CMakeBuild

import xcc.config


def build_git_and_cmake(
    name: str,
    build_prefix: str,
    install_prefix: str,
    url: str,
    branch: str,
    threads: int,
    config: xcc.config.XCC_Config,
    opts=[],
) -> List[str]:
    """Combines git clone, cmake and cmake traget='install'

        :param name: name of the project
        :type name: str
        :param build_prefix: path where source code is cloned and built
        :type build_prefix: str
        :param install_prefix: CMAKE_INSTALL_PREFIX
        :type install_prefix: str
        :param url: git clone url
        :type url: str
        :param branch: branch or version (git clone --branch)
        :type branch: str
        :param threads: number of threads for make -j (None for make -j$(nproc))
        :type threads: int
        :param config: Configuration object, which contains different information for the stage
        :type config: xcc.config.XCC_Config
        :param opts: a list of CMAKE arguments (e.g. -DCMAKE_BUILD_TYPE=RELEASE)
        :type opts: List[str]
        :returns: list of bash commands for git and cmake
        :rtype: List[str]

        """
    # commands
    cm = []
    git_conf = git()
    cm.append(
        git_conf.clone_step(
            repository=url, branch=branch, path=build_prefix, directory=name
        )
    )
    cmake_conf = CMakeBuild(prefix=install_prefix)
    cm_build_dir = build_prefix + "/" + name + "_build"
    cm_source_dir = build_prefix + "/" + name
    cm.append(
        cmake_conf.configure_step(
            build_directory=cm_build_dir, directory=cm_source_dir, opts=opts
        )
    )
    cm.append(cmake_conf.build_step(parallel=threads, target="install"))
    if not config.keep_build:
        config.paths_to_delete.append(cm_build_dir)
        config.paths_to_delete.append(cm_source_dir)
    return cm
