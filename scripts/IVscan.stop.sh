cd ../external_packages/HGCal_Module_Production_Toolkit/
python3 scripts/getIV.py --module=0 || exit 1
cd -
python3 turn_on_HV_switch.py --position=0 --delay=0 --config=../data/mmts_configurations.yaml || exit 2




### error codes
# 1: getIV.py reset failed
# 2: turn_on_HV_switch.py reset failed
