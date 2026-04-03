import os;
import datetime;
import time;
import sys;
import aiohttp;
import asyncio;
import psycopg2;
import base64;
import hashlib;
import re;
from psycopg2 import sql;
from psycopg2.extras import RealDictCursor;
import csv;
import json as JSON;
from classes.amTools import amTool;

class amModel:
 def __init__( self , cfg ):
  """Class for Queryinjg Database"""
  self.amTool = amTool();
  self.amTool.log( "Model Initiated" );
  self.cfg    = cfg;
  self.debug  = True;

 def executeQuery( self , query , customConnectionString = None , type="select"):
    connection = False;
    cursor     = False;
    try: 
       if( customConnectionString is not None ):
           connection = psycopg2.connect( user     = customConnectionString["user"],
                                          password = customConnectionString["password"],
                                          host     = customConnectionString["host"],
                                          port     = customConnectionString["port"],
                                          database = customConnectionString["database"] );
       else:
           connection = psycopg2.connect( user     = self.cfg["database"]["connection"]["user"],
                                          password = self.cfg["database"]["connection"]["password"],
                                          host     = self.cfg["database"]["connection"]["host"],
                                          port     = self.cfg["database"]["connection"]["port"],
                                          database = self.cfg["database"]["connection"]["database"] );

       cursor = connection.cursor( cursor_factory = RealDictCursor );
       cursor.execute( query );

       if( type == "select" ):
           my_query_response = cursor.fetchall();
       elif( type == "insert" ):
           my_query_response = cursor.fetchone();
       else:
           my_query_response = { "success" : "ok"  };

       # if( self.debug is True ) :
           # print( "[ Query ] : \r\n" + str( cursor.query ) + "\r\n" );

       cursor.close();
       connection.commit();

       return my_query_response;

    except( Exception, psycopg2.Error ) as error :
        self.amTool.logFile( error );
        if( self.debug is True ) :
            print( error );

        if( error.pgcode == "23505" ):
            return { "error" : "duplicate" , "code" : error.pgcode };
        else:
            return [];

    finally:
        if( connection ):
            connection.close();
            if( self.debug is True ) :
                print( "["+__name__+"] : DB Connection Closed" );

## Parcels

 async def getParcel( self , value , type="id" , limit=None , offset=None ):
    mySchema = self.cfg["database"]["schema"];
    myLimit   = "" if ( limit is None )  else ( "limit " + str( limit ) );
    myOffset  = "" if ( offset is None ) else ( "offset " + str( offset ) );
    
    myWhereClause = "";
    myValue       = None;

    if( type == "id" ) : 
        myValue       = "','".join( value );
        myWhereClause = "where uid in ('" + myValue + "') ";
    elif( type == "user" ) : 
        myWhereClause = "where \"user\" = {myValue_param} ";
    elif( type == "country" ) : 
        myWhereClause = "where country = {myValue_param} ";
    elif( type == "county" ) : 
        myWhereClause = "where county = {myValue_param} ";
    elif( type == "name" ) : 
        myWhereClause = "where name = {myValue_param} ";
    elif( type == "dat" ) : 
        myWhereClause = "where dat = {myValue_param} ";

    myQuery  = ( "select " + 
                  "id , " + 
                  "name , " + 
                  "ST_AsText( polygon ) as polygon , " + 
                  "country , " + 
                  "county , " + 
                  "ektaria , " + 
                  # "dat , " + 
                  "\"user\" , " + 
                  "\"uid\" " + 
                 "from {mySchema_param}.parcel " + 
                 myWhereClause + 
                 "order by id DESC " + 
                 str( myLimit ) + " " + str( myOffset ) + 
                 ";" );

    if myValue is None : 
        myValue = value;

    qData    = sql.SQL( myQuery ).format( 
                   mySchema_param = sql.Identifier( mySchema ),
                   myValue_param  = sql.Literal( myValue )
               );

    myResponse = self.executeQuery( qData );

    return myResponse;

 async def getParcelByDAT( self , dat=None , limit=None , offset=None ):
    mySchema = self.cfg["database"]["schema"];
    myLimit   = "" if ( limit is None )  else ( "limit " + str( limit ) );
    myOffset  = "" if ( offset is None ) else ( "offset " + str( offset ) );

    myQuery  = ( "select " + 
                 "parcel.id ," + 
                 "parcel.name ," + 
                 "ST_AsText(parcel.polygon) as polygon ," + 
                 "parcel.country ," + 
                 "parcel.county ," + 
                 "parcel.ektaria ," + 
                 "parcel.\"user\" ," + 
                 "parcel.\"uid\" " + 
                "from " + 
                 "{mySchema_param}.parcel parcel " + 
                "inner join {mySchema_param}.\"event\" evt on evt.\"parcelId\" = parcel.uid " + 
                "where evt.dat = {myDat_param} " + 
                "group by parcel.id ," + 
                 "parcel.name ," + 
                 "ST_AsText(parcel.polygon) ," + 
                 "parcel.country ," + 
                 "parcel.county ," + 
                 "parcel.ektaria ," + 
                 "parcel.\"user\" ," + 
                 "parcel.\"uid\" " + 
                "order by parcel.id desc " + 
                 str( myLimit ) + " " + str( myOffset ) + 
                 ";" );

    qData    = sql.SQL( myQuery ).format( 
                   mySchema_param = sql.Identifier( mySchema ),
                   myDat_param    = sql.Literal( dat )
               );

    myResponse = self.executeQuery( qData );

    return myResponse;


 async def addParcel( self , name=None , polygon=None , user=None , uid=None ):
    mySchema = self.cfg[ "database" ][ "schema" ];

    myEktaria  = await self.getEktariaFromPolygon( polygon );

    posOfComma = re.search( "," , polygon );
    myPolygon  = polygon[ 9 : posOfComma.start() ];
    myPoint    = myPolygon.split( " " );
    # myGeoData  = await self.getGeoDetailsFromPoint( myPoint[ 0 ] , myPoint[ 1 ] );
    myGeoData = {
        "address" : {
            "county"  : "",   
            "country" : ""
        }
    }

    if "county" not in myGeoData[ "address" ] : 
        county = "";
    else:
        county = myGeoData[ "address" ][ "county" ];
    
    if "country" not in myGeoData[ "address" ] : 
        country = "";
    else:
        country = myGeoData[ "address" ][ "country" ];

    myUniqueString = str( time.time() ) + str( myEktaria ) + str( user ) + str( name );
    myHash = hashlib.sha256();
    myHash.update( bytes( myUniqueString , "utf-8" ) );
    myUID = myHash.hexdigest();
    if( uid is not None ):
        myUID = uid;

    myQuery  = ( "insert into {mySchema_param}.parcel " + 
                 # " ( name , polygon , country , county , ektaria , dat , \"user\" , \"uid\" ) " + 
                 " ( name , polygon , country , county , ektaria , \"user\" , \"uid\" ) " + 
                 " VALUES " + 
                 " ( " + 
                   " {myName_param} , " + 
                   " {myPolygon_param} , " + 
                   " {myCountry_param} , " + 
                   " {myCounty_param} , " + 
                   " {myEktaria_param} , " + 
                   # " {myDat_param} , " + 
                   " {myUser_param} , " + 
                   " {myUid_param} " + 
                 ") RETURNING ID;" 
               );

    qData    = sql.SQL( myQuery ).format( 
                   mySchema_param  = sql.Identifier( mySchema ),
                   myName_param    = sql.Literal( name ),
                   myPolygon_param = sql.Literal( polygon ),
                   myCountry_param = sql.Literal( country ),
                   myCounty_param  = sql.Literal( county ),
                   myEktaria_param = sql.Literal( myEktaria ),
                   # myDat_param     = sql.Literal( dat ),
                   myUser_param    = sql.Literal( user ),
                   myUid_param     = sql.Literal( myUID )
               );

    myResponse = self.executeQuery( qData , None , "insert" );

    return myResponse;

 async def updateParcel( self , id=None , name=None , polygon=None ):
    mySchema = self.cfg[ "database" ][ "schema" ];

    myParcel  = await self.getParcel( id );
    if( len( myParcel ) <= 0 ):
        return { "error" : "" };

    myUpdates = {
      "uid"     : myParcel[ 0 ][ "uid" ],
      "name"    : myParcel[ 0 ][ "name" ],
      "polygon" : myParcel[ 0 ][ "polygon" ]
    }

    if( name is not None ):
        myUpdates[ "name" ] = name;
    if( polygon is not None ):
        myUpdates[ "polygon" ] = polygon;
        myUpdates[ "ektaria" ] = await self.getEktariaFromPolygon( polygon );
        posOfComma = re.search( "," , polygon );
        myPolygon  = polygon[ 9 : posOfComma.start() ];
        myPoint    = myPolygon.split( " " );
        myGeoData  = await self.getGeoDetailsFromPoint( myPoint[ 0 ] , myPoint[ 1 ] );
        if "county" not in myGeoData[ "address" ] : 
            myUpdates[ "county" ] = "";
        else:
            myUpdates[ "county" ] = myGeoData[ "address" ][ "county" ];
        
        if "country" not in myGeoData[ "address" ] : 
            myUpdates[ "country" ] = "";
        else:
            myUpdates[ "country" ]    = myGeoData[ "address" ][ "country" ];

    myResponse = [];

    myQuery  = ( "update {mySchema_param}.parcel " + 
                 " set " + 
                 " name     = {myName_param} , " + 
                 " polygon  = {myPolygon_param} , " + 
                 " country  = {myCountry_param} , " + 
                 " county   = {myCounty_param} , " + 
                 " ektaria  = {myEktaria_param} " + 
                 # " dat      = {myDat_param} " + 
                 "where uid = {myId_param};" );

    qData    = sql.SQL( myQuery ).format( 
                   mySchema_param  = sql.Identifier( mySchema ),
                   myId_param      = sql.Literal( myUpdates[ "uid" ] ),
                   myName_param    = sql.Literal( myUpdates[ "name" ] ),
                   myPolygon_param = sql.Literal( myUpdates[ "polygon" ] ),
                   myCountry_param = sql.Literal( myUpdates[ "country" ] ),
                   myCounty_param  = sql.Literal( myUpdates[ "county" ] ),
                   myEktaria_param = sql.Literal( myUpdates[ "ektaria" ] )
                   # ,myDat_param     = sql.Literal( myUpdates[ "dat" ] )
               );

    myResponse = self.executeQuery( qData , None , "update" );

    return myResponse;

 async def deleteParcel( self , id ):
    mySchema = self.cfg[ "database" ][ "schema" ];
    myQuery  = ( "delete from {mySchema_param}.parcel where uid in ( '" + "','".join( id ) + "' );" );
    qData    = sql.SQL( myQuery ).format( 
                   mySchema_param  = sql.Identifier( mySchema )
               );

    myResponse = self.executeQuery( qData , None , "delete" );

    return myResponse;

## Events

 async def addEvent( self , request ):
    mySchema = self.cfg[ "database" ][ "schema" ];
    result   = {};

    for count, event in enumerate( request ):
        myQuery  = (
                     "INSERT INTO ws_performance_indicator.\"event\" " + 
                     " ( " + 
                         "\"dat\" , " + 
                         "\"parcelId\" , " + 
                         "\"eventStart\" , " + 
                         "\"eventEnd\" , " + 
                         "\"duration\" , " + 
                         "\"type\" , " + 
                         "\"crop\" , " + 
                         "\"variety\" , " + 
                         "\"comments\" , " + 
                         "\"amount\" , " + 
                         "\"unit\" , " + 
                         "\"unitRef\" , " + 
                         "\"metric\" , " + 
                         "\"target\" , " + 
                         "\"productName\" , " + 
                         "\"stage\" , " + 
                         "\"fuelConsumption\" , " + 
                         "\"fuelType\" , " + 
                         "\"fuelUnit\" , " + 
                         "\"fuelUnitRef\" " + 
                     " ) " + 
                      "VALUES " + 
                     " ( " + 
                         " {my_dat} , " + 
                         " {my_parcelid} , " + 
                         " {my_eventstart} , " + 
                         " {my_eventend} , " + 
                         " {my_duration} , " + 
                         " {my_type} , " + 
                         " {my_crop} , " + 
                         " {my_variety} , " + 
                         " {my_comments} , " + 
                         " {my_amount} , " + 
                         " {my_unit} , " + 
                         " {my_unitref} , " + 
                         " {my_metric} , " + 
                         " {my_target} , " + 
                         " {my_productname} , " + 
                         " {my_stage} , " + 
                         " {my_fuelconsumption} , " + 
                         " {my_fueltype} , " + 
                         " {my_fuelunit} , " + 
                         " {my_fuelunitref} " + 
                     " ) RETURNING ID; "
                   );

        qData    = sql.SQL( myQuery ).format( 
                       mySchema_param     = sql.Identifier( mySchema ),
                       my_dat             = sql.Literal( request[ count ].dat ),
                       my_parcelid        = sql.Literal( request[ count ].parcelId ),
                       my_eventstart      = sql.Literal( request[ count ].eventStart ),
                       my_eventend        = sql.Literal( request[ count ].eventEnd ),
                       my_duration        = sql.Literal( request[ count ].duration ),
                       my_type            = sql.Literal( request[ count ].type ),
                       my_crop            = sql.Literal( request[ count ].crop ),
                       my_variety         = sql.Literal( request[ count ].variety ),
                       my_comments        = sql.Literal( request[ count ].comments ),
                       my_amount          = sql.Literal( request[ count ].properties.amount ),
                       my_unit            = sql.Literal( request[ count ].properties.unit ),
                       my_unitref         = sql.Literal( request[ count ].properties.unitRef ),
                       my_metric          = sql.Literal( request[ count ].properties.metric ),
                       my_target          = sql.Literal( request[ count ].properties.target ),
                       my_productname     = sql.Literal( request[ count ].properties.productName ),
                       my_stage           = sql.Literal( request[ count ].properties.stage ),
                       my_fuelconsumption = sql.Literal( request[ count ].properties.fuelConsumption ),
                       my_fueltype        = sql.Literal( request[ count ].properties.fuelType ),
                       my_fuelunit        = sql.Literal( request[ count ].properties.fuelUnit ),
                       my_fuelunitref     = sql.Literal( request[ count ].properties.fuelUnitRef )
                   );

        result = self.executeQuery( qData , None , "insert" );
        if( "error" in result ):
            return { "error" : result[ "error" ] };

    return result;

 async def getEventById( self , id ):
    mySchema = self.cfg["database"]["schema"];

    myQuery  = ( "select " + 
                  " * " + 
                 "from {mySchema_param}.event " + 
                 "where id = {myId_param};" );

    qData    = sql.SQL( myQuery ).format( 
                   mySchema_param   = sql.Identifier( mySchema ),
                   myId_param       = sql.Literal( id )
               );

    myResponse = self.executeQuery( qData );

    return myResponse;

 async def getEvent( self , event_type=None , eventStart=None , eventEnd=None , parcelId=None ):
    mySchema  = self.cfg["database"]["schema"];
    if( parcelId is None ):
        myParcels = None;
    else:
        myParcels = "'" + "','".join( parcelId.split( "," ) ) + "'";

    myWhereClause = [];

    if event_type is not None : 
        myWhereClause.append( " type = {myEventType_param} " );

    if eventStart is not None and eventEnd is not None : 
        myWhereClause.append( "( \"eventStart\" >= {myEventStart_param} and \"eventStart\" <= {myEventEnd_param} )" );

    if parcelId is not None : 
        myWhereClause.append(  " \"parcelId\" in ( " + myParcels + " ) " );

    myTest = "where " + " and ".join( myWhereClause ) if ( len( myWhereClause ) > 0 ) else "";
    
    myQuery  = ( "select " + 
                  " * " + 
                 "from {mySchema_param}.event " + myTest +";" );

    qData    = sql.SQL( myQuery ).format( 
                   mySchema_param      = sql.Identifier( mySchema ),
                   myEventType_param   = sql.Literal( event_type ),
                   myEventStart_param  = sql.Literal( eventStart ),
                   myEventEnd_param    = sql.Literal( eventEnd )
               );

    myResponse = self.executeQuery( qData );

    return myResponse;

 async def deleteEvent( self , id ):
    mySchema = self.cfg[ "database" ][ "schema" ];

    myEvent  = await self.getEventById( id );
    if( len( myEvent ) <= 0 ):
        return { "error" : "" };

    myQuery  = ( "delete from {mySchema_param}.event where id = {myId_param};" );
    qData    = sql.SQL( myQuery ).format( 
                   mySchema_param  = sql.Identifier( mySchema ),
                   myId_param      = sql.Literal( id )
               );

    myResponse = self.executeQuery( qData , None , "delete" );

    return myResponse;

 async def updateEvent( self , id , request ):
    mySchema = self.cfg[ "database" ][ "schema" ];

    myEvent  = await self.getEventById( id );
    if( len( myEvent ) <= 0 ):
        return { "error" : "Invalid Event ID" };

    myRequestDictionary = request.__dict__;
    myNewDictionary     = dict();
    for attribute in myRequestDictionary:
        if( attribute == "properties" ):
            if( myRequestDictionary[ "properties" ] is not None ) : 
                myPropertiesDictionary = myRequestDictionary[ "properties" ].__dict__;
                for property in myEvent[ 0 ]:
                    if( property in myPropertiesDictionary ) :
                        if( myPropertiesDictionary[ property ] is not None ) : 
                            myNewDictionary[ property ] = myPropertiesDictionary[ property ];
        else:
            if( attribute != "parcelId" ):
                if( attribute in myEvent[ 0 ] and myRequestDictionary[ attribute ] is not None ) :
                    myNewDictionary[ attribute ] = myRequestDictionary[ attribute ];
                else:
                    myNewDictionary[ attribute ] = myEvent[ 0 ][ attribute ];

    for field in myEvent[ 0 ]:
        if field not in myNewDictionary : 
            myNewDictionary[ field ] = myEvent[ 0 ][ field ];

    myResponse = [];

    myQuery  = ( "update {mySchema_param}.event " + 
                 " set " + 
                   "\"dat\" = {dat_param} ," + 
                   "\"eventStart\" = {eventstart_param} ," + 
                   "\"eventEnd\" = {eventend_param} ," + 
                   "\"duration\" = {duration_param} ," + 
                   "\"crop\" = {crop_param} ," + 
                   "\"variety\" = {variety_param} ," + 
                   "\"comments\" = {comments_param} ," + 
                   "\"amount\" = {amount_param} ," + 
                   "\"unit\" = {unit_param} ," + 
                   "\"unitRef\" = {unitref_param} ," + 
                   "\"metric\" = {metric_param} ," + 
                   "\"target\" = {target_param} ," + 
                   "\"productName\" = {productname_param} ," + 
                   "\"stage\" = {stage_param} ," + 
                   "\"fuelConsumption\" = {fuelconsumption_param} ," + 
                   "\"fuelType\" = {fueltype_param} ," + 
                   "\"fuelUnit\" = {fuelunit_param} ," + 
                   "\"fuelUnitRef\" = {fuelunitref_param} " + 
                 "where id = {id_param};" );

    qData    = sql.SQL( myQuery ).format( 
                   mySchema_param        = sql.Identifier( mySchema ),
                   id_param              = sql.Literal( myNewDictionary[ "id" ] ),
                   dat_param             = sql.Literal( myNewDictionary[ "dat" ] ),
                   eventstart_param      = sql.Literal( myNewDictionary[ "eventStart" ] ),
                   eventend_param        = sql.Literal( myNewDictionary[ "eventEnd" ] ),
                   duration_param        = sql.Literal( myNewDictionary[ "duration" ] ),
                   crop_param            = sql.Literal( myNewDictionary[ "crop" ] ),
                   variety_param         = sql.Literal( myNewDictionary[ "variety" ] ),
                   comments_param        = sql.Literal( myNewDictionary[ "comments" ] ),
                   amount_param          = sql.Literal( myNewDictionary[ "amount" ] ),
                   unit_param            = sql.Literal( myNewDictionary[ "unit" ] ),
                   unitref_param         = sql.Literal( myNewDictionary[ "unitRef" ] ),
                   metric_param          = sql.Literal( myNewDictionary[ "metric" ] ),
                   target_param          = sql.Literal( myNewDictionary[ "target" ] ),
                   productname_param     = sql.Literal( myNewDictionary[ "productName" ] ),
                   stage_param           = sql.Literal( myNewDictionary[ "stage" ] ),
                   fuelconsumption_param = sql.Literal( myNewDictionary[ "fuelConsumption" ] ),
                   fueltype_param        = sql.Literal( myNewDictionary[ "fuelType" ] ),
                   fuelunit_param        = sql.Literal( myNewDictionary[ "fuelUnit" ] ),
                   fuelunitref_param     = sql.Literal( myNewDictionary[ "fuelUnitRef" ] )
               );

    myResponse = self.executeQuery( qData , None , "update" );

    return myResponse;

## Measurements

 async def addMeteoMeasurementCSV( self , request ):
     mySchema = self.cfg[ "database" ][ "schema" ];

     myQueryValues = [];
     for count, event in enumerate( request ):
         myQueryValues.append( " ( " + 
             " '" + str( request[ count ].parcelId ) + "' , " + 
             " '" + str( request[ count ].timestamp ) + "' , " + 
             " '" + str( request[ count ].temperature ) + "' , " + 
             " '" + str( request[ count ].humidity ) + "' , " + 
             " '" + str( request[ count ].windstrength ) + "' , " + 
             " '" + str( request[ count ].leafwetness ) + "' , " + 
             " '" + str( request[ count ].rain ) + "' " + 
         " ) " );

     myQuery  = (
                  "INSERT INTO ws_performance_indicator.\"meteo_measurement\" " + 
                  " ( " + 
                      "\"parcelId\" , " + 
                      "\"timestamp\" , " + 
                      "\"temperature\" , " + 
                      "\"humidity\" , " + 
                      "\"windstrength\" , " + 
                      "\"leafwetness\" , " + 
                      "\"rain\" " + 
                  " ) " + 
                   "VALUES " + 
                   ",".join( myQueryValues ) + " RETURNING ID "
                );
     # self.amTool.logFile( myQuery );

     qData    = sql.SQL( myQuery ).format( 
                    mySchema_param  = sql.Identifier( mySchema ),
                    my_parcelid     = sql.Literal( request[ count ].parcelId ),
                );

     result = self.executeQuery( qData , None , "insert" );
     if( "error" in result ):
         return { "error" : result };

 async def addMeteoMeasurement( self , request ):
    mySchema = self.cfg[ "database" ][ "schema" ];

    for count, event in enumerate( request ):
        myQuery  = (
                     "INSERT INTO ws_performance_indicator.\"meteo_measurement\" " + 
                     " ( " + 
                         "\"parcelId\" , " + 
                         "\"timestamp\" , " + 
                         "\"temperature\" , " + 
                         "\"humidity\" , " + 
                         "\"windstrength\" , " + 
                         "\"leafwetness\" , " + 
                         "\"rain\" " + 
                     " ) " + 
                      "VALUES " + 
                     " ( " + 
                         " {my_parcelid} , " + 
                         " {my_timestamp} , " + 
                         " {my_temperature} , " + 
                         " {my_humidity} , " + 
                         " {my_windstrength} , " + 
                         " {my_leafwetness} , " + 
                         " {my_rain} " + 
                     " ) RETURNING ID; "
                   );

        qData    = sql.SQL( myQuery ).format( 
                       mySchema_param  = sql.Identifier( mySchema ),
                       my_parcelid     = sql.Literal( request[ count ].parcelId ),
                       my_timestamp    = sql.Literal( request[ count ].timestamp ),
                       my_temperature  = sql.Literal( request[ count ].temperature ),
                       my_humidity     = sql.Literal( request[ count ].humidity ),
                       my_windstrength = sql.Literal( request[ count ].windstrength ),
                       my_leafwetness  = sql.Literal( request[ count ].leafwetness ),
                       my_rain         = sql.Literal( request[ count ].rain )
                   );

        result = self.executeQuery( qData , None , "insert" );
        if( "error" in result ):
            return { "error" : result[ "error" ] };

    return result;

 async def getMeasurementById( self , id ):
    mySchema = self.cfg["database"]["schema"];

    myQuery  = ( "select " + 
                  " * " + 
                 "from {mySchema_param}.meteo_measurement " + 
                 "where id = {myId_param};" );

    qData    = sql.SQL( myQuery ).format( 
                   mySchema_param   = sql.Identifier( mySchema ),
                   myId_param       = sql.Literal( id )
               );

    myResponse = self.executeQuery( qData );

    return myResponse;

 async def getMeteoMeasurement( self , eventStart=None , eventEnd=None , parcelId=None ):
    mySchema  = self.cfg["database"]["schema"];
    if( parcelId is None ):
        myParcels = None;
    else:
        myParcels = "'" + "','".join( parcelId.split( "," ) ) + "'";

    myWhereClause = [];

    if eventStart is not None and eventEnd is not None : 
        myWhereClause.append( "( \"timestamp\" >= {myEventStart_param} and \"timestamp\" <= {myEventEnd_param} )" );

    if parcelId is not None : 
        myWhereClause.append(  " \"parcelId\" in ( " + myParcels + " ) " );

    myTest = "where " + " and ".join( myWhereClause ) if ( len( myWhereClause ) > 0 ) else "";

    myQuery  = ( "select " + 
                  " * " + 
                 "from {mySchema_param}.meteo_measurement " + myTest +";" );

    qData    = sql.SQL( myQuery ).format( 
                   mySchema_param      = sql.Identifier( mySchema ),
                   myEventStart_param  = sql.Literal( eventStart ),
                   myEventEnd_param    = sql.Literal( eventEnd )
               );

    myResponse = self.executeQuery( qData );

    return myResponse;

 async def deleteMeteoMeasurement( self , id ):
    mySchema = self.cfg[ "database" ][ "schema" ];

    myEvent  = await self.getMeasurementById( id );
    if( len( myEvent ) <= 0 ):
        return { "error" : "" };

    myQuery  = ( "delete from {mySchema_param}.meteo_measurement where id = {myId_param};" );
    qData    = sql.SQL( myQuery ).format( 
                   mySchema_param  = sql.Identifier( mySchema ),
                   myId_param      = sql.Literal( id )
               );

    myResponse = self.executeQuery( qData , None , "delete" );

    return myResponse;

 async def updateMeteoMeasurement( self , id , request ):
    mySchema = self.cfg[ "database" ][ "schema" ];

    myEvent  = await self.getMeasurementById( id );
    if( len( myEvent ) <= 0 ):
        return { "error" : "Invalid Measurement ID" };

    myRequestDictionary = request.__dict__;
    myNewDictionary     = dict();
    for attribute in myRequestDictionary:
        if( attribute == "properties" ):
            if( myRequestDictionary[ "properties" ] is not None ) : 
                myPropertiesDictionary = myRequestDictionary[ "properties" ].__dict__;
                for property in myEvent[ 0 ]:
                    if( property in myPropertiesDictionary ) :
                        if( myPropertiesDictionary[ property ] is not None ) : 
                            myNewDictionary[ property ] = myPropertiesDictionary[ property ];
        else:
            if( attribute != "parcelId" ):
                if( attribute in myEvent[ 0 ] and myRequestDictionary[ attribute ] is not None ) :
                    myNewDictionary[ attribute ] = myRequestDictionary[ attribute ];
                else:
                    myNewDictionary[ attribute ] = myEvent[ 0 ][ attribute ];

    for field in myEvent[ 0 ]:
        if field not in myNewDictionary : 
            myNewDictionary[ field ] = myEvent[ 0 ][ field ];

    myResponse = [];

    myQuery  = ( "update {mySchema_param}.meteo_measurement " + 
                 " set " + 
                   "\"timestamp\" = {timestamp_param} ," + 
                   "\"temperature\" = {temperature_param} ," + 
                   "\"humidity\" = {humidity_param} ," + 
                   "\"windstrength\" = {windstrength_param} ," + 
                   "\"leafwetness\" = {leafwetness_param} , " + 
                   "\"rain\" = {rain_param} " + 
                 "where id = {id_param};" );

    qData    = sql.SQL( myQuery ).format( 
                   mySchema_param     = sql.Identifier( mySchema ),
                   id_param           = sql.Literal( myNewDictionary[ "id" ] ),
                   timestamp_param    = sql.Literal( myNewDictionary[ "timestamp" ] ),
                   temperature_param  = sql.Literal( myNewDictionary[ "temperature" ] ),
                   humidity_param     = sql.Literal( myNewDictionary[ "humidity" ] ),
                   windstrength_param = sql.Literal( myNewDictionary[ "windstrength" ] ),
                   leafwetness_param  = sql.Literal( myNewDictionary[ "leafwetness" ] ),
                   rain_param         = sql.Literal( myNewDictionary[ "rain" ] )
               );

    myResponse = self.executeQuery( qData , None , "update" );

    return myResponse;

 async def getChillingDays( self , options ):
     mySchema = self.cfg[ "database" ][ "schema" ];

     myQuery = ( "select " + 
                   "timestamp ," + 
                   "temperature::float as temperature, " + 
                   "case " + 
                     "when " + 
                           "temperature::float > {myLowLimit_param} " + 
                             "and " + 
                           "temperature::float < {myHighLimit_param} " + 
                     "then 1 " + 
                     "else 0 " + 
                   "end as chilled " + 
                 "from " + 
                   "{mySchema_param}.meteo_measurement " + 
                 "where timestamp between {myFromDate_param} and {myToDate_param} " + 
                 "and \"parcelId\" = {myParcelId_param} " + 
                 "order by timestamp ASC " + 
                 "limit {myLimit_param} offset {myOffset_param}; " 
     );

     qData    = sql.SQL( myQuery ).format( 
                    mySchema_param         = sql.Identifier( mySchema ),
                    myParcelId_param       = sql.Literal( options[ "parcelId" ] ),
                    myLowLimit_param       = sql.Literal( int( options[ "lowlimit" ] ) ),
                    myHighLimit_param      = sql.Literal( int( options[ "highlimit" ] ) ),
                    myFromDate_param       = sql.Literal( options[ "fromDate" ] ),
                    myToDate_param         = sql.Literal( options[ "toDate" ] ),
                    myLimit_param          = sql.Literal( int( options[ "limit" ] ) ),
                    myOffset_param         = sql.Literal( int( options[ "offset" ] ) )
                );

     myResponse = self.executeQuery( qData );

     return myResponse;

## Generic

 async def getEktariaFromPolygon( self , polygon ):
     myQuery = ( "select " + 
                  "round( " + 
                   "( " + 
                    "st_area( " + 
                     "st_transform( " + 
                      "st_geomfromtext({myPolygon_param},4326) ,  " + 
                     "2100) " + 
                    ") / 10000 " + 
                   ")::numeric " + 
                  ",2) as \"ektaria\"" 
               );

     qData    = sql.SQL( myQuery ).format( 
                    myPolygon_param = sql.Literal( polygon )
                );

     myResponse = self.executeQuery( qData );
     if( len( myResponse ) > 0 ):
         return float( int( myResponse[ 0 ][ "ektaria" ] * 100 ) / 100 );
     else:
         return 0;

 async def getParametric( self , type ):
    mySchema = self.cfg[ "database" ][ "schema" ];
    myQuery  = ( "select id , LOWER( type ) as type , LOWER( value ) as value from {mySchema_param}.parametric where type = {myType_param};" );
    qData    = sql.SQL( myQuery ).format( 
                   mySchema_param  = sql.Identifier( mySchema ),
                   myType_param      = sql.Literal( type )
               );

    myResponse = self.executeQuery( qData , None , "select" );

    return myResponse;

 async def getParametricAll( self ):
    mySchema = self.cfg[ "database" ][ "schema" ];
    myQuery  = ( "select * from {mySchema_param}.parametric;" );
    qData    = sql.SQL( myQuery ).format( 
                   mySchema_param  = sql.Identifier( mySchema )
               );

    myResponse = self.executeQuery( qData , None , "select" );

    return myResponse;

## Geo Data from External API (Nominatim)

 async def getGeoDetailsFromPoint( self , longitude , latitude ):
     myURL = "https://nominatim.openstreetmap.org/reverse?format=json&lat=" + str( latitude ) + "&lon=" + str( longitude ) + "&zoom=8&addressdetails=1";

     async with aiohttp.ClientSession() as session:
         async with session.get( 
             url = myURL , ssl=False 
         ) as response:
             myText = await response.text();
             print( myText );
             try:
                 myJSON = JSON.loads( myText );
                 return myJSON;
             except ValueError as error :
                 print( error );
                 return { "error" : "There was an issue retrieving data from Nominatim" };

## Populate Test

 async def request( self , options ):
 
     credentials        = "amanos:4bvrwx";
     base64_credentials = base64.b64encode( credentials.encode("ascii") );

     async with aiohttp.ClientSession() as session:

         async with session.get( 
                       url     = options[ "endPoint" ] , 
                       json    = options[ "myData"] , 
                       headers = {'content-type': 'application/json' , 'accept' : 'application/json' , 'Authorization' : 'Basic YW1hbm9zOjRidnJ3eA==' } 
                    ) as response:

              myText = await response.text();
              if( self.debug == True ) : 
                  myCurl = self.amTool.log_curl( 
                      method   = "get" , 
                      postData = options[ "myData"] , 
                      endpoint = options[ "endPoint" ] , 
                      file     = False , 
                      auth     = "demo:123456"
                  );

              try:
                  myJSON = JSON.loads( myText );
                  return myJSON;
              except ValueError as error :
                  myUniqueLogID = self.amTool.getUID( "_icmissue" );
                  if( myText is not None ):
                      myParse = self.parseJavaError( myText );
                      self.amTool.logFile( " " + myUniqueLogID + " : " + myParse );
                  else:
                     self.amTool.logFile( " " + myUniqueLogID + " : " + myText );

                  if( self.debug == True ) : 
                      self.amTool.logFile( " " + myUniqueLogID + " : " + myCurl );

                  return { "error" : "There was an issues retrieving data from ICM please check logs for more details using the following id '"+str(myUniqueLogID)+"'." };

 async def getAllParcels( self ):
    mySchema   = self.cfg["database"]["schema"];
    myQuery    = ( "select " + 
                    "id , " + 
                    "name , " + 
                    "ST_AsText( polygon ) as polygon , " + 
                    "country , " + 
                    "county , " + 
                    "ektaria , " + 
                    "dat , " + 
                    "\"user\" , " + 
                    "\"uid\" " + 
                   "from {mySchema_param}.parcel " + 
                   "order by id DESC" 
                 );

    qData      = sql.SQL( myQuery ).format( 
                     mySchema_param = sql.Identifier( mySchema )
                 );

    myResponse = self.executeQuery( qData );

    return myResponse;

 async def getPolygonsFromWS( self , parcelArray ):
     myRes = [];

     for id in parcelArray : 
         cUrlOptions = {
          "endPoint" : ( "http://sense-web.neuropublic.gr:8383/locations/agronomy?lang=el&radius=100&limit=100&parcelid=" + str( id ) ),
          "myData"   : {}
         }
         parcelDetails = await self.request( cUrlOptions );
         if len( parcelDetails ) > 0 :
             if "gis" in parcelDetails[ 0 ] and len( parcelDetails[ 0 ][ "gis" ] ) > 0 and "wkt" in parcelDetails[ 0 ][ "gis" ][ 0 ] : 
                 myRes.append( parcelDetails[ 0 ][ "gis" ][ 0 ][ "wkt" ] );

     return myRes;

 async def getEventsFromWS( self , evt_type , parcelArray , fromDate="2022-01-01" , toDate="2023-12-31"):
     myRes = [];
     for id in parcelArray : 
         myURL = "http://sense-web.neuropublic.gr:8383/locations/events/" + str( evt_type ) + "?fromdate=" + str( fromDate ) + "&todate=" + str( toDate ) + "&parcelid=" + str( id ) + "&radius=100&limit=1";
         cUrlOptions = {
          "endPoint" : ( "http://sense-web.neuropublic.gr:8383/locations/events/" + str( evt_type ) + "?fromdate=" + str( fromDate ) + "&todate=" + str( toDate ) + "&parcelid=" + str( id ) + "&radius=100&limit=1" ),
          "myData"   : {}
         }
         parcelEvents = await self.request( cUrlOptions );
         if "detail" in parcelEvents :
             return { "error" : parcelEvents[ "detail" ] , "request" : myURL }
         else:
             if len( parcelEvents ) > 0 :
                 myRes.append( parcelEvents );
                 self.amTool.log( "Retrieved ( " + str( len( parcelEvents ) ) + " ) Events from ICM for Parcel with ID [ " + str( id ) + " ] " );
             else:
                 self.amTool.log( "Retrieved No Events from ICM for Parcel with ID [ " + str( id ) + " ] " );

     return myRes;

 async def updateParcelPolygon( self , polygon , uid ):
    mySchema = self.cfg[ "database" ][ "schema" ];

    myResponse = [];

    myQuery  = ( "update {mySchema_param}.parcel " + 
                 " set " + 
                 " polygon  = {myPolygon_param} " + 
                 "where uid = {myId_param};" );

    qData    = sql.SQL( myQuery ).format( 
                   mySchema_param  = sql.Identifier( mySchema ),
                   myPolygon_param = sql.Literal( polygon ) , 
                   myId_param      = sql.Literal( uid )
               );

    myResponse = self.executeQuery( qData , None , "update" );
    # self.amTool.log( "Updated Parcel [ " + str( uid ) + " ] with Polygon from ICM" );

    return myResponse;

 async def addEventToParcel( self , eventArray , uid ):
    mySchema = self.cfg[ "database" ][ "schema" ];

    for event in eventArray:

        myQuery  = (
                     "INSERT INTO ws_performance_indicator.\"event\" " + 
                     " ( " + 
                         "\"dat\" , " + 
                         "\"parcelId\" , " + 
                         "\"eventStart\" , " + 
                         "\"eventEnd\" , " + 
                         "\"duration\" , " + 
                         "\"type\" , " + 
                         "\"crop\" , " + 
                         "\"variety\" , " + 
                         "\"comments\" , " + 
                         "\"amount\" , " + 
                         "\"unit\" , " + 
                         "\"unitRef\" , " + 
                         "\"metric\" , " + 
                         "\"target\" , " + 
                         "\"productName\" , " + 
                         "\"stage\" , " + 
                         "\"fuelConsumption\" , " + 
                         "\"fuelType\" , " + 
                         "\"fuelUnit\" , " + 
                         "\"fuelUnitRef\" " + 
                     " ) " + 
                      "VALUES " + 
                     " ( " + 
                         " {my_dat} , " + 
                         " {my_parcelid} , " + 
                         " {my_eventstart} , " + 
                         " {my_eventend} , " + 
                         " {my_duration} , " + 
                         " {my_type} , " + 
                         " {my_crop} , " + 
                         " {my_variety} , " + 
                         " {my_comments} , " + 
                         " {my_amount} , " + 
                         " {my_unit} , " + 
                         " {my_unitref} , " + 
                         " {my_metric} , " + 
                         " {my_target} , " + 
                         " {my_productname} , " + 
                         " {my_stage} , " + 
                         " {my_fuelconsumption} , " + 
                         " {my_fueltype} , " + 
                         " {my_fuelunit} , " + 
                         " {my_fuelunitref} " + 
                     " ) RETURNING ID; "
                   );

        qData    = sql.SQL( myQuery ).format( 
                       mySchema_param     = sql.Identifier( mySchema ),
                       my_dat             = sql.Literal( event[ "dat" ] ),
                       my_parcelid        = sql.Literal( uid ),
                       my_eventstart      = sql.Literal( event[ "eventStart" ] ),
                       my_eventend        = sql.Literal( event[ "eventEnd" ] ),
                       my_duration        = sql.Literal( event[ "duration" ] ),
                       my_type            = sql.Literal( event[ "type" ] ),
                       my_crop            = sql.Literal( event[ "crop" ] ),
                       my_variety         = sql.Literal( event[ "variety" ] ),
                       my_comments        = sql.Literal( event[ "comments" ] ),
                       my_amount          = sql.Literal( event[ "amount" ] ),
                       my_unit            = sql.Literal( event[ "unit" ] ),
                       my_unitref         = sql.Literal( event[ "unitRef" ] ),
                       my_metric          = sql.Literal( event[ "metric" ] ),
                       my_target          = sql.Literal( event[ "target" ] ),
                       my_productname     = sql.Literal( event[ "productName" ] ),
                       my_stage           = sql.Literal( event[ "stage" ] ),
                       my_fuelconsumption = sql.Literal( event[ "fuelConsumption" ] ),
                       my_fueltype        = sql.Literal( event[ "fuelType" ] ),
                       my_fuelunit        = sql.Literal( event[ "fuelUnit" ] ),
                       my_fuelunitref     = sql.Literal( event[ "fuelUnitRef" ] )
                   );

        result = self.executeQuery( qData , None , "insert" );
        if( "error" in result ):
            return { "error" : result[ "error" ] };

    return result;