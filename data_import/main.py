# Populate place and geohash databases

# Places database
# Insert place name-latitude,longitude pairs to redis
# Ex: 'Ukraine': '48.217892,23.1328'

# Geohashes database
# Insert geohash-population_set pairs to redis
# Ex: 'sp8f': {b'1052',b'11223',b'1419',b'15853'}

# Import libraries
import pandas as pd
import redis
import geohash as gh
import proximityhash as ph
import math
import logging
import sys
import time

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

# Default country list to be used if no input country arg is given
default_country_list = ['US', 'MX', 'FR', 'CN', 'IT', 'DE', 'ID', 'ES', 'RO', 'GB', 
                        'RU', 'AU', 'PH', 'PL', 'IN', 'AT', 'UA', 'CZ', 'BE', 'TR']


# Input country code
try:
    country_code_filter = [sys.argv[1]]
except:
    print('No country code given, using default country list: ' + str(default_country_list))
    country_code_filter = default_country_list
    
# Set input file name
input_file = 'cities500.txt'
# Set input file seperator
input_sep = '\t'
# Set input csv columns
input_columns = ['geonameid','name','asciiname','alternatenames','latitude','longitude',
    'feature_class','feature_code','country_code','cc2','admin1_code','admin2_code',
    'admin3_code','admin4_code','population','elevation','dem','timezone','modification_date']

# Connect to local redis server
try:
    r = redis.Redis(host='redis', port=6379, db=0)
    r.ping()
except Exception as e:
    logging.error(e)
    sys.exit(1)

        
# Data prep
def prepare_data(country_code_filter):
    # Read input file
    df = pd.read_csv(input_file ,sep=input_sep, names=input_columns)

    # Filter by significant feature codes
    df = df[df['country_code'].isin(country_code_filter)]

    # Filter by significant feature codes
    feature_code_filter = ['PPL', 'PPLC', 'PPLA', 'PPLA2', 'PPLA3', 'PPLA4', 'PPLA5']
    df = df[df['feature_code'].isin(feature_code_filter)]

    # Remove null values
    df = df[df['population'].notnull() &
           df['latitude'].notnull() &
           df['longitude'].notnull() ]

    # Select related columns
    column_filter = ['name','asciiname','country_code','alternatenames','latitude','longitude','feature_code', 'population']
    df = df[column_filter]

    # Replace nan values
    df.fillna('', inplace=True)
    
    return df


# Insert place name, geolocation pairs to database
def upsert_place(name, asciiname, alternatenames, latitude, longitude):
    try:
        # Set record for name value
        r.set(('pl-'+name.upper()), (str(latitude)+','+str(longitude)))

        # Set record for asciiname value
        r.set(('pl-'+asciiname.upper()), (str(latitude)+','+str(longitude)))

        # Set record for each alternatename value
        if alternatenames != '':
            for a_name in alternatenames.split(","):
                r.set(('pl-'+a_name.upper()), (str(latitude)+','+str(longitude)))
    
    except Exception as e:
        # Ignore and log errors
        logging.warning(e)

              
# Insert geohash, population set pairs to database        
def upsert_geohash(latitude, longitude, population, feature_code):
    try:
        # Get geohash for current location
        cur_geohash = gh.encode(latitude, longitude, 4)
        
        # Some places cover a larger area
        # Insert population value to neighboring geohashes as well
        if feature_code in ['PPL','PPLA','PPLC']:
            cur_geohash_expanded = gh.expand(cur_geohash)
            for g in cur_geohash_expanded:
                r.sadd(g, population)
        else:
            r.sadd(cur_geohash, population)
    except Exception as e:
        # Ignore and log errors
        logging.warning(e)

        
# Insert each row to database
def main():
    # Prepare input data
    logging.info('Starting data preparation')
    df = prepare_data(country_code_filter)
    
    # Iterate through each row
    logging.info('Updating database')
    for index, row in df.iterrows():
        upsert_place(row['name'], row['asciiname'], row['alternatenames'], row['latitude'], row['longitude'])
        upsert_geohash(row['latitude'], row['longitude'], row['population'], row['feature_code'])
        if index % 1000 == 0 and index > 0:
            logging.info('Processed row count: ' + str(index))
        
    return len(df)


if __name__ == '__main__':
    start_time = time.time()
    row_count = main()
    print(f"Processed %s records in %s seconds for %s" % (row_count, int(time.time() - start_time), str(country_code_filter)))