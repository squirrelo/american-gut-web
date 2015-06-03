from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The American Gut Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

"""
Centralized database access for the American Gut web portal
"""

import urllib
import httplib
import json
import logging

from time import sleep
from random import choice

import psycopg2

from passlib.hash import bcrypt

from amgut.lib.data_access.sql_connection import SQLConnectionHandler
from amgut.lib.config_manager import AMGUT_CONFIG


# character sets for kit id, passwords and verification codes
KIT_ALPHA = "abcdefghjkmnpqrstuvwxyz"  # removed i, l and o for clarity
KIT_PASSWD = '1234567890'
KIT_VERCODE = KIT_PASSWD
KIT_PASSWD_NOZEROS = KIT_PASSWD[0:-1]
KIT_VERCODE_NOZEROS = KIT_PASSWD_NOZEROS


class GoogleAPILimitExceeded(Exception):
    pass


class AGDataAccess(object):
    """Data Access implementation for all the American Gut web portal
    """
    # arbitrary, unique ID and value
    human_sites = ['Stool',
                   'Mouth',
                   'Right hand',
                   'Left hand',
                   'Forehead',
                   'Nares',
                   'Hair',
                   'Tears',
                   'Nasal mucus',
                   'Ear wax',
                   'Vaginal mucus']

    animal_sites = ['Stool',
                    'Mouth',
                    'Nares',
                    'Ears',
                    'Skin',
                    'Fur']

    general_sites = ['Animal Habitat',
                     'Biofilm',
                     'Dust',
                     'Food',
                     'Fermented Food',
                     'Indoor Surface',
                     'Outdoor Surface',
                     'Plant habitat',
                     'Soil',
                     'Sole of shoe',
                     'Water']

    def __init__(self, con=None):
        self.connection = None
        if con is None:
            self._open_connection()
        else:
            self.connection = con
        cur = self.get_cursor()
        cur.execute('set search_path to ag, public')

        self._sql = SQLConnectionHandler(con)

    def __del__(self):
        self.connection.close()

    def get_cursor(self):
        if self.connection.closed:
            self._open_connection()

        return self.connection.cursor()

    def _open_connection(self):
        self.connection = psycopg2.connect(
            user=AMGUT_CONFIG.user, password=AMGUT_CONFIG.password,
            database=AMGUT_CONFIG.database, host=AMGUT_CONFIG.host,
            port=AMGUT_CONFIG.port)

    #####################################
    # Helper Functions
    #####################################

    def testDatabase(self):
        """Attempt to connect to the database

        Attempt a database connection. Will throw an exception if it fails.
        Returns
        "True" if successful.
        """
        if self.connection:
            return True

    def _get_col_names_from_cursor(self, cur):
        if cur.description:
            return [x[0] for x in cur.description]
        else:
            return []

    #####################################
    # Users
    #####################################

    def addGeocodingInfo(self, limit=None, retry=False):
        """Adds latitude, longitude, and elevation to ag_login_table

        Uses the city, state, zip, and country from the database to retrieve
        lat, long, and elevation from the google maps API.

        If any of that information cannot be retrieved, then cannot_geocode
        is set to 'y' in the ag_login table, and it will not be tried again
        on subsequent calls to this function.  Pass retry=True to retry all
        (or maximum of limit) previously failed geocodings.
        """

        # clear previous geocoding attempts if retry is True
        if retry:
            sql = (
                "select cast(ag_login_id as varchar(100))from ag_login "
                "where cannot_geocode = 'y'"
            )
            cursor = self.connection.cursor()
            cursor.execute(sql)
            logins = cursor.fetchall()

            for row in logins:
                ag_login_id = row[0]
                self.updateGeoInfo(ag_login_id, None, None, None, '')

        # get logins that have not been geocoded yet
        sql = (
            'select city, state, zip, country, '
            'cast(ag_login_id as varchar(100))'
            'from ag_login '
            'where elevation is null '
            'and cannot_geocode is null'
        )

        cursor = self.connection.cursor()
        cursor.execute(sql)
        logins = cursor.fetchall()

        row_counter = 0
        for row in logins:
            row_counter += 1
            if limit is not None and row_counter > limit:
                break

            ag_login_id = row[4]
            # Attempt to geocode
            address = '{0} {1} {2} {3}'.format(row[0], row[1], row[2], row[3])
            encoded_address = urllib.urlencode({'address': address})
            url = '/maps/api/geocode/json?{0}&sensor=false'.format(
                encoded_address)

            r = self.getGeocodeJSON(url)

            if r in ('unknown_error', 'not_OK', 'no_results'):
                # Could not geocode, mark it so we don't try next time
                self.updateGeoInfo(ag_login_id, None, None, None, 'y')
                continue
            elif r == 'over_limit':
                # If the reason for failure is merely that we are over the
                # Google API limit, then we should try again next time
                # ... but we should stop hitting their servers, so raise an
                # exception
                raise GoogleAPILimitExceeded("Exceeded Google API limit")

            # Unpack it and write to DB
            lat, lon = r

            encoded_lat_lon = urllib.urlencode(
                {'locations': ','.join(map(str, [lat, lon]))})

            url2 = '/maps/api/elevation/json?{0}&sensor=false'.format(
                encoded_lat_lon)

            r2 = self.getElevationJSON(url2)

            if r2 in ('unknown_error', 'not_OK', 'no_results'):
                # Could not geocode, mark it so we don't try next time
                self.updateGeoInfo(ag_login_id, None, None, None, 'y')
                continue
            elif r2 == 'over_limit':
                # If the reason for failure is merely that we are over the
                # Google API limit, then we should try again next time
                # ... but we should stop hitting their servers, so raise an
                # exception
                raise GoogleAPILimitExceeded("Exceeded Google API limit")

            elevation = r2

            self.updateGeoInfo(ag_login_id, lat, lon, elevation, '')

    def getGeocodeStats(self):
        stat_queries = [
            ("Total Rows",
             "select count(*) from ag_login"),
            ("Cannot Geocode",
             "select count(*) from ag_login where cannot_geocode = 'y'"),
            ("Null Latitude Field",
             "select count(*) from ag_login where latitude is null"),
            ("Null Elevation Field",
             "select count(*) from ag_login where elevation is null")
        ]
        results = []
        for name, sql in stat_queries:
            cur = self.get_cursor()
            cur.execute(sql)
            total = cur.fetchone()[0]
            results.append((name, total))
        return results

    def getMapMarkers(self):
        cur_completed = self.get_cursor()
        cur_ver = self.get_cursor()
        cur_ll = self.get_cursor()

        # fetch all latitide/longitude by kit id
        cur_ll.execute("""SELECT ak.supplied_kit_id, al.latitude, al.longitude
                          FROM ag_login al
                               INNER JOIN ag_kit ak
                               ON ak.ag_login_id=al.ag_login_id
                          WHERE al.latitude IS NOT NULL AND
                                al.longitude IS NOT NULL""")
        ll = {res[0]: (res[1], res[2]) for res in cur_ll.fetchall()}

        # determine all completed kits
        cur_completed.execute("""SELECT ak.supplied_kit_id
                                 FROM ag_kit ak
                                 WHERE (
                                       SELECT  count(*)
                                       FROM ag_kit_barcodes akb
                                       WHERE akb.ag_kit_id = ak.ag_kit_id
                                       ) =
                                       (
                                       SELECT  count(*)
                                       FROM ag_kit_barcodes akb
                                       WHERE akb.ag_kit_id = ak.ag_kit_id AND
                                             akb.site_sampled IS NOT NULL
                                       )""")
        completed = (res[0] for res in cur_completed.fetchall())

        # determine what kit are not verified
        cur_ver.execute("""SELECT supplied_kit_id, kit_verified
                           FROM ag_kit""")
        notverified = (res[0] for res in cur_ver.fetchall() if res[1] == 'n')

        # set green for completed kits
        res = {ll[kid]: '00FF00' for kid in completed if kid in ll}

        # set blue for unverified kits
        res.update({ll[kid]: '00B2FF' for kid in notverified if kid in ll})

        # set yellow for all others
        res.update({v: 'FFFF00' for k, v in ll.items() if v not in res})

        return [[lat, lng, c] for ((lat, lng), c) in res.items()]

    def getGeocodeJSON(self, url):
        conn = httplib.HTTPConnection('maps.googleapis.com')
        success = False
        num_tries = 0
        while num_tries < 2 and not success:
            conn.request('GET', url)
            result = conn.getresponse()

            # Make sure we get an 'OK' status
            if result.status != 200:
                return 'not_OK'

            data = json.loads(result.read())

            # if we're over the query limit, wait 2 seconds and try again,
            # it may just be that we're submitting requests too fast
            if data.get('status', None) == 'OVER_QUERY_LIMIT':
                num_tries += 1
                sleep(2)
            elif 'results' in data:
                success = True
            else:
                return 'unknown_error'

        conn.close()

        # if we got here without getting an unknown_error or succeeding, then
        # we are over the request limit for the 24 hour period
        if not success:
            return 'over_limit'

        # sanity check the data returned by Google and return the lat/lng
        if len(data['results']) == 0:
            return 'no_results'

        geometry = data['results'][0].get('geometry', {})
        location = geometry.get('location', {})
        lat = location.get('lat', {})
        lon = location.get('lng', {})

        if not lat or not lon:
            return 'unknown_error'

        return (lat, lon)

    def getElevationJSON(self, url):
        """Use Google's Maps API to retrieve an elevation

        url should be formatted as described here:
        https://developers.google.com/maps/documentation/elevation
        /#ElevationRequests

        The number of API requests is limited to 2500 per 24 hour period.
        If this function is called and the limit is surpassed, the return value
        will be "over_limit".  Other errors will cause the return value to be
        "unknown_error".  On success, the return value is the elevation of the
        location requested in the url.
        """
        conn = httplib.HTTPConnection('maps.googleapis.com')
        success = False
        num_tries = 0
        while num_tries < 2 and not success:
            conn.request('GET', url)
            result = conn.getresponse()

            # Make sure we get an 'OK' status
            if result.status != 200:
                return 'not_OK'

            data = json.loads(result.read())

            # if we're over the query limit, wait 2 seconds and try again,
            # it may just be that we're submitting requests too fast
            if data.get('status', None) == 'OVER_QUERY_LIMIT':
                num_tries += 1
                sleep(2)
            elif 'results' in data:
                success = True
            else:
                return 'unknown_error'

        conn.close()

        # if we got here without getting an unknown_error or succeeding, then
        # we are over the request limit for the 24 hour period
        if not success:
            return 'over_limit'

        # sanity check the data returned by Google and return the lat/lng
        if len(data['results']) == 0:
            return 'no_results'

        elevation = data['results'][0].get('elevation', {})

        if not elevation:
            return 'unknown_error'

        return elevation

    def getAGStats(self):
        # returned tuple consists of:
        # site_sampled, sample_date, sample_time, participant_name,
        #environment_sampled, notes
        results = self._sql.execute_proc_return_cursor('ag_stats', [])
        ag_stats = results.fetchall()
        results.close()
        return ag_stats

    def get_menu_items(self, supplied_kit_id):
        """Returns information required to populate the menu of the website"""
        ag_login_id = self.get_user_for_kit(supplied_kit_id)
        info = self.getAGKitDetails(supplied_kit_id)

        kit_verified = False
        if info['kit_verified'] == 'y':
            kit_verified = True

        human_samples = {hs: self.getParticipantSamples(ag_login_id, hs)
                         for hs in self.getHumanParticipants(ag_login_id)}
        animal_samples = {ans: self.getParticipantSamples(ag_login_id, ans)
                          for ans in self.getAnimalParticipants(ag_login_id)}
        environmental_samples = self.getEnvironmentalSamples(ag_login_id)

        return (human_samples, animal_samples, environmental_samples,
                kit_verified)

