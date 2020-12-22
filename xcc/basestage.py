"""Function to generate base stage for the container

"""

import hpccm
from hpccm.primitives import baseimage, label, environment, shell, comment
from hpccm.building_blocks.packages import packages
from hpccm.building_blocks.cmake import cmake
from hpccm.building_blocks.llvm import llvm

import xcc.config
from xcc.helper import add_comment_heading


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
            "XCC-Version": '"{}"'.format(str(config.version)),
            "Author": '"{}"'.format(config.author),
            "E-Mail": '"{}"'.format(config.email),
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

    stage += add_comment_heading("Install Clang and tools")

    clang_install_command = [
        "wget http://llvm.org/apt/llvm-snapshot.gpg.key",
        "apt-key add llvm-snapshot.gpg.key",
        "rm llvm-snapshot.gpg.key",
        'echo "" >> /etc/apt/sources.list',
    ]

    if config.clang_version < 10:
        clang_install_command += [
            'echo "deb http://apt.llvm.org/xenial/ llvm-toolchain-xenial'
            + ' main" >> /etc/apt/sources.list',
            'echo "deb-src http://apt.llvm.org/xenial/ llvm-toolchain-xenial'
            + ' main" >> /etc/apt/sources.list',
        ]
    else:
        clang_install_command += [
            'echo "deb http://apt.llvm.org/xenial/ llvm-toolchain-xenial-'
            + str(config.clang_version)
            + ' main" >> /etc/apt/sources.list',
            'echo "deb-src http://apt.llvm.org/xenial/ llvm-toolchain-xenial-'
            + str(config.clang_version)
            + ' main" >> /etc/apt/sources.list',
        ]

    # install clang/llvm
    # add ppa for modern clang/llvm versions
    stage += shell(commands=clang_install_command)

    stage += llvm(version=str(config.clang_version))
    # set clang 8 as compiler for all projects during container build time
    stage += environment(
        variables={
            "CC": "clang-" + str(config.clang_version),
            "CXX": "clang++-" + str(config.clang_version),
        }
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
    stage += add_comment_heading("Install Ninja")

    stage += shell(
        commands=[
            "cd /opt",
            "wget https://github.com/ninja-build/ninja/releases/download/v1.9.0/ninja-linux.zip",
            "unzip ninja-linux.zip",
            "mv ninja /usr/local/bin/",
            "rm ninja-linux.zip",
            "cd -",
        ]
    )

    return stage
