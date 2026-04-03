# Introduction

<h3 align="center">Quantifarm Benchmarking Tool</h3>

<p align="center">
  This common component aims to act as a single point of access,
  capable to provide aggregated datasets , derived from Calendars , Meterological Data , etc.
</p>

<p align="center">
  You will need to have Dokcer installed on your system
  <br>
  Windows : <a href="https://docs.docker.com/desktop/install/windows-install/"><strong>Installation Guide</strong></a>
  <br>
  Ubuntu : <a href="https://docs.docker.com/engine/install/ubuntu/"><strong>Installation Guide</strong></a>
  <br>
  Linux : <a href="https://docs.docker.com/desktop/install/mac-install/"><strong>Installation Guide</strong></a>
</p>

## Installation

- Create a Folder in your System
- Clone / Download the Git Code into the folder
- Execute the following command 
```console
$ docker compose up
```
- Done

<p align="center">
Afte a successful service initiation the Webservice API documentation is available here:
http://0.0.0.0:8686/documentation
</p>


## How to Use
The principle of this Calculator is simple. It requires Parcel specific Data and Calendar Data in order to 
execute models and provide aggregated results.
So in order to be able to execute aggregations we first need to populate the database with :
- **Parcel Data**
- **Calendar Data**

## Add Parcels
In order to receive the **Calculation Results** , we are going to have to add **Parcel Data** in the WebService. And those input data will be fed to the Models to produce the desired calculations.
This can be achieved by using the **[PUT]** "**/parcel**" Endpoint , under the "**Parcels**" Header , and fill in each input with the appropriate values.

<b>Example : </b>

- Go to http://localhost:8686/documentation
- Expand the **[PUT]** "**/parcel**" (under the "**Parcels**" Header).
- Press the "**Try it out**" on the right side.
- Fill in the Input Form Fields with the appropriate values.
  - **name** : Provide a custom name that will be asigned to the Parcel
  - **polygon** : Provide the Polygon of the Parcel. The format of th Polygon is displayed in the swagger documentation. (**Optional**)
  - **uid** : Provide a custom Unique ID you want to assign to the Parcel. (**Optional**)
  - **user_id** : Provide a Custom "user_id" so that all data are attached to a specific id.
- Press the "**Execute**" Button.

## Add Calendar Events
In order to receive the **Calculation Results** , we are going to have to add **Calendar Events** in the WebService. 
This can be achieved by using the **[PUT]** "**/event**" Endpoint , under the "**Calendar**" Header , and fill in each input with the appropriate values.

<b>Example : </b>

- Go to http://localhost:8686/documentation
- Expand the **[PUT]** "**/event**" (under the "**Calendar**" Header).
- Press the "**Try it out**" on the right side.
- Fill in the JSON with the appropriate values.
```
  {
    "dat": "string",
    "parcelId": "string",
    "eventStart": "2023-12-18T11:34:46.976Z",
    "eventEnd": "2023-12-18T11:34:46.976Z",
    "duration": 0,
    "type": "harvest",
    "crop": "string",
    "variety": "string",
    "comments": "string",
    "properties": {
      "amount": 0,
      "unit": "ton",
      "unitRef": "stremma",
      "metric": "string",
      "target": "string",
      "productName": "string",
      "stage": "string",
      "fuelConsumption": 0,
      "fuelType": "diesel",
      "fuelUnit": "ton",
      "fuelUnitRef": "string"
    }
  }
```
**Note** :  This EndPoint supports multiple events. You can provide a list of Dictionaries to add the events in the system.

- Press the "**Execute**" Button.

## Retrieve the Aggregation Results
In order to retrieve the Aggregation Results for a specific parcel we need to visit the **[GET] "/parcels/{parcelid}/aggregations"** Endpoint.

<b>Example : </b>

- Go to http://localhost:8686/documentation
- Expand the **[GET]** "**/parcels/{parcelid}/aggregations**" (under the "**Aggregation**" Header).
- Press the "**Try it out**" on the right side.
- Fill in the Input Form Fields with the appropriate values.
  - **parcelid** : Provide the UID you used while adding the Parcels
  - **evt_type** : Select one of the Calendar Event Types for the aggregation.
    - Harvest
    - Spray 
    - Irrigation
    - Fertilization
  - **aggregation_function** : Select one of the Types of Aggregation (Aggregation Model) Eventto execute.
    - **sum** : Provides the **Summary** of the values  provided
    - **avg** : Provides the **Average** of the values provided
    - **min** : Provides the **minimum** value of the values provided
    - **max** : Provides the **maximum** value of the values provided
    - **fromdate** : Provide the Starting Date of the period for which the aggregation models will ahve to be calculated.
    - **todate** : Provide the Ending Date of the period for which the aggregation models will ahve to be calculated.
  - Press the "**Execute**" Button.

