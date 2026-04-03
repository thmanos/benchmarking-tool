import os;
import datetime;
import sys;
import decimal;
import json as JSON;
import hashlib;
import random;
from time import time;

class SafeJSONEncoder(JSON.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (decimal.Decimal)):
            return float(obj)
        return super().default(obj);

class amTool:
 def __init__( self ):
  """Class for Misc Tools"""
  self.log( "Tools Initiated" );
  self.cfg = self.load( "./cfg/" , "config" );

 def log( self , myString , debug = True  , frameinfo = None ):
     if debug == True : 
         if frameinfo is not None :
             myLine = "[ Line : " + str( frameinfo.lineno ) + " ] ";
         else :
             myLine = "";
         
         myCurrentTime = datetime.datetime.now();
         print( "[" + datetime.datetime.strftime( myCurrentTime , "%Y-%m-%d %H:%M:%S" ) + "] : " + myLine + " " + str( myString ) , flush=True);

 def load( self , filePath , fileName , type = "json" ):
     """
      Loads Configuration from Disk
     """
     myCFG = dict();
     try:
         fileName = filePath + fileName + "." + type;
         if( os.path.exists( fileName ) == False ):
            self.log("[ amModel Error ] : File [" + fileName + "] Not Found");
            return False;

         f = open( fileName, "r" );
         if f.mode == "r":
             myContents = f.read();
             try:
                 if( type == "json" ):
                     myCFG = dict( JSON.loads( myContents ) );
                     self.log( "File ["+fileName+"] loaded." );
                 else:
                     myCFG = myContents;
             except:
                 self.log( "File ["+fileName+"] could not be loaded. Reason : ["+ str(sys.exc_info()[1]) +"]" );
         f.close();
         return myCFG;
     except:
         self.log( "Unexpected error upon loading Storage ["+fileName+"]:" + str( sys.exc_info()[1] ) );
         return False;

 def logFile( self , myString ) : 
     myCurrentTime = datetime.datetime.now();
     myPrefix = "[" + datetime.datetime.strftime( myCurrentTime , "%Y-%m-%d %H:%M:%S" ) + "] : ";

     fd = open( os.path.abspath( self.cfg["logs"]["path"]+"log.log" ) , "a+");
     fd.write( myPrefix + str( myString ) + "\n");
     fd.close();

 def log_curl( self , method , postData , endpoint , file=False , auth=False ):
     myMethod      = "";
     myAuth        = "";
     myContentType = "Content-type: application/json";
     myEndpoint    = endpoint;

     if( method     == "post" ):   myMethod = "-XPOST";
     elif( method   == "get" ):    myMethod = "-XGET";
     elif( method   == "delete" ): myMethod = "-XDELETE";
     elif( method   == "put" ):    myMethod = "-XPUT";
     else: myMethod =  "XGET";

     if( auth is not False ): myAuth = auth;

     if( file == False ):
         myPostData  = JSON.dumps( postData ).replace( "'", "\\\"" ).replace( "\"", "\\\"" );
         myLogString = f"curl {myMethod} -u {myAuth} -H \"{myContentType}\" -d \"{myPostData}\" \"{myEndpoint}\" ";
     else:
         myFileName  = file["name"];
         myFilePath  = file["path"];
         myLogString = f"curl -u {myAuth} -F name=\"{myFileName}\" -F filedata=@{myFilePath}\" \"{myEndpoint}\" ";

     print();
     print( " [ CURL ] " )
     print( myLogString );
     print();
     return myLogString;

 def getUID( self , hash ):
     currentDate     = datetime.datetime.now();
     currentTS       = round( currentDate.timestamp() );
     myStringHash    = str( currentTS ) + str( hash );
     
     return myStringHash;

 def isValidJSON( self , json ):
     try:
         myJSON = JSON.loads( json );
     except ValueError as error :
         return False;
     return True;

 def isInt( self , value ):
     try:
         isValueInt = int( value );
         return True;
     except( Exception ) as error:
         return False;

 def createFile( self , fileName , myString ) : 
     myCurrentTime = datetime.datetime.now();
     myPrefix = "[" + datetime.datetime.strftime( myCurrentTime , "%Y-%m-%d %H:%M:%S" ) + "] : ";

     fd = open( os.path.abspath( self.cfg["logs"]["path"] + datetime.datetime.strftime( myCurrentTime , "%Y_%m_%d_%H_%M_%S" ) + "_" + fileName + ".log" ) , "a+");
     fd.write( myPrefix + str( myString ) + "\n");
     fd.close();

 def getUID( self , hash = None ):
    part1 = datetime.datetime.now();
    part2 = random.random();
    
    if( hash is None ):
        myUniqueString = str( part1 ) + str( part2 );
    else:
        myUniqueString = str( hash ) + str( part1 ) + str( part2 );

    myHash = hashlib.sha256();
    myHash.update( bytes( myUniqueString , "utf-8" ) );
    myUID = myHash.hexdigest();
    return myUID;

 def json_dump( self , data ):
     print( JSON.dumps(data, indent=4, cls=SafeJSONEncoder) );