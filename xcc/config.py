"""The config object provides information for the different recipe generator stages.

"""

from typing import List, Union
from copy import deepcopy

supported_clang_version = [8, 9]


class XCC_Config:
    class build_object:
        def __init__(
            self,
            build_path: str,
            install_path: str,
            build_type: str,
            cling_install_path: str = "",
        ):
            """Contains build path, install path, build type and related cling install path for a cling or xeus-cling build.

            :param build_path: Path, where cmake build the project.
            :type build_path: str
            :param install_path: Path, where cmake install the project.
            :type install_path: str
            :param build_type: CMAKE_BUILD_TYP
            :type build_type: str
            :param cling_install_path: Installation path of a cling build.
            :type cling_install_path: str

            """
            self.build_path = build_path
            self.install_path = install_path
            self.build_type = build_type
            self.cling_install_path = cling_install_path

        def __str__(self):
            s = "build_path: " + self.build_path + "\n"
            s += "install_path: " + self.install_path + "\n"
            s += "build_type: " + self.build_type + "\n"
            s += "cling_install_path: " + self.cling_install_path + "\n"
            return s

    def __init__(
        self,
        container: str = "singularity",
        build_prefix: str = "/tmp",
        install_prefix: str = "/usr/local",
        build_type: str = "RELEASE",
        second_build_type: str = "",
        keep_build: bool = False,
        compiler_threads: int = 1,
        linker_threads: int = 1,
        build_libcxx: bool = False,
        clang_version: int = 8,
        gen_args: str = "",
    ):
        """Setup the configuration object

        :param container: 'docker' or 'singularity'
        :type container: str
        :param build_prefix: Prefix path of the source and build folders of the libraries and projects.
        :type build_prefix: str
        :param install_prefix: Prefix path where all projects will be installed.
        :type install_prefix: str
        :param build_type: Set CMAKE_BUILD_TYPE : 'DEBUG', 'RELEASE', 'RELWITHDEBINFO', 'MINSIZEREL'
        :type build_type: str
        :param second_build_type: If you want to build cling and xeus-cling a second time with different CMake build type. Set the CMake build type, for example RELEASE.
        :type second_build_type: str
        :param keep_build: Keep source and build files after installation.
        :type keep_build: str
        :param compiler_threads: Number of build threads for make (0 for all available threads).
        :type compiler_threads: int
        :param linker_threads: Number of linker threads for ninja (if 0, same number like threads)
        :type linker_threads: int
        :param build_libcxx: Build the whole stack with libc++. Also add the libc++ and libc++abi projects to the llvm build.
        :type build_libcxx: bool
        :param clang_version: Version of the project clang compiler (see XCC_Config.supported_clang_version)
        :type clang_version: int
        :param gen_args: The string will be save in the environment variable XCC_GEN_ARGS should be used the save the arguments of the generator script if None, no environment variable is created.
        :type gen_args: str

        """
        self.author = "Simeon Ehrig"
        self.email = "s.ehrig@hzdr.de"
        self.version = "2.3"

        if clang_version not in supported_clang_version:
            raise ValueError(
                "Clang version "
                + str(clang_version)
                + " is not supported\n"
                + "Supported versions: "
                + ", ".join(map(str, supported_clang_version))
            )
        else:
            self.clang_version = clang_version

        if not check_build_type(build_type):
            raise ValueError(
                "build_type have to be: 'DEBUG', 'RELEASE', 'RELWITHDEBINFO', 'MINSIZEREL'"
            )

        if second_build_type and not check_build_type(second_build_type):
            raise ValueError(
                "second_build_type have to be: 'DEBUG', 'RELEASE', 'RELWITHDEBINFO', 'MINSIZEREL'"
            )

        self.container: str = container
        self.build_prefix: str = build_prefix
        self.install_prefix: str = install_prefix
        self.build_type: str = build_type
        self.second_build_type: str = second_build_type
        self.keep_build: bool = keep_build
        self.paths_to_delete: List[str] = []
        self.compiler_threads: int = compiler_threads
        self.linker_threads: int = linker_threads
        self.build_libcxx: bool = build_libcxx
        self.gen_args: str = gen_args

    def get_copy(self):
        """Returns a deepcopy.

        :returns: Config object
        :rtype: XCC_Config

        """
        c = XCC_Config(
            container=self.container,
            build_prefix=self.build_prefix,
            install_prefix=self.install_prefix,
            build_type=self.build_type,
            second_build_type=self.second_build_type,
            keep_build=self.keep_build,
            compiler_threads=self.compiler_threads,
            linker_threads=self.linker_threads,
            build_libcxx=self.build_libcxx,
            gen_args=self.gen_args,
        )
        c.paths_to_delete = deepcopy(self.paths_to_delete)

        return c

    def get_cmake_compiler_threads(self) -> str:
        """Return a number or $(nproc), of compiler_threads is 0

        :returns: number of threads
        :rtype: str

        """
        if self.compiler_threads is None:
            self.compiler_threads = 0
        return "$(nproc)" if self.compiler_threads == 0 else str(self.compiler_threads)

    def get_cmake_linker_threads(self) -> str:
        """Return a number or $(nproc), of linker_threads is 0

        :returns: number of threads
        :rtype: str

        """

        if self.linker_threads is None:
            self.linker_threads = 0
        return (
            str(self.compiler_threads)
            if self.linker_threads == 0
            else str(self.linker_threads)
        )

    def get_cling_build(self) -> List[build_object]:
        """Create a list of build configurations for cling.

        :returns: build configurations
        :rtype: List[build_object]

        """
        cling_builds: List[XCC_Config.build_object] = []

        if not self.second_build_type:
            cling_builds.append(
                XCC_Config.build_object(
                    build_path=self.build_prefix + "/cling_build",
                    install_path=self.install_prefix,
                    build_type=self.build_type,
                )
            )
        else:
            cling_builds.append(
                XCC_Config.build_object(
                    build_path=self.build_prefix + "/build_" + self.build_type.lower(),
                    install_path=self.install_prefix
                    + "/install_"
                    + self.build_type.lower(),
                    build_type=self.build_type,
                )
            )
            cling_builds.append(
                XCC_Config.build_object(
                    build_path=self.build_prefix
                    + "/build_"
                    + self.second_build_type.lower(),
                    install_path=self.install_prefix
                    + "/install_"
                    + self.second_build_type.lower(),
                    build_type=self.second_build_type,
                )
            )

        return cling_builds

    def get_xeus_cling_build(self) -> List[build_object]:
        """Create a list of build configurations for xeus-cling.

        :returns: build configurations
        :rtype: List[build_object]

        """
        xeus_cling_builds: List[XCC_Config.build_object] = []

        if not self.second_build_type:
            xeus_cling_builds.append(
                XCC_Config.build_object(
                    build_path=self.build_prefix + "/xeus-cling_build",
                    install_path="",
                    build_type=self.build_type,
                    cling_install_path=self.install_prefix,
                )
            )
        else:
            xeus_cling_builds.append(
                XCC_Config.build_object(
                    build_path=self.build_prefix
                    + "/xeus-cling_build_"
                    + self.build_type.lower(),
                    install_path="",
                    build_type=self.build_type,
                    cling_install_path=self.install_prefix
                    + "/install_"
                    + self.build_type.lower(),
                )
            )
            xeus_cling_builds.append(
                XCC_Config.build_object(
                    build_path=self.build_prefix
                    + "/xeus-cling_build_"
                    + self.second_build_type.lower(),
                    install_path="",
                    build_type=self.second_build_type,
                    cling_install_path=self.install_prefix
                    + "/install_"
                    + self.second_build_type.lower(),
                )
            )

        return xeus_cling_builds

    def get_miniconda_path(self) -> str:
        """Create the miniconda install path

        :returns: returns the path to miniconda
        :rtype: str

        """
        return self.install_prefix + "/miniconda3"


def check_build_type(type: str) -> bool:
    """Check if input is a CMAKE_BUILD_TYPE: 'DEBUG', 'RELEASE', 'RELWITHDEBINFO', 'MINSIZEREL'

    :param type: type to check
    :type type: str
    :returns: true if it supported type, otherwise false
    :rtype: bool

    """
    if type in ["DEBUG", "RELEASE", "RELWITHDEBINFO", "MINSIZEREL"]:
        return True
    else:
        return False
