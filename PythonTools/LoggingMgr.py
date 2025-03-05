#!/usr/bin/env python3
import logging
DEBUG_MODE = True # control the console output show DEBUG or INFO

class errortype:
    def __init__(self, errTYPE:str, errTHRESHOLD:int, errPATTERN:str):
        """
        Input log filter as a list contains error type and message filter as the key - value pair

        :errTYPE: The string records what is the error. This string will be delievered to webpage.
        :errTHRESHOLD: The integer shows how much error message can be ignored. Set 0 for bouncing error immediately.
                       Set 2 to ignore the error message twice.
        :errPATTERN: Use `for errPATTERN in theMESG` to check the EXACTLY pattern in the message. This checking is line based.
        """
        
        self.type = errTYPE
        self.threshold = errTHRESHOLD
        self.pattern = errPATTERN
    def get_error_type(self, mesg):
        if self.pattern not in mesg: return None
        self.threshold -= 1
        return self.type if self.threshold<0 else f'_{self.type}_{self.threshold}_'
class errortype_contain(errortype):
    def get_error_type(self, mesg):
        if self.pattern not in mesg: return None
        self.threshold -= 1
        return self.type if self.threshold<0 else f'_{self.type}_{self.threshold}_'
class errortype_exact(errortype):
    def get_error_type(self, mesg):
        lines = mesg.strip().split('\n')
        for line in lines:
            if self.pattern == line:
                self.threshold -= 1
                return self.type if self.threshold<0 else f'_{self.type}_{self.threshold}_'
        return None
def errortype_factory( filterMETHOD:str,
        errTYPE:str, errTHRESHOLD:str,errPATTERN:str):
    if filterMETHOD.lower() == 'contain':
        return errortype_contain(errTYPE,errTHRESHOLD,errPATTERN)
    if filterMETHOD.lower() == 'exact':
        return errortype_exact(errTYPE,errTHRESHOLD,errPATTERN)
    raise KeyError(f'[Invalid filterMETHOD] input filterMETHOD "{ filterMETHOD }" is rejected from errortype_factory()')


    


from queue import Queue
log_queue = Queue()
class ErrorMessageFilter(logging.Filter):
    def __init__(self, logFILTERs:list = []):
        """
        Input log filter as a list contains errortype for filtering log

        :param logFILTER: A list with content like
                          logFILTER = [ errortype('i2cStatError', 0, 'i2c: invalid'), errtype('RestartNeeded', 5, 'waiting for next step') ]
        """
        self.log_filters = logFILTERs
    def filter(self, record):
        mesg = record.getMessage()

        # # Check for specific patterns and assign types
        throw_mesg_to_outside = False if record.levelno != logging.ERROR else True
        for error_type_filter in self.log_filters:
            error_type = error_type_filter.get_error_type(mesg)
            if error_type:
                record.levelno = logging.ERROR
                record.levelname = error_type
                throw_mesg_to_outside = True
                break
        # # if error or passing filter, put the message outside
        # if throw_mesg_to_outside:
        #     log_queue.append(record.levelname)
        #print(f'got type hiiiiiiiiiii {self.type}') # you can add actions when passing the value
        return True # False to forbid this message

# Configure separate loggers for stdout and stderr
def configure_logger(name, log_file, errMESGfilter:ErrorMessageFilter):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG) # log file always read DEBUG

    # File handler for logging
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(f"%(asctime)s [{name} - %(levelname)s] %(message)s"))

    # Add custom filter
    file_handler.addFilter(errMESGfilter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
    console_handler.setFormatter(logging.Formatter(f"%(asctime)s [{name} %(levelname)s] %(message)s"))
    # Add custom filter
    console_handler.addFilter(errMESGfilter)
    logger.addHandler(console_handler)

    return logger

# put logger at global for all functions
log_stdout = None
log_stderr = None
def testfunc_loggers():
    stdout_err_mesg_filter = ErrorMessageFilter()
    stderr_err_mesg_filter = ErrorMessageFilter( [
            errortype_contain('Type1Err', 0, '[running] 1'),
            errortype_contain('Type3Err', 0, '[running] 3'),
        ])
    log_stdout = configure_logger('out', 'log_stdout.txt', stdout_err_mesg_filter)
    log_stderr = configure_logger('err', 'log_stderr.txt', stderr_err_mesg_filter)


    log_stdout.info('hiiii')
    log_stdout.critical('alskdjfhiiii')
    log_stderr.error('[running] 1 asdf')
    log_stderr.error('asldkjfalsdkfasjkdf')


def yaml_errortype_factory( yamlDICT:dict ):
    used_vars = [ 'filterMETHOD', 'errTYPE', 'errTHRESHOLD', 'errPATTERN' ]
    for v in used_vars:
        if v not in yamlDICT:
            raise RuntimeError(f'[InvalidArgument] errortype_factory() requires dictionary containing keys {used_vars}')

    filter_method = yamlDICT['filterMETHOD'].lower()
    if filter_method == 'contain': return errortype_contain(yamlDICT['errTYPE'],yamlDICT['errTHRESHOLD'],yamlDICT['errPATTERN'])
    if filter_method == 'exact'  : return errortype_exact(yamlDICT['errTYPE'],yamlDICT['errTHRESHOLD'],yamlDICT['errPATTERN'])

    raise KeyError(f'[Invalid filterMETHOD] input filterMETHOD "{ filterMETHOD }" is rejected from errortype_factory()')
def YamlConfiguredLoggers(yamlDICT:dict):
    logout_config = yamlDICT['stdout']
    stdout_filter_rules = [ errortype_factory(c['filter_method'], c['indicator'],c['threshold'],c['pattern']) for c in logout_config['filters'] ]
    stdout_filter = ErrorMessageFilter(stdout_filter_rules)
    log_stdout = configure_logger(logout_config['name'],logout_config['file'], stdout_filter)

    logerr_config = yamlDICT['stderr']
    stderr_filter_rules = [ errortype_factory(c['filter_method'], c['indicator'],c['threshold'],c['pattern']) for c in logerr_config['filters'] ]
    stderr_filter = ErrorMessageFilter(stderr_filter_rules)
    log_stderr = configure_logger(logerr_config['name'],logerr_config['file'], stderr_filter)

    return log_stdout, log_stderr

def testfunc_YamlConfiguredLoggers():
    yaml_dict =  '''
stdout:
  name: out
  file: log_stdout.txt
  filters:
    - indicator: running
      threshold: 0
      pattern: 'RUNNING'
      filter_method: exact
    - indicator: Type0ERROR
      threshold: 0
      pattern: '[running] 0'
      filter_method: exact
    - indicator: Type3ERROR
      threshold: 0
      pattern: '[running] 3'
      filter_method: contain
    - indicator: idle
      threshold: 0
      pattern: 'FINISHED'
      filter_method: exact
stderr:
  name: err
  file: log_stderr.txt
  filters:
    - indicator: running
      threshold: 0
      pattern: 'RUNNING'
      filter_method: exact
    - indicator: Type0ERROR
      threshold: 0
      pattern: '[running] 0'
      filter_method: exact
    - indicator: RaiseError
      threshold: 0
      pattern: 'Error'
      filter_method: contain
        '''
    import yaml
    loaded_conf = yaml.safe_load(yaml_dict)
    print(loaded_conf)

    log_stdout, log_stderr = YamlConfiguredLoggers(loaded_conf)


if __name__ == "__main__":
    #testfunc_loggers()
    testfunc_YamlConfiguredLoggers()
