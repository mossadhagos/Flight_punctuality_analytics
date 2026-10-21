USE ROLE USERADMIN;

CREATE ROLE IF NOT EXISTS dlt_role
    COMMENT = 'dlt: loads source data into raw';
CREATE ROLE IF NOT EXISTS dbt_role 
    COMMENT = 'dbt: reads raw, builds staging, dimensional and marts';
CREATE ROLE IF NOT EXISTS reporter_role
    COMMENT = 'Streamlit: read only access to marts';

USE ROLE SECURITYADMIN;
GRANT ROLE dlt_role         TO ROLE SYSADMIN;
GRANT ROLE dbt_role         TO ROLE SYSADMIN;
GRANT ROLE reporter_role    TO ROLE SYSADMIN;

SHOW ROLES LIKE '%_ROLE';