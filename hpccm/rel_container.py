import argparse
import hpccm
from hpccm.primitives import baseimage, shell, environment
from hpccm.building_blocks.packages import packages
from hpccm.building_blocks.cmake import cmake
from hpccm.templates.git import git
from hpccm.templates.CMakeBuild import CMakeBuild

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
    args = parser.parse_args()

    # parse number of build threads
    # if no threads are set, it is set to None which means it is executed with -j
    if args.j:
        number = int(args.j)
        if number < 1:
            raise ValueError('-j have to be greater than 0')
    else:
        number=None

    ##################################################################
    ### set container basics
    ##################################################################
    hpccm.config.set_container_format(args.container)

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
                                   path='/tmp/cling_src', directory='llvm')
    )
    git_clang = git()
    cbc.append(git_clang.clone_step(repository='http://root.cern.ch/git/clang.git',
                                    branch='cling-patches',
                                    path='/tmp/cling_src/llvm/tools')
    )
    git_cling = git()
    cbc.append(git_cling.clone_step(repository='https://github.com/SimeonEhrig/cling.git',
                                    branch='test_release',
                                    path='/tmp/cling_src/llvm/tools')
    )

    cm = CMakeBuild()
    cbc.append(cm.configure_step(build_directory='/tmp/cling_build',
                                 directory='/tmp/cling_src/llvm',
                                 opts=[
                                     '-DCMAKE_BUILD_TYPE=Release',
                                     '-DLLVM_ABI_BREAKING_CHECKS="FORCE_OFF"',
                                     '-DCMAKE_LINKER=/usr/bin/gold',
                                     '-DLLVM_ENABLE_RTTI=ON'
                                 ]
                                 )
    )
    cbc.append(cm.build_step(parallel=number, target='install'))

    Stage0 +=shell(commands=cbc)

    ##################################################################
    ### write to file or stdout
    ##################################################################
    if args.out:
        with open(args.out, 'w') as filehandle:
            filehandle.write(Stage0.__str__())
    else:
        print(Stage0)

if __name__ == "__main__":
    main()
