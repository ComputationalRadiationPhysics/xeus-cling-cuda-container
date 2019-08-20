"""Script to generate Docker and Singularity
   xeus-cling-cuda release container

   run `python rel_container.py --help` to get container generation options

   the script requires hpccm (https://github.com/NVIDIA/hpc-container-maker)

   the script is designed to be executed standalone
"""

import argparse, json, sys
import hpccm
from hpccm.primitives import baseimage, shell, environment, raw
from hpccm.building_blocks.packages import packages
from hpccm.building_blocks.cmake import cmake
from hpccm.templates.git import git
from hpccm.templates.CMakeBuild import CMakeBuild
from hpccm.templates.rm import rm
from hpccm.templates.wget import wget
from hpccm.templates.tar import tar

def git_and_CMake(name: str, build_dir: str, url: str, branch: str, threads: int,
                  remove_list: [str] , opts=[]) -> [str]:
    """Combines git clone, cmake and cmake traget='install'

    :param name: name of the project
    :type name: str
    :param build_dir: path where source code is cloned and built
    :type build_dir: str
    :param url: git clone url
    :type url: str
    :param branch: branch or version (git clone --branch)
    :type branch: str
    :param threads: number of threads for make -j (None for make -j$(nproc))
    :type threads: int
    :param remove_list: the list contains folders and files, which will be
                        removed
                        if None, no item will be removed
    :type remove_list: [str]
    :param opts: a list of CMAKE arguments (e.g. -DCMAKE_BUILD_TYPE=RELEASE)
    :type opts: [str]
    :returns: list of bash commands for git and cmake
    :rtype: [str]

    """
    # commands
    cm = []
    git_conf = git()
    cm.append(git_conf.clone_step(repository=url, branch=branch, path=build_dir, directory=name))
    cmake_conf = CMakeBuild()
    cm_build_dir = build_dir+'/'+name+'_build'
    cm_source_dir = build_dir+'/'+name
    cm.append(cmake_conf.configure_step(build_directory=cm_build_dir,
                                        directory=cm_source_dir,
                                        opts=opts)
              )
    cm.append(cmake_conf.build_step(parallel=threads, target='install'))
    if type(remove_list) is list:
        remove_list.append(cm_build_dir)
        remove_list.append(cm_source_dir)
    return cm

def build_openssl(name: str, build_dir: str, threads: int, remove_list: [str]) -> [str]:
    """install openssl

    :param name: name of the version (e.g. openssl-1.1.1c)
                 should be sliced from the official URL
    :type name: str
    :param build_dir: path where source code is stored and built
    :type build_dir: str
    :param threads: number of threads for make -j (None for make -j$(nproc))
    :type threads: int
    :param remove_list: the list contains folders and files, which will be
                        removed
                        if None, no item will be removed
    :type remove_list: [str]
    :returns: list of bash commands
    :rtype: [str]

    """
    cm=[]
    wget_ssl = wget()
    tar_ssl = tar()
    cm.append(wget_ssl.download_step(url='https://www.openssl.org/source/'+name+'.tar.gz',
                                     directory=build_dir))
    cm.append(tar_ssl.untar_step(tarball=build_dir+'/'+name+'.tar.gz', directory=build_dir))
    cm.append('cd '+build_dir+'/'+name)
    cm.append('./config')
    cm.append('make -j'+str(threads))
    cm.append('make install -j'+str(threads))
    cm.append('cd -')
    if type(remove_list) is list:
        remove_list.append(build_dir+'/'+name)
        remove_list.append(build_dir+'/'+name+'.tar.gz')

    return cm

def gen_jupyter_kernel(cxx_std : int) -> str:
    """Generate jupyter kernel description files with cuda support for different
       C++ standards

    :param cxx_std: C++ Standard as number (options: 11, 14, 17)
    :type cxx_std: int
    :returns: json string
    :rtype: str

    """
    return json.dumps({
                      "display_name" : "C++"+str(cxx_std)+"-CUDA",
                      "argv": [
                          "/opt/miniconda3/bin/xcpp",
                          "-f",
                          "{connection_file}",
                          "-std=c++"+str(cxx_std),
                          "-xcuda"
                      ],
                      "language": "C++"+str(cxx_std)
                      }
                     )

def main():
    ##################################################################
    ### parse args
    ##################################################################
    parser = argparse.ArgumentParser(
        description='Script to generate a Dockerfile or Singularity receipt for xeus-cling-cuda')
    parser.add_argument('--container', type=str, default='singularity',
                        choices=['docker', 'singularity'],
                        help='generate receipt for docker or singularity (default: singularity)')
    parser.add_argument('-j', type=str, help='number of build threads for make (default: -j)')
    parser.add_argument('-o', '--out', type=str, help='set path of output file (default: stdout)')
    parser.add_argument('-b',  type=str, default='RELEASE',
                        choices=['DEBUG','RELEASE','RELWITHDEBINFO','MINSIZEREL'],
                        help='set the CMAKE_BUILD_TYPE (default: RELEASE)')
    parser.add_argument('--build_command', type=str,
                        choices=['docker', 'singularity'],
                        help='print the build command for the container')
    parser.add_argument('--run_command', type=str,
                        choices=['docker', 'singularity'],
                        help='print the run command for the container')
    parser.add_argument('--build_dir', type=str, default='/tmp',
                        help='Set source and build path of the libraries and projects (default: /tmp).'
                        'Run --help_build_dir to get more information.')
    parser.add_argument('--keep_build', action='store_true',
                        help='keep source and build files after installation')
    parser.add_argument('--help_build_dir', action='store_true',
                        help='get information about build process')

    args = parser.parse_args()

    ##################################################################
    ### print help for building and running docker and singularity
    ### container
    ##################################################################
    if args.build_command:
        if args.build_command == 'singularity':
            print('singularity build <receipt>.sing <receipt>')
        else:
            print('docker build -t hpccm_cling_cuda:dev .')
        sys.exit()

    if args.run_command:
        if args.run_command == 'singularity':
            print('singularity exec --nv -B /run/user/$(id -u):/run/user/$(id -u) <receipt>.sing jupyter-lab')
        else:
            print('docker run --runtime=nvidia -p 8888:8888 --network="host" --rm -it hpccm_cling_cuda:dev')
        sys.exit()

    ##################################################################
    ### print help for build
    ##################################################################

    if args.help_build_dir:
        print('Docker: There are no automatic mounts at build time.')
        print('        To "cache" builds, you have to bind folders manual.')
        print('        See Singularity')
        print('Singularity: The folders /tmp and $HOME from the host are automatically mounted at build time')
        print('        This can be used to cache builds. But it also can cause problems. To avoid problems,')
        print('        you should delete the source and build folders after building the container.')
        print('        If you you want to keep the build inside the container, you should choose an unbound')
        print('        path. For example /opt')
        sys.exit()

    # parse number of build threads
    # if no threads are set, it is set to None which means it is executed with -j
    if args.j:
        threads = int(args.j)
        if threads < 1:
            raise ValueError('-j have to be greater than 0')
    else:
        threads=None

    Stage0 = gen_stage(args.container, args.build_dir, args.b, args.keep_build, threads)

    ##################################################################
    ### write to file or stdout
    ##################################################################
    if args.out:
        with open(args.out, 'w') as filehandle:
            filehandle.write(Stage0.__str__())
    else:
        print(Stage0)


def gen_stage(container : str, build_dir : str, build_type : str, keep_build : bool, threads : int):
    """Generates the hpccm stage object that contains the description of the
       base container. Can be extended or translated to a Docker or Singularity
       Receive.

    :param container: 'docker' or 'singularity'
    :type container: str
    :param build_dir: source and build path of the libraries and projects
    :type build_dir: str
    :param build_type: set the CMAKE_BUILD_TYPE : 'DEBUG', 'RELEASE', 'RELWITHDEBINFO', 'MINSIZEREL'
    :type build_type: str
    :param keep_build: keep source and build files after installation
    :type keep_build: bool
    :param threads: number of build threads for make (None for all available threads)
    :type threads: int
    :returns: hpccm container stage with the base container
    :rtype: hpccm.Stage.Stage

    """
    if keep_build:
        # list of folders and files removed in the last step
        remove_list = None
    else:
        remove_list = []

    ##################################################################
    ### set container basics
    ##################################################################
    hpccm.config.set_container_format(container)

    Stage0 = hpccm.Stage();
    Stage0 += baseimage(image='nvidia/cuda:8.0-devel-ubuntu16.04')
    # LD_LIBRARY_PATH is not taken over correctly when the docker container is converted
    # to a singularity container.
    Stage0 += environment(variables={'LD_LIBRARY_PATH': '$LD_LIBRARY_PATH:/usr/local/cuda/lib64'})
    Stage0 += packages(ospackages=['git', 'python', 'wget', 'pkg-config', 'uuid-dev', 'gdb',
                                   'locales', 'locales-all' ])
    # set language to en_US.UTF-8 to avoid some problems with the cling output system
    Stage0 += shell(commands=['locale-gen en_US.UTF-8', 'update-locale LANG=en_US.UTF-8'])
    Stage0 += cmake(eula=True)

    ##################################################################
    ### build and install cling
    ##################################################################
    # cling_build_commands
    cbc = []

    git_llvm = git()
    cbc.append(git_llvm.clone_step(repository='http://root.cern.ch/git/llvm.git',
                                   branch='cling-patches',
                                   path=build_dir+'/cling_src', directory='llvm')
    )
    git_clang = git()
    cbc.append(git_clang.clone_step(repository='http://root.cern.ch/git/clang.git',
                                    branch='cling-patches',
                                    path=build_dir+'/cling_src/llvm/tools')
    )
    git_cling = git()
    cbc.append(git_cling.clone_step(repository='https://github.com/SimeonEhrig/cling.git',
                                    branch='test_release',
                                    path=build_dir+'/cling_src/llvm/tools')
    )

    cm_cling = CMakeBuild()
    cbc.append(cm_cling.configure_step(build_directory=build_dir+'/cling_build',
                                 directory=build_dir+'/cling_src/llvm',
                                 opts=[
                                     '-DCMAKE_BUILD_TYPE='+build_type,
                                     '-DLLVM_ABI_BREAKING_CHECKS="FORCE_OFF"',
                                     '-DCMAKE_LINKER=/usr/bin/gold',
                                     '-DLLVM_ENABLE_RTTI=ON'
                                 ]
                                 )
    )
    cbc.append(cm_cling.build_step(parallel=threads, target='install'))

    if type(remove_list) is list:
        remove_list.append(build_dir+'/cling_build')
        remove_list.append(build_dir+'/cling_src')

    Stage0 +=shell(commands=cbc)

    ##################################################################
    ### build and install xeus
    ##################################################################
    xeus_build = []
    xeus_build += git_and_CMake(name='libzmq',
                                build_dir=build_dir,
                                url='https://github.com/zeromq/libzmq.git',
                                branch='v4.2.5',
                                opts=['-DWITH_PERF_TOOL=OFF',
                                      '-DZMQ_BUILD_TESTS=OFF',
                                      '-DENABLE_CPACK=OFF',
                                      '-DCMAKE_BUILD_TYPE='+build_type
                                ],
                                threads=threads,
                                remove_list=remove_list)
    xeus_build += git_and_CMake(name='cppzmq',
                                build_dir=build_dir,
                                url='https://github.com/zeromq/cppzmq.git',
                                branch='v4.3.0',
                                opts=['-DCMAKE_BUILD_TYPE='+build_type
                                ],
                                threads=threads,
                                remove_list=remove_list)
    xeus_build += build_openssl(name='openssl-1.1.1c',
                                build_dir=build_dir,
                                threads=threads,
                                remove_list=remove_list)
    xeus_build += git_and_CMake(name='nlohmann_json',
                                build_dir=build_dir,
                                url='https://github.com/nlohmann/json.git',
                                branch='v3.3.0',
                                opts=['-DCMAKE_BUILD_TYPE='+build_type
                                ],
                                threads=threads,
                                remove_list=remove_list)
    xeus_build += git_and_CMake(name='xtl',
                                build_dir=build_dir,
                                url='https://github.com/QuantStack/xtl.git',
                                branch='0.6.5',
                                opts=['-DCMAKE_BUILD_TYPE='+build_type
                                ],
                                threads=threads,
                                remove_list=remove_list)
    xeus_build += git_and_CMake(name='xeus',
                                build_dir=build_dir,
                                url='https://github.com/QuantStack/xeus.git',
                                branch='0.20.0',
                                opts=['-DBUILD_EXAMPLES=OFF',
                                      '-DDISABLE_ARCH_NATIVE=ON',
                                      '-DCMAKE_BUILD_TYPE='+build_type
                                ],
                                threads=threads,
                                remove_list=remove_list)
    Stage0 +=shell(commands=xeus_build)

    ##################################################################
    ### build and install xeus-cling
    ##################################################################
    if container == 'singularity':
        Stage0 +=shell(commands=['mkdir -p /run/user', 'chmod 777 /run/user'])

    # install Miniconda 3, Jupyter Notebook and Jupyter Lab
    Stage0 +=shell(commands=['cd '+build_dir,
                             'wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh',
                             'chmod u+x Miniconda3-latest-Linux-x86_64.sh',
                             './Miniconda3-latest-Linux-x86_64.sh -b -p /opt/miniconda3',
                             '/opt/miniconda3/bin/conda install -y jupyter',
		             '/opt/miniconda3/bin/conda install -y -c conda-forge jupyterlab',
                             '/opt/miniconda3/bin/conda install -y -c biobuilds libuuid',
                             'cd -'
                             ]
                   )
    if type(remove_list) is list:
        remove_list.append(build_dir+'/Miniconda3-latest-Linux-x86_64.sh')
    Stage0 += environment(variables={'PATH': '$PATH:/opt/miniconda3/bin/'})

    xeus_cling_build = []
    xeus_cling_build += git_and_CMake(name='pugixml',
                                      build_dir=build_dir,
                                      url='https://github.com/zeux/pugixml.git',
                                      branch='v1.8.1',
                                      opts=['-DCMAKE_BUILD_TYPE='+build_type,
                                            '-DCMAKE_POSITION_INDEPENDENT_CODE=ON'
                                      ],
                                      threads=threads,
                                      remove_list=remove_list)
    xeus_cling_build += git_and_CMake(name='cxxopts',
                                      build_dir=build_dir,
                                      url='https://github.com/jarro2783/cxxopts.git',
                                      branch='v2.1.1',
                                      opts=['-DCMAKE_BUILD_TYPE='+build_type
                                      ],
                                      threads=threads,
                                      remove_list=remove_list)
    xeus_cling_build += git_and_CMake(name='xeus-cling',
                                      build_dir=build_dir,
                                      url='https://github.com/QuantStack/xeus-cling.git',
                                      branch='0.6.0',
                                      opts=['-DCMAKE_INSTALL_PREFIX=/opt/miniconda3/',
                                            '-DCMAKE_INSTALL_LIBDIR=/opt/miniconda3/lib',
                                            '-DCMAKE_LINKER=/usr/bin/gold',
                                            '-DCMAKE_BUILD_TYPE='+build_type,
                                            '-DDISABLE_ARCH_NATIVE=ON'
                                      ],
                                      threads=threads,
                                      remove_list=remove_list)
    Stage0 +=shell(commands=xeus_cling_build)
    ##################################################################
    ### register jupyter kernel
    ##################################################################
    # custom kernels for cuda are necessary, because the start command of cling
    # is `cling -xcuda`
    kernel_register = []
    for std in [11, 14, 17]:
        kernel_path = build_dir+'/xeus-cling-cpp'+str(std)+'-cuda'
        kernel_register.append('mkdir -p ' + kernel_path)
        kernel_register.append("echo '" + gen_jupyter_kernel(std) + "' > "
                               + kernel_path + "/kernel.json")
        kernel_register.append('jupyter-kernelspec install ' + kernel_path)
        if type(remove_list) is list:
            remove_list.append(kernel_path)

    Stage0 +=shell(commands=kernel_register)

    ##################################################################
    ### remove files
    ##################################################################
    if type(remove_list) is list:
        r = rm()
        Stage0 +=shell(commands=[r.cleanup_step(items=remove_list)])

    Stage0 += raw(docker='EXPOSE 8888')

    return Stage0

if __name__ == "__main__":
    main()
