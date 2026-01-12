-- Run the below step to create a POSTGRES DB to create the time series optimized table 

-- 1. STEP 1: bring up a postgres instance in docker
-- docker run -d \
--   --name timescaledb \
--   -p 5432:5432 \
--   -e POSTGRES_PASSWORD=postgres \
--   -e POSTGRES_DB=analytics \
--   timescale/timescaledb:latest-pg14

-- 2. STEP 2: connect to the instance


---------------------------------------------
-- Time Series Optimized Table (For history)
---------------------------------------------
CREATE TABLE events (
    timestamp TIMESTAMPTZ NOT NULL,
    user_id TEXT,
    event_type TEXT,
    page_url TEXT,
    session_id TEXT
);

-- converts the above table to a timeseries optimized db
SELECT create_hypertable('events', 'timestamp');


-- To create table which enable to check for malicious users, Following steps are followed



