moduleID="$1"
mmtsPOSITION="$2"

currentTEMPERATURE="$3"
currentHUMIDITY="$4"
switchDELAY="$5"
scannedIDlist="$6"

python3 turn_on_HV_switch.py --position="$mmtsPOSITION" --delay="$switchDELAY" --config=../data/mmts_configurations.yaml
cd ../external_packages/HGCal_Module_Production_Toolkit/
python3 scripts/getIV.py --module="$moduleID" --temperature="$currentTEMPERATURE" --humidity="$currentHUMIDITY"
python3 scripts/make_iv_curve2.py "$moduleID" ### make iv curve after scanning finished
python3 scripts/make_iv_curve2.py --summary `cat "$scannedIDlist"`
