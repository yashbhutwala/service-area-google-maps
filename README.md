# service-area-google-maps

For a given [lat,long] location, calculate a service area around it. Any point on an x-minute contour should take a total of x minutes of travel to reach from the origin. Any point within an x-minute contour should be reachable in fewer than x minutes.

### Parameters

__origin__ : must be a list containing [lat, lng]; For lat/long as per convention: N, E are positive; S, W are negative

__duration__ : Number of minutes for the service area

__mode__ : must be either 'driving' or 'walking' or 'transit' or 'bicycling', __default: 'driving'__

__number_of_angles__ : Number of points defining the service area (int), __default: 10__

__tolerance__ : Number of minutes that a test point can be away from duration to be considered acceptable, __default: 0.1__

__config_path__ : Path location (str) of the 'google_maps.cfg' file, __default: 'config/'__
  * Make a file called 'google_maps.cfg' in a directory called 'config/'
  * Format of the config file must be: (e.g. if your api_number were 1234567890, you would replace \<your api number\> below with 1234567890):

```
[api]
api_number=<your api number>
```

### Returns

* get_service_area: A list of [lat, lng] -- [[lat1, lng1], [lat2, lng2], ..., [latn, lngn]] where n = number_of_angles.

* generate_service_area_map: generates html file with an embedded Google Maps with service area

### Dependencies

This module makes use of the following Python modules that you must have installed.

* urllib.parse
* configparser
* simplejson
* urllib.request
* time
* math

### Use

```python
origin = [39.9500, -75.1667]
duration = 30
mode = 'walking'
number_of_angles = 10
get_service_area(origin, duration, mode, number_of_angles)
# OR generate html file
generate_service_area_map(origin, duration, mode, number_of_angles)
```
