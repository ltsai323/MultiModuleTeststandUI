moduleID="$1"
mmtsPOSITION="$2"

maxVOLTAGE="$3"
currentTEMPERATURE="$4"
currentHUMIDITY="$5"
switchDELAY="$6"
scanMESG="$7"


set -x -o pipefail
python3 turn_on_HV_switch.py --position="$mmtsPOSITION" --delay="$switchDELAY" --config=../data/mmts_configurations.yaml
cd ../external_packages/HGCal_Module_Production_Toolkit/

python3 scripts/getIV.py \
	--module="$moduleID" \
	--temperature="$currentTEMPERATURE" \
	--humidity="$currentHUMIDITY" \
	--max_voltage="$maxVOLTAGE" \
	--station="MMTS_${mmtsPOSITION}" \
	--message="${scanMESG}"
#python3 scripts/make_iv_curve.py "$moduleID" ### make iv curve after scanning finished
#python3 scripts/make_iv_curve.py --summary `cat "$scannedIDlist"` ### disable the IV curve plot since I used grafana dashboard generating plot
cd -
### reset switch after IV curve scanning
python3 turn_on_HV_switch.py --position=0 --delay="$switchDELAY" --config=../data/mmts_configurations.yaml
