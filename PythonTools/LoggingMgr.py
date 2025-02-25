#!/usr/bin/env python3
import logging

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
    logger.setLevel(logging.INFO)

    # File handler for logging
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(f"%(asctime)s [{name} - %(levelname)s] %(message)s"))

    # Add custom filter
    file_handler.addFilter(errMESGfilter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    #console_handler.setLevel(logging.ERROR)
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

if __name__ == "__main__":
    testfunc_loggers()
