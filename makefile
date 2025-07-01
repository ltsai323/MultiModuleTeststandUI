.PHONY: help

check_defined = \
  $(strip $(foreach 1,$1, \
  $(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
  $(if $(value $1),, \
  $(error Undefined $1$(if $2, ($2))))


initialize: ## initialize [JobName=testjob]
	$(call check_defined, JobName)
	@echo "[$(JobName) - StatusChangeInitialized] hiiii"

runtimeout=10
run: run1 run2 ## run module [JobName=testjob][runtimeout=3]
	echo hi

run1: ## run module [JobName1=testjob][runtimeout=3]
	jobname=$(JobName1) ; if [ "$$jobname" != "" ];then \
			sh scripts/run_single_module.sh $$jobname $(runtimeout) 2>&1 | tee logs/log_make_run.txt ; \
			if [ "`tail -n1 logs/log_$${jobname}_takedata.txt`" != "FINISHED" ];then sh scripts/run_single_module.sh $$jobname $(runtimeout); fi; \
			else echo run1 is stopped; fi
run2: ## run module [JobName2=testjob][runtimeout=3]
	jobname=$(JobName2) ; if [ "$$jobname" != "" ];then \
			sh scripts/run_single_module.sh $$jobname $(runtimeout) 2>&1 | tee logs/log_make_run.txt ; \
			if [ "`tail -n1 logs/log_$${jobname}_takedata.txt`" != "FINISHED" ];then sh scripts/run_single_module.sh $$jobname $(runtimeout); fi; \
			else echo run2 is stopped; fi


stop: ## stop the run command, mainly stop the secondary jobs handled in `make run` [JobName=testjob]
	$(call check_defined, JobName)
	@echo "[$(JobName) - StatusChangeStopped] Stop finished"

destroy: ## destroy [JobName=testjob]
	$(call check_defined, JobName)
	@echo "[$(JobName) - StatusChangeDestroyed] Destroy finished"
	
test: ## test function. Notice the array should be separated with space and quoted with ". [theARRAY="0 1 2 3 4 5"]
	$(call check_defined, theARRAY)
	python3 t.py $(theARRAY)

clean: ## clean all logs
	/bin/rm -f logs/log*.txt
opts = "-jN using N cpus"

IN_ARGS = [opts]

help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[32m<command>\033[0m $(IN_ARGS)\n\nCommands:\n\033[36m\033[0m\n"} /^[0-9a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help

