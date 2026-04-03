"""
The following libraries are needed
    # pip install requests
    # pip install pytest pytest-html
    # pip install jsonschema
    # pip install pytest-asyncio

To execute the test , navigate into the folder where the "test_scenario.py" file resides and 
execute the following command : 
    $ pytest --tb=short -rP test_scenario.py
"""

import requests;
import pytest;
import json;
from collections.abc import Mapping;

# CFG
printResponses = False; #This can greatly increase the verbosity level.
printCurls     = False; #This will print out every Curl executed in the unit tests.

# Global Variables for this test only
parcelDetail = {
        "id"      : "",
        "name"    : "",
        "polygon" : "",
        "country" : "",
        "county"  : "",
        "ektaria" : "",
        "dat"     : "",
        "user"    : ""
      };

configuration = {
  "username" : "admin" , 
  "password" : "123456" , 
  "endPoint" : "http://localhost:8585/",
  "aggregations" : {
    "sprays" : {
      "endPoint"         : "parcels/5/aggregation/" , 
      "expectedResponse" : { "from_date" : "" , "to_date" : "" , "type" : "" , "parcel" : [] , "aggregations" : {} },
      "body"             : {
        "event_type" : "sprays" , 
        "fromdate"   : "2023-08-29" , 
        "todate"     : "2023-08-30" 
      }
    },
    "irrigations" : {
      "endPoint"         : "parcels/5/aggregation/" , 
      "expectedResponse" : { "from_date" : "" , "to_date" : "" , "type" : "" , "parcel" : [] , "aggregations" : {} },
      "body"             : {
        "event_type" : "irrigations" , 
        "fromdate"   : "2023-08-29" , 
        "todate"     : "2023-08-30" 
      }
    },
    "harvest" : {
      "endPoint"         : "parcels/5/aggregation/" , 
      "expectedResponse" : { "from_date" : "" , "to_date" : "" , "type" : "" , "parcel" : [] , "aggregations" : {} },
      "body"             : {
        "event_type" : "harvest" , 
        "fromdate"   : "2023-08-29" , 
        "todate"     : "2023-08-30" 
      }
    },
    "fertilizations" : {
      "endPoint"         : "parcels/5/aggregation/" , 
      "expectedResponse" : { "from_date" : "" , "to_date" : "" , "type" : "" , "parcel" : [] , "aggregations" : {} },
      "body"             : {
        "event_type" : "fertilizations" , 
        "fromdate"   : "2023-08-29" , 
        "todate"     : "2023-08-30" 
      }
    }
  },
  "parcels" : {
    "create" : {
      "endPoint"         : "parcel" , 
      "expectedResponse" : { "id" : "" },
      "body"             : { 
        "name"    : "myUnitTest" , 
        "dat"     : "DAT_1234_test" , 
        "polygon" : "POLYGON((23.9450328078221 40.76302784325,23.9450894016528 40.7640470723677,23.9453283533882 40.7646519345938,23.945674204585 40.7649996088149,23.9461458198534 40.7654377709961,23.9464413654214 40.7658759302886,23.9466614525461 40.766456963156,23.9467997930249 40.7665712641057,23.9475795302708 40.765975944504,23.946843810452 40.7652996549675,23.946604858716 40.7650424726334,23.9460640732081 40.7645804944596,23.9458628506938 40.7642994958554,23.9457056456045 40.7640375469339,23.9456616281802 40.7634564929139,23.945655339977 40.7632516939747,23.9455232877018 40.7631421500972,23.9454478292589 40.7630468944047,23.9452591831513 40.7630278432499,23.9451145544687 40.7630421316166,23.9450328078221 40.76302784325))" , 
        "country" : 1 , 
        "county"  : 2 , 
        "user"    : "thanasis@thanasis.gr" 
      }
    },
    "update" : {
      "endPoint"         : "parcel" , 
      "expectedResponse" : { "success" : "ok" },
      "body"             : { 
        "id"      : parcelDetail[ "id" ] ,
        "name"    : "myUnitTest_UPDATED" , 
        "dat"     : "DAT_1234_test_UPDATED" , 
        "polygon" : "POLYGON((23.9450328078221 40.76302784325,23.9450894016528 40.7640470723677,23.9453283533882 40.7646519345938,23.945674204585 40.7649996088149,23.9461458198534 40.7654377709961,23.9464413654214 40.7658759302886,23.9466614525461 40.766456963156,23.9467997930249 40.7665712641057,23.9475795302708 40.765975944504,23.946843810452 40.7652996549675,23.946604858716 40.7650424726334,23.9460640732081 40.7645804944596,23.9458628506938 40.7642994958554,23.9457056456045 40.7640375469339,23.9456616281802 40.7634564929139,23.945655339977 40.7632516939747,23.9455232877018 40.7631421500972,23.9454478292589 40.7630468944047,23.9452591831513 40.7630278432499,23.9451145544687 40.7630421316166,23.9450328078221 40.76302784325))" , 
        "country" : 5 , 
        "county"  : 6 , 
        "user"    : "thanasis_UPDATED@thanasis.gr" 
      }
    },
    "delete" : {
      "endPoint"         : "parcel" , 
      "expectedResponse" : { "success" : "ok" },
      "body"             : { 
        "id" : parcelDetail[ "id" ] 
      }
    },
    "get_id" : {
      "endPoint"         : "parcel/ids/" + str( parcelDetail[ "id" ]  ) , 
      "expectedResponse" : [ {
        "id"      : "",
        "name"    : "",
        "polygon" : "",
        "country" : "",
        "county"  : "",
        "ektaria" : "",
        "dat"     : "",
        "user"    : ""
      }],
      "body"             : { }
    },
    "get_name" : {
      "endPoint"         : "parcel/name/" + str( parcelDetail[ "name" ]  ) , 
      "expectedResponse" : [ {
        "id"      : "",
        "name"    : "",
        "polygon" : "",
        "country" : "",
        "county"  : "",
        "ektaria" : "",
        "dat"     : "",
        "user"    : ""
      }],
      "body"             : { }
    },
    "get_user" : {
      "endPoint"         : "parcel/user/" + str( parcelDetail[ "user" ]  ) , 
      "expectedResponse" : [ {
        "id"      : "",
        "name"    : "",
        "polygon" : "",
        "country" : "",
        "county"  : "",
        "ektaria" : "",
        "dat"     : "",
        "user"    : ""
      }],
      "body"             : { }
    },
    "get_country" : {
      "endPoint"         : "parcel/country/" + str( parcelDetail[ "country" ]  ) , 
      "expectedResponse" : [ {
        "id"      : "",
        "name"    : "",
        "polygon" : "",
        "country" : "",
        "county"  : "",
        "ektaria" : "",
        "dat"     : "",
        "user"    : ""
      }],
      "body"             : { }
    },
    "get_county" : {
      "endPoint"         : "parcel/county/" + str( parcelDetail[ "county" ]  ) , 
      "expectedResponse" : [ {
        "id"      : "",
        "name"    : "",
        "polygon" : "",
        "country" : "",
        "county"  : "",
        "ektaria" : "",
        "dat"     : "",
        "user"    : ""
      }],
      "body"             : { }
    }
  }
}

def formatCurl( request ):
    headersList = [ '"{} : {}"'.format( headerProperty, headerValue ) for headerProperty, headerValue in request.headers.items() ];
    headers     = " --header ".join( headersList );

    return ( "curl -X " + str( request.method ) + 
                " " + headers + 
                " -d '" + str( request.body ) + 
                "' '" + str( request.url ) + "'"
              );

def validateResponse( expectedResponse , receivedResponse ):

    if expectedResponse is None : 
        return { "success" : "No issues in validation" };

    myParsedResponse = receivedResponse;
    if isinstance( expectedResponse, Mapping ) or isinstance( expectedResponse, list ):
        try : 
            myParsedResponse = json.loads( receivedResponse );
        except Exception as error :
            return { "error" : "Response not a valid JSON" };
    else:
        if isinstance( receivedResponse, str ):
            return { "success" : "No issues in validation" };
        else:
            return { "error" : "Expected response should be a String not an Object." };

    if isinstance( expectedResponse, Mapping ):
        if isinstance( myParsedResponse, Mapping ) == False:
            return { "error" : "Expected response should be an Object." };
        for property in expectedResponse:
            if( property not in myParsedResponse ) :
                return { "error" : "Missing response property ( " + str( property ) + " )" };

    if isinstance( expectedResponse, list ):
        if isinstance( myParsedResponse, list ) == False:
            return { "error" : "Expected response should be a List." };
        for property in expectedResponse[ 0 ]:
            if( property not in myParsedResponse[ 0 ] ) :
                return { "error" : "Missing response property ( " + str( property ) + " )" };

    return { "success" : "No issues in validation" };

def resPrint( response ):
    print( ">>> Response <<<" );
    try:
        myJSON = json.loads( response );
        if( isinstance( myJSON, list ) ):
            print( myJSON[ 0 ] );
            print();
        else:
            print( response );
            print();
    except:
        print( response );
        print();

def executeRequest( cfg , method ):
    if( method == "GET" ):
        myURLParemeters = list();
        for queryParameter in cfg[ "body" ] : 
            if( cfg[ "body" ][ queryParameter ] is not None ) : 
                myURLParemeters.append( str( queryParameter ) + "=" + str( cfg[ "body" ][ queryParameter ] ) );

        myCompleteURL = configuration[ "endPoint" ] + cfg[ "endPoint" ] + "?" + "&".join( myURLParemeters );

        myResponse = requests.get( 
            auth    = ( configuration[ "username" ] , configuration[ "password" ] ) , 
            url     = myCompleteURL ,
            headers = { 'content-type': 'application/json' }
        );
    elif( method == "PUT" ):
        myURLParemeters = list();
        for queryParameter in cfg[ "body" ] : 
            if( cfg[ "body" ][ queryParameter ] is not None ) : 
                myURLParemeters.append( str( queryParameter ) + "=" + str( cfg[ "body" ][ queryParameter ] ) );

        myCompleteURL = configuration[ "endPoint" ] + cfg[ "endPoint" ] + "?" + "&".join( myURLParemeters );

        myResponse = requests.put( 
            auth    = ( configuration[ "username" ] , configuration[ "password" ] ) , 
            url     = myCompleteURL ,
            headers = { 'content-type': 'application/json' }
        );
    elif( method == "DELETE" ):
        myURLParemeters = list();
        for queryParameter in cfg[ "body" ] : 
            if( cfg[ "body" ][ queryParameter ] is not None ) : 
                myURLParemeters.append( str( queryParameter ) + "=" + str( cfg[ "body" ][ queryParameter ] ) );

        myCompleteURL = configuration[ "endPoint" ] + cfg[ "endPoint" ] + "?" + "&".join( myURLParemeters );

        myResponse = requests.delete( 
            auth    = ( configuration[ "username" ] , configuration[ "password" ] ) , 
            url     = myCompleteURL ,
            headers = { 'content-type': 'application/json' }
        );
    elif( method == "POST" ):
        myURLParemeters = list();
        for queryParameter in cfg[ "body" ] : 
            if( cfg[ "body" ][ queryParameter ] is not None ) : 
                myURLParemeters.append( str( queryParameter ) + "=" + str( cfg[ "body" ][ queryParameter ] ) );

        myCompleteURL = configuration[ "endPoint" ] + cfg[ "endPoint" ] + "?" + "&".join( myURLParemeters );

        myResponse = requests.post( 
            auth    = ( configuration[ "username" ] , configuration[ "password" ] ) , 
            url     = myCompleteURL ,
            headers = { 'content-type': 'application/json' }
        );

    if( myResponse.status_code == 200 ):
        myValidation = validateResponse( cfg[ "expectedResponse" ] , myResponse.text );

        if( "error" in myValidation ) :
            return { "error" : myValidation[ "error" ] };
        else:
            print( ">>> CURL executed <<<" );
            print( formatCurl( myResponse.request ) );
            print( "" );
            resPrint( myResponse.text );
            return { "res" : myResponse.text };
    else:
        return { "error" : myResponse };

def test_add_parcel():
    global parcelDetail;
    try:
        myResult = executeRequest( configuration[ "parcels" ][ "create" ] , "PUT" );
        if( "error" not in myResult ): 
            print( ">>> Resolution >>>" );
            print( "Succesfully passed scenario : 'test_add_parcel' " );
            myParsedResponse = json.loads( myResult[ "res" ] );
            parcelDetail     = myParsedResponse;
            assert True;
        else:
            assert False , myResult;
    except Exception as error :
        assert False , error;

def test_update_parcel():
    try:
        configuration[ "parcels" ][ "update" ][ "body" ][ "id" ] = parcelDetail[ "id" ];
        myResult = executeRequest( configuration[ "parcels" ][ "update" ] , "POST" );
        if( "error" not in myResult ): 
            print( ">>> Resolution >>>" );
            print( "Succesfully passed scenario : 'test_update_parcel' " );
            assert True;
        else:
            assert False , myResult;
    except Exception as error :
        assert False , error;

def test_get_id_parcel():
    global parcelDetail;
    try:
        configuration[ "parcels" ][ "get_id" ][ "endPoint" ] = "parcel/ids/" + str( parcelDetail[ "id" ] );
        myResult = executeRequest( configuration[ "parcels" ][ "get_id" ] , "GET" );
        if( "error" not in myResult ): 
            print( ">>> Resolution >>>" );
            print( "Succesfully passed scenario : 'test_get_id_parcel' " );
            myParsedResponse = json.loads( myResult[ "res" ] );
            parcelDetail     = myParsedResponse[ 0 ];
            for item in parcelDetail:
                print( item + " : " + str( parcelDetail[ item ] ) );
            assert True;
        else:
            assert False , myResult;
    except Exception as error :
        assert False , error;

def test_get_name_parcel():
    try:
        configuration[ "parcels" ][ "get_name" ][ "endPoint" ] = "parcel/name/" + str( parcelDetail[ "name" ] );
        myResult = executeRequest( configuration[ "parcels" ][ "get_id" ] , "GET" );
        if( "error" not in myResult ): 
            print( ">>> Resolution >>>" );
            print( "Succesfully passed scenario : 'test_get_name_parcel' " );
            assert True;
        else:
            assert False , myResult;
    except Exception as error :
        assert False , error;

def test_get_user_parcel():
    try:
        configuration[ "parcels" ][ "get_user" ][ "endPoint" ] = "parcel/user/" + str( parcelDetail[ "user" ] );
        myResult = executeRequest( configuration[ "parcels" ][ "get_user" ] , "GET" );
        if( "error" not in myResult ): 
            print( ">>> Resolution >>>" );
            print( "Succesfully passed scenario : 'test_get_user_parcel' " );
            assert True;
        else:
            assert False , myResult;
    except Exception as error :
        assert False , error;

def test_get_country_parcel():
    try:
        configuration[ "parcels" ][ "get_country" ][ "endPoint" ] = "parcel/country/" + str( parcelDetail[ "country" ] );
        myResult = executeRequest( configuration[ "parcels" ][ "get_country" ] , "GET" );
        if( "error" not in myResult ): 
            print( ">>> Resolution >>>" );
            print( "Succesfully passed scenario : 'test_get_country_parcel' " );
            assert True;
        else:
            assert False , myResult;
    except Exception as error :
        assert False , error;

def test_get_county_parcel():
    try:
        configuration[ "parcels" ][ "get_county" ][ "endPoint" ] = "parcel/county/" + str( parcelDetail[ "county" ] );
        myResult = executeRequest( configuration[ "parcels" ][ "get_county" ] , "GET" );
        if( "error" not in myResult ): 
            print( ">>> Resolution >>>" );
            print( "Succesfully passed scenario : 'test_get_county_parcel' " );
            assert True;
        else:
            assert False , myResult;
    except Exception as error :
        assert False , error;

def test_delete_parcel():
    try:
        configuration[ "parcels" ][ "delete" ][ "body" ][ "id" ] = parcelDetail[ "id" ];
        myResult = executeRequest( configuration[ "parcels" ][ "delete" ] , "DELETE" );
        if( "error" not in myResult ): 
            print( ">>> Resolution >>>" );
            print( "Succesfully passed scenario : 'test_delete_parcel' " );
            assert True;
        else:
            assert False , myResult;
    except Exception as error :
        assert False , error;

def __test_aggregations_sprays():
    try:
        myResult = executeRequest( configuration[ "parcels" ][ "aggregation_sprays" ] , "GET" );
        if( myResult is True ): 
            print( ">>> Resolution >>>" );
            print( "Succesfully passed scenario : 'test_aggregations_sprays' " );
            assert True;
        else:
            assert False , myResult;
    except Exception as error :
        assert False , error;

def __test_aggregation_irrigations():
    try:
        myResult = executeRequest( configuration[ "parcels" ][ "aggregation_irrigations" ] , "GET" );
        if( myResult is True ): 
            print( ">>> Resolution >>>" );
            print( "Succesfully passed scenario : 'test_aggregation_irrigations' " );
            assert True;
        else:
            assert False , myResult;
    except Exception as error :
        assert False , error;

def __test_aggregation_harvest():
    try:
        myResult = executeRequest( configuration[ "parcels" ][ "aggregation_harvest" ] , "GET" );
        if( myResult is True ): 
            print( ">>> Resolution >>>" );
            print( "Succesfully passed scenario : 'test_aggregation_harvest' " );
            assert True;
        else:
            assert False , myResult;
    except Exception as error :
        assert False , error;

def __test_aggregation_fertilizations():
    try:
        myResult = executeRequest( configuration[ "parcels" ][ "aggregation_fertilizations" ] , "GET" );
        if( myResult is True ): 
            print( ">>> Resolution >>>" );
            print( "Succesfully passed scenario : 'test_aggregation_fertilizations' " );
            assert True;
        else:
            assert False , myResult;
    except Exception as error :
        assert False , error;
