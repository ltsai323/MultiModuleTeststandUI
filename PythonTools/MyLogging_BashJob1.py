from PythonTools.LoggingMgr import configure_logger_by_yamlDICT

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

log = configure_logger_by_yamlDICT(yaml_content)

if __name__ == '__main__':
    log.info('aaa')
