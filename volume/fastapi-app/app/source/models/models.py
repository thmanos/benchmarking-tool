import time;
import datetime;
from datetime import timedelta;
from typing import Optional , List;
from enum import Enum;
from pydantic import BaseModel , Field , create_model;
import models.parametrics as Parametric;

class AggregationFunctions( str , Enum ):
    SUM = "sum";
    AVG = "avg";
    MIN = "min";
    MAX = "max";

class EventProperties( BaseModel ):
    amount               : float = Field( title  = "Amount used in the Event" );
    unit                 : Parametric.Unit;
    unitRef              : Parametric.UnitReference;
    metric               : str;
    target               : Optional[ str ] = Field( None );
    productName          : Optional[ str ] = Field( None );
    stage                : Optional[ str ] = Field( None );
    fuelConsumption      : Optional[ float ] = Field( None );
    fuelType             : Optional[ Parametric.FuelType ] = Field( None );
    fuelUnit             : Optional[ Parametric.Unit ] = Field( None );
    fuelUnitRef          : Optional[ str ] = Field( None );

class Event( BaseModel ):
    dat              : Optional[ str ] = Field( None );
    eventStart       : datetime.datetime;
    eventEnd         : Optional[ datetime.datetime ] = Field( None );
    duration         : Optional[ float ] = Field( None );
    type             : Parametric.EventTypes;
    crop             : str;
    variety          : Optional[ str ] = Field( None );
    comments         : Optional[ str ] = Field( None );
    properties       : Optional[ EventProperties ] = Field( None );
    parcelId         : str;

class MeteoData( BaseModel ):
    parcelId     : str;
    timestamp    : datetime.datetime;
    temperature  : Optional [ float ] = Field( None );
    humidity     : Optional [ float ] = Field( None );
    windstrength : Optional [ float ] = Field( None );
    leafwetness  : Optional [ float ] = Field( None );
    rain         : Optional [ float ] = Field( None );

class Parcel( BaseModel ):
    uid      : str;
    name     : str;
    polygon  : str;
    country  : str;
    county   : str;
    ektaria  : float;
    user     : Optional[ str ] = None;

class OrderBy( str , Enum ):
    asc  = "asc";
    desc = "desc";

class ParametricTables( str , Enum ):
    FuelType      = "FuelType";
    Unit          = "Unit";
    UnitReference = "UnitReference";
    EventType     = "EventType";
    Country       = "Country";
    County        = "County";