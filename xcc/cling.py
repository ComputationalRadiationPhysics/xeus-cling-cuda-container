"""Function to create build instructions for cling.
"""

from typing import Tuple, List

from hpccm.templates.git import git
from hpccm.templates.CMakeBuild import CMakeBuild

import xcc.config


def build_cling(
    build_prefix: str,
    install_prefix: str,
    miniconda_prefix: str,
    build_type: str,
    cling_url: str,
    config: xcc.config.XCC_Config,
    force_keep_build: bool = None,
    cling_branch=None,
    cling_hash=None,
    threads=None,
    linker_threads=None,
    dual_build=None,
    git_cling_opts=["--depth=1"],
    build_libcxx=None,
) -> Tuple[List[str], List[str]]:
    """Return Cling build instructions.

        :param build_prefix: path where source code is cloned and built
        :type build_prefix: str
        :param install_prefix: CMAKE_INSTALL_PREFIX
        :type install_prefix: str
        :param miniconda_prefix: path to the miniconda3 installation
        :type miniconda_prefix: str
        :param build_type: CMAKE_BUILD_TYPE
        :type build_type: str
        :param cling_url: GitHub url of the Cling repository
        :type cling_url: str
        :param cling_branch: GitHub branch of the Cling repository
        :type cling_branch: str
        :param cling_hash: GitHub commit hash of the Cling repository
        :type cling_hash: str
        :param threads: number of ninja compile threads and linker threads, if not set extra
        :type threads: int
        :param linker_threads: number of ninja linker threads
        :type linker_threads: int
        :param config: Configuration object, which contains different information for the stage
        :type config: xcc.config.XCC_Config
        :param force_keep_build: Overwrite keep_build of config object
        :type force_keep_build: bool
        :param dual_build: Set a CMAKE_BUILD_TYPE to build cling a second time, e.g. if you want to have a debug and a release build of cling at the same time. The name of the build folder and CMAKE_INSTALL_PREFIX is extended by the CMAKE_BUILD_TYPE.
        :type dual_build: str
        :param git_cling_opts: Setting options for Git Clone
        :type git_cling_opts: [str]
        :param build_libcxx: Build the whole stack with libc++. Also add the
                             libc++ and libc++abi projects to the llvm build.
        :type build_libcxx: bool
        :returns: a list of build instructions and a list of the install folders
        :rtype: [str],[str]



    :param build_prefix:
    :param install_prefix:
    :param miniconda_prefix:
    :param build_type:
    :param cling_url:
    :param config:
    :param force_keep_build:
    :param cling_branch:
    :param cling_hash:
    :param threads:
    :param linker_threads:
    :param dual_build:
    :param git_cling_opts:
    :param build_libcxx:

    """
    if threads == None:
        c_threads = "$(nproc)"
    else:
        c_threads = threads

    if linker_threads == None:
        l_threads = c_threads
    else:
        l_threads = linker_threads

    cbc: List[str] = []
    git_llvm = git()
    cbc.append(
        git_llvm.clone_step(
            repository="http://root.cern.ch/git/llvm.git",
            branch="cling-patches",
            path=build_prefix,
            directory="llvm",
        )
    )
    git_clang = git()
    cbc.append(
        git_clang.clone_step(
            repository="http://root.cern.ch/git/clang.git",
            branch="cling-patches",
            path=build_prefix + "/llvm/tools",
        )
    )
    git_cling = git(opts=git_cling_opts)
    cbc.append(
        git_cling.clone_step(
            repository=cling_url,
            branch=cling_branch,
            commit=cling_hash,
            path=build_prefix + "/llvm/tools",
        )
    )
    # add libc++ and libcxxabi to the llvm project
    # Comaker detect the projects automatically and builds it.
    if build_libcxx:
        git_libcxx = git()
        cbc.append(
            git_libcxx.clone_step(
                repository="https://github.com/llvm-mirror/libcxx",
                branch="release_50",
                path=build_prefix + "/llvm/projects",
            )
        )
        git_libcxxabi = git()
        cbc.append(
            git_libcxx.clone_step(
                repository="https://github.com/llvm-mirror/libcxxabi",
                branch="release_50",
                path=build_prefix + "/llvm/projects",
            )
        )

    # modify the install folder for dual build
    if not dual_build:
        cm_builds = [
            {
                "build_dir": build_prefix + "/cling_build",
                "install_dir": install_prefix,
                "build_type": build_type,
            }
        ]
    else:
        cm_builds = [
            {
                "build_dir": build_prefix + "/build_" + build_type.lower(),
                "install_dir": install_prefix + "/install_" + build_type.lower(),
                "build_type": build_type,
            },
            {
                "build_dir": build_prefix + "/build_" + dual_build.lower(),
                "install_dir": install_prefix + "/install_" + dual_build.lower(),
                "build_type": dual_build.lower(),
            },
        ]

    cling_install_prefix: List[str] = []

    for build in cm_builds:
        cmake_opts = [
            "-G Ninja",
            "-DCMAKE_BUILD_TYPE=" + build["build_type"],
            '-DLLVM_ABI_BREAKING_CHECKS="FORCE_OFF"',
            "-DCMAKE_LINKER=/usr/bin/gold",
            "-DLLVM_ENABLE_RTTI=ON",
            "'-DCMAKE_JOB_POOLS:STRING=compile={0};link={1}'".format(
                c_threads, l_threads
            ),
            "'-DCMAKE_JOB_POOL_COMPILE:STRING=compile'",
            "'-DCMAKE_JOB_POOL_LINK:STRING=link'",
            '-DLLVM_TARGETS_TO_BUILD="host;NVPTX"',
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        ]

        # build the project with libc++
        # the flag is not necessary to enable the build of libc++ and libc++abi
        if build_libcxx:
            cmake_opts.append("-DLLVM_ENABLE_LIBCXX=ON")

        cm_cling = CMakeBuild(prefix=build["install_dir"])
        cbc.append(
            cm_cling.configure_step(
                build_directory=build["build_dir"],
                directory=build_prefix + "/llvm",
                opts=cmake_opts,
            )
        )
        cbc.append(cm_cling.build_step(parallel=None, target="install"))
        cling_install_prefix.append(build["install_dir"])

        cbc.append("PATH_bak=$PATH")
        cbc.append("PATH=$PATH:" + build["install_dir"] + "/bin")
        cbc.append("cd " + build["install_dir"] + "/share/cling/Jupyter/kernel")
        cbc.append(miniconda_prefix + "/bin/pip install -e .")
        cbc.append("PATH=$PATH_bak")
        cbc.append("cd - ")

    if force_keep_build != None:
        keep_build = force_keep_build
    else:
        keep_build = config.keep_build

    if not keep_build:
        for build in cm_builds:
            config.paths_to_delete.append(build["build_dir"])
        config.paths_to_delete.append(build_prefix + "/llvm")

    return cbc, cling_install_prefix
