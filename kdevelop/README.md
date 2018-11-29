# Kdevelop extension for dev-xeus-cling-cuda

This container extends the dev-xeus-cling-cuda.sing container with a kdevelop IDE. The extension is completely optional.

# About
Cling is a really huge project. For effective development a is IDE really useful. But a lot of IDEs has problems, to handle big project like cling, clang/llvm or the linux kernel. Kdevelop is really efficient and can handle this project size but it also needs some configuration.

Beside, often I develop on powerful workstation systems via ssh. So, using a IDE is not easy, because you have to handle the distribution of graphical output and source code and build environment.

As result of this two points, I develop this extension, to use my complete development stack including the IDE on a remote system. It's also a documentation of the configuration and easy possibility to change my development system.

# Installation

At first, you have to [build](../README.md) the `dev-xeus-cling-cuda.sing` container. Afterwards, run the following commands.
```bash
   #cd xeus-cling-cuda-container/kdevelop
   ./config_generator.sh
   sudo singularity build kdev-xeus-cling-cuda.sing kdev-xeus-cling-cuda
```
Now, the container with kdevelop is ready. Important, the container just works with the current user. If different users want to use kdevelop, they all have to build his own container. 

## Building the Container on another System

If you have no root permission on your development system, you can build the container on a another system. In this case, you can generate the `kdev_config.json` on you development system an copy it to the system, which you want to build the container. Alternative, you can write the `kdev_config.json` by yourself. The content is the follow:

``` json
{
        "XCC_USER_ID" : "<user id>"
}
```
To get the user, simply run `id -u` on your development system.

# Usage

For easy usage, there are two scripts in the folder: `run_shell.sh` and `run_kdevelop.sh`. The first script starts a interactive shell season of the container. The second script starts kdevelop direct. 
If you want to use custom commands, you have to use the parameter `-B /run/user/$(id -u):/run/user/$(id -u)` in your `singularity` command. This binding command allows to 'redirect' the graphical output of the container to the host. 

# Configuration of Kdevelop for the Cling Project

Before you load in the cling project in kdevelop go to `Settings->Configure KDevelop->LanguageSupport->Background Parser` and disable the Background Parser. Otherwise the parser will crash at parsing a test case file from clang. After this, import the cling source code via `Project->Open / Import Project`. Then click right on the project root in the project browser and choose `Open Configuration...`. Afterwards, choose `Project Filter` in the configuration window and add an new rule. Add to the `pattern` the path `tools/clang/test`. The other properties should be `Files and Folders` and `Exclude`. Now you can re-enable the Background Parser. Now, you will see a progress bar on the lower right corner. 

Parsing the whole code takes a lot of time. On my Intel 14 Core System, I need about 20 minutes. Sometimes, the parser just parse with one core. In this case, simple restart kdevelop. Unfortunately, the parsing process isn't interruptable, so you have to do the process in one session. The parsing process have to run one times. Afterwards, the index will be loaded from disk and auto completion is avail after few seconds.
