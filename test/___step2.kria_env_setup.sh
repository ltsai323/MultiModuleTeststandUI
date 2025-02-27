#!/usr/bin/env sh
if [ "$BASH_SCRIPT_FOLDER" == "" ]; then echo "[EnvironmentFailure] Required variable BASH_SCRIPT_FOLDER not set. Load use_python_lib.sh"; exit; fi
source $BASH_SCRIPT_FOLDER/step0.functions.sh

if [ "$1" == "check" ]; then exec_at_kria 'systemctl status i2c-server.service && systemctl status daq-server.service'; fi
if [ "$1" == "reload" ]; then exec_at_kria 'systemctl restart i2c-server.service && systemctl restart daq-server.service'; fi

<<LISTED_OUTPUT_MESG
" SUC
● i2c-server.service - zmq_server.py start/stop service script
     Loaded: loaded (/usr/lib/systemd/system/i2c-server.service; disabled; preset: disabled)
     Active: active (running) since Tue 2025-02-25 18:41:14 CST; 46s ago
   Main PID: 1017 (python3)
      Tasks: 3 (limit: 18610)
     Memory: 14.2M
        CPU: 584ms
     CGroup: /system.slice/i2c-server.service
             └─1017 /usr/bin/python3 /opt/hexactrl/ROCv3/i2c/zmq_server.py

Feb 25 18:41:15 localhost.localdomain bash[1017]: [I2C] Found 0 address(es) on bus 7
Feb 25 18:41:15 localhost.localdomain bash[1017]: [I2C] Board identification: V3 HD Bottom HB
Feb 25 18:41:15 localhost.localdomain bash[1017]: ['s0_resetn', 's0_resyncload', 's0_i2c_rstn', 's0_pwr_en', 's1_resetn', 's1_resyncload', 's1_i2c_rstn', 's1_pwr_en', 's2_resetn', 's2_resyncload', 's2_i2c_rstn', 's2_pwr_en', 's0_power_pg', 's0_error_l', 's0_error_r', 's1_power_pg', 's1_error_l', 's1_error_r', 's2_power_pg', 's2_error_l', 's2_error_r', 'adc_rdy_pwr', 'adc_rdy_s0', 'adc_rdy_s1', 'adc_rdy_s2', 'QSPI_CLK', 'QSPI_DQ1', 'QSPI_DQ2', 'QSPI_DQ3', 'QSPI_DQ0', 'QSPI_CS_B', 'SPI_CLK', 'SOMLED1', 'SOMLED2', 'SPI_CS_B', 'SPI_MISO', 'SPI_MOSI', 'FWUEN', 'EMMC_DAT0', 'EMMC_DAT1', 'EMMC_DAT2', 'EMMC_DAT3', 'EMMC_DAT4', 'EMMC_DAT5', 'EMMC_DAT6', 'EMMC_DAT7', 'EMMC_CMD', 'EMMC_CLK', 'EMMC_RST', 'I2C1_SCL', 'I2C1_SDA', 'PMU0', '', '', '', '', 'PMU_PS_SHUTDOWN', '', '', 'PMU_SOM_PWR', '', 'UART1_TX', 'UART1_RX', 'ETH_MDIO_RST', 'SD1_DAT4', 'SD1_DAT5', 'SD1_DAT6', 'SD1_DAT7', '', '', '', 'SD1_DAT0', 'SD1_DAT1', 'SD1_DAT2', 'SD1_DAT3', 'SD1_CMD', 'SD1_CLK', 'PCB_1V2_EN', 'QSH_3V3_EN', 'FAN_CTRL', 'QSH_12V_EN', 'PMOD3V3_EN', 'QSH_1V2_EN', '', '', '', 'CLKCHIP_RST', 'I2C0_SCL', 'I2C0_SDA', 'GEM3_TXCLK', 'GEM3_TXD0', 'GEM3_TXD1', 'GEM3_TXD2', 'GEM3_TXD3', 'GEM3_TXCTL', 'GEM3_RXCLK', 'GEM3_RXD0', 'GEM3_RXD1', 'GEM3_RXD2', 'GEM3_RXD3', 'GEM3_RXCTL', 'GEM3_MDC', 'GEM3_MDIO', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''] False
Feb 25 18:41:15 localhost.localdomain bash[1017]: [GPIO] Identified gpio map :  {'roc_s0': ['s0_resetn', 's0_i2c_rstn'], 'roc_s1': ['s1_resetn', 's1_i2c_rstn'], 'roc_s2': ['s2_resetn', 's2_i2c_rstn']}
Feb 25 18:41:15 localhost.localdomain bash[1017]: {'roc_s0': ['s0_resetn', 's0_i2c_rstn'], 'roc_s1': ['s1_resetn', 's1_i2c_rstn'], 'roc_s2': ['s2_resetn', 's2_i2c_rstn']}
Feb 25 18:41:15 localhost.localdomain bash[1017]: [roc_s0_0] GPIO reset
Feb 25 18:41:15 localhost.localdomain bash[1017]: [roc_s0_1] GPIO reset
Feb 25 18:41:15 localhost.localdomain bash[1017]: [roc_s1_0] GPIO reset
Feb 25 18:41:15 localhost.localdomain bash[1017]: [roc_s1_1] GPIO reset
Feb 25 18:41:15 localhost.localdomain bash[1017]: Identify a board with HGCROC Siv3
● daq-server.service - daq-client start/stop service script
     Loaded: loaded (/usr/lib/systemd/system/daq-server.service; enabled; preset: disabled)
     Active: active (running) since Tue 2025-02-25 18:41:14 CST; 46s ago
   Main PID: 1018 (daq-server)
      Tasks: 4 (limit: 18610)
     Memory: 1.4M
        CPU: 4.813s
     CGroup: /system.slice/daq-server.service
             └─1018 /opt/hexactrl/ROCv3/bin/daq-server -f /opt/cms-hgcal-firmware/hgc-test-systems/active/uHAL_xml/connections.xml

Feb 25 18:41:14 localhost.localdomain systemd[1]: Started daq-client start/stop service script.
"
LISTED_OUTPUT_MESG
