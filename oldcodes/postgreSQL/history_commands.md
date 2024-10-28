	> sudo docker pull postgres
	> sudo docker create --name test-postgreSQL -p 8080:5432 -e POSTGRES_PASSWORD=admin postgres
	> sudo docker start test-postgreSQL
	> sudo docker exec test-postgreSQL psql --help
	> sudo docker exec test-postgreSQL psql -V
	> sudo docker exec test-postgreSQL psql -U postgres -l
psql is the PostgreSQL interactive terminal.

# pSQL arguments
	Usage:
	  psql [OPTION]... [DBNAME [USERNAME]]
	
	General options:
	  -c, --command=COMMAND    run only single command (SQL or internal) and exit
	  -d, --dbname=DBNAME      database name to connect to (default: "root")
	  -f, --file=FILENAME      execute commands from file, then exit
	  -l, --list               list available databases, then exit
	  -v, --set=, --variable=NAME=VALUE
	                           set psql variable NAME to VALUE
	                           (e.g., -v ON_ERROR_STOP=1)
	  -V, --version            output version information, then exit
	  -X, --no-psqlrc          do not read startup file (~/.psqlrc)
	  -1 ("one"), --single-transaction
	                           execute as a single transaction (if non-interactive)
	  -?, --help[=options]     show this help, then exit
	      --help=commands      list backslash commands, then exit
	      --help=variables     list special variables, then exit
	
	Input and output options:
	  -a, --echo-all           echo all input from script
	  -b, --echo-errors        echo failed commands
	  -e, --echo-queries       echo commands sent to server
	  -E, --echo-hidden        display queries that internal commands generate
	  -L, --log-file=FILENAME  send session log to file
	  -n, --no-readline        disable enhanced command line editing (readline)
	  -o, --output=FILENAME    send query results to file (or |pipe)
	  -q, --quiet              run quietly (no messages, only query output)
	  -s, --single-step        single-step mode (confirm each query)
	  -S, --single-line        single-line mode (end of line terminates SQL command)
	
	Output format options:
	  -A, --no-align           unaligned table output mode
	      --csv                CSV (Comma-Separated Values) table output mode
	  -F, --field-separator=STRING
	                           field separator for unaligned output (default: "|")
	  -H, --html               HTML table output mode
	  -P, --pset=VAR[=ARG]     set printing option VAR to ARG (see \pset command)
	  -R, --record-separator=STRING
	                           record separator for unaligned output (default: newline)
	  -t, --tuples-only        print rows only
	  -T, --table-attr=TEXT    set HTML table tag attributes (e.g., width, border)
	  -x, --expanded           turn on expanded table output
	  -z, --field-separator-zero
	                           set field separator for unaligned output to zero byte
	  -0, --record-separator-zero
	                           set record separator for unaligned output to zero byte
	
	Connection options:
	  -h, --host=HOSTNAME      database server host or socket directory (default: "local socket")
	  -p, --port=PORT          database server port (default: "5432")
	  -U, --username=USERNAME  database user name (default: "root")
	  -w, --no-password        never prompt for password
	  -W, --password           force password prompt (should happen automatically)
	
	For more information, type "\?" (for internal commands) or "\help" (for SQL
	commands) from within psql, or consult the psql section in the PostgreSQL
	documentation.
	
	Report bugs to <pgsql-bugs@lists.postgresql.org>.
	PostgreSQL home page: <https://www.postgresql.org/>

# Send command to database
There are 3 methods:
1. docker exec
2. bash in this container
3. CLI in PostgreSQL
### Command via 'docker exec'
	> sudo docker exec -it test-postgreSQL psql -U postgres -c "create role testUSER with login password 'TESTuser';"
	> sudo docker exec -it test-postgreSQL psql -U postgres -c "create role userDOCKERexec with login password 'TESTuser';"
	> sudo docker exec -it test-postgreSQL psql -U postgres -c "create database databaseDOCKERexec with owner userDOCKERexec"
	> sudo docker exec -it test-postgreSQL psql -U postgres -c '\l'
### Command via 'bash in the container'
	> sudo docker exec -it test-postgreSQL bash 
	cd /usr/lib/postgresql/
	cd 16/bin
	ls
	createuser -U postgres -P userBASHinside
	createdb -U postgres -O userBASHinside databaseBASHinside
	psql -l -U userBASHinside
### Command via 'PostgreSQL CLI'
	> sudo docker exec -it test-postgreSQL psql -U postgres
	

## Used Other Commands

	sudo docker stop test-postgreSQL # stop the service
