import json, sys, os
import shutil, subprocess
from typing import Dict

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
            build(config)
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

def build(config : Dict):
    """Generate the singularity recipe and build it.

    :param config: Json config with number of compile and linker threads
    :type config: Dict

    """
    # generate recipe
    xcc_gen = gn.XCC_gen(build_prefix='/opt',
                         threads=config['compile_threads'],
                         linker_threads=config['linker_threads'])
    with open('recipe.def', 'w') as recipe_file:
        recipe_file.write(xcc_gen.gen_release_single_stage().__str__())
        recipe_file.close()

    # build image
    process = subprocess.Popen(['singularity',
                                'build',
                                '--fakeroot',
                                'xeus-cling-cuda-container.sif',
                                'recipe.def'],
                               stdout=subprocess.PIPE)
    output, error = process.communicate()
    if error is not None:
        print('"singularity build --fakeroot xeus-cling-cuda-container.sif recipe.def" failed')
        exit(1)

    with open('build.log', 'w') as build_log:
        build_log.write(output.decode('utf-8'))
        build_log.close()

if __name__ == '__main__':
    main()