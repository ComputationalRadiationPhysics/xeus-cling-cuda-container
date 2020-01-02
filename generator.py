"""The file contains a generator class that can create different versions of the
 xeus-cling-cuda stack. The class has no user interface and is designed for
integration into other projects. Use the

* gen_devel_stage()
* gen_release_single_stage()
* gen_release_multi_stage() (experimental)

interfaces to get hpccm.Stage objects which contains ready-made recipes. You can
 also create your own stack with different build fragments. Use the

* build_*()

functions to obtain lists of build instructions for the various software parts.

"""

import json
from typing import Tuple, List, Dict, Union
import hpccm
from hpccm.primitives import baseimage, shell, environment, raw, copy, runscript, label
from hpccm.building_blocks.packages import packages
from hpccm.building_blocks.cmake import cmake
from hpccm.building_blocks.llvm import llvm
from hpccm.templates.git import git
from hpccm.templates.CMakeBuild import CMakeBuild
from hpccm.templates.rm import rm
from hpccm.templates.wget import wget
from hpccm.templates.tar import tar


class XCC_gen:

    def __init__(self, container='singularity', build_prefix='/tmp',
                 install_prefix='/usr/local', build_type='RELEASE',
                 keep_build=False, threads=None, linker_threads=None,
                 clang_version=8, gen_args=None, build_libcxx=None):
        """Set up the basic configuration of all projects in the container. There are only a few exceptions in the dev-stage, see gen_devel_stage().

        :param container: 'docker' or 'singularity'
        :type container: str
        :param build_prefix: prefix path of the source and build folders of the libraries and projects
        :type build_prefix: str
        :param install_prefix: prefix path where all projects will be installed
        :type install_prefix: str
        :param build_type: set the CMAKE_BUILD_TYPE : 'DEBUG', 'RELEASE', 'RELWITHDEBINFO', 'MINSIZEREL'
        :type build_type: str
        :param keep_build: keep source and build files after installation
        :type keep_build: str
        :param threads: number of build threads for make (None for all available threads)
        :type threads: int
        :param linker_threads: number of linker threads for ninja (if None, same number like threads)
        :type linker_threads: int
        :param clang_version: version of the project clang compiler (default: 8 - supported: 8, 9)
        :type clang_version: int
        :param gen_args: the string will be save in the environment variable XCC_GEN_ARGS
                         should be used the save the arguments of the generator script
                         if None, no environment variable is created
        :type gen_args: str
        :param build_libcxx: Build the whole stack with libc++. Also add the
                             libc++ and libc++abi projects to the llvm build.
        :type build_libcxx: bool

        """
        self.container = container
        self.build_prefix = build_prefix
        self.install_prefix = install_prefix
        self.build_type = build_type
        self.threads = threads
        self.linker_threads = linker_threads
        self.build_libcxx = build_libcxx

        if keep_build:
            self.remove_list = None
        else:
            # list of folders and files removed in the last step
            self.remove_list = []

        supported_clang_version = [8, 9]
        if clang_version not in supported_clang_version:
            raise ValueError('Clang version ' + str(clang_version) + ' is not supported\n' +
                             'Supported versions: ' + ', '.join(map(str, supported_clang_version)))
        else:
            self.clang_version = clang_version

        self.gen_args=gen_args

        self.author = 'Simeon Ehrig'
        self.email = 's.ehrig@hzdr.de'
        self.version = '2.2'

        # the list contains all projects with properties that are built and
        # installed from source code
        # the list contains dictionaries with at least two entries: name and tag
        # * name is a unique identifier
        # * tag describes which build function must be used
        # the order of the list is important for the build steps
        self.project_list : List[Dict[str, str]] = []

        self.cling_url = 'https://github.com/root-project/cling.git'
        self.cling_branch = None
        self.cling_hash = '595580b'

        self.project_list.append({'name': 'cling',
                                  'tag': 'cling'})

        #######################################################################
        # xeus dependencies
        #######################################################################
        self.project_list.append({'name': 'openssl',
                                  'tag': 'openssl'})

        self.add_git_cmake_entry(name='libzmq',
                                 url='https://github.com/zeromq/libzmq.git',
                                 branch='v4.2.5',
                                 opts=['-DWITH_PERF_TOOL=OFF',
                                       '-DZMQ_BUILD_TESTS=OFF',
                                       '-DENABLE_CPACK=OFF',
                                       '-DCMAKE_BUILD_TYPE='+build_type
                                       ])
        self.add_git_cmake_entry(name='cppzmq',
                                 url='https://github.com/zeromq/cppzmq.git',
                                 branch='v4.3.0',
                                 opts=['-DCMAKE_BUILD_TYPE='+build_type
                                       ])
        self.add_git_cmake_entry(name='nlohmann_json',
                                 url='https://github.com/nlohmann/json.git',
                                 branch='v3.7.0',
                                 opts=['-DCMAKE_BUILD_TYPE='+build_type
                                       ])
        self.add_git_cmake_entry(name='xtl',
                                 url='https://github.com/QuantStack/xtl.git',
                                 branch='0.6.9',
                                 opts=['-DCMAKE_BUILD_TYPE='+build_type
                                       ])
        self.add_git_cmake_entry(name='xeus',
                                 url='https://github.com/QuantStack/xeus.git',
                                 branch='0.23.3',
                                 opts=['-DBUILD_EXAMPLES=OFF',
                                       '-DDISABLE_ARCH_NATIVE=ON',
                                       '-DCMAKE_BUILD_TYPE='+build_type
                                       ])

        #######################################################################
        ### xeus-cling and dependencies
        #######################################################################

        self.project_list.append({'name': 'miniconda3',
                                  'tag': 'miniconda'})

        self.add_git_cmake_entry(name='pugixml',
                                 url='https://github.com/zeux/pugixml.git',
                                 branch='v1.8.1',
                                 opts=['-DCMAKE_BUILD_TYPE='+build_type,
                                       '-DCMAKE_POSITION_INDEPENDENT_CODE=ON'
                                       ])
        self.add_git_cmake_entry(name='cxxopts',
                                 url='https://github.com/jarro2783/cxxopts.git',
                                 branch='v2.2.0',
                                 opts=['-DCMAKE_BUILD_TYPE='+build_type
                                       ])
        self.project_list.append({'name' : 'xeus-cling',
                                  'tag' : 'xeus-cling',
                                  'url' : 'https://github.com/QuantStack/xeus-cling.git',
                                  'branch' : '0.8.0'})

        self.project_list.append({'name': 'jupyter_kernel',
                                  'tag': 'jupyter_kernel'})

        self.add_git_cmake_entry(name='xproperty',
                                 url='https://github.com/QuantStack/xproperty.git',
                                 branch='0.8.1',
                                 opts=['-DCMAKE_BUILD_TYPE='+build_type
                                       ])

        self.add_git_cmake_entry(name='xwidgets',
                                 url='https://github.com/QuantStack/xwidgets.git',
                                 branch='0.19.0',
                                 opts=['-DCMAKE_BUILD_TYPE='+build_type
                                       ])

    def add_libcxx_cmake_arg(self, inputlist : List[str]) -> List[str]:
        """If the class attribute build_libcxx is true, add
        -DCMAKE_CXX_FLAGS="-stdlib=libc++" to cmake flags in inputlist.

        :param inputlist: List of cmake flags
        :type inputlist: List[str]
        :returns: inputlist plus -DCMAKE_CXX_FLAGS="-stdlib=libc++" if
                  self.build_libcxx is true
        :rtype: List[str]

        """
        if self.build_libcxx:
            inputlist.append('-DCMAKE_CXX_FLAGS="-stdlib=libc++"')
        return inputlist

    def add_git_cmake_entry(self, name: str, url: str, branch: str, opts=[]):
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
        self.project_list.append({'name': name,
                                  'tag': 'git_cmake',
                                  'url': url,
                                  'branch': branch,
                                  'opts': self.add_libcxx_cmake_arg(opts)})

    def gen_devel_stage(self, project_path: str, dual_build_type=None) -> hpccm.Stage:
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
        stage0 += environment(variables={'XCC_PROJECT_PATH': project_path})

        # the following projects are being built outside the container
        self.__gen_project_builds(stage=stage0,
                                  exclude_list=['cling',
                                                'xeus-cling',
                                                'miniconda',
                                                'jupyter_kernel'])

        if type(self.remove_list) is list:
            r = rm()
            stage0 += shell(commands=[r.cleanup_step(items=self.remove_list)])

        stage0 += raw(docker='EXPOSE 8888')

        cm_runscript : List[str] = []
        # set clang as compiler
        cm_runscript += ['export CC=clang-' + str(self.clang_version),
                         'export CXX=clang++-' + str(self.clang_version)]

        ##################################################################
        # miniconda
        ##################################################################
        cm, env = self.build_miniconda(
            build_prefix='/tmp', install_prefix=project_path)
        stage0 += environment(variables=env)
        cm_runscript += cm

        ##################################################################
        # cling
        ##################################################################
        # the default behavior is PREFIX=/usr/local/ -> install to /usr/local/bin ...
        # for development it is better to install to project_path/install
        # if the second build is activated, two different installation folders will be created automatically
        cling_install_prefix = [project_path]
        if dual_build_type is None:
            cling_install_prefix[0] += '/install'

        cm, cling_install_prefix = self.build_cling(build_prefix=project_path,
                                                    install_prefix=cling_install_prefix[0],
                                                    build_type=self.build_type,
                                                    cling_url=self.cling_url,
                                                    cling_branch=self.cling_branch,
                                                    cling_hash=self.cling_hash,
                                                    threads=self.threads,
                                                    linker_threads=self.linker_threads,
                                                    remove_list=None,
                                                    dual_build=dual_build_type,
                                                    git_cling_opts=[''],
                                                    build_libcxx=self.build_libcxx)
        cm_runscript += cm

        ##################################################################
        # xeus-cling
        ##################################################################
        for p in self.project_list:
            if p['name'] == 'xeus-cling':
                xc = p

        cm_runscript += self.build_xeus_cling(build_prefix=project_path,
                                              build_type=self.build_type,
                                              url=xc['url'],
                                              branch=xc['branch'],
                                              threads=self.threads,
                                              remove_list=None,
                                              miniconda_path=project_path+'/miniconda3',
                                              cling_path=cling_install_prefix,
                                              second_build=dual_build_type,
                                              build_libcxx=self.build_libcxx)

        cm_runscript += self.build_dev_jupyter_kernel(build_prefix=project_path+'/kernels',
                                                      miniconda_prefix=project_path)

        stage0 += runscript(commands=cm_runscript)
        return stage0

    def gen_release_single_stage(self) -> hpccm.Stage:
        """Get a release recipe for the stack. The stack contains a single stage. Requires a little more memory on singularity and much on docker, but it is less error prone.

        :returns: hpccm Stage
        :rtype: hpccm.Stage

        """
        stage0 = self.__gen_base_stage()

        self.__gen_project_builds(stage=stage0)

        if type(self.remove_list) is list:
            r = rm()
            stage0 += shell(commands=[r.cleanup_step(items=self.remove_list)])

        stage0 += raw(docker='EXPOSE 8888')

        return stage0

    def gen_release_multi_stages(self) -> List[hpccm.Stage]:
        """Get a release recipe for the stack. The stack contains two stages. Save a little bit memory on singularity and much on docker, but it is more error prone.

        :returns: list of hpccm Stages
        :rtype: List[hpccm.Stage]

        """
        if (not self.install_prefix.startswith('/tmp') and
                not self.install_prefix.startswith('/opt')):
            raise ValueError('multi stage release container: install_prefix'
                             'must start with /tmp or /opt\n'
                             'Your path: ' + self.install_prefix)

        ##################################################################
        # set container basics
        ##################################################################
        stage0 = self.__gen_base_stage()

        self.__gen_project_builds(
            stage=stage0, exclude_list=['jupyter_kernel'])

        ##################################################################
        # create release stage copy application
        ##################################################################
        stage1 = hpccm.Stage()
        stage1 += baseimage(image='nvidia/cuda:8.0-devel-ubuntu16.04',
                            _as='stage1')
        stage1 += environment(
            variables={'LD_LIBRARY_PATH': '$LD_LIBRARY_PATH:/usr/local/cuda/lib64'})

        stage1 += packages(ospackages=['locales', 'locales-all'])
        # set language to en_US.UTF-8 to avoid some problems with the cling output system
        stage1 += shell(commands=['locale-gen en_US.UTF-8',
                                  'update-locale LANG=en_US.UTF-8'])

        # the semantic of the copy command is depend on the container software
        # singularity COPY /opt/foo /opt results to /opt/foo on the target
        # docker COPY /opt/foo /opt results to /opt on the target
        if self.container == 'singularity':
            if self.install_prefix.startswith('/tmp'):
                stage1 += copy(src=self.install_prefix,
                               dest='/opt/')
            else:
                stage1 += copy(_from='stage0',
                               src=self.install_prefix,
                               dest='/opt/')
        else:
            stage1 += copy(_from='stage0',
                           src=self.install_prefix,
                           dest='/opt/xeus_cling_cuda_install')

        # merge content of install_dir in /usr/local
        stage1 += shell(commands=['cp -rl /opt/xeus_cling_cuda_install/* /usr/local/',
                                  'rm -r /opt/xeus_cling_cuda_install/'])

        if self.container == 'singularity':
            stage1 += shell(commands=['mkdir -p /run/user',
                                      'chmod 777 /run/user'])

        # copy Miniconda 3 with all packages
        if self.container == 'singularity':
            stage1 += copy(_from='stage0',
                           src='/opt/miniconda3',
                           dest='/opt/')
        else:
            stage1 += copy(_from='stage0',
                           src='/opt/miniconda3',
                           dest='/opt/miniconda3')

        stage1 += environment(variables={'PATH': '$PATH:/opt/miniconda3/bin/'})

        stage1 += shell(commands=self.build_jupyter_kernel(
            build_prefix=self.build_prefix,
            miniconda_prefix='/opt',
            remove_list=self.remove_list))

        ##################################################################
        # remove files
        ##################################################################
        if type(self.remove_list) is list:
            r = rm()
            stage1 += shell(commands=[r.cleanup_step(
                items=self.remove_list+[self.install_prefix])])

        stage1 += raw(docker='EXPOSE 8888')

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
        hpccm.config.set_container_format(self.container)
        if self.container == 'singularity':
            hpccm.config.set_singularity_version('3.3')

        stage0 = hpccm.Stage()
        stage0 += baseimage(image='nvidia/cuda:8.0-devel-ubuntu16.04',
                            _as='stage0')

        stage0 += label(metadata={'XCC Version': str(self.version),
                                  'Author': self.author,
                                  'E-Mail': self.email})

        if self.gen_args:
            stage0 += environment(
                variables={'XCC_GEN_ARGS': '"' + self.gen_args + '"'})

        # LD_LIBRARY_PATH is not taken over correctly when the docker container
        # is converted to a singularity container.
        stage0 += environment(
            variables={'LD_LIBRARY_PATH': '$LD_LIBRARY_PATH:/usr/local/cuda/lib64'})
        stage0 += environment(
            variables={'CMAKE_PREFIX_PATH': self.install_prefix})
        stage0 += packages(ospackages=['git', 'python', 'wget', 'pkg-config',
                                       'uuid-dev', 'gdb', 'locales',
                                       'locales-all', 'unzip'])
        # set language to en_US.UTF-8 to avoid some problems with the cling output system
        stage0 += shell(commands=['locale-gen en_US.UTF-8',
                                  'update-locale LANG=en_US.UTF-8'])

        # install clang/llvm
        # add ppa for modern clang/llvm versions
        stage0 += shell(commands=['wget http://llvm.org/apt/llvm-snapshot.gpg.key',
	                          'apt-key add llvm-snapshot.gpg.key',
	                          'rm llvm-snapshot.gpg.key',
	                          'echo "" >> /etc/apt/sources.list',
	                          'echo "deb http://apt.llvm.org/xenial/ llvm-toolchain-xenial-' + str(self.clang_version) + ' main" >> /etc/apt/sources.list',
	                          'echo "deb-src http://apt.llvm.org/xenial/ llvm-toolchain-xenial-' + str(self.clang_version) + ' main" >> /etc/apt/sources.list'])

        stage0 += llvm(version=str(self.clang_version))
        # set clang 8 as compiler for all projects during container build time
        stage0 += shell(commands=['export CC=clang-' + str(self.clang_version),
                                  'export CXX=clang++-' + str(self.clang_version)])

        # install clang development tools
        clang_extra = ['clang-tidy-' + str(self.clang_version),
                       'clang-tools-' + str(self.clang_version)]

        # install libc++ and libc++abi depending of the clang version
        if self.build_libcxx:
            clang_extra += ['libc++1-' + str(self.clang_version),
                            'libc++-' + str(self.clang_version) + '-dev',
                            'libc++abi1-' + str(self.clang_version),
                            'libc++abi-' + str(self.clang_version) + '-dev']
        stage0 += packages(ospackages=clang_extra)

        stage0 += cmake(eula=True, version='3.15.2')

        # the folder is necessary for jupyter lab
        if self.container == 'singularity':
            stage0 += shell(commands=['mkdir -p /run/user',
                                      'chmod 777 /run/user'])

        # install ninja build system
        stage0 += shell(commands=['cd /opt',
                                  'wget https://github.com/ninja-build/ninja/releases/download/v1.9.0/ninja-linux.zip',
                                  'unzip ninja-linux.zip',
                                  'mv ninja /usr/local/bin/',
                                  'rm ninja-linux.zip',
                                  'cd -'])

        return stage0

    def __gen_project_builds(self, stage: hpccm.Stage, exclude_list=[]):
        """Add build instructions to the stage of the various projects contained in self.project_list

        :param stage: hpccm stage in which the instructions are added
        :type stage: hpccm.Stage
        :param exclude_list: List of names, which will skipped. Can be used when a project is added otherwise.
        :type exclude_list: [str]

        """
        for p in self.project_list:
            if p['tag'] == 'cling':
                if 'cling' not in exclude_list:
                    stage += shell(commands=self.build_cling(
                        build_prefix=self.build_prefix,
                        install_prefix=self.install_prefix,
                        build_type=self.build_type,
                        cling_url=self.cling_url,
                        cling_branch=self.cling_branch,
                        cling_hash=self.cling_hash,
                        threads=self.threads,
                        linker_threads=self.linker_threads,
                        remove_list=self.remove_list,
                        build_libcxx=self.build_libcxx)[0]
                    )
            elif p['tag'] == 'xeus-cling':
                if 'xeus-cling' not in exclude_list:
                    stage += shell(commands=self.build_xeus_cling(
                        build_prefix=self.build_prefix,
                        build_type=self.build_type,
                        url=p['url'],
                        branch=p['branch'],
                        threads=self.threads,
                        remove_list=self.remove_list,
                        miniconda_path='/opt/miniconda3',
                        cling_path=self.install_prefix,
                        build_libcxx=self.build_libcxx
                    ))
            elif p['tag'] == 'git_cmake':
                if p['name'] not in exclude_list:
                    stage += shell(commands=self.build_git_and_cmake(
                        name=p['name'],
                        build_prefix=self.build_prefix,
                        install_prefix=self.install_prefix,
                        url=p['url'],
                        branch=p['branch'],
                        threads=self.threads,
                        remove_list=self.remove_list,
                        opts=p['opts'])
                    )
            elif p['tag'] == 'openssl':
                if 'openssl' not in exclude_list:
                    shc, env = self.build_openssl(
                        name='openssl-1.1.1c',
                        build_prefix=self.build_prefix,
                        install_prefix=self.install_prefix,
                        threads=self.threads,
                        remove_list=self.remove_list)
                    stage += shell(commands=shc)
                    stage += environment(variables=env)
            elif p['tag'] == 'miniconda':
                if 'miniconda' not in exclude_list:
                    shc, env = self.build_miniconda(
                        build_prefix=self.build_prefix,
                        install_prefix='/opt',
                        remove_list=self.remove_list)
                    stage += shell(commands=shc)
                    stage += environment(variables=env)
            elif p['tag'] == 'jupyter_kernel':
                if 'jupyter_kernel' not in exclude_list:
                    stage += shell(commands=self.build_jupyter_kernel(
                        build_prefix=self.build_prefix,
                        miniconda_prefix='/opt',
                        remove_list=self.remove_list))
            else:
                raise ValueError('unknown tag: ' + p['tag'])

    @staticmethod
    def build_cling(build_prefix: str, install_prefix: str, build_type: str,
                    cling_url: str, cling_branch=None, cling_hash=None,
                    threads=None, linker_threads=None, remove_list=None,
                    dual_build=None, git_cling_opts=['--depth=1'],
                    build_libcxx=None) -> Tuple[List[str], List[str]]:
        """Return Cling build instructions.

        :param build_prefix: path where source code is cloned and built
        :type build_prefix: str
        :param install_prefix: CMAKE_INSTALL_PREFIX
        :type install_prefix: str
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
        :param remove_list: The list contains folders and files, which will be removed. If None, no item will be removed
        :type remove_list: [str]
        :param dual_build: Set a CMAKE_BUILD_TYPE to build cling a second time, e.g. if you want to have a debug and a release build of cling at the same time. The name of the build folder and CMAKE_INSTALL_PREFIX is extended by the CMAKE_BUILD_TYPE.
        :type dual_build: str
        :param git_cling_opts: Setting options for Git Clone
        :type git_cling_opts: [str]
        :param build_libcxx: Build the whole stack with libc++. Also add the
                             libc++ and libc++abi projects to the llvm build.
        :type build_libcxx: bool
        :returns: a list of build instructions and a list of the install folders
        :rtype: [str],[str]

        """
        if threads == None:
            c_threads = '$(nproc)'
        else:
            c_threads = threads

        if linker_threads == None:
            l_threads = c_threads
        else:
            l_threads = linker_threads

        cbc : List[str] = []
        git_llvm = git()
        cbc.append(git_llvm.clone_step(repository='http://root.cern.ch/git/llvm.git',
                                       branch='cling-patches',
                                       path=build_prefix, directory='llvm'))
        git_clang = git()
        cbc.append(git_clang.clone_step(repository='http://root.cern.ch/git/clang.git',
                                        branch='cling-patches',
                                        path=build_prefix+'/llvm/tools'))
        git_cling = git(opts=git_cling_opts)
        cbc.append(git_cling.clone_step(repository=cling_url,
                                        branch=cling_branch,
                                        commit=cling_hash,
                                        path=build_prefix+'/llvm/tools'))
        # add libc++ and libcxxabi to the llvm project
        # Comaker detect the projects automatically and builds it.
        if build_libcxx:
            git_libcxx = git()
            cbc.append(git_libcxx.clone_step(repository='https://github.com/llvm-mirror/libcxx',
                                             branch='release_50',
                                             path=build_prefix+'/llvm/projects'))
            git_libcxxabi = git()
            cbc.append(git_libcxx.clone_step(repository='https://github.com/llvm-mirror/libcxxabi',
                                             branch='release_50',
                                             path=build_prefix+'/llvm/projects'))

        # modify the install folder for dual build
        if not dual_build:
            cm_builds = [{'build_dir': build_prefix+'/cling_build',
                          'install_dir': install_prefix,
                          'build_type': build_type}]
        else:
            cm_builds = [{'build_dir': build_prefix+'/build_' + build_type.lower(),
                          'install_dir': install_prefix + '/install_' + build_type.lower(),
                          'build_type': build_type},
                         {'build_dir': build_prefix + '/build_' + dual_build.lower(),
                          'install_dir': install_prefix + '/install_' + dual_build.lower(),
                          'build_type': dual_build.lower()}]

        cling_install_prefix : List[str] = []

        for build in cm_builds:
            cmake_opts = [
                '-G Ninja',
                '-DCMAKE_BUILD_TYPE=' + build['build_type'],
                '-DLLVM_ABI_BREAKING_CHECKS="FORCE_OFF"',
                '-DCMAKE_LINKER=/usr/bin/gold',
                '-DLLVM_ENABLE_RTTI=ON',
                "'-DCMAKE_JOB_POOLS:STRING=compile={0};link={1}'".format(c_threads, l_threads),
                "'-DCMAKE_JOB_POOL_COMPILE:STRING=compile'",
                "'-DCMAKE_JOB_POOL_LINK:STRING=link'",
                '-DLLVM_TARGETS_TO_BUILD="host;NVPTX"',
                '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON'
            ]

            # build the project with libc++
            # the flag is not necessary to enable the build of libc++ and libc++abi
            if build_libcxx:
                cmake_opts.append('-DLLVM_ENABLE_LIBCXX=ON')

            cm_cling = CMakeBuild(prefix=build['install_dir'])
            cbc.append(cm_cling.configure_step(build_directory=build['build_dir'],
                                               directory=build_prefix+'/llvm',
                                               opts=cmake_opts))
            cbc.append(cm_cling.build_step(parallel=None, target='install'))
            cling_install_prefix.append(build['install_dir'])

        if type(remove_list) is list:
            for build in cm_builds:
                remove_list.append(build['build_dir'])
            remove_list.append(build_prefix+'/llvm')

        return cbc, cling_install_prefix

    @staticmethod
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

    @staticmethod
    def build_git_and_cmake(name: str, build_prefix: str, install_prefix: str, url: str, branch: str, threads: int,
                            remove_list: Union[None, List[str]], opts=[]) -> List[str]:
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
        :param remove_list: The list contains folders and files, which will be removed. If None, no item will be removed.
        :type remove_list: Union[None, List[str]]
        :param opts: a list of CMAKE arguments (e.g. -DCMAKE_BUILD_TYPE=RELEASE)
        :type opts: List[str]
        :returns: list of bash commands for git and cmake
        :rtype: List[str]

        """
        # commands
        cm = []
        git_conf = git()
        cm.append(git_conf.clone_step(repository=url,
                                      branch=branch, path=build_prefix, directory=name))
        cmake_conf = CMakeBuild(prefix=install_prefix)
        cm_build_dir = build_prefix+'/'+name+'_build'
        cm_source_dir = build_prefix+'/'+name
        cm.append(cmake_conf.configure_step(build_directory=cm_build_dir,
                                            directory=cm_source_dir,
                                            opts=opts)
                  )
        cm.append(cmake_conf.build_step(parallel=threads, target='install'))
        if type(remove_list) is list:
            remove_list.append(cm_build_dir)
            remove_list.append(cm_source_dir)
        return cm

    @staticmethod
    def build_openssl(name: str, build_prefix: str, install_prefix: str, threads: int, remove_list: Union[None, List[str]]) -> Tuple[List[str], Dict[str, str]]:
        """install openssl

        :param name: Name of the version (e.g. openssl-1.1.1c). Should be sliced from the official URL.
        :type name: str
        :param build_prefix: path where source code is stored and built
        :type build_prefix: str
        :param install_prefix: CMAKE_INSTAll_PREFIX
        :type install_prefix: str
        :param threads: number of threads for make -j (None for make -j$(nproc))
        :type threads: int
        :param remove_list: The list contains folders and files, which will be removed. If None, no item will be removed.
        :type remove_list: Union[None, List[str]]
        :returns: list of bash commands and dictionary of environment variables
        :rtype: List[str], {str,str}

        """
        make_threads = "$(nproc)"
        if threads:
            make_threads = str(threads)

        cm = []
        wget_ssl = wget()
        tar_ssl = tar()
        cm.append(wget_ssl.download_step(url='https://www.openssl.org/source/'+name+'.tar.gz',
                                             directory=build_prefix))
        cm.append(tar_ssl.untar_step(tarball=build_prefix +
                                     '/'+name+'.tar.gz', directory=build_prefix))
        cm.append('cd '+build_prefix+'/'+name)
        cm.append('./config --prefix=' + install_prefix +
                  ' -Wl,-rpath=/usr/local/lib')
        cm.append('make -j'+make_threads)
        cm.append('make install -j'+make_threads)
        cm.append('cd -')
        if type(remove_list) is list:
            remove_list.append(build_prefix+'/'+name)
            remove_list.append(build_prefix+'/'+name+'.tar.gz')

        return cm, {'OPENSSL_ROOT_DIR': install_prefix}

    @staticmethod
    def build_miniconda(build_prefix: str, install_prefix: str, remove_list=None) -> Tuple[List[str], Dict[str, str]]:
        """Return Miniconda 3 installation instructions

        :param build_prefix: path which the installation script is stored
        :type build_prefix: str
        :param install_prefix: path which miniconda is installed
        :type install_prefix: str
        :param remove_list: The list contains folders and files, which will be removed. If None, no item will be removed.
        :type remove_list: [str]
        :returns: list of bash commands and dictionary of environment variables
        :rtype: [str], {str,str}

        """
        cm = ['cd '+build_prefix,
              'wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh',
              'chmod u+x Miniconda3-latest-Linux-x86_64.sh',
              './Miniconda3-latest-Linux-x86_64.sh -b -p ' + install_prefix + '/miniconda3',
              install_prefix + '/miniconda3/bin/conda install -y jupyter',
              install_prefix + '/miniconda3/bin/conda install -y -c conda-forge jupyterlab',
              install_prefix + '/miniconda3/bin/conda install -y -c biobuilds libuuid',
              install_prefix + '/miniconda3/bin/conda install -y widgetsnbextension -c conda-forge',
              #install_prefix + '/miniconda3/bin/conda labextension install -y @jupyter-widgets/jupyterlab-manager'
              'cd -'
              ]

        if type(remove_list) is list:
            remove_list.append(
                build_prefix+'/Miniconda3-latest-Linux-x86_64.sh')

        return cm, {'PATH': '$PATH:' + install_prefix + '/miniconda3/bin/'}

    @staticmethod
    def build_jupyter_kernel(build_prefix: str, miniconda_prefix: str, user_install=False, remove_list=None) -> List[str]:
        """Returns jupyter kernel and instructions to install it

        :param build_prefix: path, where the kernels are stored
        :type build_prefix: str
        :param miniconda_prefix: path to the miniconda installation (should contain xcpp executable)
        :type miniconda_prefix: str
        :param user_install: if true, add flag --user to jupyter-kernelspec install
        :type user_install: bool
        :param remove_list: The list contains folders and files, which will be removed. If None, no item will be removed.
        :type remove_list: [str]
        :returns: list of bash commands
        :rtype: List[str]

        """
        user_install_arg = ''
        if user_install:
            user_install_arg = '--user '

        kernel_register = []
        for std in [11, 14, 17]:
            kernel_path = build_prefix+'/xeus-cling-cpp'+str(std)+'-cuda'
            kernel_register.append('mkdir -p ' + kernel_path)
            kernel_register.append("echo '" +
                                   XCC_gen.gen_jupyter_kernel(miniconda_prefix, std) +
                                   "' > " + kernel_path + "/kernel.json")
            kernel_register.append(
                'jupyter-kernelspec install ' + user_install_arg + kernel_path)
            if type(remove_list) is list:
                remove_list.append(kernel_path)

        return kernel_register

    @staticmethod
    def build_dev_jupyter_kernel(build_prefix: str, miniconda_prefix: str, remove_list=None) -> List[str]:
        """Returns jupyter kernel and instructions to install it in the miniconda3 folder. For release builds, please use build_jupyter_kernel().

        :param build_prefix: path, where the kernels are stored
        :type build_prefix: str
        :param miniconda_prefix: path to the miniconda installation (should contain xcpp executable)
        :type miniconda_prefix: str
        :param remove_list: The list contains folders and files, which will be removed. If None, no item will be removed.
        :type remove_list: [str]
        :returns: list of bash commands
        :rtype: List[str]

        """

        kernel_register = []
        kernel_register.append('mkdir -p ' + miniconda_prefix + '/miniconda3/share/jupyter/kernels/')

        for std in [11, 14, 17]:
            kernel_path = build_prefix+'/xeus-cling-cpp'+str(std)+'-cuda'
            kernel_register.append('mkdir -p ' + kernel_path)
            kernel_register.append("echo '" +
                                   XCC_gen.gen_jupyter_kernel(miniconda_prefix, std) +
                                   "' > " + kernel_path + "/kernel.json")
            kernel_register.append('cp -r ' + kernel_path + ' ' + miniconda_prefix + '/miniconda3/share/jupyter/kernels/')
            if type(remove_list) is list:
                remove_list.append(kernel_path)

        return kernel_register

    @classmethod
    def gen_jupyter_kernel(self, miniconda_prefix: str, cxx_std: int) -> str:
        """Generate jupyter kernel description files with cuda support for different C++ standards

        :param miniconda_prefix: path to the miniconda installation
        :type miniconda_prefix: str
        :param cxx_std: C++ Standard as number (options: 11, 14, 17)
        :type cxx_std: int
        :returns: json string
        :rtype: str

        """
        return json.dumps({
            'display_name': 'C++'+str(cxx_std)+'-CUDA',
            'argv': [
                miniconda_prefix + '/miniconda3/bin/xcpp',
                '-f',
                '{connection_file}',
                '-std=c++'+str(cxx_std),
                '-xcuda'
            ],
            'language': 'C++'+str(cxx_std)
        }
        )

    def __str__(self):
        s = ''
        for p in self.project_list:
            if p['tag'] == 'git_cmake':
                s = s + 'Git and CMake: ' + p['name'] + '\n'
            else:
                s = s + p['tag'] + ': ' + p['name'] + '\n'

        return s
