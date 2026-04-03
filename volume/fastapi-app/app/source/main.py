# uvicorn main:app --port 8686 --host 192.168.1.108 --reload --root-path /
from   inspect import currentframe, getframeinfo;
from   typing  import Optional , List;
from   fastapi import Depends , FastAPI, File, UploadFile , Form , Request , HTTPException , status , Query , Path;
from   fastapi.staticfiles   import StaticFiles;
from   fastapi.responses     import HTMLResponse;
from   fastapi.security      import HTTPBasic, HTTPBasicCredentials;
from   fastapi.openapi.utils import get_openapi;
from   enum     import Enum;
from   pydantic import BaseModel , Field , ValidationError;
import time;
import datetime;
from   datetime import timedelta;
import os;
import os.path;
from   os import path;
from decimal import *;
import pathlib;
import aiohttp;
import aiofiles;
import asyncio;
import json as JSON;
import sys;
import random;
import hashlib;
import csv;
import psycopg2;
import models.models            as     ResModel;
import models.parametrics       as     Parametric;
from   cfg.tags                 import Tags;
from   classes.amModel          import amModel;
from   classes.amTools          import amTool;
from   classes.amAccess         import amAccess;
from   classes.amLocalization   import amLocalization;
from   classes.amAggregation    import amAggregation;
from   classes.amAggregation_db import amAggregationDB;

security         = HTTPBasic();
amTool           = amTool();
cfg              = amTool.load( "./cfg/" , "config" );
amTool.cfg       = cfg;
amAccess         = amAccess( cfg );
myModel          = amModel( cfg );
myLocale         = amLocalization( cfg );
myTags           = Tags();
myAggregation    = amAggregation( cfg );
myAggregationDB  = amAggregationDB( cfg );

fromDate_default = datetime.date.today() - timedelta( days = 1);
toDate_default   = datetime.date.today();
endpoint_tags    = myTags.list;

amTool.log( "----------------------------------------------------------" );

app = FastAPI( 
              title        = cfg["service"]["title"],
              description  = cfg["service"]["description"],
              version      = cfg["service"]["version"],
              openapi_tags = endpoint_tags , 
              redoc_url    = None , 
              # openapi_url  = "/cfg/openapi.json" , 
              docs_url     = "/" + cfg["service"]["docs_url"]
      );

app.mount(
           "/"+cfg["uploads"]["images"]["service_name"] , 
           StaticFiles( directory = cfg["uploads"]["images"]["path"] ), 
           name=cfg["uploads"]["images"]["service_name"] 
         );

def getCredentials( credentials ):
    return { "username" : credentials.username, "password" : credentials.password }

def validateDate( date_string ):
    try:
        datetime.datetime.strptime( date_string , '%Y-%m-%d %H:%M:%S' );
        return True;
    except ValueError:
        return False;

def parseStringIntoArrayWithIntegers( string ):
   myListArrayResponse = list();

   if( string is None ):
       return None;

   if( string.find(",") > 0 ):
       myList = string.split( "," );
       for item in myList : 
           if( amTool.isInt( item ) ):
               myListArrayResponse.append( item );
           else:
               print( "This is not a number" );
       return myListArrayResponse;
   else:
       if( amTool.isInt( string ) ):
           return [ string ];
       else:
           print( "This is not a number" );
           return myListArrayResponse;

def parseModelsStringIntoArray( models ):
   myListArrayResponse = list();

   if( models.find(",") > 0 ):
       myList = models.split( "," );
       for item in myList : 
           myListArrayResponse.append( item );

       return myListArrayResponse;
   else:
       return [ models ];

def logRequest( request ):
    amTool.log( request.url );

# OTHER

async def validateRequest( request , typeOfValidation ):
    response = {
     "isvalid" : False , 
     "error"   : ""
    };

    myMainsearchCriteria = "";

    for type in typeOfValidation : 
        if( type == "coords" ) : 
            if ( "longitude" in request.query_params and "latitude" in request.query_params ):
                myMainsearchCriteria = "coords";
        if( type == "locationid" ) :
            if ( "locationid" in request.query_params ) : 
                myMainsearchCriteria = "locationid";
        if( type == "parcelid" ) :
            if ( "parcelid" in request.query_params ) : 
                myMainsearchCriteria = "parcelid";

    if( myMainsearchCriteria == "" ):
        raise HTTPException( status_code = 400, detail = "Missing query parameters. At least one entity of parameters from ( "+" , ".join( typeOfValidation )+" ) must be provided." );

async def isValidApp( request: Request , credentials  : HTTPBasicCredentials = Depends( security ) ):
    appCredentials  = getCredentials( credentials );
    myOptions       = dict();
    myOptions[ "un" ] = appCredentials[ "username" ];
    myOptions[ "pw" ] = appCredentials[ "password" ];

    hasAppAccess = await amAccess.getAppAccess( myOptions );

    if( hasAppAccess is False ):
        raise HTTPException( status_code = 401 );
    else:
        await amAccess.logSession( hasAppAccess[ 0 ][ "user_id" ] , request );
        return True;

@app.middleware("http")
async def add_process_time_header( request: Request, call_next ):
    startTime = time.time();
    response  = await call_next( request );
    endTime   = time.time();
    totalTime = endTime - startTime;
    response.headers[ "X-Process-Time" ] = str( totalTime );
    amTool.log( "\"" + str( request.method ) + "\"" + " " + str( request.url ) + " (Code:" + str( response.status_code ) + ")" + " [Duration : " + str( round( totalTime ,3 ) ) + "]" );
    return response;

# Parametrics

@app.get( "/parametrics/types/{type}", 
          tags         = [ "Parametrics" ] , 
          # dependencies = [ Depends( isValidApp ) ] , 
          summary      = "Parametrics",
          description  = "Parametrics" 
        ) #Working
async def getEventTypes(
       type : ResModel.ParametricTables
    ):

    myResponse = await myModel.getParametric( type );
 
    return myResponse;

@app.get( "/parametrics/update", 
          tags         = [ "Parametrics" ] , 
          summary      = "Parametrics",
          description  = "Parametrics" 
        ) 
async def updateParametricTable():
    myResponse = await myModel.getParametricAll( );

    if len( myResponse ) == 0 : 
        raise HTTPException( 
            status_code = 500, 
            detail      = "Server Issue. Can not Update." 
        );

    fileName = "models/parametrics.py";

    myConfigParametrics = {
        "EventType"     : [ "class EventTypes( str , Enum ):\r\n" ],
        "Unit"          : [ "class Unit( str , Enum ):\r\n" ],
        "UnitReference" : [ "class UnitReference( str , Enum ):\r\n" ],
        "FuelType"      : [ "class FuelType( str , Enum ):\r\n" ]
    }

    try:
        f = open( fileName, "w" );

        f.write( "import time;\r\n" );
        f.write( "import datetime;\r\n" );
        f.write( "from datetime import timedelta;\r\n" );
        f.write( "from typing import Optional , List;\r\n" );
        f.write( "from enum import Enum;\r\n" );
        f.write( "from pydantic import BaseModel , Field , create_model;\r\n" );
        f.write( "\r\n" );

        for row in myResponse:
            if row[ "type" ] in myConfigParametrics : 
                myConfigParametrics[ row[ "type" ] ].append( "\t\t\t\t" + str( row[ "value" ] ).upper() + " = \"" + str( row[ "value" ] ).lower()+ "\";\r\n" );

        for cfg in myConfigParametrics : 
            f.writelines( myConfigParametrics[ cfg ] );
            f.write( "\r\n" );

        f.close();
        return { "res" : "success" };
    except( Exception ) as error :
        raise HTTPException( 
            status_code = 500, 
            detail      = "Server Issue. File Issue." 
        );

# Parcel Actions : Create , Delete , Update , Select

@app.get( "/parcel/ids/{id}", 
          tags           = [ "Parcels" ] , 
          # dependencies   = [ Depends( isValidApp ) ] , 
          summary        = "Retrieve Parcel from Database",
          description    = "Retrieve Parcel from Database",
          response_model = List[ ResModel.Parcel ] 
        ) #Working
async def getParcelById(
                 request    : Request
               , id         : str
               , limit      : Optional[ int ] = 10
               , offset     : Optional[ int ] = 0
          ):
 
    myResponse = [];
    
    myParcelsArray = id.split( "," );
    
    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Retrieving Parcels from Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.getParcel( myParcelsArray , "id" , limit , offset );

    return myResponse;

@app.get( "/parcel/name/{name}", 
          tags           = [ "Parcels" ] , 
          # dependencies   = [ Depends( isValidApp ) ] , 
          summary        = "Retrieve Parcel from Database",
          description    = "Retrieve Parcel from Database",
          response_model = List[ ResModel.Parcel ] 
        ) #Working
async def getParcelByName(
                 request    : Request
               , name       : str
               , limit      : Optional[ int ] = 10
               , offset     : Optional[ int ] = 0
          ):
 
    myResponse = [];

    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Retrieving Parcels from Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.getParcel( name , "name" , limit , offset );

    return myResponse;

@app.get( "/parcel/user/{user}", 
          tags           = [ "Parcels" ] , 
          # dependencies   = [ Depends( isValidApp ) ] , 
          summary        = "Retrieve Parcel from Database",
          description    = "Retrieve Parcel from Database",
          response_model = List[ ResModel.Parcel ] 
        ) #Working
async def getParcelByUser(
                 request    : Request
               , user       : str
               , limit      : Optional[ int ] = 10
               , offset     : Optional[ int ] = 0
          ):

    myResponse = [];

    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Retrieving Parcels from Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.getParcel( user , "user" , limit , offset );

    return myResponse;

@app.get( "/parcel/country/{country}", 
          tags           = [ "Parcels" ] , 
          # dependencies   = [ Depends( isValidApp ) ] , 
          summary        = "Retrieve Parcel from Database",
          description    = "Retrieve Parcel from Database",
          response_model = List[ ResModel.Parcel ] 
        ) #Working
async def getParcelByCountry(
                 request    : Request
               , country    : str
               , limit      : Optional[ int ] = 10
               , offset     : Optional[ int ] = 0
          ):
 
    myResponse = [];
    
    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Retrieving Parcels from Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.getParcel( country , "country" , limit , offset );

    return myResponse;

@app.get( "/parcel/county/{county}", 
          tags           = [ "Parcels" ] , 
          # dependencies   = [ Depends( isValidApp ) ] , 
          summary        = "Retrieve Parcel from Database",
          description    = "Retrieve Parcel from Database",
          response_model = List[ ResModel.Parcel ] 
        ) #Working
async def getParcelByCounty(
                 request    : Request
               , county     : str
               , limit      : Optional[ int ] = 10
               , offset     : Optional[ int ] = 0
          ):
 
    myResponse = [];
    
    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Retrieving Parcels from Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.getParcel( county , "county" , limit , offset );

    return myResponse;

@app.get( "/parcel/dat", 
          tags           = [ "Parcels" ] , 
          # dependencies   = [ Depends( isValidApp ) ] , 
          summary        = "Retrieve Parcel from Database",
          description    = "Retrieve Parcel from Database",
          response_model = List[ ResModel.Parcel ] 
        ) #Working
async def getParcelByDat(
                 request    : Request
               , dat        : str
               , limit      : Optional[ int ] = 10
               , offset     : Optional[ int ] = 0
          ):
 
    myResponse = [];
    
    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Retrieving Parcels from Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.getParcelByDAT( dat , limit , offset );

    return myResponse;

@app.put( "/parcel", 
          tags         = [ "Parcels" ] , 
          # dependencies = [ Depends( isValidApp ) ] , 
          summary      = "Add a Parcel in Database",
          description  = "Add a Parcel in Database" 
        ) #Working
async def addParcel(
                 request : Request
               , name    : str  = None
               , polygon : str = "POLYGON((23.9450328078221 40.76302784325,23.9450894016528 40.7640470723677,23.9453283533882 40.7646519345938,23.945674204585 40.7649996088149,23.9461458198534 40.7654377709961,23.9464413654214 40.7658759302886,23.9466614525461 40.766456963156,23.9467997930249 40.7665712641057,23.9475795302708 40.765975944504,23.946843810452 40.7652996549675,23.946604858716 40.7650424726334,23.9460640732081 40.7645804944596,23.9458628506938 40.7642994958554,23.9457056456045 40.7640375469339,23.9456616281802 40.7634564929139,23.945655339977 40.7632516939747,23.9455232877018 40.7631421500972,23.9454478292589 40.7630468944047,23.9452591831513 40.7630278432499,23.9451145544687 40.7630421316166,23.9450328078221 40.76302784325))"
               , uid     : Optional[ str ] = None
               , user    : Optional[ str ] = "guest"
          ):

    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Adding Parcel to Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.addParcel( name , polygon , user , uid );

    if "error" in myResponse:
        if( myResponse[ "error" ] == "duplicate" ):
            raise HTTPException( 
                status_code = 400, 
                detail      = "Entry already exists" 
            );
        else:
            return myResponse;
    else:
        return myResponse;

@app.delete( "/parcel", 
          tags         = [ "Parcels" ] , 
          # dependencies = [ Depends( isValidApp ) ] , 
          summary      = "Delete a Parcel from the Database",
          description  = "Delete a Parcel from the Database" 
        ) 
async def deleteParcel( 
                 id   : str
          ):

    myResponse = [];
    myIdsArray = id.split( "," );

    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Deleting Parcel from Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.deleteParcel( myIdsArray );

    return myResponse;

@app.post( "/parcel", 
          tags         = [ "Parcels" ] , 
          # dependencies = [ Depends( isValidApp ) ] , 
          summary      = "Update a Parcel in the Database",
          description  = "Update a Parcel in the Database" 
        ) #Working
async def updateParcel(
                 request    : Request
               , id         : Optional[ str ] = None
               , name       : Optional[ str ] = None
               , polygon    : Optional[ str ] = "POLYGON((23.9450328078221 40.76302784325,23.9450894016528 40.7640470723677,23.9453283533882 40.7646519345938,23.945674204585 40.7649996088149,23.9461458198534 40.7654377709961,23.9464413654214 40.7658759302886,23.9466614525461 40.766456963156,23.9467997930249 40.7665712641057,23.9475795302708 40.765975944504,23.946843810452 40.7652996549675,23.946604858716 40.7650424726334,23.9460640732081 40.7645804944596,23.9458628506938 40.7642994958554,23.9457056456045 40.7640375469339,23.9456616281802 40.7634564929139,23.945655339977 40.7632516939747,23.9455232877018 40.7631421500972,23.9454478292589 40.7630468944047,23.9452591831513 40.7630278432499,23.9451145544687 40.7630421316166,23.9450328078221 40.76302784325))"
               , user       : Optional[ str ] = "guest"
          ):

    myResponse = [];
    myParcelsArray = id.split( "," );

    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Updating Parcel to Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.updateParcel( myParcelsArray , name , polygon );
    if( "error" in myResponse ):
        raise HTTPException( 
            status_code = 400, 
            detail      = "Invalid Parcel ID." 
        );
    else:
        return myResponse;

# Calendar Actions 

@app.put( "/event", 
          tags         = [ "Calendar" ] , 
          # dependencies = [ Depends( isValidApp ) ] , 
          summary      = "Add an Event",
          description  = "Add an Event" 
        ) #Working
async def addEvent( request : List[ ResModel.Event ] ):
 
    myResponse = [];

    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Adding Event to Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.addEvent( request );

    return myResponse;

@app.get( "/event/id/{event_id}", 
          tags         = [ "Calendar" ] , 
          # dependencies = [ Depends( isValidApp ) ] , 
          summary      = "Get Event By ID",
          description  = "Get Event By ID" 
        ) #Working
async def getEventById( event_id : Optional[int] = None ):

    myResponse = [];

    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Retrieving Event from Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.getEventById( event_id );

    return myResponse;

@app.get( "/event", 
          tags         = [ "Calendar" ] , 
          # dependencies = [ Depends( isValidApp ) ] , 
          summary      = "Get Event By Properties",
          description  = "Get Event By Properties" 
        ) #Working
async def getEvent( 
        event_type : Optional[ str ] = None
      , parcelid   : Optional[ str ] = None
      , fromdate   : Optional[ str ] = None
      , todate     : Optional[ str ] = None
    ):

    myResponse = [];

    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Retrieving Event from Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.getEvent( event_type , fromdate , todate , parcelid );

    return myResponse;

@app.delete( "/event", 
          tags         = [ "Calendar" ] , 
          # dependencies = [ Depends( isValidApp ) ] , 
          summary      = "Delete an Event",
          description  = "Delete an Event" 
        ) #Working
async def deleteEvent( 
      id : int
    ):

    myResponse = [];

    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Deleting Event from Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.deleteEvent( id );

    return myResponse;

@app.post( "/event", 
          tags         = [ "Calendar" ] , 
          # dependencies = [ Depends( isValidApp ) ] , 
          summary      = "Update Event in Database",
          description  = "Update Event in Database" 
        ) #Working
async def updateEvent(
                 request : ResModel.Event
               , id      : Optional[ int ]
          ):

    myResponse = [];

    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Updating Event to Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.updateEvent( id , request );
    if( "error" in myResponse ):
        raise HTTPException( 
            status_code = 400, 
            detail      = "Invalid Event ID." 
        );
    else:
        return myResponse;

# Measurement Actions 

@app.put( "/measurement", 
          tags         = [ "Measurements" ] , 
          # dependencies = [ Depends( isValidApp ) ] , 
          summary      = "Add an Event",
          description  = "Add an Event" 
        ) #Working
async def addMeteoMeasurement( request : List[ ResModel.MeteoData ] ):
 
    myResponse = [];

    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Adding Event to Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.addMeteoMeasurement( request );

    return myResponse;

@app.get( "/measurement/id/{event_id}", 
          tags         = [ "Measurements" ] , 
          # dependencies = [ Depends( isValidApp ) ] , 
          summary      = "Get Event By ID",
          description  = "Get Event By ID" 
        ) #Working
async def getMeasurementById( event_id : int ):

    myResponse = [];

    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Retrieving Event from Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.getMeasurementById( event_id );

    return myResponse;

@app.get( "/measurement", 
          tags         = [ "Measurements" ] , 
          # dependencies = [ Depends( isValidApp ) ] , 
          summary      = "Get Event By Properties",
          description  = "Get Event By Properties" 
        ) #Working
async def getMeteoMeasurement( 
        parcelId   : Optional[ str ] = None
      , fromdate   : Optional[ str ] = None
      , todate     : Optional[ str ] = None
    ):

    myResponse = [];

    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Retrieving Event from Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.getMeteoMeasurement( fromdate , todate , parcelId );

    return myResponse;

@app.delete( "/measurement", 
          tags         = [ "Measurements" ] , 
          # dependencies = [ Depends( isValidApp ) ] , 
          summary      = "Delete an Event",
          description  = "Delete an Event" 
        ) #Working
async def deleteMeteoMeasurement( 
      id : int
    ):

    myResponse = [];

    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Deleting Event from Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.deleteMeteoMeasurement( id );

    return myResponse;

@app.post( "/measurement", 
          tags         = [ "Measurements" ] , 
          # dependencies = [ Depends( isValidApp ) ] , 
          summary      = "Update Event in Database",
          description  = "Update Event in Database" 
        ) #Working
async def updateMeteoMeasurement(
                 request : ResModel.MeteoData 
               , id      : Optional[ int ]
          ):

    myResponse = [];

    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    amTool.log( "--- Updating Event to Database ---" , cfg[ "settings" ][ "debug" ] );
    myResponse = await myModel.updateMeteoMeasurement( id , request );
    if( "error" in myResponse ):
        raise HTTPException( 
            status_code = 400, 
            detail      = "Invalid Event ID." 
        );
    else:
        return myResponse;

# Aggregation Actions on Parcels

@app.get( "/parcels/{parcelid}/aggregations/", 
          tags         = [ "Aggregation" ] , 
          # dependencies = [ Depends( isValidApp ) ] , 
          summary      = "Get aggregated event data",
          description  = "Get aggregated event data ( Sum of Irrigations , etc ) for a single or a collection of parcels." 
        ) #Working
async def getAggregations(
                 request              : Request
               , parcelid             : str
               , evt_type             : Parametric.EventTypes
               , aggregation_function : ResModel.AggregationFunctions
               , fromdate             : datetime.date = "2020-01-01"
               , todate               : datetime.date = "2025-01-01"
          ):

    myResponse = {};

    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    # myParcelsArray = parseStringIntoArrayWithIntegers( parcelid );
    myParcelsArray = parcelid.split( "," );
    myResponse     = await myAggregationDB.getMetricAggregations( {
      "fn"           : aggregation_function , 
      "parcel"       : myParcelsArray , 
      "type"         : evt_type , 
      "fromdate"     : fromdate ,
      "todate"       : todate 
    } );

    if( "error" not in myResponse ) : 
        return myResponse;
    else:
        return {
          "error"  : "Failed to retrieve Events" 
        };

@app.get( "/parcels/{parcelid}/meteoaggregations/", 
          tags         = [ "Aggregation" ] , 
          # dependencies = [ Depends( isValidApp ) ] , 
          summary      = "Get aggregated Meteo data",
          description  = "Get aggregated Meteo data ( Sum of RainFall , etc ) for a single or a collection of parcels." 
        ) #Working
async def getMeasurementAggregations(
                 request              : Request
               , parcelid             : str
               , measurement_type     : Parametric.MeteoMeasurementTypes
               , aggregation_function : ResModel.AggregationFunctions
               , fromdate             : datetime.date = "2020-01-01"
               , todate               : datetime.date = "2025-01-01"
          ):

    myResponse = {};

    if( cfg[ "settings" ][ "debug" ] is True ):
        print( "" , flush=True );

    myParcelsArray = parcelid.split( "," );
    myResponse     = await myAggregationDB.getMeasurementAggregations( {
      "fn"           : aggregation_function , 
      "parcel"       : myParcelsArray , 
      "type"         : measurement_type , 
      "fromdate"     : fromdate ,
      "todate"       : todate 
    } );

    if( "error" not in myResponse ) : 
        return myResponse;
    else:
        return {
          "error"  : "Failed to retrieve Events" 
        };

@app.get( "/parcels/{parcelid}/chilling-days/", 
          tags         = [ "Aggregation" ] , 
          # dependencies = [ Depends( isValidApp ) ] , 
          summary      = "Get Chilling Days",
          description  = "Provides the Chilling days based on user defined thresholds." 
        ) #Working
async def getChillingDays(
                 request                 : Request
               , parcelid                : str
               , fromdate                : datetime.date   = fromDate_default
               , todate                  : datetime.date   = toDate_default
               , chilling_low_threshold  : Optional[ int ] = 2
               , chilling_high_threshold : Optional[ int ] = 7 
          ):

    myChillingData = await myModel.getChillingDays( {
      "parcelId"       : parcelid,
      "fromDate"       : fromdate ,
      "toDate"         : todate , 
      "lowlimit"       : chilling_low_threshold , 
      "highlimit"      : chilling_high_threshold ,
      "limit"          : 86400,
      "offset"         : 0
    } );

    myResponse = {
      "from_date"    : fromdate,
      "to_date"      : todate,
      "parcelId"     : parcelid , 
      "data"         : []
    }

    if( "error" not in myChillingData ) : 
        if( len( myChillingData ) > 0 ):
            myNewDataSet      = [];
            myCumulativeIndex = 0;
            mySum             = 0;
            for record in myChillingData:
                myTemp = 0 if (record[ "temperature" ] is None) else record[ "temperature" ];
                mySum  = float( mySum ) + float( myTemp );
                if( int( record[ "chilled" ] ) == 1 ):
                    myCumulativeIndex = myCumulativeIndex + 1;

                    myNewDataSet.append( {
                        "timestamp"   : record[ "timestamp" ] , 
                        "temperature" : record[ "temperature" ] , 
                        "index"       : myCumulativeIndex , 
                        "chill"       : record[ "chilled" ]
                    } );
            myResponse[ "data" ] = myNewDataSet;
        return myResponse;
    else:
        return {
          "error"  : "Failed to retrieve Measurements" 
        };

# Imports
@app.post( "/import/parcel", 
          tags           = [ "Imports" ] , 
          # dependencies   = [ Depends( isValidApp ) ] , 
          summary        = "Import from Various Sources",
          description    = "Import from Various Sources"
          # ,response_model = List[ ResModel.Parcel ] 
        ) #Working
async def uploadParcel(
              username : str ,
              filedata : UploadFile = File(...) 
          ):

    uploadsPath = cfg[ "uploads" ][ "tmp" ][ "path" ];
    newFileName = amTool.getUID();
    extension   = ".csv";
    if( filedata.content_type != "text/csv" ) : 
        raise HTTPException( 
          status_code = 400, 
          detail      = "Only CSV is permitted for upload" 
        );

    newFilePath = f"{uploadsPath}{newFileName}{extension}";
    amTool.log( "[ INFO ] : [ uploadsPath ] = " + str( uploadsPath ) );
    amTool.log( "[ INFO ] : [ extension ] = " + str( extension ) );
    amTool.log( "[ INFO ] : [ newFilePath ] = " + str( newFilePath ) );

    myArrayOfParcels = [];

    try:
        with open( newFilePath , "wb+" ) as newFileHandler:
            newFileHandler.write( filedata.file.read() );
    except( Exception ) as error :
        amTool.log( "[ ERROR - Line 802 ] : Failed to Write File." );
        amTool.log( error );

    try:
        with open( newFilePath , newline='') as csvfile:
            spamreader = csv.reader( csvfile, delimiter = ';', quotechar = '"' );
            for index , row in enumerate( spamreader ):
                if( index > 0 ) :
                    if( len( row ) > 0 ):
                        myUID          = None if len( row ) <= 2 else row[ 2 ];
                        myParcelObject = {
                          "name"    : row[ 0 ],
                          "polygon" : row[ 1 ],
                          "user"    : username,
                          "uid"     : myUID
                        }

                        myArrayOfParcels.append( myParcelObject );
    except( Exception ) as error :
        amTool.log( "[ ERROR - Line 821 ] : Failed to Open created File in Disk for parsing." );
        amTool.log( error );

    amTool.log( "--- Adding Parcel to Database ---" , cfg[ "settings" ][ "debug" ] );

    myResponse = [];

    try:
        for parcel in myArrayOfParcels:
            parcel[ "polygon" ] = parcel[ "polygon" ].replace( "POLYGON ((" , "POLYGON((" );
            myAddResponse = await myModel.addParcel( 
              parcel[ "name" ] , 
              parcel[ "polygon" ] , 
              parcel[ "user" ] ,
              parcel[ "uid" ] 
            );

            if "error" in myAddResponse:
                if( myAddResponse[ "error" ] == "duplicate" ):
                    myResponse.append( { "name" : parcel[ "name" ] , "error" : "duplicate" } );
                else:
                    myResponse.append( { "name" : parcel[ "name" ] , "error" : myAddResponse[ "error" ] } );
            else:
                myResponse.append( { "name" : parcel[ "name" ] , "id" : myAddResponse[ "id" ] } );
    except( Exception ) as error : 
        amTool.log( "[ ERROR - Line 846 ] : Failed to add Parcels in the Database." );
        amTool.log( error );

    try:
        if len( myArrayOfParcels ) > 0 :
            pathlib.Path.unlink( newFilePath );
    except( Exception ) as error:
        amTool.log( "[ ERROR - Line 853 ] : Failed to remove Uploaded file from temporary directory." );
        amTool.log( error );

    return myResponse;

@app.post( "/import/event", 
          tags           = [ "Imports" ] , 
          # dependencies   = [ Depends( isValidApp ) ] , 
          summary        = "Import from Various Sources",
          description    = "Import from Various Sources"
          # ,response_model = List[ ResModel.Parcel ] 
        ) #Working
async def uploadEvent(
              parcelid : str ,
              filedata : UploadFile = File(...) 
          ):

    uploadsPath = cfg[ "uploads" ][ "tmp" ][ "path" ];
    newFileName = amTool.getUID();
    extension   = ".csv";
    if( filedata.content_type != "text/csv" ) : 
        raise HTTPException( 
          status_code = 400, 
          detail      = "Only CSV is permitted for upload" 
        );

    newFilePath = f"{uploadsPath}{newFileName}{extension}";
    amTool.log( "[ INFO ] : [ uploadsPath ] = " + str( uploadsPath ) );
    amTool.log( "[ INFO ] : [ extension ] = " + str( extension ) );
    amTool.log( "[ INFO ] : [ newFilePath ] = " + str( newFilePath ) );

    errorArray  = [];

    try:
        with open( newFilePath , "wb+" ) as newFileHandler:
            newFileHandler.write( filedata.file.read() );
    except( Exception ) as error :
        print( error );

    try:
        with open( newFilePath , newline='') as csvfile:
            spamreader = csv.reader( csvfile, delimiter = ';', quotechar = '"' );
            myArrayOfEvents = [];
            for index , row in enumerate( spamreader ):
                if( index > 0 ) : 
                    if( len( row ) > 0 ):
                        myProperties  = ResModel.EventProperties(
                            amount          = row[ 8 ],
                            unit            = row[ 9 ],
                            unitRef         = row[ 10 ],
                            metric          = row[ 11 ],
                            target          = None if row[ 12 ] == "" else row[ 12 ],
                            productName     = None if row[ 13 ] == "" else row[ 13 ],
                            stage           = None if row[ 14 ] == "" else row[ 14 ],
                            fuelConsumption = None if row[ 15 ] == "" else row[ 15 ],
                            fuelType        = None if row[ 16 ] == "" else row[ 16 ],
                            fuelUnit        = None if row[ 17 ] == "" else row[ 17 ],
                            fuelUnitRef     = None if row[ 18 ] == "" else row[ 18 ]
                        );
                        myEventObject = ResModel.Event( 
                            dat                        = row[ 0 ],
                            eventStart                 = row[ 1 ],
                            eventEnd                   = row[ 2 ],
                            duration                   = row[ 3 ],
                            type                       = row[ 4 ],
                            crop                       = row[ 5 ],
                            variety                    = row[ 6 ],
                            comments                   = row[ 7 ],
                            properties                 = myProperties , 
                            parcelId                   = parcelid
                        );
                        myArrayOfEvents.append( myEventObject );
    except( ValidationError ) as error : 
        amTool.log( "[ ERROR ] : Validation Error" , cfg[ "settings" ][ "debug" ] );
        if len( error.errors() ) > 0 :
            for err in error.errors():
                myError = { 
                  "field" : "",
                  "msg"   : "",
                  "provided_value" : ""
                };

                myError[ "field" ]          = err[ "loc" ][ 0 ];
                myError[ "msg" ]            = err[ "msg" ];
                myError[ "provided_value" ] = err[ "input" ];
                errorArray.append( myError );
        else:
            errorArray.append( { "msg" : "No errors" } );
    except( Exception ) as error :
        amTool.log( "[ ERROR ] : Validation Error" , cfg[ "settings" ][ "debug" ] );
        amTool.log( error , cfg[ "settings" ][ "debug" ] );
        errorArray.append( { "msg" : "Generic Error" } );

    if len( myArrayOfEvents ) > 0 and len( errorArray ) <= 0 :
        amTool.log( "--- Adding Event to Database ---" , cfg[ "settings" ][ "debug" ] );

        # for index , item in enumerate( myArrayOfEvents ):
            # print( myArrayOfEvents[ index ].dat );

        myResponse = await myModel.addEvent( myArrayOfEvents );
    else:
        myResponse = { "error" : errorArray };

    try:
        if len( myArrayOfEvents ) > 0 :
            pathlib.Path.unlink( newFilePath );
    except( Exception ) as error:
        amTool.log( "[ ERROR - Line 959 ] : Failed to remove Uploaded file from temporary directory." );
        amTool.log( error );

    return myResponse;

@app.post( "/import/meteo", 
          tags           = [ "Imports" ] , 
          # dependencies   = [ Depends( isValidApp ) ] , 
          summary        = "Import from Various Sources",
          description    = "Import from Various Sources"
          # ,response_model = List[ ResModel.Parcel ] 
        ) #Working
async def uploadMeteo(
              parcelid : str ,
              filedata : UploadFile = File(...) 
          ):
    
    myResponse  = {};
    uploadsPath = cfg[ "uploads" ][ "tmp" ][ "path" ];
    newFileName = amTool.getUID();
    extension   = ".csv";
    if( filedata.content_type != "text/csv" ) : 
        raise HTTPException( 
          status_code = 400, 
          detail      = "Only CSV is permitted for upload" 
        );

    newFilePath = f"{uploadsPath}{newFileName}{extension}";
    amTool.log( "[ INFO ] : [ uploadsPath ] = " + str( uploadsPath ) );
    amTool.log( "[ INFO ] : [ extension ] = " + str( extension ) );
    amTool.log( "[ INFO ] : [ newFilePath ] = " + str( newFilePath ) );

    errorArray  = [];

    try:
        with open( newFilePath , "wb+" ) as newFileHandler:
            newFileHandler.write( filedata.file.read() );
    except( Exception ) as error :
        print( error );

    try:
        with open( newFilePath , newline='') as csvfile:
            spamreader = csv.reader( csvfile, delimiter = ';', quotechar = '"' );
            myArrayOfEvents = [];
            for index , row in enumerate( spamreader ):
                if( index > 0 ) : 
                    if( len( row ) == 6 ):
                        myEventObject = ResModel.MeteoData( 
                            parcelId      = parcelid,
                            timestamp     = row[ 0 ],
                            temperature   = row[ 1 ],
                            humidity      = row[ 2 ],
                            windstrength  = row[ 3 ],
                            leafwetness   = row[ 4 ],
                            rain          = row[ 5 ]
                        );

                        myArrayOfEvents.append( myEventObject );
                    else: 
                        print( row );
    except( ValidationError ) as error : 
        amTool.log( "[ ERROR ] : Validation Error. 1st Exception" , cfg[ "settings" ][ "debug" ] );
        print( error );
        if len( error.errors() ) > 0 :
            for err in error.errors():
                myError = { 
                  "field" : "",
                  "msg"   : "",
                  "provided_value" : ""
                };

                myError[ "field" ]          = err[ "loc" ][ 0 ];
                myError[ "msg" ]            = err[ "msg" ];
                myError[ "provided_value" ] = err[ "input" ];
                errorArray.append( myError );
        else:
            errorArray.append( { "msg" : "No errors" } );
    except( Exception ) as error :
        amTool.log( "[ ERROR ] : Validation Error. 2nd Exception" , cfg[ "settings" ][ "debug" ] );
        amTool.log( error , cfg[ "settings" ][ "debug" ] );
        errorArray.append( { "msg" : "Generic Error" } );

    if len( myArrayOfEvents ) > 0 and len( errorArray ) <= 0 :
        amTool.log( "--- Adding Measurement to Database ---" , cfg[ "settings" ][ "debug" ] );
        myResponse = await myModel.addMeteoMeasurementCSV( myArrayOfEvents );
    else:
        myResponse = { "error" : errorArray };

    try:
        pathlib.Path.unlink( newFilePath );
        amTool.log( "[ INFO ] : File [ " + newFilePath + " ] succesfully removed from storage." );
    except( Exception ) as error:
        amTool.log( "[ ERROR - Line 1045 ] : Failed to remove Uploaded file from temporary directory." );
        amTool.log( error );

    return myResponse;