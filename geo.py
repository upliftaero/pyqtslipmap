# These functions are taken in their entirety from MAVProxy's mav_util.py file
# Thanks to Andrew Tridgell
import math
from PyQt4.QtCore import *

radius_of_earth = 6378100.0 # in meters
circumference_of_earth = 40075000.0 # in meters

class QLatLon:
    def __init__(self, lat=0.0, lon=0.0):
        self.lat = lat
        self.lon = lon

    def distanceTo(self, coord):
        return gps_distance(self.lat, self.lon, coord.lat, coord.lon)

    def bearingTo(self, coord):
        return gps_bearing(self.lat, self.lon, coord.lat, coord.lon)

    def distanceXYTo(self, coord):
        return gps_relxy( self.lat, self.lon, coord.lat, coord.lon)

    def coordinateAtBearingRange(self, bearing, distance):
        return gps_newpos(self.lat, self.lon, bearing, distance)

    def coordinateAtOffset(self, east, north):
        return gps_offset(self.lat, self.lon, east, north)



def meters_per_pixel(lat, zoom):
    return circumference_of_earth * math.cos(lat)/2 ** (float(zoom)+8.0)

def gps_distance(lat1, lon1, lat2, lon2):
    '''return distance between two points in meters,
    coordinates are in degrees
    thanks to http://www.movable-type.co.uk/scripts/latlong.html'''
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    lon1 = math.radians(lon1)
    lon2 = math.radians(lon2)
    dLat = lat2 - lat1
    dLon = lon2 - lon1

    a = math.sin(0.5*dLat)**2 + math.sin(0.5*dLon)**2 * math.cos(lat1) * math.cos(lat2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0-a))
    return radius_of_earth * c


def gps_bearing(lat1, lon1, lat2, lon2):
    '''return bearing between two points in degrees, in range 0-360
    thanks to http://www.movable-type.co.uk/scripts/latlong.html'''
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    lon1 = math.radians(lon1)
    lon2 = math.radians(lon2)
    dLat = lat2 - lat1
    dLon = lon2 - lon1
    y = math.sin(dLon) * math.cos(lat2)
    x = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dLon)
    bearing = math.degrees(math.atan2(y, x))
    if bearing < 0:
        bearing += 360.0
    return bearing

def gps_relxy(lat1, lon1, lat2, lon2):
    '''return the x and y components of distance to the given coordinate'''
    bearing = gps_bearing(lat1, lon1, lat2, lon2)
    dist = gps_distance(lat1, lon1, lat2, lon2)
    dx = dist * math.sin(math.radians(bearing))
    dy = dist * math.cos(math.radians(bearing))
    print(dx, dy)
    return QPoint(dx, dy)


def wrap_valid_longitude(lon):
    ''' wrap a longitude value around to always have a value in the range
        [-180, +180) i.e 0 => 0, 1 => 1, -1 => -1, 181 => -179, -181 => 179
    '''
    return (((lon + 180.0) % 360.0) - 180.0)

def gps_newpos(lat, lon, bearing, distance):
    '''extrapolate latitude/longitude given a heading and distance
    thanks to http://www.movable-type.co.uk/scripts/latlong.html
    '''
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    brng = math.radians(bearing)
    dr = distance/radius_of_earth

    lat2 = math.asin(math.sin(lat1)*math.cos(dr) +
                     math.cos(lat1)*math.sin(dr)*math.cos(brng))
    lon2 = lon1 + math.atan2(math.sin(brng)*math.sin(dr)*math.cos(lat1),
                             math.cos(dr)-math.sin(lat1)*math.sin(lat2))
    newpos = QLatLon(math.degrees(lat2), wrap_valid_longitude(math.degrees(lon2)))
    return newpos

def gps_offset(lat, lon, east, north):
    '''return new lat/lon after moving east/north
    by the given number of meters'''
    bearing = math.degrees(math.atan2(east, north))
    distance = math.sqrt(east**2 + north**2)
    return gps_newpos(lat, lon, bearing, distance)

