# population-api

A Flask REST API with built-in places database that returns the approximate population in an area for a given place name and radius(km).

### Description
Imported data is stored as key-value pairs in Redis.
There are two types of keys:
- Place name keys
     - Insert (place name)-(latitude,longitude) pairs to redis
     - Ex: 'Ukraine': '48.217892,23.1328'
- Geohash keys
     - Insert (geohash)-(population_set) pairs to redis
     - Ex: 'sp8f': {b'1052',b'11223',b'1419',b'15853'}

Data import process finds the level 4 geohash of a given geolocation and stores the population value as a set.
If the given place is a city, the same process is applied to the neighboring geohashes as well. 

The same process also puts a record in the database for each name, ascii name and alternate name with their respective geolocation.

Then each API call finds the geohashes in the given area, unions all population values and returns the sum as the approximate population.
![Image](/images/geohash1.png?raw=true)

### Docker Usage

Create a docker network:
~~~
docker network create my-pop-network
~~~

Start redis and flask API:
If prompted, change the docker-compose.yml version accordingly. (Ex: 3.9 to 3.3)
~~~
cd web_service
docker-compose up
~~~

Example API call:
~~~
http://127.0.0.1:5000/population?place=Istanbul&radius=200
~~~
Response:
~~~
{"population": 296088}
~~~

### API Documentation

Swagger UI for API docs can be accessed from the link below:

~~~
http://localhost:5000/docs
~~~

![Image](/images/docs.png?raw=true)


## Additional Data import
20 of the most populated countries are included in the database:  
['US', 'MX', 'FR', 'CN', 'IT', 'DE', 'ID', 'ES', 'RO', 'GB', 'RU', 'AU', 'PH', 'PL', 'IN', 'AT', 'UA', 'CZ', 'BE', 'TR']  
Use the 2-letter country codes found in the link below to import additional places by country:  
https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes  
~~~
cd data_import
docker build -t data-import .
docker run --network my-pop-network data-import <2-letter-cc>
~~~

Example import for Norway and test with Oslo:
~~~
cd data_import
docker build -t data-import .
docker run --network my-pop-network data-import NO
curl "curl "localhost:5000/population?place=Oslo&radius=30"
~~~

### Limitations and Todos

 - Bulk data import
     - Currently initial data insertion takes ~8 minutes.
      - Redis backup files are used to speed up this process for the initial 20 countries.
 - Flask is not suitable for production use
      - Better input validation, error handling, routing, WSGI is necessary for prod use
 - Places with same names
      - Currently different places with same names overwrites previously inserted keys(place names)

### References
- Simple API docs: https://github.com/sanjan/flask_swagger
- Dataset: http://download.geonames.org/export/dump/readme.txt
- proximityhash module and images: https://github.com/ashwin711/proximityhash
