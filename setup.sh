
if [ -d "external_packages/hgcal-module-testing-gui/" ]; then
  echo "[ExistedPackage] Andrew's package (DAQ) found";
else
  echo "[Install Andrew's package (DAQ)] initialize 'hgcal-module-testing-gui' from Andrew "
  echo git clone https://gitlab.cern.ch/acrobert/hgcal-module-testing-gui.git external_packages/hgcal-module-testing-gui
  echo cd external_packages/hgcal-module-testing-gui
  echo python3 writeconfig.py
  echo vi -O configuration.yaml ../hgcal-module-testing-gui-configuration.yaml
fi


if [ -d "external_packages/HGCal_Module_Production_Toolkit" ]; then
  echo "[ExistedPackage] youying's package (IV scan) found"
else
  echo "[Install youying's package (IV scan)] initialize 'HGCal_Module_Production_Toolkit' from youying "
  git clone https://github.com/youyingli/HGCal_Module_Production_Toolkit.git external_packages/HGCal_Module_Production_Toolkit
fi
