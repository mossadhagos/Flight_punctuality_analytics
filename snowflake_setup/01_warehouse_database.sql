USE ROLE SYSADMIN;

CREATE WAREHOUSE IF NOT EXISTS flight_wh
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE 
    COMMENT = 'Warehouse for flight punctuality PoC';

CREATE DATABASE IF NOT EXISTS flight_db 
    COMMENT = 'Flight punctuality analytics';

USE DATABASE flight_db;

CREATE SCHEMA IF NOT EXISTS raw             COMMENT = 'Loaded by dlt, untouched source data';
CREATE SCHEMA IF NOT EXISTS staging         COMMENT = 'dbt: cleaned and typed source data';
CREATE SCHEMA IF NOT EXISTS dimensional     COMMENT = 'dbt: facts and dimensions';
CREATE SCHEMA IF NOT EXISTS marts           COMMENT = 'dbt: aggregeated tables for the dashboard';

SHOW SCHEMAS IN DATABASE flight_db;