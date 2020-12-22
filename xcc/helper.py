"""Different helper functions for generating container recipe
"""

from typing import List, Union

import hpccm.primitives
from hpccm.primitives import shell, comment, environment

from hpccm.templates.git import git
from hpccm.templates.CMakeBuild import CMakeBuild

import xcc.config


def build_git_and_cmake(
    name: str,
    url: str,
    branch: str,
    config: xcc.config.XCC_Config,
    opts=[],
) -> List[Union[shell, comment]]:
    """Combines git clone, cmake and cmake traget='install'

    :param name: name of the project
    :type name: str
    :param url: git clone url
    :type url: str
    :param branch: branch or version (git clone --branch)
    :type branch: str
    :param config: Configuration object, which contains different information for the stage
    :type config: xcc.config.XCC_Config
    :param opts: a list of CMAKE arguments (e.g. -DCMAKE_BUILD_TYPE=RELEASE)
    :type opts: List[str]
    :returns: list of hpccm.primitives commands for git and cmake
    :rtype: List[Union[shell, comment]]

    """
    instr: List[Union[shell, comment]] = []

    instr.append(add_comment_heading("Build " + name))

    cm: List[str] = []
    git_conf = git()
    cm.append(
        git_conf.clone_step(
            repository=url, branch=branch, path=config.build_prefix, directory=name
        )
    )
    cmake_conf = CMakeBuild(prefix=config.install_prefix)
    cm_build_dir = config.build_prefix + "/" + name + "_build"
    cm_source_dir = config.build_prefix + "/" + name
    cm.append(
        cmake_conf.configure_step(
            build_directory=cm_build_dir, directory=cm_source_dir, opts=opts
        )
    )
    cm.append(
        cmake_conf.build_step(
            parallel=config.get_cmake_compiler_threads(), target="install"
        )
    )
    if not config.keep_build:
        config.paths_to_delete.append(cm_build_dir)
        config.paths_to_delete.append(cm_source_dir)

    instr.append(shell(commands=cm))

    return instr


def add_libcxx_cmake_arg(inputList: List[str]) -> List[str]:
    """If the class attribute build_libcxx is true, add -DCMAKE_CXX_FLAGS="-stdlib=libc++" to cmake flags in inputlist.

    :param inputlist: List of cmake flags
    :type inputlist: List[str]
    :returns: inputlist plus -DCMAKE_CXX_FLAGS="-stdlib=libc++" if self.build_libcxx is true
    :rtype: List[str]

    """
    for i, elem in enumerate(inputList):
        if elem.startswith('-DCMAKE_CXX_FLAGS="'):
            inputList[i] = elem[:-1] + ' -stdlib=libc++"'
            return inputList

    inputList.append('-DCMAKE_CXX_FLAGS="-stdlib=libc++"')
    return inputList


def add_comment_heading(msg: str) -> hpccm.primitives.comment:
    """Create a nice heading for the recipe.

    :param msg: Title of the heading
    :type msg: str
    :returns: Heading with titel
    :rtype: hpccm.primitives.comment

    """
    return comment(
        "////////////////////////////////////////////////////////////////////"
        + "{:/^68}".format(" {} ".format(msg))
        + "////////////////////////////////////////////////////////////////////"
    )
