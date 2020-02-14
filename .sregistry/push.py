import sys, json, os
import shutil, subprocess

def main():
    check_singularity()

    # extract the version from the container
    container_version = get_container_version()
    if container_version is None:
        print('could not find container version in xeus-cling-cuda-container')
        exit(1)

    answer = ''
    while answer not in ('y', 'n'):
        answer = input('is version ' + container_version + ' correct? [y/n] : ')
        if answer == 'y':
            login_sregistry()
            sign_container(False)
            sign_container(True)
            push_container(container_version, False)
            push_container('latest', False)
            push_container(container_version, True)
            push_container('latest', True)
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

def get_container_version():
    """Extract the version from the xeus-cling-cuda-container

    """
    c_version = 'singularity inspect -d xeus-cling-cuda-container.sif'
    p_version = subprocess.Popen(c_version.split(), stdout=subprocess.PIPE)
    output, error = p_version.communicate()

    if error is not None:
        print('could not run: ' + c_version)
        exit(1)

    for line in output.decode("utf-8").split('\n'):
        if 'XCC Version' in line:
            # since the tag is generated, it should have same form every time
            # XCC Version x.x
            return line.strip()[len('XCC Version '):]

    return None

def login_sregistry():
    """Login to the sregistry account

    """
    # login to the remote server
    c_login = 'singularity remote login --tokenfile ' + str(os.getenv("HOME")) + '/.singularity/sylabs-token'
    p_login = subprocess.Popen(c_login.split())
    output, error = p_login.communicate()

    if error is not None:
        print('could not run: ' + c_login)
        exit(1)


def sign_container(libcxx : bool):
    """Sign the container with the private key

    :param libcxx: sign the libc++ container version
    :type libcxx: bool

    """
    image_name = 'xeus-cling-cuda-container-cxx.sif' if libcxx else 'xeus-cling-cuda-container.sif'
    c_sign = 'singularity sign ' + image_name
    p_sign = subprocess.Popen(c_sign.split())
    output, error = p_sign.communicate()

    if error is not None:
        print('could not run: ' + c_sign)
        exit(1)


def push_container(version : str, libcxx : bool):
    """upload the image

    :param version: is used for the tag
    :type version: str
    :param libcxx: push the libc++ container version
    :type libcxx: bool

    """
    image_name = 'xeus-cling-cuda-container-cxx.sif' if libcxx else 'xeus-cling-cuda-container.sif'
    library_name = 'xeus-cling-cuda-cxx:' if libcxx else 'xeus-cling-cuda:'

    # upload the container
    c_push = 'singularity push ' + image_name + ' library://sehrig/default/' + library_name + version
    p_push = subprocess.Popen(c_push.split())
    output, error = p_push.communicate()

    if error is not None:
        print('could not run: ' + c_push)
        exit(1)

if __name__ == '__main__':
    main()
