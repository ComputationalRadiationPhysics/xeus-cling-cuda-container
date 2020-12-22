"""Function to create build instructions for cling.
"""

from typing import List, Union

from hpccm.primitives import shell, comment
from hpccm.templates.git import git
from hpccm.templates.CMakeBuild import CMakeBuild

import xcc.config
from xcc.helper import add_comment_heading


def build_cling(
    cling_url: str,
    config: xcc.config.XCC_Config,
    cling_branch=None,
    cling_hash=None,
    git_cling_opts=["--depth=1"],
) -> List[Union[shell, comment]]:
    """Return Cling build instructions.

    :param cling_url: GitHub url of the Cling repository
    :type cling_url: str
    :param cling_branch: GitHub branch of the Cling repository
    :type cling_branch: str
    :param cling_hash: GitHub commit hash of the Cling repository
    :type cling_hash: str
    :param config: Configuration object, which contains different information for the stage
    :type config: xcc.config.XCC_Config
    :param git_cling_opts: Setting options for Git Clone
    :type git_cling_opts: [str]
    :returns: a list of hpccm.primitives
    :rtype: List[Union[shell, comment]]

    """
    compiler_threads = config.get_cmake_compiler_threads()
    linker_threads = config.get_cmake_linker_threads()

    instr: List[Union[shell, comment]] = []

    instr.append(add_comment_heading("Install Cling"))
    instr.append(add_comment_heading("Download Cling sources"))

    prepare_sources: List[str] = []

    git_llvm = git()
    prepare_sources.append(
        git_llvm.clone_step(
            repository="http://root.cern.ch/git/llvm.git",
            branch="cling-patches",
            path=config.build_prefix,
            directory="llvm",
        )
    )
    git_clang = git()
    prepare_sources.append(
        git_clang.clone_step(
            repository="http://root.cern.ch/git/clang.git",
            branch="cling-patches",
            path=config.build_prefix + "/llvm/tools",
        )
    )
    git_cling = git(opts=git_cling_opts)
    prepare_sources.append(
        git_cling.clone_step(
            repository=cling_url,
            branch=cling_branch,
            commit=cling_hash,
            path=config.build_prefix + "/llvm/tools",
        )
    )
    # add libc++ and libcxxabi to the llvm project
    # Comaker detect the projects automatically and builds it.
    if config.build_libcxx:
        git_libcxx = git()
        prepare_sources.append(
            git_libcxx.clone_step(
                repository="https://github.com/llvm-mirror/libcxx",
                branch="release_50",
                path=config.build_prefix + "/llvm/projects",
            )
        )
        git_libcxxabi = git()
        prepare_sources.append(
            git_libcxx.clone_step(
                repository="https://github.com/llvm-mirror/libcxxabi",
                branch="release_50",
                path=config.build_prefix + "/llvm/projects",
            )
        )

    instr.append(shell(commands=prepare_sources))

    for build in config.get_cling_build():
        build_commands: List[str] = []
        instr.append(add_comment_heading("Build Cling " + build.build_type))

        cmake_opts = [
            "-G Ninja",
            "-DCMAKE_BUILD_TYPE=" + build.build_type,
            '-DLLVM_ABI_BREAKING_CHECKS="FORCE_OFF"',
            "-DCMAKE_LINKER=/usr/bin/gold",
            "-DLLVM_ENABLE_RTTI=ON",
            "'-DCMAKE_JOB_POOLS:STRING=compile={0};link={1}'".format(
                compiler_threads, linker_threads
            ),
            "'-DCMAKE_JOB_POOL_COMPILE:STRING=compile'",
            "'-DCMAKE_JOB_POOL_LINK:STRING=link'",
            '-DLLVM_TARGETS_TO_BUILD="host;NVPTX"',
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        ]

        # build the project with libc++
        # the flag is not necessary to enable the build of libc++ and libc++abi
        if config.build_libcxx:
            cmake_opts.append("-DLLVM_ENABLE_LIBCXX=ON")

        cm_cling = CMakeBuild(prefix=build.install_path)
        build_commands.append(
            cm_cling.configure_step(
                build_directory=build.build_path,
                directory=config.build_prefix + "/llvm",
                opts=cmake_opts,
            )
        )
        build_commands.append(cm_cling.build_step(parallel=None, target="install"))

        build_commands.append("PATH_bak=$PATH")
        build_commands.append("PATH=$PATH:" + build.install_path + "/bin")
        build_commands.append(
            "cd " + build.install_path + "/share/cling/Jupyter/kernel"
        )
        build_commands.append(config.get_miniconda_path() + "/bin/pip install -e .")
        build_commands.append("PATH=$PATH_bak")
        build_commands.append("cd - ")

        instr.append(shell(commands=build_commands))

    if not config.keep_build:
        for build in config.get_cling_build():
            config.paths_to_delete.append(build.build_path)
        config.paths_to_delete.append(config.build_prefix + "/llvm")

    return instr
