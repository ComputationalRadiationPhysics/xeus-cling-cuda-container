"""Function to create xeus-cling build instruction.
"""

def build_xeus_cling(build_prefix: str, build_type: str, url: str, branch: str, threads: int,
                         remove_list: Union[None, List[str]], miniconda_path : str,
                         cling_path : List[str], second_build=None, build_libcxx=None) -> List[str]:
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
        :param remove_list: The list contains folders and files, which will be removed. If None, no item will be removed.
        :type remove_list: Union[None, List[str]]
        :param miniconda_path: Path to the Miniconda installation. Set it as CMAKE_INSTALL_PREFIX
        :type miniconda_path: str
        :param cling_path: Paths to the cling installations. Dual build uses the first path for the first build and the second path for the second build.
        :type cling_path: List[str]
        :param second_build: Set a CMAKE_BUILD_TYPE to build xeus-cling a second time, e.g. if you want to have a debug and a release build of xeus-cling at the same time. The name of the build folder and CMAKE_INSTALL_PREFIX is extended by the CMAKE_BUILD_TYPE.
        :type second_build: str
        :param build_libcxx: Build the whole stack with libc++.
        :type build_libcxx: bool
        :returns:  a list of build instructions
        :rtype: List[str]

        """
        cm = []
        git_conf = git()
        cm.append(git_conf.clone_step(repository=url,
                                      branch=branch,
                                      path=build_prefix,
                                      directory='xeus-cling'))

        # build_directories
        xeus_cling_builds = []

        if not second_build:
            xeus_cling_builds.append(build_prefix+'/xeus-cling_build')
        else:
            xeus_cling_builds.append(build_prefix+'/xeus-cling_build_' + build_type.lower())
            xeus_cling_builds.append(build_prefix+'/xeus-cling_build_' + second_build.lower())

        # backup PATH
        # xeus-cling requires the llvm-config executable file from the cling installation
        # for dual build different bin paths are necessary
        cm.append('bPATH=$PATH')
        # index
        i = 0
        for build_dir in xeus_cling_builds:
            # add path to llvm-config for the xeus-cling build
            cm.append('PATH=$bPATH:/' + cling_path[i] + '/bin')
            cmake_opts = ['-DCMAKE_INSTALL_LIBDIR=' + miniconda_path + '/lib',
                          '-DCMAKE_LINKER=/usr/bin/gold',
                          '-DCMAKE_BUILD_TYPE='+build_type,
                          '-DDISABLE_ARCH_NATIVE=ON',
                          '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
                          '-DCMAKE_PREFIX_PATH=' + cling_path[i],
                          '-DCMAKE_CXX_FLAGS="-I ' + cling_path[i] + '/include"'
            ]

            if build_libcxx:
                cmake_opts.append('-DCMAKE_CXX_FLAGS="-stdlib=libc++"')

            cmake_conf = CMakeBuild(prefix=miniconda_path)
            cm.append(cmake_conf.configure_step(build_directory=build_dir,
                                                directory=build_prefix+'/xeus-cling',
                                                opts=cmake_opts))
            cm.append(cmake_conf.build_step(parallel=threads, target='install'))
            i += 1

        if type(remove_list) is list:
            for build_dir in xeus_cling_builds:
                remove_list.append(build_dir)
            remove_list.append(build_prefix+'/xeus-cling')

        return cm
