USE ROLE USERADMIN;

CREATE USER IF NOT EXISTS dlt_user
    PASSWORD = '<set_manually>'                
    DEFAULT_ROLE = dlt_role
    DEFAULT_WAREHOUSE = flight_wh
    DEFAULT_NAMESPACE = flight_db.raw
    MUST_CHANGE_PASSWORD = FALSE
    COMMENT = 'Service user for dlt';           

CREATE USER IF NOT EXISTS dbt_user
    PASSWORD = '<set_manually>'                 
    DEFAULT_ROLE = dbt_role
    DEFAULT_WAREHOUSE = flight_wh
    DEFAULT_NAMESPACE = flight_db.staging       
    MUST_CHANGE_PASSWORD = FALSE
    COMMENT = 'Service user for dbt';

CREATE USER IF NOT EXISTS reporter_user
    PASSWORD = '<set_manually>'                 
    DEFAULT_ROLE = reporter_role
    DEFAULT_WAREHOUSE = flight_wh
    DEFAULT_NAMESPACE = flight_db.marts
    MUST_CHANGE_PASSWORD = FALSE
    COMMENT = 'Service user for Streamlit (only read)';

GRANT ROLE dlt_role                 TO USER dlt_user;     
GRANT ROLE dbt_role                 TO USER dbt_user;
GRANT ROLE reporter_role            TO USER reporter_user;

SHOW USERS LIKE '%_USER';