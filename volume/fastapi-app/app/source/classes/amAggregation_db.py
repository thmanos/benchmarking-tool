import os;
import datetime;
import sys;
import aiohttp;
import asyncio;
import re;
import psycopg2;
from   typing import Optional, Dict, Any;
from   psycopg2 import sql;
from   psycopg2.extras import RealDictCursor;
import csv;
import json as JSON;
from classes.amTools import amTool;

class amAggregationDB:
 def __init__( self , cfg ):
  """Class for Queryinjg Database"""
  self.amTool = amTool();
  self.amTool.log( "Model Initiated" );
  self.cfg    = cfg;
  self.debug  = False;

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

 async def getAggregation( self , options ):
     mySchema = self.cfg[ "database" ][ "schema" ];

     myQuery = ( "select " + 
                  "" + options[ "fn" ] + "( amount ) as total ," + 
                  "\"parcelId\" ," + 
                  options[ "agg_property" ] + " " + 
                  " from ws_performance_indicator.\"event\" " + 
                  " where \"parcelId\" in ( " + ",".join( options[ "parcel" ] ) + " ) " + 
                  " group by \"parcelId\"," + options[ "agg_property" ] + ";"
     );

     qData    = sql.SQL( myQuery ).format(
                    mySchema_param         = sql.Identifier( mySchema )
                    # ,myFromDate_param       = sql.Literal( options[ "fromDate" ] )
                    # ,myToDate_param         = sql.Literal( options[ "toDate" ] )
                );

     myResponse = self.executeQuery( qData );

     return myResponse;

 def normalizeValues( self , unit , amount ) : 
     myResponse = 0;

     if( unit == "kg" ) : 
         myResponse = amount * 1000;
         myUnit     = "gr";
     elif( unit == "tn" ) : 
         myResponse = amount * 1000000;
         myUnit     = "gr";
     elif( unit == "lt" ) : 
         myResponse = amount * 1000;
         myUnit     = "ml";
     else:
         myResponse = amount;
         myUnit     = unit;

     return {
      "amount" : myResponse , 
      "unit"   : myUnit
     };

 async def getTotalEktaria( self , parcelsArray ):
    mySchema = self.cfg[ "database" ][ "schema" ];
    myQuery = (
                "select " + 
                  "sum( parcel.ektaria ) as total " + 
                "from ws_performance_indicator.parcel " + 
                "where parcel.uid in ( '" + "','".join( parcelsArray ) + "' ) "
    );

    qData    = sql.SQL( myQuery ).format(
                   mySchema_param = sql.Identifier( mySchema )
               );

    myResult = self.executeQuery( qData );

    return myResult;

 async def getTotalEvents( self , options ):
    mySchema = self.cfg[ "database" ][ "schema" ];
    myQuery = (
                "select " + 
                  "count(*) as amount " + 
                "from " + 
                  "{mySchema_param}.\"event\" evt " + 
                    "inner join ws_performance_indicator.parcel parcel on parcel.uid = evt.\"parcelId\" " + 
                "where " + 
                  "parcel.uid in ( '" + "','".join( options[ "parcel" ] ) + "' ) " + 
                  "and evt.type = {myType_param}"
    );

    qData    = sql.SQL( myQuery ).format(
                   mySchema_param = sql.Identifier( mySchema ),
                   myType_param   = sql.Literal( options[ "type" ] )
               );

    myResult = self.executeQuery( qData );
    if len( myResult ) > 0 :
        return myResult[ 0 ][ "amount" ];
    else:
        return 0;
 
 def extract_npk( self, text: str ) -> Optional[ Dict[ str, Any ] ]:
     """
     Extract N-P-K grade from a product string.
     Accepts missing parts and fills them with 0:
       - "11-15-15"
       - "21-7"      -> k = 0
       - "21"        -> p = 0, k = 0
       - "-7-11"     -> n = 0
       - "21--11"    -> p = 0
     Returns None if no plausible N/P/K pattern is found.
     """
     if not text:
         return None;

     # N [-] P (optional) [-] K (optional)
     # Accept hyphen, en-dash, em-dash; accept comma as decimal separator.
     pattern = re.compile(
         r'(?<!\d)'
         r'(\d+(?:[.,]\d+)?)?'      # N (optional)
         r'\s*[-–—]\s*'
         r'(\d+(?:[.,]\d+)?)?'      # P (optional)
         r'(?:\s*[-–—]\s*'
         r'(\d+(?:[.,]\d+)?)?'      # K (optional)
         r')?'
         r'(?!\d)'
     );

     m = pattern.search( text );
     if not m:
         return None;

     def to_float_or_zero( s: Optional[ str ] ) -> float:
         if not s:
             return 0.0;
         return float( s.replace( ",", "." ) );

     n_s, p_s, k_s = m.group( 1 ), m.group( 2 ), m.group( 3 );

     # If everything is missing, this was just a dash match; treat as no NPK found.
     if n_s is None and p_s is None and k_s is None:
         return None;

     match_str = m.group( 0 ).strip();

     # Normalize match to always show 3 numbers in "match"
     match_norm = f"{to_float_or_zero(n_s):g}-{to_float_or_zero(p_s):g}-{to_float_or_zero(k_s):g}";

     return {
         "n"         : to_float_or_zero( n_s ),
         "p"         : to_float_or_zero( p_s ),
         "k"         : to_float_or_zero( k_s ),
         "match"     : match_norm,
         "raw_match" : match_str,
     }

 async def getMetricAggregations( self , options ):
    totalEktaria = await self.getTotalEktaria( options[ "parcel" ] );
    mySchema     = self.cfg[ "database" ][ "schema" ];
    myQuery      = (
                     "select " + 
                       "res.total , " + 
                       "res.unit , " + 
                       "res.metric , " +  
                       "res.uid , " + 
                       "res.\"unitRef\" , " + 
                       "res.\"productName\" , " + 
                       "res.dat , " + 
                       "res.crop , " + 
                       "ektaria " + 
                     "from ws_performance_indicator.parcel " + 
                     "inner join ( " + 
                      "select " + 
                        "" + options[ "fn" ] + "( evt.amount ) as total , " + 
                        "evt.unit , " + 
                        "evt.metric , " + 
                        "evt.dat , " + 
                        "evt.crop , " + 
                        "parcel.uid , " + 
                        "evt.\"productName\" , " + 
                        "evt.\"unitRef\"  " + 
                      "from ws_performance_indicator.\"event\" evt " + 
                       "inner join ws_performance_indicator.parcel parcel on parcel.uid = evt.\"parcelId\" " + 
                      "where parcel.uid in ( '" + "','".join( options[ "parcel" ] ) + "' ) " + 
                      "and evt.type = {myType_param} " + 
                      "and evt.\"eventStart\" between {myFromDate_param} and {myToDate_param} " + 
                      "group by parcel.uid , evt.metric , evt.unit , evt.\"unitRef\" , evt.\"productName\" , evt.dat , evt.crop " + 
                     ") res on res.uid = parcel.uid"
    );

    qData        = sql.SQL( myQuery ).format(
                       mySchema_param   = sql.Identifier( mySchema ),
                       myType_param     = sql.Literal( options[ "type" ] ) , 
                       myFromDate_param = sql.Literal( options[ "fromdate" ] ) , 
                       myToDate_param   = sql.Literal( options[ "todate" ] ) 
                   );

    myResult     = self.executeQuery( qData );
    # print( myResult );

    myResponse   = {
        "metric" : {},
        "info"   : {
            "crop" : []
        },
        "dat"    : []
    };

    if options[ "type" ] == "fertilization" :
        myResponse[ "npk" ] = {
            "N" : 0,
            "P" : 0,
            "K" : 0
        };
    crops = [];
    for row in myResult:
        if myResponse[ "info" ][ "crop" ] is not None and myResponse[ "info" ][ "crop" ] not in crops : 
            crops.append( row[ "crop" ] );

        if row[ "dat" ] != "" :
            if row[ "dat" ] not in myResponse[ "dat" ] : 
                myResponse[ "dat" ].append( row[ "dat" ] );

        if options[ "type" ] == "fertilization" :
            extraction = self.extract_npk( row[ "productName" ] );
            if extraction is not None: 
                myResponse[ "npk" ][ "N" ] = myResponse[ "npk" ][ "N" ] + extraction[ "n" ];
                myResponse[ "npk" ][ "P" ] = myResponse[ "npk" ][ "P" ] + extraction[ "p" ];
                myResponse[ "npk" ][ "K" ] = myResponse[ "npk" ][ "K" ] + extraction[ "k" ];

        normalizedValue = self.normalizeValues( row[ "unit" ] , row[ "total" ] );
        myMetric = row[ "metric" ];
        if myMetric not in myResponse[ "metric" ] : 
            myResponse[ "metric" ][ myMetric ] = {
                "total"         : 0,
                "unit"          : "",
                "metric"        : "",
                "id"            : 0,
                "per_hectar"    : 0,
                "total_hect"    : 0
            }

        if( row[ "unitRef" ] == "stremma" ) : 
            # print( "evt.amount : " + str( row[ "total" ] ) );
            # print( "Normalized Value to '" + str( normalizedValue[ "unit" ] ) + "': " + str( normalizedValue[ "amount" ] ) + " | Ektaria : " + str( row[ "ektaria" ] ) );
            # print(  str( myResponse[ "metric" ][ myMetric ][ "total" ] ) + " + ( " + str( normalizedValue[ "amount" ] ) + " * " + str( row[ "ektaria" ] ) + " ) " );
            myResponse[ "metric" ][ myMetric ][ "total" ] = myResponse[ "metric" ][ myMetric ][ "total" ] + ( normalizedValue[ "amount" ] * row[ "ektaria" ] );
            # print( myResponse[ "metric" ][ myMetric ][ "total" ] );
        else:
            myResponse[ "metric" ][ myMetric ][ "total" ] = myResponse[ "metric" ][ myMetric ][ "total" ] + normalizedValue[ "amount" ];

        myResponse[ "metric" ][ myMetric ][ "unit" ]       = normalizedValue[ "unit" ];
        myResponse[ "metric" ][ myMetric ][ "metric" ]     = myMetric;
        myResponse[ "metric" ][ myMetric ][ "id" ]         = row[ "uid" ];
        myResponse[ "metric" ][ myMetric ][ "total_hect" ] = totalEktaria[ 0 ][ "total" ];

        self.amTool.json_dump( myResponse[ "metric" ] );

        perHectar = 0;
        if myResponse[ "metric" ][ myMetric ][ "total" ] > 0 : 
            if( row[ "unitRef" ] == "stremma" ) : 
                perHectar = round( ( normalizedValue[ "amount" ] * row[ "ektaria" ] ) / totalEktaria[ 0 ][ "total" ] , 2 );
            else : 
                perHectar = round( normalizedValue[ "amount" ] / totalEktaria[ 0 ][ "total" ] , 2 );

            myResponse[ "metric" ][ myMetric ][ "per_hectar" ] += perHectar;

    new_list = sorted( myResponse[ "metric" ], key=lambda x: myResponse[ "metric" ][ x ][ "total" ], reverse=True );
    myResponse[ "info" ][ "rank" ] = new_list;

    myResponse[ "info" ][ "crop" ] = crops;

    myResponse[ "info" ][ "total_events" ] = await self.getTotalEvents({
      "type"   : options[ "type" ],
      "parcel" : options[ "parcel" ]
    });

    myResponse[ "info" ][ "total_parcels" ] = len( options[ "parcel" ] );

    return myResponse;

 async def getMeasurementAggregations( self , options ):
    mySchema            = self.cfg[ "database" ][ "schema" ];
    myAggregationField  = "ROUND(" + options[ "fn" ] + "(meteo_measurement.\"" + options[ "type" ] + "\")::numeric, 2) AS " + options[ "type" ] + " ";
    myQuery      = (
                     "SELECT " + 
                        "meteo_measurement.\"parcelId\", " + 
                        "EXTRACT(YEAR FROM \"timestamp\") AS year, " + 
                        "EXTRACT(MONTH FROM \"timestamp\") AS month, " + 
                        myAggregationField + 
                     "FROM " + 
                         "{mySchema_param}.meteo_measurement " + 
                     "WHERE " + 
                         "meteo_measurement.\"" + options[ "type" ] + "\" IS NOT NULL " + 
                     "and meteo_measurement.\"parcelId\" in ( '" + "','".join( options[ "parcel" ] ) + "' ) " + 
                     "and \"timestamp\" between {myFromDate_param} and {myToDate_param} " + 
                     "GROUP BY " + 
                         "meteo_measurement.\"parcelId\", " + 
                         "EXTRACT(YEAR FROM \"timestamp\"), " + 
                         "EXTRACT(MONTH FROM \"timestamp\") " + 
                     "ORDER BY " + 
                         "meteo_measurement.\"parcelId\", " + 
                         "year, " + 
                         "month;" 
    );

    qData        = sql.SQL( myQuery ).format(
                       mySchema_param   = sql.Identifier( mySchema ),
                       myType_param     = sql.Literal( options[ "type" ] ) , 
                       myFromDate_param = sql.Literal( options[ "fromdate" ] ) , 
                       myToDate_param   = sql.Literal( options[ "todate" ] ) 
                   );

    myResponse     = self.executeQuery( qData );

    return myResponse;
