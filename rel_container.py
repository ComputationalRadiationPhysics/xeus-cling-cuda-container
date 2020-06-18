"""Script to generate Docker or Singularity
   xeus-cling-cuda release container

   run `python rel_container.py --help` to get container generation options

   the script requires hpccm (https://github.com/NVIDIA/hpc-container-maker)

   the script is designed to be executed standalone
"""

import argparse
import json
import sys
import os
import xcc.generator as gn


def main():
    ##################################################################
    # parse args
    ##################################################################
    parser = argparse.ArgumentParser(
        description='Script to generate a Dockerfile or Singularity receipt for xeus-cling-cuda',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--container', type=str, default='singularity',
                        choices=['docker', 'singularity'],
                        help='generate receipt for docker or singularity (default: singularity)')
    parser.add_argument(
        '-j', type=str, help='number of build threads for make (default: -j)')
    parser.add_argument(
        '-l', type=str, help='number of linker threads for the cling build (default: -j)')
    parser.add_argument('-o', '--out', type=str,
                        help='set path of output file (default: stdout)' +
                        'if --store_gen_command is set to 1, save file with arguments beside the recipe')
    parser.add_argument('--build_command', type=str,
                        choices=['docker', 'singularity'],
                        help='print the build command for the container')
    parser.add_argument('--run_command', type=str,
                        choices=['docker', 'singularity'],
                        help='print the run command for the container')
    parser.add_argument('--build_prefix', type=str, default='/tmp',
                        help='Set source and build path of the libraries and projects.\n'
                        'Only the prefixes /tmp (build outside the container with singularity) and /opt are allowed (default: /tmp).'
                        'Run --help_build_dir to get more information.')
    parser.add_argument('--keep_build', action='store_true',
                        help='keep source and build files after installation\n'
                        'only for singularity supported, because it can store builds in the host memory\n'
                        'for docker, it is not useful, because the multi-stage build')
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
    # print help for building and running docker and singularity
    # container
    ##################################################################
    if args.build_command:
        if args.build_command == 'singularity':
            print('singularity build --fakeroot <receipt>.sif <receipt>.def')
        else:
            print('docker build -t hpccm_cling_cuda:dev .')
        sys.exit()

    if args.run_command:
        if args.run_command == 'singularity':
            print(
                'singularity exec --nv -B /run/user/$(id -u):/run/user/$(id -u) <receipt>.sif jupyter-lab')
        else:
            print(
                'docker run --runtime=nvidia -p 8888:8888 --network="host" --rm -it hpccm_cling_cuda:dev')
        sys.exit()

    ##################################################################
    # print help for build
    ##################################################################

    if args.help_build_prefix:
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
        threads = None

    if args.l:
        linker_threads = int(args.l)
        if linker_threads < 1:
            raise ValueError('-l have to be greater than 0')
    else:
        linker_threads = None

    # depending on the container software, certain build locations can be difficult
    build_prefix = str(args.build_prefix)
    if (not build_prefix.startswith('/tmp')) and (not build_prefix.startswith('/opt')):
        raise ValueError('--build_dir have to start with /tmp or /opt')

    gen_args=None
    if args.store_gen_command == 1:
        gen_args=' '.join(sys.argv)
        if args.out:
            with open(os.path.dirname(os.path.abspath(args.out)) + '/'  +
                      os.path.splitext(os.path.basename(args.out))[0] + '_command.txt', 'w') as filehandle:
                filehandle.write(gen_args)

    xcc_gen = gn.XCC_gen(container=args.container,
                         build_prefix=build_prefix,
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

    stage = xcc_gen.gen_release_single_stage()

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
