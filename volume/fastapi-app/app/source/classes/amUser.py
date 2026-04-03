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

class amUser:
 def __init__( self ):
     """Class for User Access Levels"""
     self.amTool = amTool();
     self.amTool.log( "UserAccess Initiated" );
     self.cfg      = self.amTool.load( "./cfg/" , "config" );
     self.isAdmin  = False;
     self.access   = dict();

 async def getUserAccess( self , credentials ):
    connection = False;
    try: 
       connection = psycopg2.connect( user     = self.cfg["database"]["connection"]["user"],
                                      password = self.cfg["database"]["connection"]["password"],
                                      host     = self.cfg["database"]["connection"]["host"],
                                      port     = self.cfg["database"]["connection"]["port"],
                                      database = self.cfg["database"]["connection"]["database"] );

       cursor     = connection.cursor( cursor_factory = RealDictCursor );

       mySchema   = self.cfg["database"]["schema"];

       myQuery = ( "select * from {mySchema_param}.user where email = {email_param} and password = {password_param};" );
       qData   = sql.SQL( myQuery ).format(
                     mySchema_param   = sql.Identifier( mySchema ),
                     email_param      = sql.Literal( credentials["un"] ),
                     password_param   = sql.Literal( credentials["pw"] )
                 );

       cursor.execute( qData );
       my_query_response = cursor.fetchall();
       cursor.close();
       connection.commit();

       if( len( my_query_response ) > 0 ):
           return my_query_response;
       else:
           return False;

    except( Exception, psycopg2.Error ) as error :
        return { "error" : error };

    finally:
        if( connection ):
            connection.close();
            print( "[getUserAccess] : DB Connection Closed" );

 def hasAccessToTracker( self , imei ):
     hasAccess = False;
     if( self.isAdmin > 0 ):
         return True;

     for accessDetail in self.access :
         if( accessDetail[ "imei" ] == imei ):
             hasAccess = True;
         else:
             hasAccess = False;

     return hasAccess;