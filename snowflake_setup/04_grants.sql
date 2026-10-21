USE ROLE SECURITYADMIN;

GRANT USAGE ON WAREHOUSE flight_wh TO ROLE dlt_role; 
GRANT USAGE ON WAREHOUSE flight_wh TO ROLE dbt_role;
GRANT USAGE ON WAREHOUSE flight_wh TO ROLE reporter_role;


GRANT USAGE ON DATABASE flight_db TO ROLE dlt_role;
GRANT USAGE ON DATABASE flight_db TO ROLE dbt_role;
GRANT USAGE ON DATABASE Flight_db TO ROLE reporter_role;

GRANT USAGE, CREATE TABLE ON SCHEMA flight_db.raw TO ROLE dlt_role;


GRANT USAGE ON SCHEMA flight_db.raw TO ROLE dbt_role;
GRANT SELECT ON ALL TABLES       IN SCHEMA flight_db.raw TO ROLE dbt_role;
GRANT SELECT ON FUTURE TABLES   IN SCHEMA flight_db.raw TO ROLE dbt_role;

GRANT USAGE, CREATE TABLE, CREATE VIEW ON SCHEMA flight_db.staging      TO ROLE dbt_role;
GRANT USAGE, CREATE TABLE, CREATE VIEW ON SCHEMA flight_db.dimensional  TO ROLE dbt_role;
GRANT USAGE, CREATE TABLE, CREATE VIEW ON SCHEMA flight_db.marts        TO ROLE dbt_role;


GRANT USAGE ON SCHEMA flight_db.marts TO ROLE reporter_role;
GRANT SELECT ON  ALL TABLES     IN SCHEMA flight_db.marts TO ROLE reporter_role;
GRANT SELECT ON FUTURE TABLES   IN SCHEMA flight_db.marts TO ROLE reporter_role;
GRANT SELECT ON ALL VIEWS       IN SCHEMA flight_db.marts TO ROLE reporter_role;
GRANT SELECT ON FUTURE VIEWS    IN SCHEMA flight_db.marts TO ROLE reporter_role;



SHOW GRANTS TO ROLE dlt_role;
SHOW GRANTS TO ROLE dbt_role;
SHOW GRANTS TO ROLE reporter_role;
SHOW FUTURE GRANTS IN SCHEMA flight_db.raw;
SHOW FUTURE GRANTS IN SCHEMA flight_db.marts;