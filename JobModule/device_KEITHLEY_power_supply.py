import asyncio
import pyvisa
import sys
import os
import numpy as np
from datetime import datetime

# 假設這些是您的日誌模組
# 您可能需要根據實際情況調整這些導入
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from PythonTools.MyLogging_BashJob1 import log as rs232log
    from PythonTools.MyLogging_BashJob1 import log as bashlog
except ImportError:
    # 如果找不到日誌模組，創建簡單的替代
    class SimpleLogger:
        def debug(self, msg): print(f"[DEBUG] {msg}")
        def info(self, msg): print(f"[INFO] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
    rs232log = SimpleLogger()
    bashlog = SimpleLogger()

class RS232Dev:
    """RS232 設備類，用於管理與儀器的連接"""
    def __init__(self, tag):
        self.rm = pyvisa.ResourceManager()
        self.tag = tag
        self.task = None

    def __del__(self):
        if hasattr(self, 'rm'):
            self.rm.close()

    def SetTask(self, t):
        self.task = t

    async def Await(self):
        """等待任務完成"""
        if not hasattr(self, 'task') or self.task is None:
            return  # 沒有需要等待的任務
        if not self.task.done():
            bashlog.debug(f'[{self.tag} - Await] 等待測量任務完成')
            await self.task


async def set_status(instr, commands):
    """向儀器發送命令"""
    try:
        # 處理單個命令或命令列表
        cmds = [commands] if isinstance(commands, str) else commands
        for cmd in cmds:
            instr.write(cmd)
            await asyncio.sleep(0.1)  # 命令之間的短暫等待
        
        await asyncio.sleep(0.5)  # 完成所有命令後等待
        return True
    except pyvisa.VisaIOError as e:
        bashlog.error(f"VISA 錯誤: {e}")
        return False
    except Exception as e:
        bashlog.error(f"錯誤: {e}")
        return False


async def query_value(instr, command):
    """向儀器發送查詢命令並讀取回應"""
    try:
        instr.write(command)
        response = instr.read().strip()
        return response
    except pyvisa.VisaIOError as e:
        bashlog.error(f"VISA 查詢錯誤: {e}")
        return None
    except Exception as e:
        bashlog.error(f"查詢錯誤: {e}")
        return None


async def IV_Monitor(instr, stop_event=None):
    """監控電流和電壓的背景任務"""
    try:
        while True:
            if stop_event and stop_event.is_set():
                bashlog.info("[IVMonitor] 接收到停止信號")
                break

            # 讀取電流
            current = await query_value(instr, "READ?")
            if current:
                # Keithley 通常返回 電流,電壓,電阻 的三元組
                values = current.split(',')
                if len(values) >= 2:
                    meas_I = values[0]
                    meas_V = values[1]
                    bashlog.info(f'[測量IV] V({meas_V}) 和 I({meas_I})')
                else:
                    bashlog.error(f"解析測量值失敗: {current}")

            await asyncio.sleep(2)  # 每 2 秒更新一次
    except asyncio.CancelledError:
        bashlog.info("[IVMonitor] 任務被取消")
    except Exception as e:
        bashlog.error(f"監控時發生錯誤: {e}")


async def SetupKeithley2410(tag, resource, setup_type='volt_source'):
    """設置 Keithley 2410 的初始配置"""
    commands = {
        'volt_source': [
            '*RST',                      # 重置到出廠設置
            ':SOUR:FUNC VOLT',           # 設置為電壓源模式
            ':SOUR:VOLT:MODE FIXED',     # 固定電壓模式
            ':SOUR:VOLT:RANG 20',        # 設置電壓範圍為 20V
            ':SOUR:VOLT:LEV 0',          # 初始電壓設為 0V
            ':SENS:FUNC "CURR"',         # 測量電流
            ':SENS:CURR:PROT 0.1',       # 電流保護限制為 100mA
            ':SENS:CURR:RANG:AUTO ON',   # 自動電流量程
            ':OUTP OFF'                  # 初始輸出關閉
        ],
        'curr_source': [
            '*RST',
            ':SOUR:FUNC CURR',           # 設置為電流源模式
            ':SOUR:CURR:MODE FIXED',     # 固定電流模式
            ':SOUR:CURR:RANG 100E-3',    # 設置電流範圍為 100mA
            ':SOUR:CURR:LEV 0',          # 初始電流設為 0A
            ':SENS:FUNC "VOLT"',         # 測量電壓
            ':SENS:VOLT:PROT 20',        # 電壓保護限制為 20V
            ':SENS:VOLT:RANG:AUTO ON',   # 自動電壓量程
            ':OUTP OFF'                  # 初始輸出關閉
        ],
        'meter_only': [
            '*RST',
            ':SOUR:FUNC VOLT',
            ':SOUR:VOLT:LEV 0',
            ':SENS:FUNC "CURR","VOLT"',  # 同時測量電流和電壓
            ':SENS:CURR:PROT 0.1',
            ':SENS:CURR:RANG:AUTO ON',
            ':SENS:VOLT:RANG:AUTO ON',
            ':OUTP OFF'
        ]
    }

    try:
        cmd_list = commands[setup_type]
    except KeyError as e:
        available_keys = ', '.join(commands.keys())
        error_msg = f'[無效設置類型] 輸入的設置類型 "{setup_type}" 無效。可用選項: {available_keys}'
        raise KeyError(error_msg) from e

    rs232 = RS232Dev(tag)
    try:
        # 建立連接
        bashlog.info(f"正在連接到 {resource} 資源...")
        instr = rs232.rm.open_resource(resource)
        
        # 設置通訊參數
        instr.baud_rate = 9600
        instr.timeout = 5000  # 5 秒超時
        instr.read_termination = '\n'
        instr.write_termination = '\n'
        
        # 發送設置命令
        bashlog.info(f"正在設置 Keithley 為 {setup_type} 模式...")
        result = await set_status(instr, cmd_list)
        
        if result:
            bashlog.info(f"儀器設置完成: {setup_type}")
            # 保存儀器資源到設備
            rs232.instrument = instr
            return rs232
        else:
            bashlog.error("設置儀器時出錯")
            return None
    except Exception as e:
        bashlog.error(f"連接或設置時出錯: {e}")
        return None


async def SetVoltage(rs232_dev, voltage_value):
    """設置輸出電壓值"""
    if not hasattr(rs232_dev, 'instrument'):
        bashlog.error("無有效的儀器連接")
        return False
    
    instr = rs232_dev.instrument
    try:
        # 設置電壓值
        cmd = f':SOUR:VOLT:LEV {voltage_value}'
        await set_status(instr, cmd)
        bashlog.info(f"電壓設置為 {voltage_value}V")
        return True
    except Exception as e:
        bashlog.error(f"設置電壓時出錯: {e}")
        return False


async def EnableOutput(rs232_dev, enable=True):
    """打開或關閉輸出"""
    if not hasattr(rs232_dev, 'instrument'):
        bashlog.error("無有效的儀器連接")
        return False
    
    instr = rs232_dev.instrument
    try:
        cmd = ':OUTP ON' if enable else ':OUTP OFF'
        await set_status(instr, cmd)
        status = "開啟" if enable else "關閉"
        bashlog.info(f"輸出已{status}")
        return True
    except Exception as e:
        bashlog.error(f"切換輸出時出錯: {e}")
        return False


async def ReadIV(rs232_dev):
    """讀取當前的電壓和電流值"""
    if not hasattr(rs232_dev, 'instrument'):
        bashlog.error("無有效的儀器連接")
        return None, None
    
    instr = rs232_dev.instrument
    try:
        response = await query_value(instr, "READ?")
        if response:
            values = response.split(',')
            if len(values) >= 2:
                # Keithley 2410 通常返回 電流,電壓,電阻,...
                current = float(values[0])
                voltage = float(values[1])
                return voltage, current
        
        bashlog.error("讀取 IV 失敗或返回無效數據")
        return None, None
    except Exception as e:
        bashlog.error(f"讀取 IV 時出錯: {e}")
        return None, None


async def StartIVMonitor(rs232_dev, stop_event=None):
    """啟動背景 IV 監控任務"""
    if not hasattr(rs232_dev, 'instrument'):
        bashlog.error("無有效的儀器連接")
        return False
    
    instr = rs232_dev.instrument
    try:
        # 創建並啟動監控任務
        bashlog.info("啟動 IV 監控...")
        task = asyncio.create_task(IV_Monitor(instr, stop_event))
        rs232_dev.SetTask(task)
        return True
    except Exception as e:
        bashlog.error(f"啟動 IV 監控時出錯: {e}")
        return False


async def StopIVMonitor(rs232_dev, stop_event):
    """停止 IV 監控任務"""
    if stop_event:
        stop_event.set()
    
    if hasattr(rs232_dev, 'task') and rs232_dev.task:
        try:
            # 給任務一點時間響應停止事件
            await asyncio.sleep(0.5)
            if not rs232_dev.task.done():
                rs232_dev.task.cancel()
                bashlog.info("IV 監控任務已取消")
        except Exception as e:
            bashlog.error(f"停止 IV 監控時出錯: {e}")


async def PerformIVSweep(rs232_dev, start_v, stop_v, step_v, delay=0.5):
    """執行 IV 掃描，在指定電壓範圍內測量電流"""
    if not hasattr(rs232_dev, 'instrument'):
        bashlog.error("無有效的儀器連接")
        return None
    
    instr = rs232_dev.instrument
    results = []
    
    try:
        # 設置為掃描模式
        setup_cmds = [
            '*RST',
            ':SOUR:FUNC VOLT',           # 電壓源
            ':SOUR:VOLT:MODE FIXED',     # 固定模式 (會用手動步進)
            ':SENS:FUNC "CURR"',         # 測量電流
            ':SENS:CURR:PROT 0.1',       # 電流保護 100mA
            ':SENS:CURR:RANG:AUTO ON',   # 自動範圍
            ':FORM:ELEM CURR,VOLT',      # 返回電流和電壓數據
        ]
        
        await set_status(instr, setup_cmds)
        
        # 打開輸出
        await set_status(instr, ':OUTP ON')
        bashlog.info(f"開始 IV 掃描: {start_v}V 到 {stop_v}V, 步長 {step_v}V")
        
        # 計算掃描點
        num_points = int(abs(stop_v - start_v) / step_v) + 1
        voltage_points = [start_v + step_v * i for i in range(num_points)]
        
        # 執行掃描
        for voltage in voltage_points:
            # 設置電壓
            await set_status(instr, f':SOUR:VOLT:LEV {voltage}')
            # 等待穩定
            await asyncio.sleep(delay)
            
            # 讀取測量值
            response = await query_value(instr, "READ?")
            if response:
                values = response.split(',')
                if len(values) >= 2:
                    current = float(values[0])
                    measured_v = float(values[1])
                    bashlog.info(f'IV點: 設置 {voltage}V, 測量 {measured_v}V, {current}A')
                    results.append((measured_v, current))
                else:
                    bashlog.error(f"解析測量值失敗: {response}")
        
        # 關閉輸出
        await set_status(instr, ':OUTP OFF')
        bashlog.info("IV 掃描完成")
        
        # 如果需要，可以保存結果到檔案
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"iv_sweep_{timestamp}.csv"
        with open(filename, 'w') as f:
            f.write("Voltage(V),Current(A)\n")
            for v, i in results:
                f.write(f"{v},{i}\n")
        bashlog.info(f"結果已保存到 {filename}")
        
        return results
    
    except Exception as e:
        bashlog.error(f"IV 掃描時出錯: {e}")
        # 確保輸出關閉
        try:
            await set_status(instr, ':OUTP OFF')
        except:
            pass
        return None


def InitChecking(dev):
    """檢查設備是否可用"""
    failed_reason = ''
    rm = None
    try:
        rm = pyvisa.ResourceManager()
        instr = rm.open_resource(dev)
        # 簡單的識別查詢來確認設備可用
        idn = instr.query('*IDN?')
        if not idn or "KEITHLEY" not in idn.upper():
            failed_reason = f'設備 "{dev}" 不是 Keithley 儀器或無法識別'
    except Exception as e:
        failed_reason = f'檢查設備時出錯: {e}'
    finally:
        if rm:
            rm.close()
        return failed_reason


# 主程序示例
if __name__ == "__main__":
    # 使用適當的設備地址，例如 GPIB 或 RS232
    DEVICE_ADDRESS = "GPIB0::24::INSTR"  # 示例 GPIB 地址，根據實際情況修改
    # 對於 RS232，可能類似：
    # DEVICE_ADDRESS = "ASRL/dev/ttyUSB0::INSTR"
    
    async def main():
        # 檢查設備
        error = InitChecking(DEVICE_ADDRESS)
        if error:
            print(f"初始化檢查失敗: {error}")
            return
        
        print("[INFO] 設備檢查通過")
        
        # 設置為電壓源模式
        rs232_dev = await SetupKeithley2410('keithley', DEVICE_ADDRESS, 'volt_source')
        if not rs232_dev:
            print("設置儀器失敗")
            return
        
        # 設置電壓為 1V 並啟用輸出
        await SetVoltage(rs232_dev, 1.0)
        await EnableOutput(rs232_dev, True)
        
        # 讀取 IV 值
        voltage, current = await ReadIV(rs232_dev)
        if voltage is not None and current is not None:
            print(f"測量結果: {voltage}V, {current}A")
        
        # 關閉輸出
        await EnableOutput(rs232_dev, False)
        
        # 執行 IV 掃描 (0V 到 5V, 步長 0.5V)
        results = await PerformIVSweep(rs232_dev, 0, 5, 0.5)
        
        # 使用停止事件來控制監控任務
        stop_event = asyncio.Event()
        
        # 啟動 IV 監控 (在實際應用中這可能會運行更長時間)
        await StartIVMonitor(rs232_dev, stop_event)
        
        # 運行一段時間後停止
        await asyncio.sleep(10)
        await StopIVMonitor(rs232_dev, stop_event)
        
        print("[INFO] 測試完成!")
    
    # 運行主程序
    asyncio.run(main())
