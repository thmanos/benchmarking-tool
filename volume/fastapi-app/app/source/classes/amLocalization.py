import os;
import datetime;
import sys;
import json as JSON;
from classes.amTools import amTool;

class amLocalization:
 def __init__( self , cfg ):
     """Class for Localization Levels"""
     self.amTool = amTool();
     self.amTool.log( "Localization class has been Initiated" );
     self.locale = dict();
     self.loadLocalizationFile();
     self.loadLocalizationPool();
     self.LangMapping = {
      "α" : "a", "β" : "v", "γ" : "g", "δ" : "d", "ε" : "e", "ζ" : "z",  "η" : "i",   "θ" : "th",
      "ι" : "i", "κ" : "k", "λ" : "l", "μ" : "m", "ν" : "n", "ξ" : "x",  "ο" : "o",   "π" : "p",
      "ρ" : "r", "σ" : "s", "τ" : "t", "υ" : "u", "φ" : "f", "χ" : "ch", "ψ" : "ps",  "ω" : "o",
      "ή" : "i", "ί" : "i", "ό" : "o", "ώ" : "o", "ά" : "a", "έ" : "e",  "ύ" : "u",   "ς" : "s"
     };

 def loadLocalizationFile( self ):
     fd          = open( "../resources/localization/en.json", "r" , encoding='UTF-8' );
     myFileText  = fd.read();
     self.locale = JSON.loads( myFileText );
     fd.close();

 def loadLocalizationPool( self ):
     fd               = open( "../resources/localization/en_pool.json", "r" , encoding='UTF-8' );
     myFileText       = fd.read();
     self.locale_pool = JSON.loads( myFileText );
     fd.close();

 def translate( self , text , add_to_file = False ):
     # If it is not a String return the value back
     if( isinstance( text , str ) is False ):
         return text;
     else:
         myStringToSearch = text.lower().replace( " " , "_" );

         if myStringToSearch in self.locale :
             return self.locale[ myStringToSearch ];
         else:
             if add_to_file == True :
                 if myStringToSearch not in self.locale_pool:
                     self.addToLangFile( myStringToSearch );

         if( myStringToSearch[0] in self.LangMapping ):
             return self.transliterate( myStringToSearch );
         else:
             return myStringToSearch;

 def transliterate( self , text ):
     myTransString = "";

     for character in text.lower():
         if( character in self.LangMapping ):
             myTransString = myTransString + self.LangMapping[ character ];
         else:
             myTransString = myTransString + character;

     return myTransString;

 def addToLangFile( self , text ):
     fd       = open( "../resources/localization/en_pool.json" , "r+" , encoding='UTF-8' );
     myLocale = JSON.loads( fd.read() );
     myLocale[ text ] = text;
     fd.seek( 0, 0 );
     fd.truncate();
     fd.write( JSON.dumps( myLocale ) );
     fd.close();
     self.loadLocalizationPool();