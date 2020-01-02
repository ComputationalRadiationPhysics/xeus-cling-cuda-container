"""Script to a Singularity development container of the xeus-cling-cuda stack.

   run `python dev_container.py --help` to get container generation options

   the script requires hpccm (https://github.com/NVIDIA/hpc-container-maker)

   the script is designed to be executed standalone
"""

import argparse
import sys
import os
import generator as gn


def main():
    ##################################################################
    # parse args
    ##################################################################
    parser = argparse.ArgumentParser(
        description='Script to generate Singularity receipt for a xeus-cling-cuda development container',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        '-j', type=str, help='number of build threads for make (default: -j)')
    parser.add_argument(
        '-l', type=str, help='number of linker threads for the cling build (default: -j)')
    parser.add_argument('-o', '--out', type=str,
                        help='set path of output file (default: stdout)\n' +
                        'if --store_gen_command is set to 1, save file with arguments beside the recipe')
    parser.add_argument('-b',  type=str, default='',
                        choices=['DEBUG', 'RELEASE',
                                 'RELWITHDEBINFO', 'MINSIZEREL'],
                        help='set the CMAKE_BUILD_TYPE (default: DEBUG)')
    parser.add_argument('--second_build',  type=str, default='',
                        choices=['', 'DEBUG', 'RELEASE',
                                 'RELWITHDEBINFO', 'MINSIZEREL'],
                        help='If set, create a second cling build. Can be used, for example, if you want to get a debug and release version of cling.')
    parser.add_argument('--build_command', action='store_true',
                        help='print the build command for the container')
    parser.add_argument('--run_command', action='store_true',
                        help='print the run command for the container')
    parser.add_argument('--build_prefix', type=str, default='/tmp',
                        help='Set source and build path of the libraries and projects.\n'
                        'Only the prefixes /tmp (build outside the container with singularity) and /opt are allowed (default: /tmp).'
                        'Run --help_build_dir to get more information.')
    parser.add_argument('--project_path', type=str, default=os.getcwd() + '/build',
                        help='Set prefix folder of Miniconda, Cling and Xeus-Cling. Default: $(pwd)/build')
    parser.add_argument('--keep_build', action='store_true',
                        help='keep source and build files after installation\n')
    parser.add_argument('--help_build_prefix', action='store_true',
                        help='get information about build process')
    parser.add_argument('--clang_version', type=int, default=8,
                        choices=[8, 9],
                        help='set the version of the clang project compiler (default: 8)')
    parser.add_argument('--store_gen_command', type=int, default=1,
                        choices=[0, 1],
                        help='save the command with which the recipe was generated (default: 1)')
    parser.add_argument('--cling_url', type=str,
                        help='Set custom Cling GitHub url.')
    parser.add_argument('--cling_branch', type=str,
                        help='Used only when --cling_url is set. Change the GitHub branch of Cling. Cling GitHub Commit Hash is deleted.')
    parser.add_argument('--cling_hash', type=str,
                        help='Used only when --cling_url is set. Change the GitHub Commit of Cling. Cling GitHub branch is deleted.')
    parser.add_argument('--build_libcxx', action='store_true',
                        help='Set the flag to build the whole stack with libc++. '
                        'Also add the libc++ and libc++abi projects to the llvm build.')

    args = parser.parse_args()

    ##################################################################
    # print help for building and running the container
    ##################################################################
    if args.build_command:
        print('build the container')
        print('singularity build --fakeroot <recipe>.sif <recipe>.def')
        print('download and build the source code to be further developed')
        print('singularity run <recipe>.sif')
        sys.exit()

    if args.run_command:
        print('singularity exec --nv -B /run/user/$(id -u):/run/user/$(id -u) <receipt>.sif jupyter-lab')
        sys.exit()

    ##################################################################
    # print help for build
    ##################################################################

    if args.help_build_prefix:
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
        threads = None

    if args.l:
        linker_threads = int(args.l)
        if linker_threads < 1:
            raise ValueError('-l have to be greater than 0')
    else:
        linker_threads = None

    # depending on the path, certain build locations can be difficult
    build_prefix = str(args.build_prefix)
    if (not build_prefix.startswith('/tmp')) and (not build_prefix.startswith('/opt')):
        raise ValueError('--build_prefix have to start with /tmp or /opt')

    gen_args=None
    if args.store_gen_command == 1:
        gen_args=' '.join(sys.argv)
        if args.out:
            with open(os.path.dirname(os.path.abspath(args.out)) + '/'  +
                      os.path.splitext(os.path.basename(args.out))[0] + '_command.txt', 'w') as filehandle:
                filehandle.write(gen_args)

    xcc_gen = gn.XCC_gen(container='singularity',
                         build_prefix=build_prefix,
                         install_prefix='/usr/local',
                         build_type=args.b,
                         keep_build=args.keep_build,
                         threads=threads,
                         linker_threads=linker_threads,
                         clang_version=args.clang_version,
                         gen_args=gen_args,
                         build_libcxx=args.build_libcxx)

    if args.cling_url:
        if args.cling_branch is not None and args.cling_hash is not None:
            print('--cling_branch and --cling_hash cannot be used at the same time')
            exit(1)
        else:
            xcc_gen.cling_url = args.cling_url
            xcc_gen.cling_branch = args.cling_branch
            xcc_gen.cling_hash = args.cling_hash

    stage = xcc_gen.gen_devel_stage(project_path=os.path.abspath(args.project_path),
                                    dual_build_type = (None if args.second_build == '' else args.second_build))

    ##################################################################
    # write to file or stdout
    ##################################################################
    if args.out:
        with open(args.out, 'w') as filehandle:
            filehandle.write(stage.__str__())
    else:
        print(stage)


if __name__ == "__main__":
    main()
