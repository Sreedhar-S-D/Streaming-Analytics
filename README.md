**INTRODUCTION**
____________________________________________________________________________________________________________________________________

This is a basic analytics service service that processes user events and provides basic real-time insights for three basic events:
1. Active users count
2. Top 5 pages
3. Number of active sessions for the same user


User Events are sent by a mock data service and a mock payload can be found over here:
```
{
 "timestamp": "2024-03-15T14:30:00Z",
 "user_id": "usr_789",
 "event_type": "page_view",
 "page_url": "/products/electronics",
 "session_id": "sess_456"
}
```


**ARCHITECTURE**
____________________________________________________________________________________________________________________________________


![Architecture Diagram](./architecture.png)

We have a Mock Data Generator which will generate the payload as shown in the introduction. Its a UI with 3 buttons:
1. With Button 1 you will be able to send 100 requests per second
2. With Button 2 you will be able to send 1,000 requests per second
3. With Button 3 you will be able to send 10,000 requests per second

You can see the events in the developer tools console as well by clicking right click + Inspect -> Console Tab.

**Mock Data Generator + Kafka**
These events are sent to a Kafka queue which injest all those events sent from the mock data generator.
Kafka queue has been added to the architecture so that the services which will process the mock JSON data will not be overwhelmed with so many requests.

**Validator and Bot Detection**
Then a services keeps polling from this Kafka queue at a rate of 10,000 events per second.
A validator will then validate if the event sent adheres to the standard JSON payload as shown in the introduction. If it does not adhere, the event is skipped.

If the it does adhere, then the event is sent to the bot detector. This bot detector checks if its a valid user request. The assumption here is that a person
would be able to visit 10 pages at once. If in the json payload, for a particular timestamp, there are more than 10 page visits for a particular user then those events are dropped. It uses Redis to achieve the mentioned step using INCR.

**TimeSeries DB Writer + Redis Writer**
Once the correct events arrive, two threads parallely write to a Postgres DB instance in which we have a table which is optimized for timeseries data and a Redis instance respectively.
Sorted sets have been used to calculate the statistics:
1. Active users count
2. Top 5 pages
3. Number of active sessions for the same user
Events are written in batches to both the timeseries optimized table in postgres and redis and not one by one.
The Kafka offset is not increased until the commits to the postgres DB is not a success but not for the Redis instance as we have Redis-Timeseries consolidation service which will keep the Redis and Timeseries table in sync.

**Redis Data Reader**
Then a process will read from the redis instance and will be serve the relevant statistics in the form of APIs

**Client**
The client will call APIs served from the Redis Data Reader and show it in a react app.

**Redis-Timeseries Consolidation**
In case the Redis instance fails then we can run this service and keep the timeseries db and the redis instance in sync.



**INSTALLATION PROCEDURE**
____________________________________________________________________________________________________________________________________

To run this project we need a machine with atleast 8 GB of RAM and 100 GB of storage (even this is a lot but playing safe here )
And would need to install the following softwares:
1. [docker](https://docs.docker.com/engine/install/)
2. [python](https://www.python.org/downloads/) , preferrably version more than v3.10
3. [node and npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) 



**WHICH FOLDER IS WHAT??**
____________________________________________________________________________________________________________________________________

Folder 
1. **Dashboard-app** ->  Upon running this folder, it will bring up the UI with which we can see the analytics
2. **JSON-value-generator-ad-clicks** -> This folder contains the frontend and the backend for the mock data generator which will generate the JSON payload as shown in the introduction
3. **Kafka_Reader** -> This contains the kafka reader, the validator and bot detection service and the service which writes to the timeseries db and redis cache.
4. **Kafka-local** -> This just contains a docker compose file which will help to bring up a kafka instance in docker.
5. **Postgres-init** -> Contains just setup of how to setup up the necessary tables for this project
6. **Redis-db-Reader** -> Contains the APIs which interact with Redis and serves the APIs for the UI analytics frontend


**HOW TO GET THIS PROJECT RUNNING??**
____________________________________________________________________________________________________________________________________

Upon installing python, we'll need to have a few libraries which we will get via pip, so you can do:
`pip install -r requirements.txt`
OR
`pip3 install -r requirements.txt`


1. Step 1: Get the mock data generator running:

cd into folder `JSON-value-generator-ad-clicks`
do npm install, this will install dependencies

Then cd into folder `simple-backend` and run the command `uvicorn requests:app --reload --port 4000` to get the backend up and running on port number 4000.

To serve the frontend cd into folder `simple-frontend`, run command `npm install` -> this will install all dependencies and run `npm run dev` to serve the frontend on port number 5173 and you can access it over here in [http://localhost:5173/](http://localhost:5173/).

--
2. Before you hit any API via the frontend, make sure you have the Kafka-local up and ready.
cd into folder Kafka-local -> and run the command `docker compose up -d` which will bring up a local Kafka instance.

Now you can hit any API via the frontend but we cannot see any analytics as such till now.

--
3. Now we need to bring up the Service which does the validation, bot detection and writing to the timeseries db and the Redis cache.

so you can cd into `Kafka_Reader` and just run the command python `python3 analytics_ingestion.py` -> This will bring up the above service.


--
4. Now before we hit any API, we need to make sure redis is running and the tables present in the timeseries optimized table is present.
So we can get Redis up and running by executing the command:
```
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7
```

To get the Postgres instance up, we follow the steps mentioned in the Readme.md file of Postgres-init. This will bring up the normal db to detect bots and also the time series optimized tables.

---
5. Now to be able to read the data from redis and to be able to see in the UI, we can do the following:
a. Bring up the backed by doing cd Redis-Db-Reader and then bring up the db by running the command `uvicorn data_reader:app --reload --port 8000` which will bring up the backend on port 4000.
b. Then bring up the frontend by cd Dashboard-app, running `npm install` which will install the dependencies, then go to folder ViewStats by doing `cd ViewStats` and run `npm install` to install all the dependencies and then `npm run dev` to brin up the frontend on port 5174: [http://localhost:5174/](http://localhost:5174/).



**Sample Video**
____________________________________________________________________________________________________________________________________