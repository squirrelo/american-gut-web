
@staticmethod
def getAGLogins(self):
        results = self._sql.execute_proc_return_cursor('ag_get_logins', [])
        rows = results.fetchall()
        col_names = self._get_col_names_from_cursor(results)
        results.close()

        return_res = [dict(zip(col_names, row)) for row in rows]

        return return_res

@classmethod
def authenticateWebAppUser(self, username, password):
        """ Attempts to validate authenticate the supplied username/password

        Attempt to authenticate the user against the list of users in
        web_app_user table. If successful, a dict with user innformation is
        returned. If not, the function returns False.
        """
        data = self._sql.execute_proc_return_cursor(
            'ag_authenticate_user', [username, password])
        row = data.fetchone()
        col_names = self._get_col_names_from_cursor(data)
        data.close()
        if row:
            results = dict(zip(col_names, row))

            if not bcrypt.verify(password, results['kit_password']):
                return False

            results['ag_login_id'] = str(results['ag_login_id'])

            return results
        else:
            return False

    def addAGLogin(self, email, name, address, city, state, zip_, country):
        clean_email = email.strip().lower()
        sql = "select ag_login_id from ag_login WHERE LOWER(email) = %s"
        cur = self.get_cursor()
        cur.execute(sql, [clean_email])
        ag_login_id = cur.fetchone()
        if not ag_login_id:
            # create the login
            sql = ("INSERT INTO ag_login (email, name, address, city, state, "
                   "zip, country) VALUES (%s, %s, %s, %s, %s, %s, %s) "
                   "RETURNING ag_login_id")
            cur.execute(sql, [clean_email, name, address, city,
                              state, zip_, country])
            ag_login_id = cur.fetchone()
            self.connection.commit()
        return ag_login_id[0]

    def updateAGLogin(self, ag_login_id, email, name, address, city, state,
                      zip, country):
        self.get_cursor().callproc('ag_update_login', [ag_login_id,
                                   email.strip().lower(), name,
                                   address, city, state, zip, country])
        self.connection.commit()

def getAGSurveyDetails(self, ag_login_id, participant_name):
        results = self._sql.execute_proc_return_cursor('ag_get_survey_details',
                                                       [ag_login_id,
                                                        participant_name])
        rows = results.fetchall()
        col_names = self._get_col_names_from_cursor(results)
        results.close()

        rows = [dict(zip(col_names, row)) for row in rows]

        data = {row['question']: row['answer'] for row in rows
                if row['answer']}

        return data


    # note: only used by the password migration
    def getAGKitsByLogin(self):
        results = self._sql.execute_proc_return_cursor('ag_get_kits_by_login',
                                                       [])
        rows = results.fetchall()
        col_names = self._get_col_names_from_cursor(results)
        results.close()

        return_res = [dict(zip(col_names, row)) for row in rows]

        return return_res

    def get_login_by_email(self, email):
        sql = """select name, address, city, state, zip, country, ag_login_id
                 from ag_login where email = %s"""
        cursor = self.get_cursor()
        cursor.execute(sql, [email])
        col_names = self._get_col_names_from_cursor(cursor)
        row = cursor.fetchone()

        login = {}
        if row:
            login = dict(zip(col_names, row))
            login['email'] = email

        return login

def get_login_info(self, ag_login_id):
        sql = """select  ag_login_id, email, name, address, city, state, zip,
                         country
                 from    ag_login
                 where   ag_login_id = %s"""
        cursor = self.get_cursor()
        cursor.execute(sql, [ag_login_id])
        col_names = [x[0] for x in cursor.description]
        results = [dict(zip(col_names, row)) for row in cursor.fetchall()]
        cursor.close()
        return results

def get_user_info(self, supplied_kit_id):
        sql = """SELECT  cast(agl.ag_login_id as varchar(100)) as ag_login_id,
                        agl.email, agl.name, agl.address, agl.city,
                        agl.state, agl.zip, agl.country
                 from    ag_login agl
                        inner join ag_kit agk
                        on agl.ag_login_id = agk.ag_login_id
                 where   agk.supplied_kit_id = %s"""
        cursor = self.get_cursor()
        cursor.execute(sql, [supplied_kit_id])
        row = cursor.fetchone()
        col_names = self._get_col_names_from_cursor(cursor)

        user_data = {}
        if row:
            user_data = dict(zip(col_names, row))
            user_data['ag_login_id'] = str(user_data['ag_login_id'])

        return user_data

def check_if_consent_exists(self, ag_login_id, participant_name):
        """Return True if a consent already exists"""
        sql = """select exists(
                    select 1
                    from ag_consent
                    where ag_login_id=%s and
                        participant_name=%s)"""
        cursor = self.get_cursor()
        cursor.execute(sql, (ag_login_id, participant_name))
        return cursor.fetchone()[0]

@property
def participants:
    pass

def addParticipantException(self, ag_login_id, participant_name):
        self.get_cursor().callproc('ag_insert_participant_exception',
                                   [ag_login_id, participant_name])
        self.connection.commit()

def getAGKitIDsByEmail(self, email):
        """Returns a list of kitids based on email

        email is email address of login
        returns a list of kit_id's associated with the email or an empty list
        """
        results = self._sql.execute_proc_return_cursor(
            'ag_get_kit_id_by_email', [email.lower()])
        kit_ids = [row[0] for row in results]
        results.close()
        return kit_ids

def handoutCheck(self, username, password):
        cursor = self.get_cursor()
        cursor.execute("""SELECT distinct(password)
                          FROM ag.ag_handout_kits
                          WHERE kit_id=%s""", [username])
        to_check = cursor.fetchone()

        if not to_check:
            return False
        else:
            return bcrypt.verify(password, to_check[0]

def updateGeoInfo(self, ag_login_id, lat, lon, elevation, cannot_geocode):
        self.get_cursor().callproc('ag_update_geo_info',
                                   [ag_login_id, lat, lon, elevation,
                                    cannot_geocode])
        self.connection.commit()


def getAvailableBarcodes(self, ag_login_id):
        results = self._sql.execute_proc_return_cursor('ag_available_barcodes',
                                                       [ag_login_id])
        return_res = [row[0] for row in results]
        results.close()
        return return_res

    def getConsent(self, survey_id):
        conn_handler = SQLConnectionHandler()
        with conn_handler.get_postgres_cursor() as cur:
            cur.execute("""SELECT agc.participant_name,
                                  agc.participant_email,
                                  agc.parent_1_name,
                                  agc.parent_2_name,
                                  agc.is_juvenile,
                                  agc.deceased_parent,
                                  agc.ag_login_id,
                                  agc.date_signed,
                                  agc.assent_obtainer,
                                  agc.age_range,
                                  agl.survey_id
                           FROM ag_consent agc JOIN
                                ag_login_surveys agl
                                USING (ag_login_id, participant_name)
                           WHERE agl.survey_id=%s""", [survey_id])
            colnames = [x[0] for x in cur.description]
            result = cur.fetchone()
            if result:
                result = {k: v for k, v in zip(colnames, result)}
                if 'date_signed' in result:
                    result['date_signed'] = str(result['date_signed'])
                return result

def getHumanParticipants(self, ag_login_id):
        conn_handler = SQLConnectionHandler()
        # get people from new survey setup
        new_survey_sql = ("SELECT participant_name FROM ag_consent "
                          "WHERE ag_login_id = %s")
        results = conn_handler.execute_fetchall(new_survey_sql, [ag_login_id])
        return [row[0] for row in results]

    def getAnimalParticipants(self, ag_login_id):
        results = self._sql.execute_proc_return_cursor(
            'ag_get_animal_participants', [ag_login_id])

        return_res = [row[0] for row in results]
        results.close()
        return return_res

    def getParticipantExceptions(self, ag_login_id):
        results = self._sql.execute_proc_return_cursor(
            'ag_get_participant_exceptions', [ag_login_id])

        return_res = [row[0] for row in results]
        results.close()
        return return_res

    def getParticipantSamples(self, ag_login_id, participant_name):
        results = self._sql.execute_proc_return_cursor(
            'ag_get_participant_samples', [ag_login_id, participant_name])
        rows = results.fetchall()
        col_names = self._get_col_names_from_cursor(results)
        results.close()

        barcodes = [dict(zip(col_names, row)) for row in rows]

        return barcodes

    def getEnvironmentalSamples(self, ag_login_id):
        barcodes = []
        results = self._sql.execute_proc_return_cursor(
            'ag_get_environmental_samples', [ag_login_id])
        rows = results.fetchall()
        col_names = self._get_col_names_from_cursor(results)
        results.close()

        barcodes = [dict(zip(col_names, row)) for row in rows]

        return barcodes

def getAGCode(self, passwd_length, type='alpha'):
        if type == 'alpha':
            x = ''.join([choice(KIT_ALPHA)
                for i in range(passwd_length-1)])
            return x
        if type == 'numeric':
            x = ''.join([choice(KIT_PASSWD)
                for i in range(passwd_length-1)])
            return choice(KIT_PASSWD_NOZEROS) + x

    def addAGHumanParticipant(self, ag_login_id, participant_name):
        self.get_cursor().callproc('ag_add_participant',
                                   [ag_login_id, participant_name])
        self.connection.commit()

    def addAGAnimalParticipant(self, ag_login_id, participant_name):
        self.get_cursor().callproc('ag_add_animal_participant',
                                   [ag_login_id, participant_name])
        self.connection.commit()

    def logParticipantSample(self, ag_login_id, barcode, sample_site,
                             environment_sampled, sample_date, sample_time,
                             participant_name, notes):

        conn_handler = SQLConnectionHandler()
        if sample_site is not None:
            # Get survey id
            sql = ("SELECT survey_id FROM ag_login_surveys WHERE ag_login_id = "
                   "%s AND participant_name = %s")

            survey_id = conn_handler.execute_fetchone(
                sql, (ag_login_id, participant_name))
            if survey_id:
                # remove the list encapulation
                survey_id = survey_id[0]
            else:
                raise RuntimeError("No survey ID for ag_login_id %s and "
                                   "participant name %s" % (ag_login_id,
                                                            participant_name))
        else:
            # otherwise, it is an environmental sample
            survey_id = None

        # Add barcode info
        sql = """update  ag_kit_barcodes
                 set     site_sampled = %s,
                         environment_sampled = %s,
                         sample_date = %s,
                         sample_time = %s,
                         participant_name = %s,
                         notes = %s,
                         survey_id = %s
                 where   barcode = %s"""
        conn_handler.execute(sql, [
            sample_site, environment_sampled, sample_date, sample_time,
            participant_name, notes, survey_id, barcode])
        self.connection.commit()
