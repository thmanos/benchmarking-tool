import time;
import datetime;
from datetime import timedelta;
from typing import Optional , List;
from enum import Enum;
from pydantic import BaseModel , Field , create_model;

class EventTypes( str , Enum ):
				HARVEST = "harvest";
				SPRAY = "spray";
				IRRIGATION = "irrigation";
				PHAENOLOGICAL_STAGE = "phaenological_stage";
				FERTILIZATION = "fertilization";

class MeteoMeasurementTypes( str , Enum ):
    TEMPERATURE = "temperature";
    HUMIDITY = "humidity";
    WINDSTRENGTH = "windstrength";
    LEAFWETNESS = "leafwetness";
    RAIN = "rain";

class Unit( str , Enum ):
    TON = "ton";
    KG = "kg";
    GR = "gr";
    KL = "kl";
    LT = "lt";
    ML = "ml";
    M3 = "m3";

class UnitReference( str , Enum ):
				STREMMA = "stremma";
				HECTAR = "hectar";

class FuelType( str , Enum ):
				DIESEL = "diesel";
				GAS = "gas";
				ELECTRICITY = "electricity";
				WINDTURBINE = "windturbine";
				HYDRO = "hydro";

