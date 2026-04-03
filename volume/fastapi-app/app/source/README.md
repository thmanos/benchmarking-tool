# Introduction

<h3 align="center">Quantifarm Benchmarking Tool</h3>

<p align="center">
  This common component aims to act as a single point of access,
  capable to provide aggregated datasets , derived from Calendars , Meterological Data , etc.
</p>

<p align="center">
  The following Technolgies / APIs / Libraries are utilised:
  <br>
  Python 3 : <a href="https://docs.python.org/3/"><strong>Explore Python 3.6+ docs »</strong></a>
  <br>
  FastAPI : <a href="https://fastapi.tiangolo.com/"><strong>FastAPI »</strong></a>
</p>


## Table of contents

- [Quick start](#quick-start)
- [Testing it out Instructions](#testing-it-out-instructions)

## Quick start

### Python and Libraries

- Install [Python 3.6+](https://www.python.org/downloads/)
- Install an ASGI Server like Uvicorn : 

```console
$ pip install uvicorn
```

- Install the following Python libraries : 

```console
$ pip install aiohttp
$ pip install python-multipart
$ pip install aiofiles
$ pip install psycopg2
$ pip install fastapi
```

### Configuration Files

- Set the correct Database Info in "/cfg/config.json"

### Start API Server

- Start Uvicorn

```console
$ uvicorn main:app --port 8686 --host 127.0.0.1 --reload --root-path /
```

## Endpoint Documentation 
You can set the Documentation path by changing the "docs_url" in "config.json" which can be found inside "/cfg" : 

```console
localhost:8000/docs
```

# Testing it out Instructions

This section expects you to have : 
- A ASGI Server installed and Running with your Python Code

## Python Code : Setup your WebService Configuration File
Navigate to your WebService source code and edit "/cfg/config.json" with the appropriate info.
- service -> endpoint : Is the root url of your (FastApi) Web Service. For Example "http://localhost:8000"
- logs -> path : Is the Path to where the Log files will be created.
- database -> connection : Your Database connection String details.
- database -> schema : The Schema that will be used for Layer Data.
- database -> tables : The name of the Tables you want to be created in the Schema and will keep the corresponding information.
- uploads -> tmp : Is the path to the Temporary folder where files will be uploaded.
- uploads -> images -> : Is the path to the folder where images will be uploaded.
- uploads -> service_name -> : Provide the name of the folder where images will be uploaded.


# Importing CSVs

- Importing Parcel : There is a Demo CSV in the "test_data" folder of the Project named "parcel.csv"
- Importing Event : There is a Demo CSV in the "test_data" folder of the Project named "event.csv"
