import os;
import datetime;
import sys;
import aiohttp;
import asyncio;
import psycopg2;
from psycopg2 import sql;
from psycopg2.extras import RealDictCursor
import csv;
import json as JSON;
from classes.amTools import amTool;

class amAggregation:
 def __init__( self , cfg ):
  """Class for Queryinjg Database"""
  self.amTool = amTool();
  self.amTool.log( "Model Initiated" );
  self.cfg    = cfg;
  self.debug  = True;

 def executeQuery( self , query , customConnectionString = None ):
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

       cursor     = connection.cursor( cursor_factory = RealDictCursor );

       cursor.execute( query );
       if( self.debug is True ) :
           print( cursor.query );

       my_query_response = cursor.fetchall();
       cursor.close();
       connection.commit();

       return my_query_response;

    except( Exception, psycopg2.Error ) as error :
        self.amTool.logFile( error );
        if( self.debug is True ) :
            if cursor is not False : 
                self.amTool.logFile( cursor.query );
            print( error );
        return [];

    finally:
        if( connection ):
            connection.close();
            if( self.debug is True ) :
                print( "["+__name__+":getLocations] : DB Connection Closed" );

 async def getSumDepths( self , options ):
        mySchema = self.cfg[ "database" ][ "schema" ];

        mySensorQuerySelectArray = list();
        for sensor in options[ "sensorName" ] :
            mySensorFunction_param = options[ "sensorName" ][ sensor ];
            mySensorQuerySelectArray.append( "(T1.json_data::jsonb->'sensors'->'" + sensor + "'->'" + str( mySensorFunction_param ) + "')::float " );

        myOrderBy_param = "ASC";
        if( options[ "orderby" ].lower() == "desc" ):
            myOrderBy_param = "DESC";
        else:
            myOrderBy_param = "ASC";

        myQuery = ( "select " + 
           " extract( epoch from T1.m_date ) as m_date , " + 
           "sum( " + ( " + ".join( mySensorQuerySelectArray ) ) + " ) as sum_depths " + 
           "from main.measurements T1 " + 
           "inner join main.map_locations T2 on T2.location_id = T1.location_id " + 
           "where T1.m_date between {myFromDate_param} and {myToDate_param} " + 
           "and tr = {myTimeResolution_param} " + 
           "and T1.location_id = {myLocationId_param} " + 
           "group by T1.m_date " + 
           "order by T1.m_date " + options[ "orderby" ] + " " + 
           "limit {myLimit_param} offset {myOffset_param}; " 
        );

        qData    = sql.SQL( myQuery ).format( 
                       mySchema_param         = sql.Identifier( mySchema ),
                       myLocationId_param     = sql.Literal( int( options[ "locationid" ] ) ),
                       myFromDate_param       = sql.Literal( options[ "fromDate" ] ),
                       myToDate_param         = sql.Literal( options[ "toDate" ] ),
                       myTimeResolution_param = sql.Literal( int( options[ "timeResolution" ] ) ),
                       myLimit_param          = sql.Literal( int( options[ "limit" ] ) ),
                       myOffset_param         = sql.Literal( int( options[ "offset" ] ) )
                   );

        myResponse = self.executeQuery( qData );

        return myResponse;

 async def getChillingDays( self , options ):
        mySchema = self.cfg[ "database" ][ "schema" ];

        mySensorQuerySelectArray = list();
        for sensor in options[ "sensorName" ] :
            mySensorFunction_param = options[ "sensorName" ][ sensor ];
            mySensorQuerySelectArray.append( "(T1.json_data::jsonb->'sensors'->'" + sensor + "'->'" + str( mySensorFunction_param ) + "')::float " );

        myOrderBy_param = "ASC";
        if( options[ "orderby" ].lower() == "desc" ):
            myOrderBy_param = "DESC";
        else:
            myOrderBy_param = "ASC";

        myQuery = ( "select " + 
                      "extract( epoch from	T1.m_date ) as m_date ," + 
                      "(T1.json_data::jsonb->'sensors'->'wsht30_temp'->'1')::float as \"temp\" , " + 
                      "case " + 
                        "when " + 
                              "(T1.json_data::jsonb->'sensors'->'wsht30_temp'->'1')::float > {myLowLimit_param} " + 
                                "and " + 
                              "(T1.json_data::jsonb->'sensors'->'wsht30_temp'->'1')::float < {myHighLimit_param} " + 
                        "then 1 " + 
                        "else 0 " + 
                      "end as chilled 	" + 
                    "from " + 
                      "main.measurements T1 " + 
                        "inner join main.map_locations T2 on	T2.location_id = T1.location_id " + 
                    "where " + 
                      "T1.m_date between {myFromDate_param} and {myToDate_param} " + 
                      "and tr = 60 " + 
                      "and T1.location_id = {myLocationId_param} " + 
                    "order by T1.m_date " + options[ "orderby" ] + " " + 
                    "limit {myLimit_param} offset {myOffset_param}; " 
        );

        qData    = sql.SQL( myQuery ).format( 
                       mySchema_param         = sql.Identifier( mySchema ),
                       myLocationId_param     = sql.Literal( int( options[ "locationid" ] ) ),
                       myLowLimit_param       = sql.Literal( int( options[ "lowlimit" ] ) ),
                       myHighLimit_param      = sql.Literal( int( options[ "highlimit" ] ) ),
                       myFromDate_param       = sql.Literal( options[ "fromDate" ] ),
                       myToDate_param         = sql.Literal( options[ "toDate" ] ),
                       myLimit_param          = sql.Literal( int( options[ "limit" ] ) ),
                       myOffset_param         = sql.Literal( int( options[ "offset" ] ) )
                   );

        myResponse = self.executeQuery( qData );

        return myResponse;
