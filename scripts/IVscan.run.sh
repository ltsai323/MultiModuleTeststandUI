moduleID="$1"
mmtsPOSITION="$2"

currentTEMPERATURE="$3"
currentHUMIDITY="$4"

echo python3 turn_on_HV_switch.py --position=$mmtsPOSITION --delay=0 --config=../data/mmts_configurations.yaml
python3 turn_on_HV_switch.py --position=$mmtsPOSITION --delay=0 --config=../data/mmts_configurations.yaml
cd ../external_packages/HGCal_Module_Production_Toolkit/
echo python3 scripts/getIV.py --module=$moduleID --temperature=$currentTEMPERATURE --humidity=$currentHUMIDITY
