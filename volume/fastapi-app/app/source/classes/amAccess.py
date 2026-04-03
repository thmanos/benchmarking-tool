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

class amAccess:
 def __init__( self , cfg ):
     """Class for User Access Levels"""
     self.amTool = amTool();
     self.amTool.log( "UserAccess Initiated" );
     self.cfg      = cfg;
     self.isAdmin  = False;
     self.access   = dict();
     self.error    = False;
     self.debug    = True;

 def executeQuery( self , query , type = "select" ):
    connection = False;
    cursor     = False;
    try: 
       connection = psycopg2.connect( user     = self.cfg["database"]["connection"]["user"],
                                      password = self.cfg["database"]["connection"]["password"],
                                      host     = self.cfg["database"]["connection"]["host"],
                                      port     = self.cfg["database"]["connection"]["port"],
                                      database = self.cfg["database"]["connection"]["database"] );

       cursor     = connection.cursor( cursor_factory = RealDictCursor );

       cursor.execute( query );
       if( self.debug is True ) :
           print( cursor.query );

       if( type == "insert" ) :
           if( str( cursor.query ).find( "RETURNING" ) > 0 ) : 
               my_query_response = cursor.fetchone();
           else:
               my_query_response = [];
       elif ( type == "update" or type == "delete" ):
           my_query_response = [];
       else: 
           my_query_response = cursor.fetchall();

       connection.commit();
       cursor.close();
       
       self.error = False;

       return my_query_response;

    except( Exception, psycopg2.Error ) as error :
        self.amTool.logFile( error );
        if( self.debug is True ) :
            print( error );
            if cursor is not False : 
                self.amTool.logFile( cursor.query );

        self.error = error;
        return [];

    finally:
        if( connection ):
            connection.close();
            if( self.debug is True ) :
                print( "["+__name__+" DB Connection Closed" );

 async def getAppAccess( self , credentials ):
     mySchema   = self.cfg[ "database" ][ "authschema" ];

     myQuery = ( "select user_id from {mySchema_param}.user where username = {username_param} and password = {password_param};" );
     qData   = sql.SQL( myQuery ).format(
                   mySchema_param   = sql.Identifier( mySchema ),
                   username_param   = sql.Literal( credentials["un"] ),
                   password_param   = sql.Literal( credentials["pw"] )
               );

     myResponse = self.executeQuery( qData , "select" );

     if( len( myResponse ) > 0 ):
         return myResponse;
     else:
         return False;

 async def logSession( self , user_id , request ):
     myRequest            = dict();
     myEligibleProperties = [ "client" , "method" , "root_path" , "path" , "query_string" ];
     for item in request:
         if item in myEligibleProperties : 
             if( item == "client" ) : 
                 myRequest[ item ] = request[ item ][ 0 ];
             elif( item == "query_string" ) : 
                 myRequest[ item ] = str( request[ item ] );
             else:
                 myRequest[ item ] = request[ item ];

     myQuery  = ( 
                  "insert into {mySchema_param}.log_session " + 
                  " ( user_id , request , error ) " + 
                  " VALUES " + 
                  " ( {user_id_param} , {request_param} , {error_param} );" 
                );
     qData    = sql.SQL( myQuery ).format(
                   mySchema_param   = sql.Identifier( self.cfg[ "database" ][ "authschema" ] ),
                   user_id_param    = sql.Literal( int( user_id ) ),
                   request_param    = sql.Literal( JSON.dumps( myRequest ) ),
                   error_param      = sql.Literal( "" )
              );

     myResponse = self.executeQuery( qData , "insert" );
