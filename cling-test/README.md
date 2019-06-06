# Test environment extension for `make cling-test`

This container extends the dev-xeus-cling-cuda.sing container by Python 2.7 to run `make cling-test`. The extension is completely optional.

# About
Python 2.7 is installed in an extra container because it may cause some problems with the jupyter kernel.

# Installation

At first, you have to [build](../README.md) the `dev-xeus-cling-cuda.sing` container. Then run the following command.
```bash
   sudo singularity build clingTest-xeus-cling-cuda.sing clingTest-xeus-cling-cuda
```

Then you can run the new container with the script `./run_shell`.

# Usage

**Import:** The Python path of the cling-test tool is set at build time. Therefore, you must create a new cmake build with the `cmake` command. Alternatively, you can run again the `cmake` on a existing build. If the `cmake` prints the following line, everything is fine.

```bash
...
-- Found PythonInterp: /usr/bin/python2.7 (found version "2.7.12")
...
```
