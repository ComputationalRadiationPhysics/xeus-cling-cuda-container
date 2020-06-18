import json, sys, os
import shutil, subprocess
from typing import Dict

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import xcc.generator as gn


def main():
    if len(sys.argv) < 2:
        print('usage: python3 recipe.py /path/config.json')
        exit(0)
    with open(str(sys.argv[1])) as config_file:
        config = json.load(config_file)['build']
        config_file.close()

    print('compile threads: ' + str(config['compile_threads']) + '\n'
          'linker threads: ' + str(config['linker_threads']))

    create(config, True)
    create(config, False)

def create(config : Dict, libcxx : bool):
    """Generate the singularity recipe.

    :param config: Json config with number of compile and linker threads
    :type config: Dict
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

    # generate recipe
    xcc_gen = gn.XCC_gen(build_prefix='/opt',
                         threads=config['compile_threads'],
                         linker_threads=config['linker_threads'],
                         build_libcxx=libcxx)
    with open(recipe_name, 'w') as recipe_file:
        recipe_file.write(xcc_gen.gen_release_single_stage().__str__())
        recipe_file.close()

if __name__ == '__main__':
    main()
