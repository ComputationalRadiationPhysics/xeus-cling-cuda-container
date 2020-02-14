import json, sys, os
import shutil, subprocess
from typing import Dict
import recipe as rc

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import generator as gn

def main():
    if len(sys.argv) < 2:
        print('usage: python3 build.py /path/config.json')
        exit(0)

    check_singularity()

    # load the number of compile and link threads from a json file
    with open(str(sys.argv[1])) as config_file:
        config = json.load(config_file)['build']
        config_file.close()

    print('compile threads: ' + str(config['compile_threads']) + '\n'
          'linker threads: ' + str(config['linker_threads']) + '\n')

    answer = ''
    while answer not in ('y', 'n'):
        answer = input('is the config correct? [y/n] : ')
        if answer == 'y':
            rc.create(config, False)
            build(False)
            rc.create(config, True)
            build(True)
        if answer == 'n':
            exit(1)

def check_singularity():
    """Check if the singularity container software is available and runs 'singularity --version'

    """
    if not shutil.which('singularity'):
        print('could not find singularity')
        exit(1)

    process = subprocess.Popen(['singularity', '--version'], stdout=subprocess.PIPE)
    output, error = process.communicate()
    if error is not None:
        print('could not run "singularity --version"')
        exit(1)

    print(output.decode("utf-8"))

def build(libcxx : bool):
    """Generate the singularity recipe and build it.
    :param libcxx: build the container with libc++
    :type libcxx: bool

    """
    if libcxx:
        recipe_name = 'recipe_libcxx.def'
        image_name = 'xeus-cling-cuda-container-cxx.sif'
        log_name = 'build_libcxx.log'
    else:
        recipe_name = 'recipe.def'
        image_name = 'xeus-cling-cuda-container.sif'
        log_name = 'build.log'

    # build image
    process = subprocess.Popen(['singularity',
                                'build',
                                '--fakeroot',
                                image_name,
                                recipe_name],
                               stdout=subprocess.PIPE)
    output, error = process.communicate()
    if error is not None:
        print('"singularity build --fakeroot ' + image_name + ' ' + recipe_name  + '" failed')
        exit(1)

    with open(log_name, 'w') as build_log:
        build_log.write(output.decode('utf-8'))
        build_log.close()

if __name__ == '__main__':
    main()
