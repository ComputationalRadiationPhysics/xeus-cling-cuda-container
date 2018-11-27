# Xeus-Cling-Cuda-Container
The repository contains singularity container descriptions, which allows to build the xeus-cling - cling-cuda stack from source with few commands. 

# General Information
The containers of this repository contains scripts to build a full stack of xeus-cling with a cling 0.6-dev version (has CUDA extension) and jupyter notebook.

There are different containers available

- release (coming soon)
	- contains a full integrated xeus-cling-cuda stack built in the release mode
- dev
	- partial integrated in the container
		- all libraries, which should not modified, are integrate in the container
		- miniconda, cling and xeus-cling are built outside the container and allows modifications on the code

There is also the possibility to [install](https://github.com/QuantStack/xeus-cling) xeus-cling via conda. But this installation use cling version 0.5 and does not support CUDA.

# Installation

To build and use the container, your host system needs two requirements:
- [Singularity](http://singularity.lbl.gov/) >= 2.6.0
- Nvidia CUDA Driver, which supports CUDA >= 8.0

## Release
coming soon

## Dev
The installation of the dev container is separated in three parts, because it allows modification of the source code of cling and xeus-cling by the user. The three parts are: 
- generating a configuration
- build container as root
- build applications as user

### Configuration
You can write the `config.json` by yourself or use the script `generate_config.sh` to generate one. The `config.json` have to be in same folder where you start the build process of the container.

Structure of the `config.json`
```json
{
    "XCC_PROJECT_PATH" : "/path/to/miniconda_xeus-cling_cling_installation",
    "XCC_BUILD_TYPE" : "CMAKE_BUILD_TYPE",
    "XCC_NUM_THREADS" : "Number or empty like make -j"
}
```

**Hint 1:** Cling needs a lot of RAM to build. Be careful at setting the number of threads. Otherwise, you get a out-of-memory error at link time. There are some experience about thread memory combinations to building cling. Working combinations are:
- 4 Threads with 32 GB RAM
- 14 Threads with 128 GB RAM

**Hint 2:** Be careful with hyperthreading. It can change the memory consumption dramatically.

### Build Container as Root

To build the container simply use the following command in the project folder.

``` bash
    sudo singularity build dev-xeus-cling-cuda.sing dev-xeus-cling-cuda
```

**Hint:** If you don not have root permission the your system, you can build the container on another system with root permission and copy it to your target system. Attention, the next step 'build applications as user' can not be running on another system. It have to be running on the target system.

### Build Applications as User

This step builds miniconda, cling and xeus-cling with your user permission in the path `$XCC_PROJECT_PATH`. To start the build process, simply use the following command.

``` bash
    singularity run dev-xeus-cling-cuda.sing
```

**Hint:** In dependency of the `XCC_BUILD_TYPE` the build can need a lot of memory. The `Debug` build needs about 82 GB.

# Running
To use the xeus-cling-cuda stack via jupyter notebook use the following command.

``` bash
    singularity exec --nv dev-xeus-cling-cuda.sing jupyter-notebook
```

**Hint 1:** If you get CUDA driver errors at runtime, maybe you forget to set the `--nv` flag.
**Hint 2:** If you use a SSH connection, don't forget the [prot forwarding](https://help.ubuntu.com/community/SSH/OpenSSH/PortForwarding) for port 8888.

# Development

If you change the code of xeus-cling or cling you have to build the applications again. There are two commands to run `make` and `make install` for cling or xeus-cling.

``` bash
    singularity run --app build_cling dev-xeus-cling-cuda.sing
```

``` bash
    singularity run --app build_xeus-cling dev-xeus-cling-cuda.sing
```
