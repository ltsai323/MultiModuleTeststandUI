import PythonTools.LoggingMgr as LoggingMgr

def configure_logger():
    import yaml
    yaml_content = '''
name: bashjob
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
'''
    conf = yaml.safe_load(yaml_content)


    stdout_filter_rules = [ LoggingMgr.errortype_factory(c['filter_method'], c['indicator'],c['threshold'],c['pattern']) for c in conf['filters'] ]
    stdout_filter = LoggingMgr.ErrorMessageFilter(stdout_filter_rules)
    log_stdout = LoggingMgr.configure_logger2(conf['name'],conf['file'], stdout_filter)
    return log_stdout

log = configure_logger()

if __name__ == '__main__':
    #configure_logger()
    log.info('aaa')
