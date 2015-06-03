"""
Kit object for the american gut portal
"""

import urllib
import httplib
import json
import logging

from time import sleep
from random import choice

from passlib.hash import bcrypt

from amgut.lib.data_access.sql_connection import SQLConnectionHandler
from amgut.lib.config_manager import AMGUT_CONFIG


# character sets for kit id, passwords and verification codes
KIT_ALPHA = "abcdefghjkmnpqrstuvwxyz"  # removed i, l and o for clarity
KIT_PASSWD = '1234567890'
KIT_VERCODE = KIT_PASSWD
KIT_PASSWD_NOZEROS = KIT_PASSWD[0:-1]
KIT_VERCODE_NOZEROS = KIT_PASSWD_NOZEROS


class AGKit(object):
    def _make_kit_id(cls, kit_id_length=8):
        kit_id = ''.join([choice(KIT_ALPHA) for i in range(kit_id_length)])
        return kit_id

    @staticmethod
    def used_kit_ids():
        """Grab in use kit IDs, return set of them"""
        cursor.execute("SELECT supplied_kit_id FROM ag_kit")
        kits = set([i[0] for i in cursor.fetchall()])
        return kits


    @staticmethod
    def register_handout_kit(self, user, supplied_kit_id):
        """
        Returns
        -------
        AGKit object
            object for newly registered kit
        """
        printresults = self.checkPrintResults(supplied_kit_id)
        if printresults is None:
            printresults = 'n'

        sql = """
            DO $do$
            DECLARE
                k_id uuid;
                bc varchar;
            BEGIN
                INSERT INTO ag_kit
                (ag_login_id, supplied_kit_id, kit_password, swabs_per_kit,
                 kit_verification_code, print_results)
                SELECT '{0}', kit_id, password, swabs_per_kit,
                    verification_code, '{1}'
                    FROM ag_handout_kits WHERE kit_id = %s LIMIT 1
                RETURNING ag_kit_id INTO k_id;
                FOR bc IN
                    SELECT barcode FROM ag_handout_kits WHERE kit_id = %s
                LOOP
                    INSERT  INTO ag_kit_barcodes
                        (ag_kit_id, barcode, sample_barcode_file)
                        VALUES (k_id, bc, bc || '.jpg');
                END LOOP;
                DELETE FROM ag_handout_kits WHERE kit_id = %s;
            END $do$;
            """.format(supplied_kit_id, printresults)

        conn_handler = SQLConnectionHandler()
        try:
            conn_handler.execute(sql, [supplied_kit_id] * 3)
        except psycopg2.IntegrityError:
            logging.exception('Error on skid %s:' % supplied_kit_id)
            return False
        return True

    @classmethod
    def make_new_kit(cls):
        cur = self.get_cursor()
        obs_kit_ids = get_used_kit_ids(cur)
        kit_id = make_kit_id(8)
        while kit_id in obs_kit_ids:
            kit_id = make_kit_id(8)

        return cls(kit_id)

    @classmethod
    def getAGHandoutKitIDsAndPasswords(self):
        sql = "SELECT kit_id, password FROM ag_handout_kits"
        cur = self.get_cursor()
        cur.execute(sql)

        return cur.fetchall()

    def __init__(self, supplied_kit_id, handout):
        """Iniialize a kit object

        Parameters
        ----------
        supplied_kit_id : str
            Supplied kit id for the current kit
        handout : bool
            Whether this is a handout kit (unregistered) or a registered kit

        Returns
        -------
        results : UUID or None
            user id attached to this kit, or None if handout kit
        """
        self.skid = supplied_kit_id
        self.handout = handout

        conn_handler = SQLConnectionHandler()
        kit_id = conn_handler.execute_fetchone(
            "SELECT ag_kit_id FROM ag.ag_kit WHERE supplied_kit_id = %s",
            [self.skid])
        self._id = None if kit_id is None else kit_id[0]

        @property
        def user(self):
            sql = """SELECT ag_login_id FROM ag_kit
                     JOIN ag_login using (ag_login_id)
                     where ag_kit_id = %s"""
            res = conn_handler.execute_fetchone(sql, self._id)
            if res:
                return res[0]
            else:
                return None

        @property
        def barcodes(self):
            if handout:
                sql = "SELECT barcode FROM ag_handout_kits WHERE kit_id = %s"
            else:
                sql = """SELECT barcode from ag_kit_barcodes
                         INNER JOIN ag_kit USING (ag_kit_id)
                         WHERE ag_kit_id = %s"""
            conn_handler = SQLConnectionHandler()
            res = conn_handler.execute_fetchall(sql, [self._id])
            return [x[0] for x in res]

        @property
        def print_results_exist(self):
            sql = """SELECT print_results from ag_handout_kits
                     WHERE kit_id = %s"""
            conn_handler = SQLConnectionHandler()
            res = conn_handler.execute_fetchall(sql)
            return None if res is None else res[0].strip()

        @property
        def verification_code(self):
            """returns the verification code for the kit"""
            sql = """SELECT kit_verification_code FROM ag_kit WHERE
                   ag_kit_id = %s"""
            cursor = self.get_cursor()
            cursor.execute(sql, [self._id])
            results = cursor.fetchone()[0]
            return results












        def get_kit_info_by_login(self, ag_login_id):
            sql = """select  cast(ag_kit_id as varchar(100)) as ag_kit_id,
                            cast(ag_login_id as varchar(100)) as ag_login_id,
                            supplied_kit_id, kit_password, swabs_per_kit,
                            kit_verification_code, kit_verified
                    from    ag_kit
                    where   ag_login_id = %s"""
            cursor = self.get_cursor()
            cursor.execute(sql, [ag_login_id])
            col_names = [x[0] for x in cursor.description]
            results = [dict(zip(col_names, row)) for row in cursor.fetchall()]
            cursor.close()
            return results

def ag_set_pass_change_code(self, email, kitid, pass_code):
        """updates ag_kit table with the supplied pass_code

        email is email address of participant
        kitid is supplied_kit_kd in the ag_kit table
        pass_code is the password change verfication value
        """
        self.get_cursor().callproc('ag_set_pass_change_code',
                                   [email, kitid, pass_code])
        self.connection.commit()

    def ag_update_kit_password(self, kit_id, password):
        """updates ag_kit table with password

        kit_id is supplied_kit_id in the ag_kit table
        password is the new password
        """
        password = bcrypt.encrypt(password)

        self.get_cursor().callproc('ag_update_kit_password',
                                   [kit_id, password])
        self.connection.commit()

    def ag_update_handout_kit_password(self, kit_id, password):
        """updates ag_handout_kits table with password

        kit_id is kit_id in the ag_handout_kits table
        password is the new password
        """
        password = bcrypt.encrypt(password)

        cursor = self.get_cursor()
        cursor.execute("""UPDATE ag_handout_kits
                          SET password=%s
                          WHERE kit_id=%s""", [password, kit_id])
        self.connection.commit()

    def ag_verify_kit_password_change_code(self, email, kitid, passcode):
        """returns true if it still in the password change window

        email is the email address of the participant
        kitid is the supplied_kit_id in the ag_kit table
        passcode is the password change verification value
        """
        cursor = self.get_cursor()
        cursor.callproc('ag_verify_password_change_code', [email, kitid,
                                                           passcode])
        return cursor.fetchone()[0]

def verifyKit(self, supplied_kit_id):
        """Set the KIT_VERIFIED for the supplied_kit_id to 'y'"""
        self.get_cursor().callproc('ag_verify_kit_status',
                                   [supplied_kit_id])
        self.connection.commit()


def getAGKitDetails(self, supplied_kit_id):
        results = self._sql.execute_proc_return_cursor('ag_get_kit_details',
                                                       [supplied_kit_id])
        row = results.fetchone()
        col_names = self._get_col_names_from_cursor(results)
        results.close()

        kit_details = {}
        if row:
            kit_details = dict(zip(col_names, row))
        return kit_details

    def getAGHandoutKitDetails(self, supplied_kit_id):
        sql = "SELECT * FROM ag_handout_kits WHERE kit_id = %s"
        cur = self.get_cursor()
        cur.execute(sql, [supplied_kit_id])
        row = cur.fetchone()
        col_names = self._get_col_names_from_cursor(cur)
        cur.close()

        kit_details = dict(zip(col_names, row))

        return kit_details

def addAGKit(self, ag_login_id, kit_id, kit_password, swabs_per_kit,
                 kit_verification_code, printresults='n'):
        """
        Returns
        -------
        int
            1:  success
            -1: insert failed due to IntegrityError

        Notes
        -----
        Whatever is passed as kit_password will be added AS IS. This means you
        must hash the password before passing, if desired.
        """
        try:
            self.get_cursor().callproc('ag_insert_kit',
                                       [ag_login_id, kit_id,
                                        kit_password, swabs_per_kit,
                                        kit_verification_code,
                                        printresults])
            self.connection.commit()
        except psycopg2.IntegrityError:
            logging.exception('Error on skid %s:' % ag_login_id)
            self.connection.rollback()
            return -1
        return 1

    def updateAGKit(self, ag_kit_id, supplied_kit_id, kit_password,
                    swabs_per_kit, kit_verification_code):
        kit_password = bcrypt.encrypt(kit_password)

        self.get_cursor().callproc('ag_update_kit',
                                   [ag_kit_id, supplied_kit_id,
                                    kit_password, swabs_per_kit,
                                    kit_verification_code])
        self.connection.commit()

