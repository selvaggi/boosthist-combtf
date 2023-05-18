#!/bin/bash


#export PYTHONPATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ):$PYTHONPATH"
#echo $PYTHONPATH
#export PYTHONPATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/python:$PYTHONPATH"
#echo $PYTHONPATH


export PYTHONPATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/python:$PYTHONPATH"


echo $PYTHONPATH
