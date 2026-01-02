if [ ! -f 'data/mmts_configurations.yaml' ]; then 
  cp data/mmts_configurations.yaml.template data/mmts_configurations.yaml
  vi data/mmts_configurations.yaml
fi

if [ -d "external_packages/hgcal-module-testing-gui/" ]; then
  echo "[ExistedPackage] Andrew's package (DAQ) found";
else
  echo "[Install Andrew's package (DAQ)] initialize 'hgcal-module-testing-gui' from Andrew "
  git clone https://gitlab.cern.ch/acrobert/hgcal-module-testing-gui.git external_packages/hgcal-module-testing-gui
  cd external_packages/hgcal-module-testing-gui
  python3 writeconfig.py
  vi -O configuration.yaml ../hgcal-module-testing-gui-configuration.yaml
  cd -
fi


if [ -d "external_packages/HGCal_Module_Production_Toolkit" ]; then
  echo "[ExistedPackage] youying's package (IV scan) found"
else
  echo "[Install youying's package (IV scan)] initialize 'HGCal_Module_Production_Toolkit' from youying "
  git clone https://github.com/ltsai323/HGCal_Module_Production_Toolkit.git external_packages/HGCal_Module_Production_Toolkit
  ln -s $PWD/data/mmts_configurations.yaml external_packages/HGCal_Module_Production_Toolkit/configurations.yaml
  mkdir external_packages/HGCal_Module_Production_Toolkit/out
fi
