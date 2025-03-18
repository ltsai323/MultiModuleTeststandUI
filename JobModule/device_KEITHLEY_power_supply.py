import asyncio
import pyvisa
import sys
import os
import numpy as np
from datetime import datetime
import asyncio.exceptions

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
        self.instrument = None

    def __del__(self):
        """清理資源"""
        if hasattr(self, 'instrument') and self.instrument is not None:
            self.instrument.close()
        if hasattr(self, 'rm') and self.rm is not None:
            self.rm.close()

    def set_task(self, t):
        """設置異步任務"""
        self.task = t

    async def await_task(self):
        """等待任務完成"""
        if not hasattr(self, 'task') or self.task is None:
            return  # 沒有需要等待的任務
            
        if not self.task.done():
            bashlog.debug(f'[{self.tag} - Await] 等待測量任務完成')
            await self.task


class KeithleyCommands:
    """Keithley 命令類，包含常用的 SCPI 命令常數"""
    # 重置和狀態命令
    RESET = "*RST"
    CLEAR = "*CLS"
    IDN = "*IDN?"
    OPC = "*OPC?"
    
    # 錯誤查詢
    ERROR = ":SYSTem:ERRor?"
    
    # 源控制命令
    SOURCE_VOLTAGE = ":SOURce:FUNCtion:MODE VOLTage"
    SOURCE_CURRENT = ":SOURce:FUNCtion:MODE CURRent"
    
    # 量測命令
    MEASURE_VOLTAGE = ":SENSe:FUNCtion 'VOLTage:DC'"
    MEASURE_CURRENT = ":SENSe:FUNCtion 'CURRent:DC'"
    MEASURE_RESISTANCE = ":SENSe:FUNCtion 'RESistance'"
    MEASURE_CONCURRENT_ON = ":SENSe:FUNCtion:CONCurrent ON"
    MEASURE_CONCURRENT_OFF = ":SENSe:FUNCtion:CONCurrent OFF"
    
    # 掃描命令
    SWEEP_LINEAR = ":SOURce:SWEep:SPACing LINear"
    SWEEP_LOG = ":SOURce:SWEep:SPACing LOGarithmic"
    
    # 輸出控制
    OUTPUT_ON = ":OUTPut:STATe ON"
    OUTPUT_OFF = ":OUTPut:STATe OFF"
    
    # 觸發命令
    TRIGGER_IMMEDIATE = ":INITiate"
    TRIGGER_ABORT = ":ABORt"
    
    # 數據讀取命令
    READ = ":READ?"
    FETCH = ":FETCh?"
    MEASURE = ":MEASure?"


class KeithleyInstrument:
    """Keithley 儀器控制類"""
    def __init__(self, device_tag, resource_name):
        """初始化 Keithley 儀器
        
        Args:
            device_tag: 設備標籤，用於日誌
            resource_name: VISA 資源名稱，例如 "GPIB0::24::INSTR"
        """
        self.device_tag = device_tag
        self.resource_name = resource_name
        self.rs232_dev = None
        self.instrument = None

    async def connect(self):
        """連接到儀器並進行基本設置"""
        try:
            self.rs232_dev = RS232Dev(self.device_tag)
            instr = self.rs232_dev.rm.open_resource(self.resource_name)
            
            # 設置通訊參數
            if self.resource_name.startswith("ASRL"):
                instr.baud_rate = 9600
                instr.data_bits = 8
                instr.stop_bits = pyvisa.constants.StopBits.one
                instr.parity = pyvisa.constants.Parity.none
                instr.flow_control = pyvisa.constants.VI_ASRL_FLOW_NONE
                instr.read_termination = '\r'
                instr.write_termination = '\r'
            
            instr.timeout = 10000  # 10 秒超時，對於掃描操作可能需要
            
            # 儲存儀器實例
            self.rs232_dev.instrument = instr
            self.instrument = instr
            
            # 清除錯誤佇列並設置儀器
            await self.send_command(KeithleyCommands.CLEAR)
            
            # 驗證連接
            idn = await self.query_command(KeithleyCommands.IDN)
            if idn:
                bashlog.info(f"已連接到儀器: {idn}")
                return True
            else:
                bashlog.error("無法獲取儀器識別信息")
                return False
                
        except Exception as e:
            bashlog.error(f"連接到 {self.resource_name} 時出錯: {e}")
            return False
    
    async def disconnect(self):
        """斷開與儀器的連接"""
        try:
            if self.instrument:
                # 確保輸出關閉
                await self.output_off()
                
                # 關閉連接
                self.instrument.close()
                self.instrument = None
                
            if self.rs232_dev:
                if hasattr(self.rs232_dev, 'rm'):
                    self.rs232_dev.rm.close()
                self.rs232_dev = None
                
            bashlog.info(f"已斷開與 {self.resource_name} 的連接")
            return True
        except Exception as e:
            bashlog.error(f"斷開連接時出錯: {e}")
            return False
    
    async def send_command(self, command):
        """向儀器發送命令
        
        Args:
            command: SCPI 命令字符串或命令列表
            
        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        if not self.instrument:
            bashlog.error("儀器未連接")
            return False
            
        try:
            commands = command if isinstance(command, list) else [command]
            for cmd in commands:
                self.instrument.write(cmd)
                await asyncio.sleep(0.05)  # 添加小延遲以確保命令處理
            return True
        except Exception as e:
            bashlog.error(f"發送命令時出錯: {e}")
            return False
    
    async def query_command(self, command):
        """向儀器發送查詢命令並獲取回應
        
        Args:
            command: SCPI 查詢命令
            
        Returns:
            str: 命令的回應，失敗時返回 None
        """
        if not self.instrument:
            bashlog.error("儀器未連接")
            return None
            
        try:
            result = self.instrument.query(command)
            return result.strip() if result else None
        except Exception as e:
            bashlog.error(f"查詢命令時出錯: {e}")
            return None
    
    async def check_errors(self):
        """檢查儀器錯誤佇列並記錄所有錯誤
        
        Returns:
            list: 錯誤訊息列表，沒有錯誤時為空列表
        """
        errors = []
        if not self.instrument:
            return errors
            
        try:
            while True:
                error = await self.query_command(KeithleyCommands.ERROR)
                if not error or "0,\"No error\"" in error:
                    break
                errors.append(error)
                bashlog.error(f"儀器錯誤: {error}")
                
            return errors
        except Exception as e:
            bashlog.error(f"檢查錯誤時出錯: {e}")
            return [f"檢查錯誤時出錯: {e}"]
    
    async def reset(self):
        """重置儀器到默認狀態並清除錯誤佇列"""
        result = await self.send_command([KeithleyCommands.RESET, KeithleyCommands.CLEAR])
        await self.check_errors()
        return result
    
    async def setup_as_voltage_source(self, voltage_range=20, voltage_level=0, current_compliance=0.1):
        """將儀器設置為電壓源模式
        
        Args:
            voltage_range: 電壓範圍，單位為伏特
            voltage_level: 初始電壓值，單位為伏特
            current_compliance: 電流限制，單位為安培
            
        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        cmds = [
            KeithleyCommands.RESET,
            KeithleyCommands.SOURCE_VOLTAGE,
            f":SOURce:VOLTage:RANGe {voltage_range}",
            f":SOURce:VOLTage:LEVel {voltage_level}",
            KeithleyCommands.MEASURE_CURRENT,
            f":SENSe:CURRent:PROTection {current_compliance}",
            ":SENSe:CURRent:RANGe:AUTO ON",
            # 設置積分時間 (NPLC - 電源線週期數)
            ":SENSe:CURRent:NPLCycles 1.0",
            # 設置數據格式
            ":FORMat:ELEMents VOLTage,CURRent,RESistance,TIME,STATus"
        ]
        
        result = await self.send_command(cmds)
        await self.check_errors()
        
        if result:
            bashlog.info(f"已設置為電壓源模式，範圍 {voltage_range}V，初始值 {voltage_level}V，電流限制 {current_compliance}A")
        
        return result
    
    async def setup_as_current_source(self, current_range=0.1, current_level=0, voltage_compliance=20):
        """將儀器設置為電流源模式
        
        Args:
            current_range: 電流範圍，單位為安培
            current_level: 初始電流值，單位為安培
            voltage_compliance: 電壓限制，單位為伏特
            
        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        cmds = [
            KeithleyCommands.RESET,
            KeithleyCommands.SOURCE_CURRENT,
            f":SOURce:CURRent:RANGe {current_range}",
            f":SOURce:CURRent:LEVel {current_level}",
            KeithleyCommands.MEASURE_VOLTAGE,
            f":SENSe:VOLTage:PROTection {voltage_compliance}",
            ":SENSe:VOLTage:RANGe:AUTO ON",
            # 設置積分時間
            ":SENSe:VOLTage:NPLCycles 1.0",
            # 設置數據格式
            ":FORMat:ELEMents VOLTage,CURRent,RESistance,TIME,STATus"
        ]
        
        result = await self.send_command(cmds)
        await self.check_errors()
        
        if result:
            bashlog.info(f"已設置為電流源模式，範圍 {current_range}A，初始值 {current_level}A，電壓限制 {voltage_compliance}V")
        
        return result
    
    async def setup_measurement_speed(self, nplc=1.0):
        """設置測量速度/積分時間
        
        Args:
            nplc: 電源線週期數 (0.01 到 10)，較小的值測量速度較快但噪聲較大
            
        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        cmds = [
            f":SENSe:CURRent:NPLCycles {nplc}",
            f":SENSe:VOLTage:NPLCycles {nplc}",
            f":SENSe:RESistance:NPLCycles {nplc}"
        ]
        
        result = await self.send_command(cmds)
        await self.check_errors()
        
        if result:
            bashlog.info(f"測量速度已設置為 {nplc} NPLC")
        
        return result
    
    async def setup_measurement_filter(self, enable=True, count=10, type="REPeat"):
        """設置測量濾波器
        
        Args:
            enable: 是否啟用濾波器
            count: 濾波器計數 (1 到 100)
            type: 濾波器類型，"REPeat" 或 "MOVing"
            
        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        state = "ON" if enable else "OFF"
        cmds = [
            f":SENSe:AVERage:TCONtrol {type}",
            f":SENSe:AVERage:COUNt {count}",
            f":SENSe:AVERage:STATe {state}"
        ]
        
        result = await self.send_command(cmds)
        await self.check_errors()
        
        if result:
            status = "啟用" if enable else "停用"
            bashlog.info(f"測量濾波器已{status}，計數 {count}，類型 {type}")
        
        return result
    
    async def set_voltage(self, voltage_level):
        """設置輸出電壓
        
        Args:
            voltage_level: 電壓值，單位為伏特
            
        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        result = await self.send_command(f":SOURce:VOLTage:LEVel {voltage_level}")
        
        if result:
            bashlog.info(f"電壓已設置為 {voltage_level} V")
        
        return result
    
    async def set_current(self, current_level):
        """設置輸出電流
        
        Args:
            current_level: 電流值，單位為安培
            
        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        result = await self.send_command(f":SOURce:CURRent:LEVel {current_level}")
        
        if result:
            bashlog.info(f"電流已設置為 {current_level} A")
        
        return result
    
    async def output_on(self):
        """打開輸出"""
        result = await self.send_command(KeithleyCommands.OUTPUT_ON)
        
        if result:
            bashlog.info("輸出已開啟")
        
        return result
    
    async def output_off(self):
        """關閉輸出"""
        result = await self.send_command(KeithleyCommands.OUTPUT_OFF)
        
        if result:
            bashlog.info("輸出已關閉")
        
        return result
    
    async def read_measurements(self):
        """讀取當前測量值
        
        Returns:
            dict: 測量結果字典，包含電壓、電流等
        """
        try:
            response = await self.query_command(KeithleyCommands.READ)
            if not response:
                bashlog.error("讀取測量失敗，無回應")
                return None
                
            values = response.split(',')
            if len(values) >= 5:  # 電壓、電流、電阻、時間、狀態
                result = {
                    'voltage': float(values[0]),
                    'current': float(values[1]),
                    'resistance': float(values[2]),
                    'timestamp': float(values[3]),
                    'status': int(float(values[4]))
                }
                return result
            else:
                bashlog.error(f"讀取測量失敗，數據格式不正確: {response}")
                return None
        except Exception as e:
            bashlog.error(f"讀取測量時出錯: {e}")
            return None
    
    async def read_iv(self):
        """讀取當前的電壓和電流
        
        Returns:
            tuple: (電壓, 電流)，失敗時返回 (None, None)
        """
        measurements = await self.read_measurements()
        
        if measurements:
            return measurements['voltage'], measurements['current']
        
        return None, None
    
    async def setup_voltage_sweep_linear(self, start_v, stop_v, step_v=None, points=None):
        """設置線性電壓掃描
        
        必須指定 step_v 或 points 之一
        
        Args:
            start_v: 起始電壓
            stop_v: 終止電壓
            step_v: 電壓步長
            points: 掃描點數
            
        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        if step_v is None and points is None:
            bashlog.error("必須指定電壓步長或掃描點數")
            return False
            
        if step_v is not None and points is not None:
            bashlog.error("不能同時指定電壓步長和掃描點數")
            return False
        
        try:
            cmds = [
                KeithleyCommands.SOURCE_VOLTAGE,
                ":SOURce:VOLTage:MODE SWEep",
                KeithleyCommands.SWEEP_LINEAR,  # 線性掃描
                f":SOURce:VOLTage:STARt {start_v}",
                f":SOURce:VOLTage:STOP {stop_v}",
            ]
            
            if step_v is not None:
                cmds.append(f":SOURce:VOLTage:STEP {step_v}")
            else:  # points is not None
                cmds.append(f":SOURce:SWEep:POINts {points}")
            
            # 設置掃描源範圍模式
            cmds.append(":SOURce:SWEep:RANGing BEST")  # 使用最佳固定範圍
            
            result = await self.send_command(cmds)
            await self.check_errors()
            
            if result:
                if step_v is not None:
                    bashlog.info(f"已設置線性電壓掃描: {start_v}V 到 {stop_v}V，步長 {step_v}V")
                else:
                    bashlog.info(f"已設置線性電壓掃描: {start_v}V 到 {stop_v}V，{points} 個點")
            
            return result
        except Exception as e:
            bashlog.error(f"設置電壓掃描時出錯: {e}")
            return False
    
    async def setup_voltage_sweep_log(self, start_v, stop_v, points):
        """設置對數電壓掃描
        
        Args:
            start_v: 起始電壓 (必須非零且與 stop_v 同號)
            stop_v: 終止電壓
            points: 掃描點數
            
        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        if start_v * stop_v <= 0:
            bashlog.error("對數掃描的起始和終止電壓必須非零且同號")
            return False
        
        try:
            cmds = [
                KeithleyCommands.SOURCE_VOLTAGE,
                ":SOURce:VOLTage:MODE SWEep",
                KeithleyCommands.SWEEP_LOG,  # 對數掃描
                f":SOURce:VOLTage:STARt {start_v}",
                f":SOURce:VOLTage:STOP {stop_v}",
                f":SOURce:SWEep:POINts {points}",
                ":SOURce:SWEep:RANGing BEST"  # 使用最佳固定範圍
            ]
            
            result = await self.send_command(cmds)
            await self.check_errors()
            
            if result:
                bashlog.info(f"已設置對數電壓掃描: {start_v}V 到 {stop_v}V，{points} 個點")
            
            return result
        except Exception as e:
            bashlog.error(f"設置對數電壓掃描時出錯: {e}")
            return False
    
    async def setup_current_sweep_linear(self, start_i, stop_i, step_i=None, points=None):
        """設置線性電流掃描
        
        必須指定 step_i 或 points 之一
        
        Args:
            start_i: 起始電流
            stop_i: 終止電流
            step_i: 電流步長
            points: 掃描點數
            
        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        if step_i is None and points is None:
            bashlog.error("必須指定電流步長或掃描點數")
            return False
            
        if step_i is not None and points is not None:
            bashlog.error("不能同時指定電流步長和掃描點數")
            return False
        
        try:
            cmds = [
                KeithleyCommands.SOURCE_CURRENT,
                ":SOURce:CURRent:MODE SWEep",
                KeithleyCommands.SWEEP_LINEAR,  # 線性掃描
                f":SOURce:CURRent:STARt {start_i}",
                f":SOURce:CURRent:STOP {stop_i}",
            ]
            
            if step_i is not None:
                cmds.append(f":SOURce:CURRent:STEP {step_i}")
            else:  # points is not None
                cmds.append(f":SOURce:SWEep:POINts {points}")
            
            # 設置掃描源範圍模式
            cmds.append(":SOURce:SWEep:RANGing BEST")  # 使用最佳固定範圍
            
            result = await self.send_command(cmds)
            await self.check_errors()
            
            if result:
                if step_i is not None:
                    bashlog.info(f"已設置線性電流掃描: {start_i}A 到 {stop_i}A，步長 {step_i}A")
                else:
                    bashlog.info(f"已設置線性電流掃描: {start_i}A 到 {stop_i}A，{points} 個點")
            
            return result
        except Exception as e:
            bashlog.error(f"設置電流掃描時出錯: {e}")
            return False
    
    async def setup_buffer(self, buffer_size=100):
        """設置數據緩衝區
        
        Args:
            buffer_size: 緩衝區大小 (1 到 2500)
            
        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        try:
            cmds = [
                f":TRACe:POINts {buffer_size}",
                ":TRACe:FEED SENSe",
                ":TRACe:FEED:CONTrol NEXT",
                ":TRACe:CLEar"
            ]
            
            result = await self.send_command(cmds)
            await self.check_errors()
            
            if result:
                bashlog.info(f"數據緩衝區已設置為 {buffer_size} 個點")
            
            return result
        except Exception as e:
            bashlog.error(f"設置數據緩衝區時出錯: {e}")
            return False
    
    async def read_buffer(self):
        """讀取緩衝區中的數據
        
        Returns:
            list: 緩衝區中的測量結果列表
        """
        try:
            response = await self.query_command(":TRACe:DATA?")
            if not response:
                bashlog.error("讀取緩衝區失敗，無回應")
                return []
                
            # 處理緩衝區數據
            values = response.split(',')
            points = len(values) // 5  # 每個測量點有 5 個值
            results = []
            
            for i in range(points):
                point = {
                    'voltage': float(values[i*5]),
                    'current': float(values[i*5+1]),
                    'resistance': float(values[i*5+2]),
                    'timestamp': float(values[i*5+3]),
                    'status': int(float(values[i*5+4]))
                }
                results.append(point)
            
            return results
        except Exception as e:
            bashlog.error(f"讀取緩衝區數據時出錯: {e}")
            return []
    
    async def perform_iv_sweep(self, start_v, stop_v, points=None, step_v=None, use_buffer=True):
        """執行 IV 掃描
        
        Args:
            start_v: 起始電壓
            stop_v: 終止電壓
            points: 掃描點數
            step_v: 電壓步長
            use_buffer: 是否使用緩衝區存儲數據
            
        Returns:
            list: 測量結果列表，失敗時返回空列表
        """
        try:
            # 設置為電壓源並配置掃描
            await self.setup_as_voltage_source()
            
            # 設置掃描
            if step_v is not None:
                sweep_result = await self.setup_voltage_sweep_linear(start_v, stop_v, step_v=step_v)
                # 計算所需點數
                total_points = int(abs(stop_v - start_v) / step_v) + 1
            elif points is not None:
                sweep_result = await self.setup_voltage_sweep_linear(start_v, stop_v, points=points)
                total_points = points
            else:
                # 默認使用 10 個點
                points = 10
                sweep_result = await self.setup_voltage_sweep_linear(start_v, stop_v, points=points)
                total_points = points
            
            if not sweep_result:
                bashlog.error("設置掃描失敗")
                return []
            
            # 設置觸發計數
            await self.send_command(f":TRIGger:COUNt {total_points}")
            
            if use_buffer:
                # 設置數據緩衝區
                await self.setup_buffer(total_points)
            
            # 打開輸出並執行掃描
            await self.output_on()
            await self.send_command(KeithleyCommands.TRIGGER_IMMEDIATE)
            
            # 等待掃描完成
            await self.query_command(KeithleyCommands.OPC)
            
            results = []
            if use_buffer:
                # 從緩衝區讀取數據
                buffer_data = await self.read_buffer()
                for point in buffer_data:
                    results.append((point['voltage'], point['current']))
            else:
                # 使用 FETCh? 命令讀取數據
                fetch_data = await self.query_command(KeithleyCommands.FETCH)
                if fetch_data:
                    values = fetch_data.split(',')
                    num_points = len(values) // 5
                    for i in range(num_points):
                        voltage = float(values[i*5])
                        current = float(values[i*5+1])
                        results.append((voltage, current))
            
            # 關閉輸出
            await self.output_off()
            
            # 保存結果到檔案
            if results:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"iv_sweep_{timestamp}.csv"
                with open(filename, 'w') as f:
                    f.write("Voltage(V),Current(A)\n")
                    for v, i in results:
                        f.write(f"{v},{i}\n")
                bashlog.info(f"IV 掃描完成，結果已保存到 {filename}")
                
            return results
        except Exception as e:
            bashlog.error(f"執行 IV 掃描時出錯: {e}")
            # 確保輸出關閉
            await self.output_off()
            return []
    
    async def start_iv_monitor(self, interval=2.0):
        """啟動背景 IV 監控任務
        
        Args:
            interval: 測量間隔，單位為秒
            
        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        if not self.rs232_dev:
            bashlog.error("儀器未連接")
            return False
        
        try:
            # 創建監控任務
            async def monitor_task():
                try:
                    bashlog.info("IV 監控已啟動")
                    while True:
                        voltage, current = await self.read_iv()
                        if voltage is not None and current is not None:
                            bashlog.info(f"IV 監控: V={voltage}V, I={current}A")
                        await asyncio.sleep(interval)
                except asyncio.CancelledError:
                    bashlog.info("IV 監控已停止")
                except Exception as e:
                    bashlog.error(f"IV 監控時出錯: {e}")
            
            # 啟動任務並存儲到設備對象
            task = asyncio.create_task(monitor_task())
            self.rs232_dev.set_task(task)
            return True
        except Exception as e:
            bashlog.error(f"啟動 IV 監控時出錯: {e}")
            return False
    
    async def stop_iv_monitor(self):
        """停止 IV 監控任務
        
        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        if not self.rs232_dev:
            return False
        
        try:
            if hasattr(self.rs232_dev, 'task') and self.rs232_dev.task:
                self.rs232_dev.task.cancel()
                try:
                    # 等待任務取消
                    await asyncio.sleep(0.5)
                except asyncio.CancelledError:
                    pass
                
                bashlog.info("IV 監控已停止")
            return True
        except Exception as e:
            bashlog.error(f"停止 IV 監控時出錯: {e}")
            return False
    
    async def perform_custom_measurement_sequence(self, voltage_levels, measurement_time=1.0):
        """執行自定義測量序列
        
        Args:
            voltage_levels: 電壓值列表
            measurement_time: 每個電壓點停留的時間
            
        Returns:
            list: 測量結果列表
        """
        results = []
        
        try:
            # 設置為電壓源
            await self.setup_as_voltage_source()
            
            # 啟用輸出
            await self.output_on()
            
            for voltage in voltage_levels:
                # 設置電壓
                await self.set_voltage(voltage)
                
                # 等待穩定
                await asyncio.sleep(measurement_time)
                
                # 進行測量
                voltage, current = await self.read_iv()
                if voltage is not None and current is not None:
                    results.append((voltage, current))
                    bashlog.info(f"測量點: V={voltage}V, I={current}A")
            
            # 關閉輸出
            await self.output_off()
            
            # 保存結果到檔案
            if results:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"custom_measurement_{timestamp}.csv"
                with open(filename, 'w') as f:
                    f.write("Voltage(V),Current(A)\n")
                    for v, i in results:
                        f.write(f"{v},{i}\n")
                bashlog.info(f"自定義測量序列完成，結果已保存到 {filename}")
            
            return results
        except Exception as e:
            bashlog.error(f"執行自定義測量序列時出錯: {e}")
            # 確保輸出關閉
            await self.output_off()
            return []


async def validate_instrument(resource_name):
    """驗證儀器是否可用
    
    Args:
        resource_name: VISA 資源名稱
    
    Returns:
        str: 錯誤訊息，成功時返回空字符串
    """
    try:
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()
        
        bashlog.info(f"可用的 VISA 資源: {resources}")
        
        instr = rm.open_resource(resource_name)
        
        # 設置串口參數（如果是串口設備）
        if resource_name.startswith("ASRL"):
            instr.baud_rate = 9600
            instr.data_bits = 8
            instr.stop_bits = pyvisa.constants.StopBits.one
            instr.parity = pyvisa.constants.Parity.none
            instr.flow_control = pyvisa.constants.VI_ASRL_FLOW_NONE
            instr.timeout = 5000
        
        # 驗證是否為 Keithley 儀器
        idn = instr.query("*IDN?")
        if "KEITHLEY" not in idn.upper():
            return f"設備不是 Keithley 儀器: {idn}"
        
        bashlog.info(f"已發現 Keithley 儀器: {idn}")
        instr.close()
        rm.close()
        return ""
    except Exception as e:
        return f"驗證儀器時出錯: {e}"


# 示例使用
async def main():
    # 使用適當的設備地址
    resource_name = "GPIB0::24::INSTR"  # 示例 GPIB 地址，根據實際情況修改
    # 對於 RS232，可能類似：
    # resource_name = "ASRL/dev/ttyUSB0::INSTR"
    
    # 驗證儀器
    error = await validate_instrument(resource_name)
    if error:
        print(f"儀器驗證失敗: {error}")
        return
    
    print("儀器驗證成功，開始測試...")
    
    # 創建儀器控制對象
    keithley = KeithleyInstrument("keithley2410", resource_name)
    
    try:
        # 連接到儀器
        if not await keithley.connect():
            print("連接儀器失敗")
            return
        
        # 設置為電壓源
        await keithley.setup_as_voltage_source(voltage_range=20, voltage_level=0, current_compliance=0.1)
        
        # 設置測量速度
        await keithley.setup_measurement_speed(nplc=1.0)
        
        # 打開輸出並設置電壓
        await keithley.set_voltage(1.0)
        await keithley.output_on()
        
        # 讀取 IV 值
        voltage, current = await keithley.read_iv()
        print(f"測量結果: {voltage}V, {current}A")
        
        # 關閉輸出
        await keithley.output_off()
        
        # 執行掃描
        print("執行 IV 掃描...")
        results = await keithley.perform_iv_sweep(0, 5, points=11)
        
        if results:
            print(f"掃描得到 {len(results)} 個數據點")
        
        # 執行自定義測量序列
        print("執行自定義測量序列...")
        custom_voltages = [0, 1, 2, 3, 4, 5, 4, 3, 2, 1, 0]
        custom_results = await keithley.perform_custom_measurement_sequence(custom_voltages, measurement_time=0.5)
        
        if custom_results:
            print(f"自定義測量得到 {len(custom_results)} 個數據點")
        
        # 啟動 IV 監控
        print("啟動 IV 監控...")
        await keithley.set_voltage(2.5)
        await keithley.output_on()
        await keithley.start_iv_monitor(interval=1.0)
        
        # 運行一段時間
        print("IV 監控中...")
        await asyncio.sleep(5)
        
        # 停止監控
        await keithley.stop_iv_monitor()
        await keithley.output_off()
        
        print("測試完成!")
    except Exception as e:
        print(f"運行測試時出錯: {e}")
    finally:
        # 關閉連接
        await keithley.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
