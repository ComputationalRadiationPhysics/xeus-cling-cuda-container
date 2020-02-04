# Xeus-Cling-Cuda-Container
The repository contains container recipes to build the entire stack of Xeus-Cling and Cling including cuda extension with just a few commands.

# General Information
The containers contain Xeus-Cling, Jupyter Notebook and Lab and the latest version of Xeus-Cling-CUDA (https://github.com/SimeonEhrig/cling/tree/test_release).

Various containers are available. All recipes are generated using Python scripts and the [hpccm](https://github.com/NVIDIA/hpc-container-maker) library.

- release
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

# General Requirements

To build and use the container, your host system needs two prerequisites:
- [Singularity](http://singularity.lbl.gov/) >= 3.3.0
- Nvidia CUDA Driver, which supports CUDA >= 8.0

# Building Containers

## General hints

* **Hint 1:** Cling requires a lot of RAM to build. Be careful when setting the number of threads. Otherwise you will get an out-of-memory error at link time. Working memory thread combinations are:
  * 4 Threads with 32 GB RAM
  * 14 Threads with 128 GB RAM
* **Hint 2:** Be careful with hyperthreading. It can drastically change the memory usage.
* **Hint 3:** If you use Singularity and do not have root permission on your system, you can use the argument `--fakeroot` or you can build the container on another system with root permission and copy it to your target system.

## Release
The recipes are written in Python with [hpccm](https://github.com/NVIDIA/hpc-container-maker). No container images are created directly. Instead it creates recipes for singularity and docker. To build a singularity container, follow these steps.

```bash
# create recipe
python rel_container.py -o rel-xeus-cling-cuda.def
# build container
singularity build --fakeroot rel-xeus-cling-cuda.sif rel-xeus-cling-cuda.def
```

Use the `python rel-container.py --help` command to display all possible recipe configuration options. For example, you can set the number of threads with `python rel-container.py -j 4 -o rel-xeus-cling-cuda` (by default, all threads of the system are used).

## Dev

The development container is also generated via Python script and built via Singularity. In addition to the normal build process, there is a second build stage. In this step, the source code of the projects to be further developed is downloaded and built. This is necessary because the container is read-only. The files of this step are stored on the host system, e.g. a folder in the home directory. 

```bash
# create recipe
python dev_container.py -o dev-xeus-cling-cuda.def --project_path=/home/user/project/cling
# build container
singularity build --fakeroot dev-xeus-cling-cuda.sif dev-xeus-cling-cuda.def
singularity run dev-xeus-cling-cuda.sif
```

* **Hint 1:** Relative `project_path`s are automatically converted to absolute paths.
* **Hint 2:** Depending on the `XCC_BUILD_TYPE` the build may require a lot of storage space. The `Debug` build needs about 82 GB.

Use the `python dev-container.py --help` command to display all possible recipe configuration options.

# Downloading Container from the Registry 

The built release containers are also available in the singularity register:

```bash
singularity pull library://sehrig/default/xeus-cling-cuda 
```

or

```bash
# the stack was built with the LLVM's libc++ and cling used libc++ (solves some problems)
 singularity pull library://sehrig/default/xeus-cling-cuda-cxx 
 ```

# Running
To use the xeus-cling-cuda stack via jupyter notebook use the following command.

``` bash
    singularity exec --nv rel-xeus-cling-cuda.sif jupyter-notebook
```

To start jupyter-lab, you must use the following command.

``` bash
    singularity exec --nv -B /run/user/$(id -u):/run/user/$(id -u) rel-xeus-cling-cuda.sif jupyter-lab
```

* **Hint 1:** If you get a CUDA driver error at runtime, you may have forgotten to set the `--nv` flag.
* **Hint 2:** If you are using a SSH connection, do not forget the [port forwarding](https://help.ubuntu.com/community/SSH/OpenSSH/PortForwarding) for port 8888.
* **Hint 3:** If you want fully isolation (e.g. because you have problems with other kernel configurations in your home directory) use the `--no-home` argument and manually bind a directory for notebooks via `-B /path/on/host:/path/in/container/`.

# Development

If you change the code of xeus-cling or cling, you need to rebuild the applications. There are two ways to rebuild the application.

## via interface shell
It runs an interactive shell session

``` bash
    singularity shell --nv dev-xeus-cling-cuda.sif
```

## via exec command
Run the container, executes the commands inside the container and exit it.

``` bash
    singularity exec --nv dev-xeus-cling-cuda.sif cd path/to/code && make
```
