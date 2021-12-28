# ipmi-sensor
Reads ipmitool sensor on an interval and uploads the events to a rest api

## Overview

The default fan speed on an Ampere Falcon platform is really loud for at home use.  

This sets the default to 10% and checks the ipmi sensor every x interval seconds.
If the temperature goes above a threshold, the fan speed is set +5% for each interval
it is above. Once the temperature goes below the threshold, the fan speed decreases to 
the default fan speed.