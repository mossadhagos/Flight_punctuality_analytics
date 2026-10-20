USE ROLE ACCOUNTADMIN;

SHOW DATABASES LIKE 'flight_db';
SHOW SCHEMAS IN DATABASE flight_db;
SHOW WAREHOUSES;

GRANT OWNERSHIP ON DATABASE flight_db                TO ROLE SYSADMIN COPY CURRENT GRANTS;
GRANT OWNERSHIP ON ALL SCHEMAS IN DATABASE flight_db TO ROLE SYSADMIN COPY CURRENT GRANTS;

REVOKE ROLE dbt_role FROM USER dlt_user;
GRANT  ROLE dlt_role TO   USER dlt_user;
ALTER USER dbt_user SET DEFAULT_NAMESPACE = 'flight_db.staging';

ALTER USER dlt_user      SET PASSWORD = 'Dlt_User_pass_2026';
ALTER USER dbt_user      SET PASSWORD = 'Dbt_User_pass_2026';
ALTER USER reporter_user SET PASSWORD = 'Reporter_User_pass2026';

CREATE USER IF NOT EXISTS samuel
    PASSWORD             = 'Samuel_is_here1'
    EMAIL                = 'oloruntobi.samuel.aboaba@stud.sti.se'
    DISPLAY_NAME         = 'samuel'
    DEFAULT_ROLE         = SYSADMIN
    DEFAULT_WAREHOUSE    = flight_wh
    DEFAULT_NAMESPACE    = flight_db.raw
    MUST_CHANGE_PASSWORD = TRUE;


CREATE USER IF NOT EXISTS andreas
    PASSWORD             = 'Andreas_is_here1'
    EMAIL                = 'andreas.holmberg@stud.sti.se'
    DISPLAY_NAME         = 'andreas'
    DEFAULT_ROLE         = SYSADMIN
    DEFAULT_WAREHOUSE    = flight_wh
    DEFAULT_NAMESPACE    = flight_db.raw
    MUST_CHANGE_PASSWORD = TRUE;

GRANT ROLE SYSADMIN TO USER samuel;
GRANT ROLE SYSADMIN TO USER andreas;

SHOW GRANTS TO USER samuel;
SHOW GRANTS TO USER andreas;   

SHOW GRANTS TO USER dlt_user;       
SHOW GRANTS TO USER dbt_user;       
SHOW GRANTS TO USER reporter_user;  
SHOW FUTURE GRANTS IN SCHEMA flight_db.raw;
SHOW FUTURE GRANTS IN SCHEMA flight_db.marts;