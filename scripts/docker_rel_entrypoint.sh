#!/usr/bin/env bash

# this script is for the `docker run` command of the release container
# it adds some flags to jupyter notebook/lab, which are necessary that it works in docker

case "$1" in
    "jupyter-notebook") shift
			jupyter-notebook --allow-root --ip=0.0.0.0 $@;;
    "jupyter-lab") shift
		   jupyter-lab --allow-root --ip=0.0.0.0 $@;;
    "jupyter") shift
	       if [ "$1" == "notebook" ]; then
		   shift
		   jupyter notebook --allow-root --ip=0.0.0.0 $@
	       fi;;
    *) exec $@
       exit 1;;
esac
