-- create new user.
CREATE USER test1 WITH PASSWORD 'testPWD';
CREATE ROLE test2 WITH LOGIN PASSWORD 'testPWD';


-- Create the database
CREATE DATABASE TESTDB WITH OWNER test2;

-- Connect to the database
\c TESTDB;

-- Create the CPU_usage table
CREATE TABLE CPU_usage (
	injection_time TIMESTAMP DEFAULT current_timestamp,
	usage NUMERIC
);

-- Grant necessary privileges to the test user
GRANT ALL PRIVILEGES ON DATABASE TESTDB TO test1;
GRANT ALL PRIVILEGES ON DATABASE TESTDB TO test2;
GRANT ALL PRIVILEGES ON TABLE CPU_usage TO test1;

-- Grant inject permission to test1 user.
-- Somehow the CPU_usage table is not in database testdb.
-- instead, it is put at public.cpu_usage.
GRANT INSERT ON TABLE public.cpu_usage TO test1;
