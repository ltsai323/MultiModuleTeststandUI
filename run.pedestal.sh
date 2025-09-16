moduleID="'$1'"
runTAG="'$2'"
mmtsPOSITION="'$3'"
moduleSTATUS="'$4'"
daqINSPECTOR="'$5'"

cd hgcal-module-testing-gui/
python3 InteractionGUI.directrun.py '../mmts_configurations.yaml' $moduleID $runTAG $mmtsPOSITION $moduleSTATUS $daqINSPECTOR || exit 0 ## return 0 prevent make command failed
#python3 InteractionGUI.directrun.py '../mmts_configurations.yaml' '320-XH-T4C-PM-00019' 'run1' '1L' 'Untaped' 'test-user' || exit 0
cd ..
