#!/usr/bin/env sh

THIS_SCRIPT="${BASH_SOURCE[0]}"

CURRENT_PATH=`dirname $( realpath $THIS_SCRIPT ) `

export PYTHONPATH=$PWD:$PYTHONPATH
export LOG_LEVEL=INFO ## DEBUG, INFO, WARNING, CRITICAL

export BASH_SCRIPT_FOLDER=$PWD/scripts/task2_pedestalrun/
export FLASK_BASE=$CURRENT_PATH


export LOG_LEVEL=INFO

######### loading libraries from Andrew's UI
#export AndrewModuleTestingGUI_BASE=/home/ntucms/workspace/hgcal-module-testing-gui
export AndrewModuleTestingGUI_BASE=$PWD/external_packages/hgcal-module-testing-gui
#if [ "$AndrewModuleTestingGUI_BASE" == "" ]; then echo "[InvalidPath] Need to modify variable 'AndrewModuleTestingGUI_BASE' in  $THIS_SCRIPT" && exit 1; fi
#if [ ! -d "$AndrewModuleTestingGUI_BASE" ]; then echo "[InvalidPath] variable 'AndrewModuleTestingGUI_BASE' should access correct path"; exit 2; fi

