-- Create the database
CREATE DATABASE TESTDB;

-- Connect to the database
\c TESTDB;

-- Create the CPU_usage table
CREATE TABLE CPU_usage (
	injection_time TIMESTAMP DEFAULT current_timestamp,
	usage NUMERIC
);

