"""Function to generate base stage for the container

"""

import hpccm
from hpccm.primitives import baseimage, label, environment, shell
from hpccm.building_blocks.packages import packages
from hpccm.building_blocks.cmake import cmake
from hpccm.building_blocks.llvm import llvm

import xcc.config


def gen_base_stage(config: xcc.config.XCC_Config) -> hpccm.Stage:
    """Returns an nvidia cuda container stage, which has some basic configuration.

    * labels are set
    * software via apt installed
    * set language to en_US.UTF-8
    * install modern cmake version
    * create folder /run/user

    :param config: Configuration object, which contains different information for the stage
    :type config: xcc.config.XCC_Config
    :returns: hpccm Stage
    :rtype: hpccm.Stage

    """
    hpccm.config.set_container_format(config.container)
    if config.container == "singularity":
        hpccm.config.set_singularity_version("3.3")

    stage = hpccm.Stage()
    stage += baseimage(image="nvidia/cuda:8.0-devel-ubuntu16.04", _as="stage")

    stage += label(
        metadata={
            "XCC Version": str(config.version),
            "Author": config.author,
            "E-Mail": config.email,
        }
    )

    if config.gen_args:
        stage += environment(variables={"XCC_GEN_ARGS": '"' + config.gen_args + '"'})

    # LD_LIBRARY_PATH is not taken over correctly when the docker container
    # is converted to a singularity container.
    stage += environment(
        variables={"LD_LIBRARY_PATH": "$LD_LIBRARY_PATH:/usr/local/cuda/lib64"}
    )
    stage += environment(variables={"CMAKE_PREFIX_PATH": config.install_prefix})
    stage += packages(
        ospackages=[
            "git",
            "python",
            "wget",
            "pkg-config",
            "uuid-dev",
            "gdb",
            "locales",
            "locales-all",
            "unzip",
        ]
    )
    # set language to en_US.UTF-8 to avoid some problems with the cling output system
    stage += shell(
        commands=["locale-gen en_US.UTF-8", "update-locale LANG=en_US.UTF-8"]
    )

    stage += shell(
        commands=[
            "",
            "#/////////////////////////////",
            "#// Install Clang and tools //",
            "#/////////////////////////////",
        ]
    )

    # install clang/llvm
    # add ppa for modern clang/llvm versions
    stage += shell(
        commands=[
            "wget http://llvm.org/apt/llvm-snapshot.gpg.key",
            "apt-key add llvm-snapshot.gpg.key",
            "rm llvm-snapshot.gpg.key",
            'echo "" >> /etc/apt/sources.list',
            'echo "deb http://apt.llvm.org/xenial/ llvm-toolchain-xenial-'
            + str(config.clang_version)
            + ' main" >> /etc/apt/sources.list',
            'echo "deb-src http://apt.llvm.org/xenial/ llvm-toolchain-xenial-'
            + str(config.clang_version)
            + ' main" >> /etc/apt/sources.list',
        ]
    )

    stage += llvm(version=str(config.clang_version))
    # set clang 8 as compiler for all projects during container build time
    stage += shell(
        commands=[
            "export CC=clang-" + str(config.clang_version),
            "export CXX=clang++-" + str(config.clang_version),
        ]
    )

    # install clang development tools
    clang_extra = [
        "clang-tidy-" + str(config.clang_version),
        "clang-tools-" + str(config.clang_version),
    ]

    # install libc++ and libc++abi depending of the clang version
    if config.build_libcxx:
        clang_extra += [
            "libc++1-" + str(config.clang_version),
            "libc++-" + str(config.clang_version) + "-dev",
            "libc++abi1-" + str(config.clang_version),
            "libc++abi-" + str(config.clang_version) + "-dev",
        ]
    stage += packages(ospackages=clang_extra)

    stage += cmake(eula=True, version="3.18.0")

    # the folder is necessary for jupyter lab
    if config.container == "singularity":
        stage += shell(commands=["mkdir -p /run/user", "chmod 777 /run/user"])

    # install ninja build system
    stage += shell(
        commands=[
            "",
            "#/////////////////////////////",
            "#// Install Ninja           //",
            "#/////////////////////////////",
            "cd /opt",
            "wget https://github.com/ninja-build/ninja/releases/download/v1.9.0/ninja-linux.zip",
            "unzip ninja-linux.zip",
            "mv ninja /usr/local/bin/",
            "rm ninja-linux.zip",
            "cd -",
        ]
    )

    return stage
