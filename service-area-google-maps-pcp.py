from __future__ import division
import hashlib
import hmac
import base64
import urllib.parse as urlparse
import configparser as ConfigParser
import simplejson
import urllib.request as urllib2
import time
import datetime
from math import cos, sin, tan, sqrt, pi, radians, degrees, asin, atan2

# urlparse --> urllib.parse (Python 3)
# ConfigParser --> configparser (Python 3)
# pip install simplejson
# urllib2 --> urllib.request AND urllib.error

def build_url(origin='',
              destination='',
              mode='',
              config_path='config/'):
    """
    Determine the url to pass for the desired search.
    """
    if origin == '':
        raise Exception('origin cannot be blank.')
    elif isinstance(origin, list) and len(origin) == 2:
        origin_str = ','.join(map(str, origin))
    else:
        raise Exception('origin should be a list [lat, lng]')

    if destination == '':
        raise Exception('destination cannot be blank.')
    elif isinstance(destination, list):
        destination_str = ''
        for element in destination:
            if isinstance(element, str):
                destination_str = '{0}|{1}'.format(destination_str, element.replace(' ', '+'))
            elif isinstance(element, list) and len(element) == 2:
                destination_str = '{0}|{1}'.format(destination_str, ','.join(map(str, element)))
            else:
                raise Exception('destination must be a list of lists [lat, lng]')
        destination_str = destination_str.strip('|')
    else:
        raise Exception('destination must be a a list of lists [lat, lng]')

	# mode must be either 'driving' or 'walking' or 'transit' or 'bicycling'        
    if mode not in ['driving', 'walking', 'transit', 'bicycling']:
    	raise Exception("mode must be either 'driving' or 'walking' or 'transit' or 'bicycling'")

    # Get the Google API keys from an external config file
    # If it's your own personal Google Maps account, it looks like this:
    # [api]
    # api_number=<your api number>
    #
    config = ConfigParser.SafeConfigParser()
    config.read('{}google_maps.cfg'.format(config_path))
    key = config.get('api', 'api_number')    
    # Convert the URL string to a URL, which we can parse
    # using the urlparse() function into path and query
    # Note that this URL should already be URL-encoded
    prefix = 'https://maps.googleapis.com/maps/api/distancematrix/json?&units=imperial'

    url = urlparse.urlparse('{0}&mode={1}&origins={2}&destinations={3}&key={4}'.format(prefix, mode, origin_str, destination_str, key))
    full_url = url.scheme + '://' + url.netloc + url.path + '?' + url.query
    return full_url

def parse_json(url=''):
    """
    Parse the json response from the API
    """
    req = urllib2.Request(url)
    opener = urllib2.build_opener()
    f = opener.open(req)
    d = simplejson.load(f)

    if not d['status'] == 'OK':
        raise Exception('Error. Google Maps API return status: {}'.format(d['status']))

    addresses = d['destination_addresses']

    i = 0
    durations = [0] * len(addresses)
    for row in d['rows'][0]['elements']:
        if not row['status'] == 'OK':
            # raise Exception('Error. Google Maps API return status: {}'.format(row['status']))
            durations[i] = 9999
        else:
            if 'duration_in_traffic' in row:
                durations[i] = row['duration_in_traffic']['value'] / 60
            else:
                durations[i] = row['duration']['value'] / 60
        i += 1
    return [addresses, durations]

def geocode_address(address='',
                    config_path='config/'):
    """
    For use in calculating distances between 2 locations, the [lat, lng] is needed instead of the address.
    """
    # Convert origin and destination to URL-compatible strings
    if address == '':
        raise Exception('address cannot be blank.')
    elif isinstance(address, str) or isinstance(address, unicode):
        address_str = address.replace(' ', '+')
    else:
        raise Exception('address should be a string.')

    config = ConfigParser.SafeConfigParser()
    config.read('{}google_maps.cfg'.format(config_path))
    key = config.get('api', 'api_number')

    prefix = 'https://maps.googleapis.com/maps/api/geocode/json'
    url = urlparse.urlparse('{0}?address={1}&key={2}'.format(prefix,
                                                             address_str,
                                                             key))
    full_url = url.scheme + '://' + url.netloc + url.path + '?' + url.query

    # Request geocode from address
    req = urllib2.Request(full_url)
    opener = urllib2.build_opener()
    f = opener.open(req)
    d = simplejson.load(f)

    # Parse the json to pull out the geocode
    if not d['status'] == 'OK':
        raise Exception('Error. Google Maps API return status: {}'.format(d['status']))
    geocode = [d['results'][0]['geometry']['location']['lat'],
               d['results'][0]['geometry']['location']['lng']]
    return geocode

def select_destination(origin='',
                       angle='',
                       radius='',
                       config_path='config/'):
    """
    Given a distance and polar angle, calculate the geocode of a destination point from the origin.
    """
    if origin == '':
        raise Exception('origin cannot be blank.')
    if angle == '':
        raise Exception('angle cannot be blank.')
    if radius == '':
        raise Exception('radius cannot be blank.')

    if isinstance(origin, list) and len(origin) == 2:
        origin_geocode = origin
    else:
        raise Exception('origin should be a list: [lat, lng]')

    # Find the location on a sphere a distance 'radius' along a bearing 'angle' from origin
    # This uses haversines rather than simple Pythagorean distance in Euclidean space because spheres are more complicated than planes.
    r = 3963.1676  # Radius of the Earth in miles
    bearing = radians(angle)  # Bearing in radians converted from angle in degrees
    lat1 = radians(origin_geocode[0])
    lng1 = radians(origin_geocode[1])
    lat2 = asin(sin(lat1) * cos(radius / r) + cos(lat1) * sin(radius / r) * cos(bearing))
    lng2 = lng1 + atan2(sin(bearing) * sin(radius / r) * cos(lat1), cos(radius / r) - sin(lat1) * sin(lat2))
    lat2 = degrees(lat2)
    lng2 = degrees(lng2)
    return [lat2, lng2]

def get_bearing(origin='',
                destination=''):
    """
    Calculate the bearing from origin to destination
    """
    if origin == '':
        raise Exception('origin cannot be blank')
    if destination == '':
        raise Exception('destination cannot be blank')

    bearing = atan2(sin((destination[1] - origin[1]) * pi / 180) * cos(destination[0] * pi / 180),
                    cos(origin[0] * pi / 180) * sin(destination[0] * pi / 180) -
                    sin(origin[0] * pi / 180) * cos(destination[0] * pi / 180) * cos((destination[1] - origin[1]) * pi / 180))
    bearing = bearing * 180 / pi
    bearing = (bearing + 360) % 360
    return bearing

def sort_points(origin='',
                serv='',
                config_path='config/'):
    """
    Put the service area points in a proper order
    """
    if origin == '':
        raise Exception('origin cannot be blank.')
    if serv == '':
        raise Exception('serv cannot be blank.')

    if isinstance(origin, list) and len(origin) == 2:
        origin_geocode = origin
    else:
        raise Exception('origin should be a list: [lat, lng]')

    bearings = []
    for row in serv:
        bearings.append(get_bearing(origin_geocode, row))

    points = zip(bearings, serv)
    sorted_points = sorted(points)
    sorted_serv = [point[1] for point in sorted_points]
    return sorted_serv

def get_service_area(origin='',
                  duration='',
                  mode='',
                  number_of_angles=10,
                  tolerance=0.1,
                  config_path='config/'):
    """
    Putting it all together.
    Given a starting location and amount of time for the service area to represent (e.g. a 15 minute service area from origin)
      use the Google Maps distance matrix API to check travel times along a number of bearings around the origin for
      an equal number of radii. Perform a binary search on radius along each bearing until the duration returned from
      the API is within a tolerance of the service area duration.
    origin = string address or [lat, lng] 2-list
    duration = minutes that the service area contour value should map
    mode = mode of transportation to use
    number_of_angles = how many bearings to calculate this contour for (think of this like resolution)
    tolerance = how many minutes within the exact answer for the contour is good enough
    config_path = where the google_maps.cfg file is located that contains API credentials (described in build_url)
    """
    if origin == '':
        raise Exception('origin cannot be blank')
    if duration == '':
        raise Exception('duration cannot be blank')
    if mode == '':
        raise Exception('mode cannot be blank')  
    if not isinstance(number_of_angles, int):
        raise Exception('number_of_angles must be an int')
    if not isinstance(tolerance, float):
        raise Exception('tolerance must be a float')
    if isinstance(origin, list) and len(origin) == 2:
        origin_geocode = origin
    else:
        raise Exception('origin should be a list [lat, lng]')

    # Make a radius list, one element for each angle,
    # whose elements will update until the service area is found
    rad1 = [duration / 12] * number_of_angles  # initial r guess based on 5 mph speed
    phi1 = [i * (360 / number_of_angles) for i in range(number_of_angles)]
    data0 = [0] * number_of_angles
    rad0 = [0] * number_of_angles
    rmin = [0] * number_of_angles
    rmax = [1.25 * duration] * number_of_angles  # rmax based on 75 mph speed
    serv = [[0, 0]] * number_of_angles

    # Counter to ensure we're not getting out of hand
    j = 0

    # Here's where the binary search starts
    while sum([a - b for a, b in zip(rad0, rad1)]) != 0:
        rad2 = [0] * number_of_angles
        for i in range(number_of_angles):
            serv[i] = select_destination(origin, phi1[i], rad1[i], config_path)
            time.sleep(0.1)
        url = build_url(origin, serv, mode, config_path)
        data = parse_json(url)
        for i in range(number_of_angles):
            if (data[1][i] < (duration - tolerance)) & (data0[i] != data[0][i]):
                rad2[i] = (rmax[i] + rad1[i]) / 2
                rmin[i] = rad1[i]
            elif (data[1][i] > (duration + tolerance)) & (data0[i] != data[0][i]):
                rad2[i] = (rmin[i] + rad1[i]) / 2
                rmax[i] = rad1[i]
            else:
                rad2[i] = rad1[i]
            data0[i] = data[0][i]   
        rad0 = rad1
        rad1 = rad2
        j += 1
        if j > 500:
            raise Exception("This is taking too long, so I'm just going to quit.")

    for i in range(number_of_angles):
        serv[i] = geocode_address(data[0][i], config_path)
        # This does not work: serv[i] = data[0][i]
        time.sleep(0.1)

    serv = sort_points(origin, serv, config_path)
    return serv

def generate_service_area_map(origin='',
                           duration='',
                           mode='',
                           number_of_angles=10,
                           tolerance=0.1,
                           config_path='config/'):
    """
    Call the get_service_area function and generate a simple html file using its output.
    """
    if origin == '':
        raise Exception('origin cannot be blank')
    if duration == '':
        raise Exception('duration cannot be blank')
    if mode == '':
        raise Exception('mode cannot be blank')        
    if not isinstance(number_of_angles, int):
        raise Exception('number_of_angles must be an int')
    if not isinstance(tolerance, float):
        raise Exception('tolerance must be an float')
    if isinstance(origin, list) and len(origin) == 2:
        origin_geocode = origin
    else:
        raise Exception('origin should be a list: [lat, lng]')

    serv = get_service_area(origin, duration, mode, number_of_angles, tolerance, config_path)

    htmltext = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no">
    <meta charset="utf-8">
    <title>Service Area</title>
    <style>
      html, body, #map-canvas {{
        height: 100%;
        margin: 0px;
        padding: 0px
      }}
    </style>
    <script src="https://maps.googleapis.com/maps/api/js?v=3.exp&signed_in=true"></script>
    <script>
    function initialize() {{
      var mapOptions = {{
        zoom: 12,
        center: new google.maps.LatLng({0},{1}),
        mapTypeId: google.maps.MapTypeId.TERRAIN
      }};
      var map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);
      var marker = new google.maps.Marker({{
          position: new google.maps.LatLng({0},{1}),
          map: map
      }});
      var serviceArea;
      var serviceAreaCoords = [
    """.format(origin_geocode[0], origin_geocode[1])

    for i in serv:
        htmltext += 'new google.maps.LatLng({},{}), \n'.format(i[0], i[1])

    htmltext += """
      ];
      serviceArea = new google.maps.Polygon({
        paths: serviceAreaCoords,
        strokeColor: '#000',
        strokeOpacity: 0.5,
        strokeWeight: 1,
        fillColor: '#000',
        fillOpacity: 0.25
      });
      serviceArea.setMap(map);
    }
    google.maps.event.addDomListener(window, 'load', initialize);
    </script>
    </head>
    <body>
    <div id="map-canvas"></div>
    </body>
    </html>
    """
    with open('service_area.html', 'w') as f:
        f.write(htmltext)
    return serv

origin = [39.9500, -75.1667]
duration = 30
mode = 'walking'
number_of_angles = 25
# get_service_area(origin, duration, mode, number_of_angles)
generate_service_area_map(origin, duration, mode, number_of_angles)
