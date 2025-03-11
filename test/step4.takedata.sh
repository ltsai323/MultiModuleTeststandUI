#!/usr/bin/env sh

jobTAG=$1
kriaIP=$2
moduleID=$3

if [ "$moduleID" == "" ]; then echo "[$jobTAG - JobDisabled] Empty module ID received"; exit; fi
if [ "$BASH_SCRIPT_FOLDER" == "" ]; then echo "[$jobTAG - EnvironmentFailure] Required variable BASH_SCRIPT_FOLDER not set. Load use_python_lib.sh"; exit; fi
source $BASH_SCRIPT_FOLDER/step0.functions.sh


moduleTYPE=`python3 $BASH_SCRIPT_FOLDER/decode_serialnumber_to_module_type.py $moduleID`
echo "[$jobTAG - RecognizedModuleType] the type is '$moduleTYPE'"

############### Need to be implemented ###############
#if [ "$moduleTYPE" == "Bare Hexaboard HD Full" ]; then
#  yamlfile=initHD-bottom.yaml
#  initpath=/home/ntucms/electronic_test_kria/HD_bottom
#fi
if [ "$moduleTYPE" == "Hexaboard HD Bottom" ]; then
  yamlfile=initHD-bottom.yaml
  initpath=/home/ntucms/electronic_test_kria/HD_bottom
fi





if [ "$yamlfile" == "" ]; then echo "[$jobTAG - InvalidModuleType] input module ID '$moduleID' generates module type '$moduleTYPE'. No related yaml file in data taking"; exit; fi
if [ "$initpath" == "" ]; then echo "[$jobTAG - InvalidModuleType] input module ID '$moduleID' generates module type '$moduleTYPE'. No related folder in data taking"; exit; fi


echo "[$jobTAG - Running ] taking data using yamlfile $yamlfile at $initpath"
#exec_at_ctrlpc "cd /home/ntucms/electronic_test_kria/HD_bottom && python3 pedestal_run.py -i $kriaIP -f initHD-bottom.yaml -d $moduleID -I && echo FINISHED"
exec_at_ctrlpc "cd $initpath && python3 pedestal_run.py -i $kriaIP -f $yamlfile -d $moduleID -I && echo FINISHED"
echo "[$jobTAG - Finished] taking data ENDED"

### errors
<<LISTED_OUTPUT_MESG
" ERROR - if nothing found in 20 second <- timeout TBD
"
LISTED_OUTPUT_MESG
