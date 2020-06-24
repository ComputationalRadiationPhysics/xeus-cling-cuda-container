"""The file contains a generator class that can create different versions of the
 xeus-cling-cuda stack. The class has no user interface and is designed for
integration into other projects. Use the

* gen_devel_stage()
* gen_release_single_stage()
* gen_release_multi_stage() (experimental)

"""

from typing import Tuple, List, Dict, Union
from copy import deepcopy
import hpccm
from hpccm.primitives import baseimage, shell, environment, raw, copy, runscript, label
from hpccm.building_blocks.packages import packages
from hpccm.building_blocks.cmake import cmake
from hpccm.building_blocks.llvm import llvm
from hpccm.templates.rm import rm

from xcc.cling import build_cling
from xcc.xeuscling import build_xeus_cling
from xcc.helper import build_git_and_cmake, add_libcxx_cmake_arg
from xcc.openssl import build_openssl
from xcc.miniconda import build_miniconda
from xcc.jupyter import build_dev_jupyter_kernel, build_rel_jupyter_kernel
import xcc.config


class XCC_gen:
    def __init__(
        self,
        container="singularity",
        build_prefix="/tmp",
        install_prefix="/usr/local",
        build_type="RELEASE",
        keep_build=False,
        threads=None,
        linker_threads=None,
        clang_version=8,
        gen_args=None,
        build_libcxx=None,
    ):
        """Set up the basic configuration of all projects in the container. There are only a few exceptions in the dev-stage, see gen_devel_stage().

        :param container: 'docker' or 'singularity'
        :type container: str
        :param build_prefix: Prefix path of the source and build folders of the libraries and projects.
        :type build_prefix: str
        :param install_prefix: Prefix path where all projects will be installed.
        :type install_prefix: str
        :param build_type: Set CMAKE_BUILD_TYPE : 'DEBUG', 'RELEASE', 'RELWITHDEBINFO', 'MINSIZEREL'
        :type build_type: str
        :param keep_build: Keep source and build files after installation.
        :type keep_build: str
        :param threads: number of build threads for make (None for all available threads)
        :type threads: int
        :param linker_threads: number of linker threads for ninja (if None, same number like threads)
        :type linker_threads: int
        :param clang_version: version of the project clang compiler (default: 8 - supported: 8, 9)
        :type clang_version: int
        :param gen_args: The string will be save in the environment variable XCC_GEN_ARGS should be used the save the arguments of the generator script if None, no environment variable is created.
        :type gen_args: str
        :param build_libcxx: Build the whole stack with libc++. Also add the libc++ and libc++abi projects to the llvm build.
        :type build_libcxx: bool

        """
        self.config = xcc.config.XCC_Config(
            container=container,
            build_prefix=build_prefix,
            install_prefix=install_prefix,
            build_type=build_type,
            keep_build=keep_build,
            compiler_threads=threads,
            linker_threads=linker_threads,
            build_libcxx=bool(build_libcxx),
            clang_version=clang_version,
            gen_args=gen_args,
        )

        # the list contains all projects with properties that are built and
        # installed from source code
        # the list contains dictionaries with at least two entries: name and tag
        # * name is a unique identifier
        # * tag describes which build function must be used
        # the order of the list is important for the build steps
        self.project_list = []  # type: ignore

        self.cling_url = "https://github.com/root-project/cling.git"
        self.cling_branch = None
        self.cling_hash = "595580b"

        # have to be before building cling, because the cling jupyter kernel
        # needs pip
        self.project_list.append({"name": "miniconda3", "tag": "miniconda"})

        self.project_list.append({"name": "cling", "tag": "cling"})

        #######################################################################
        # xeus dependencies
        #######################################################################
        self.project_list.append({"name": "openssl", "tag": "openssl"})

        self.add_git_cmake_entry(
            name="libzmq",
            url="https://github.com/zeromq/libzmq.git",
            branch="v4.2.5",
            opts=[
                "-DWITH_PERF_TOOL=OFF",
                "-DZMQ_BUILD_TESTS=OFF",
                "-DENABLE_CPACK=OFF",
                "-DCMAKE_BUILD_TYPE=" + build_type,
            ],
        )
        self.add_git_cmake_entry(
            name="cppzmq",
            url="https://github.com/zeromq/cppzmq.git",
            branch="v4.3.0",
            opts=["-DCMAKE_BUILD_TYPE=" + build_type],
        )
        self.add_git_cmake_entry(
            name="nlohmann_json",
            url="https://github.com/nlohmann/json.git",
            branch="v3.7.0",
            opts=["-DCMAKE_BUILD_TYPE=" + build_type],
        )
        self.add_git_cmake_entry(
            name="xtl",
            url="https://github.com/QuantStack/xtl.git",
            branch="0.6.9",
            opts=["-DCMAKE_BUILD_TYPE=" + build_type],
        )
        self.add_git_cmake_entry(
            name="xeus",
            url="https://github.com/QuantStack/xeus.git",
            branch="0.23.3",
            opts=[
                "-DBUILD_EXAMPLES=OFF",
                "-DDISABLE_ARCH_NATIVE=ON",
                "-DCMAKE_BUILD_TYPE=" + build_type,
            ],
        )

        #######################################################################
        ### xeus-cling and dependencies
        #######################################################################
        self.add_git_cmake_entry(
            name="pugixml",
            url="https://github.com/zeux/pugixml.git",
            branch="v1.8.1",
            opts=[
                "-DCMAKE_BUILD_TYPE=" + build_type,
                "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
            ],
        )
        self.add_git_cmake_entry(
            name="cxxopts",
            url="https://github.com/jarro2783/cxxopts.git",
            branch="v2.2.0",
            opts=["-DCMAKE_BUILD_TYPE=" + build_type],
        )
        self.project_list.append(
            {
                "name": "xeus-cling",
                "tag": "xeus-cling",
                "url": "https://github.com/QuantStack/xeus-cling.git",
                "branch": "0.8.0",
            }
        )

        self.project_list.append({"name": "jupyter_kernel", "tag": "jupyter_kernel"})

        self.add_git_cmake_entry(
            name="xproperty",
            url="https://github.com/QuantStack/xproperty.git",
            branch="0.8.1",
            opts=["-DCMAKE_BUILD_TYPE=" + build_type],
        )

        self.add_git_cmake_entry(
            name="xwidgets",
            url="https://github.com/QuantStack/xwidgets.git",
            branch="0.19.0",
            opts=["-DCMAKE_BUILD_TYPE=" + build_type],
        )

    def add_git_cmake_entry(
        self, name: str, url: str, branch: str, opts: List[str] = []
    ):
        """add git-and-cmake entry to self.project_list.

        The shape is:
          {'name' : name,
          'url' : url,
          'branch' : branch,
          'opts' : opts}

        :param name: name of the project
        :type name: str
        :param url: git clone url
        :type url: str
        :param branch: branch or version (git clone --branch)
        :type branch: str
        :param opts: a list of CMAKE arguments (e.g. -DCMAKE_BUILD_TYPE=RELEASE)
        :type opts: [str]
        """
        if self.config.build_libcxx:
            opts = add_libcxx_cmake_arg(opts)

        self.project_list.append(
            {
                "name": name,
                "tag": "git_cmake",
                "url": url,
                "branch": branch,
                "opts": opts,
            }
        )

    def gen_devel_stage(
        self, project_path: str, dual_build_type: str = ""
    ) -> hpccm.Stage:
        """Get a recipe for the development stack. The build process is divided into two parts. The first is building the container. The container contains all software parts that should not be changed during development. The second part contains a runscript that downloads and build the software parts that can be modified, e.g. cling.

        :param project_path: Path on the host system on which the modifiable software projects live
        :type project_path: str
        :param dual_build_type: If you want to build cling and xeus-cling a second time with different CMake build type. Set the CMake build type, for example RELEASE
        :type dual_build_type: str
        :returns: hpccm Stage
        :rtype: hpccm.Stage

        """
        stage0 = self.__gen_base_stage()
        # set the path to the changeable project as environment variable
        stage0 += environment(variables={"XCC_PROJECT_PATH": project_path})

        # the following projects are being built outside the container
        self.__gen_project_builds(
            stage=stage0,
            exclude_list=["cling", "xeus-cling", "miniconda", "jupyter_kernel"],
        )

        if not self.config.keep_build:
            r = rm()
            stage0 += shell(
                commands=[r.cleanup_step(items=self.config.paths_to_delete)]
            )

        stage0 += raw(docker="EXPOSE 8888")

        runscript_config = self.config.get_copy()
        runscript_config.build_prefix = project_path
        runscript_config.install_prefix = project_path
        runscript_config.second_build_type = dual_build_type
        runscript_config.keep_build = True

        cm_runscript: List[str] = []
        # set clang as compiler
        cm_runscript += [
            "export CC=clang-" + str(self.config.clang_version),
            "export CXX=clang++-" + str(self.config.clang_version),
        ]

        ##################################################################
        # miniconda
        ##################################################################
        cm, env = build_miniconda(config=runscript_config)
        stage0 += environment(variables=env)
        cm_runscript += cm

        ##################################################################
        # cling
        ##################################################################
        # the default behavior is PREFIX=/usr/local/ -> install to /usr/local/bin ...
        # for development it is better to install to project_path/install
        # if the second build is activated, two different installation folders will be created automatically
        cm = build_cling(
            cling_url=self.cling_url,
            cling_branch=self.cling_branch,
            cling_hash=self.cling_hash,
            config=runscript_config,
            git_cling_opts=[""],
        )
        cm_runscript += cm

        ##################################################################
        # xeus-cling
        ##################################################################
        for p in self.project_list:
            if p["name"] == "xeus-cling":
                xc = p

        cm_runscript += build_xeus_cling(
            url=xc["url"], branch=xc["branch"], config=runscript_config,
        )

        cm_runscript += build_dev_jupyter_kernel(config=runscript_config)

        stage0 += runscript(commands=cm_runscript)
        return stage0

    def gen_release_single_stage(self) -> hpccm.Stage:
        """Get a release recipe for the stack. The stack contains a single stage. Requires a little more memory on singularity and much on docker, but it is less error prone.

        :returns: hpccm Stage
        :rtype: hpccm.Stage

        """
        stage0 = self.__gen_base_stage()

        self.__gen_project_builds(stage=stage0)

        if not self.config.keep_build:
            r = rm()
            stage0 += shell(
                commands=[r.cleanup_step(items=self.config.paths_to_delete)]
            )

        stage0 += raw(docker="EXPOSE 8888")

        return stage0

    def gen_release_multi_stages(self) -> List[hpccm.Stage]:
        """Get a release recipe for the stack. The stack contains two stages. Save a little bit memory on singularity and much on docker, but it is more error prone.

        :returns: list of hpccm Stages
        :rtype: List[hpccm.Stage]

        """
        if not self.config.install_prefix.startswith(
            "/tmp"
        ) and not self.config.install_prefix.startswith("/opt"):
            raise ValueError(
                "multi stage release container: install_prefix"
                "must start with /tmp or /opt\n"
                "Your path: " + self.config.install_prefix
            )

        ##################################################################
        # set container basics
        ##################################################################
        stage0 = self.__gen_base_stage()

        self.__gen_project_builds(stage=stage0, exclude_list=["jupyter_kernel"])

        ##################################################################
        # create release stage copy application
        ##################################################################
        stage1 = hpccm.Stage()
        stage1 += baseimage(image="nvidia/cuda:8.0-devel-ubuntu16.04", _as="stage1")
        stage1 += environment(
            variables={"LD_LIBRARY_PATH": "$LD_LIBRARY_PATH:/usr/local/cuda/lib64"}
        )

        stage1 += packages(ospackages=["locales", "locales-all"])
        # set language to en_US.UTF-8 to avoid some problems with the cling output system
        stage1 += shell(
            commands=["locale-gen en_US.UTF-8", "update-locale LANG=en_US.UTF-8"]
        )

        # the semantic of the copy command is depend on the container software
        # singularity COPY /opt/foo /opt results to /opt/foo on the target
        # docker COPY /opt/foo /opt results to /opt on the target
        if self.config.container == "singularity":
            if self.config.install_prefix.startswith("/tmp"):
                stage1 += copy(src=self.config.install_prefix, dest="/opt/")
            else:
                stage1 += copy(
                    _from="stage0", src=self.config.install_prefix, dest="/opt/"
                )
        else:
            stage1 += copy(
                _from="stage0",
                src=self.config.install_prefix,
                dest="/opt/xeus_cling_cuda_install",
            )

        # merge content of install_dir in /usr/local
        stage1 += shell(
            commands=[
                "cp -rl /opt/xeus_cling_cuda_install/* /usr/local/",
                "rm -r /opt/xeus_cling_cuda_install/",
            ]
        )

        if self.config.container == "singularity":
            stage1 += shell(commands=["mkdir -p /run/user", "chmod 777 /run/user"])

        # copy Miniconda 3 with all packages
        if self.config.container == "singularity":
            stage1 += copy(_from="stage0", src="/opt/miniconda3", dest="/opt/")
        else:
            stage1 += copy(
                _from="stage0", src="/opt/miniconda3", dest="/opt/miniconda3"
            )

        stage1 += environment(variables={"PATH": "$PATH:/opt/miniconda3/bin/"})

        stage1 += shell(commands=build_rel_jupyter_kernel(config=self.config,))

        ##################################################################
        # remove files
        ##################################################################
        if not self.config.keep_build:
            r = rm()
            stage1 += shell(
                commands=[
                    r.cleanup_step(
                        items=self.config.paths_to_delete + [self.config.install_prefix]
                    )
                ]
            )

        stage1 += raw(docker="EXPOSE 8888")

        return [stage0, stage1]

    def __gen_base_stage(self) -> hpccm.Stage:
        """Returns an nvidia cuda container stage, which has some basic configuration.

            * labels are set
            * software via apt installed
            * set language to en_US.UTF-8
            * install modern cmake version
            * create folder /run/user

            :returns: hpccm Stage
            :rtype: hpccm.Stage

            """
        hpccm.config.set_container_format(self.config.container)
        if self.config.container == "singularity":
            hpccm.config.set_singularity_version("3.3")

        stage0 = hpccm.Stage()
        stage0 += baseimage(image="nvidia/cuda:8.0-devel-ubuntu16.04", _as="stage0")

        stage0 += label(
            metadata={
                "XCC Version": str(self.config.version),
                "Author": self.config.author,
                "E-Mail": self.config.email,
            }
        )

        if self.config.gen_args:
            stage0 += environment(
                variables={"XCC_GEN_ARGS": '"' + self.config.gen_args + '"'}
            )

        # LD_LIBRARY_PATH is not taken over correctly when the docker container
        # is converted to a singularity container.
        stage0 += environment(
            variables={"LD_LIBRARY_PATH": "$LD_LIBRARY_PATH:/usr/local/cuda/lib64"}
        )
        stage0 += environment(
            variables={"CMAKE_PREFIX_PATH": self.config.install_prefix}
        )
        stage0 += packages(
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
        stage0 += shell(
            commands=["locale-gen en_US.UTF-8", "update-locale LANG=en_US.UTF-8"]
        )

        # install clang/llvm
        # add ppa for modern clang/llvm versions
        stage0 += shell(
            commands=[
                "wget http://llvm.org/apt/llvm-snapshot.gpg.key",
                "apt-key add llvm-snapshot.gpg.key",
                "rm llvm-snapshot.gpg.key",
                'echo "" >> /etc/apt/sources.list',
                'echo "deb http://apt.llvm.org/xenial/ llvm-toolchain-xenial-'
                + str(self.config.clang_version)
                + ' main" >> /etc/apt/sources.list',
                'echo "deb-src http://apt.llvm.org/xenial/ llvm-toolchain-xenial-'
                + str(self.config.clang_version)
                + ' main" >> /etc/apt/sources.list',
            ]
        )

        stage0 += llvm(version=str(self.config.clang_version))
        # set clang 8 as compiler for all projects during container build time
        stage0 += shell(
            commands=[
                "export CC=clang-" + str(self.config.clang_version),
                "export CXX=clang++-" + str(self.config.clang_version),
            ]
        )

        # install clang development tools
        clang_extra = [
            "clang-tidy-" + str(self.config.clang_version),
            "clang-tools-" + str(self.config.clang_version),
        ]

        # install libc++ and libc++abi depending of the clang version
        if self.config.build_libcxx:
            clang_extra += [
                "libc++1-" + str(self.config.clang_version),
                "libc++-" + str(self.config.clang_version) + "-dev",
                "libc++abi1-" + str(self.config.clang_version),
                "libc++abi-" + str(self.config.clang_version) + "-dev",
            ]
        stage0 += packages(ospackages=clang_extra)

        stage0 += cmake(eula=True, version="3.15.2")

        # the folder is necessary for jupyter lab
        if self.config.container == "singularity":
            stage0 += shell(commands=["mkdir -p /run/user", "chmod 777 /run/user"])

        # install ninja build system
        stage0 += shell(
            commands=[
                "cd /opt",
                "wget https://github.com/ninja-build/ninja/releases/download/v1.9.0/ninja-linux.zip",
                "unzip ninja-linux.zip",
                "mv ninja /usr/local/bin/",
                "rm ninja-linux.zip",
                "cd -",
            ]
        )

        return stage0

    def __gen_project_builds(self, stage: hpccm.Stage, exclude_list=[]):
        """Add build instructions to the stage of the various projects contained in self.project_list

        :param stage: hpccm stage in which the instructions are added
        :type stage: hpccm.Stage
        :param exclude_list: List of names, which will skipped. Can be used when a project is added otherwise.
        :type exclude_list: [str]

        """
        for p in self.project_list:
            if p["tag"] == "cling":
                if "cling" not in exclude_list:
                    stage += shell(
                        commands=build_cling(
                            cling_url=self.cling_url,
                            cling_branch=self.cling_branch,
                            cling_hash=self.cling_hash,
                            config=self.config,
                        )[0]
                    )
            elif p["tag"] == "xeus-cling":
                if "xeus-cling" not in exclude_list:
                    stage += shell(
                        commands=build_xeus_cling(
                            url=p["url"], branch=p["branch"], config=self.config,
                        )
                    )
            elif p["tag"] == "git_cmake":
                if p["name"] not in exclude_list:
                    stage += shell(
                        commands=build_git_and_cmake(
                            name=p["name"],
                            url=p["url"],
                            branch=p["branch"],
                            config=self.config,
                            opts=p["opts"],
                        )
                    )
            elif p["tag"] == "openssl":
                if "openssl" not in exclude_list:
                    shc, env = build_openssl(name="openssl-1.1.1c", config=self.config,)
                    stage += shell(commands=shc)
                    stage += environment(variables=env)
            elif p["tag"] == "miniconda":
                if "miniconda" not in exclude_list:
                    shc, env = build_miniconda(config=self.config,)
                    stage += shell(commands=shc)
                    stage += environment(variables=env)
            elif p["tag"] == "jupyter_kernel":
                if "jupyter_kernel" not in exclude_list:
                    stage += shell(
                        commands=build_rel_jupyter_kernel(config=self.config,)
                    )
            else:
                raise ValueError("unknown tag: " + p["tag"])

    def __str__(self):
        s = ""
        for p in self.project_list:
            if p["tag"] == "git_cmake":
                s = s + "Git and CMake: " + p["name"] + "\n"
            else:
                s = s + p["tag"] + ": " + p["name"] + "\n"

        return s
