# Xeus-Cling-Cuda-Container
The repository contains container recipes to build the entire stack of Xeus-Cling and Cling including cuda extension with just a few commands.

# General Information
The containers contain Xeus-Cling, Jupyter Notebook and Lab and the latest version of Xeus-Cling-CUDA (https://github.com/SimeonEhrig/cling/tree/test_release).

Various containers are available

- release
	- recipe is written in Python with [hpccm](https://github.com/NVIDIA/hpc-container-maker)
	- it can generate recipes for
		- singularity (official supported)
		- docker (experimental)
	- contains a fully integrated xeus-cling-cuda stack built in release mode
		- singularity need extra flag `--no-home` for full isolation
- dev
	- partly integrated into the container
		- all libraries which should not to changed are integrated in the container
		- miniconda, cling and xeus-cling are built outside the container and allow modifications on the code

It is also possible to [install](https://github.com/QuantStack/xeus-cling) xeus-cling via conda. But this installation use cling version 0.5 and does not support CUDA.

# Installation

To build and use the container, your host system needs two prerequisites:
- [Singularity](http://singularity.lbl.gov/) >= 2.6.0
- Nvidia CUDA Driver, which supports CUDA >= 8.0

## General hints

* **Hint 1:** Cling requires a lot of RAM to build. Be careful when setting the number of threads. Otherwise you will get an out-of-memory error at link time. Working memory thread combinations are:
  * 4 Threads with 32 GB RAM
  * 14 Threads with 128 GB RAM

* **Hint 2:** Be careful with hyperthreading. It can drastically change the memory usage.

* **Hint 3:** If you do not have root permission on your system, you can build the container on another system with root permission and copy it to your target system.

## Release
The recipes are written in Python with [hpccm](https://github.com/NVIDIA/hpc-container-maker). No container images are created directly. Instead it creates recipes for singularity and docker. To build a singularity container, follow these steps.

```bash
# create recipe
python rel-container.py -o rel-xeus-cling-cuda
# build container
sudo singularity build rel-xeus-cling-cuda.sing rel-xeus-cling-cuda
```

Use the `python rel-container.py --help` command to display all possible recipe configuration options. For example, you can set the number of threads with `python rel-container.py -j 4 -o rel-xeus-cling-cuda` (by default, all threads of the system are used).

## Dev
The installation of the dev container is divided into three parts, because the modification of the source code of cling and xeus-cling by the user is possible. The three parts are: 
- generating a configuration
- build container as root
- build applications as user

### Configuration
You can write the `config.json` yourself or use the `generate_config.sh` script to generate it. The `config.json` must be in same folder where you start the container build process.

Structure of the `config.json`
```json
{
    "XCC_PROJECT_PATH" : "/path/to/miniconda_xeus-cling_cling_installation",
    "XCC_BUILD_TYPE" : "CMAKE_BUILD_TYPE",
    "XCC_NUM_THREADS" : "Number or empty like make -j"
}
```

### Build Container as Root

To build the container, simply use the following command in the project folder.

``` bash
    sudo singularity build dev-xeus-cling-cuda.sing dev-xeus-cling-cuda
```


### Build Applications as User

**Attention**, this step cannot be performed on another system. It must run on the target system.

This step builds miniconda, cling and xeus-cling with your user permission in the path `$XCC_PROJECT_PATH`. To start the build process, simply use the following command.

``` bash
    singularity run dev-xeus-cling-cuda.sing
```

**Hint:** Depending on the `XCC_BUILD_TYPE` the build may require a lot of storage space. The `Debug` build needs about 82 GB.

# Running
To use the xeus-cling-cuda stack via jupyter notebook use the following command.

``` bash
    singularity exec --nv rel-xeus-cling-cuda.sing jupyter-notebook
```

To start jupyter-lab, you must use the following command.

``` bash
    singularity exec --nv -B /run/user/$(id -u):/run/user/$(id -u) rel-xeus-cling-cuda.sing jupyter-lab
```

* **Hint 1:** If you get a CUDA driver error at runtime, you may have forgotten to set the `--nv` flag.
* **Hint 2:** If you are using a SSH connection, do not forget the [port forwarding](https://help.ubuntu.com/community/SSH/OpenSSH/PortForwarding) for port 8888.
* **Hint 3:** If you want fully isolation (e.g. because you have problems with other kernel configurations in your home directory) use the `--no-home` argument and manually bind a directory for notebooks via `-B /path/on/host:/path/in/container/`.

# Development

If you change the code of xeus-cling or cling, you need to rebuild the applications. There are two commands to run `make` and `make install` for cling or xeus-cling.

``` bash
    singularity run --app build_cling dev-xeus-cling-cuda.sing
```

``` bash
    singularity run --app build_xeus-cling dev-xeus-cling-cuda.sing
```
