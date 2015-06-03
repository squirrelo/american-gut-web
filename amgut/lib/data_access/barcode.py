from amgut.lib.data_access import Base, session
from sqlalchemy import Column, String, Integer, DateTime, Enum
from sqlalchemy.sql import func

class Barcode(Base):
    __tablename__ = 'barcodes'

    barcode  = Column(varchar, primary_key=True)
    create_date_time = Column(DateTime, default=func.now())
    status = Column(String(100))
    scan_date = Column(String(20))
    sample_postmark_date = Column(String(20))
    biomass_remaining = Column(String(1))
    sequencing_status = Column(Enum(
        'WAITING', 'SUCCESS', 'FAILED_SEQUENCING', 'FAILED_SEQUENCING_1',
        'FAILED_SEQUENCING_2', 'FAILED_SEQUENCING_3'))
    obsolete = Column(String(1))










    @staticmethod
    def all_barcodes(self):
        results = self._sql.execute_proc_return_cursor('ag_get_barcodes', [])
        return_res = [row[0] for row in results]
        results.close()
        return return_res

    def __init__(self, barcode):
        self.barcode = barcode



    def getAGBarcodesByLogin(self, ag_login_id):
        # returned tuple consists of:
        # site_sampled, sample_date, sample_time, participant_name,
        # environment_sampled, notes
        results = self._sql.execute_proc_return_cursor(
            'ag_get_barcodes_by_login',
            [ag_login_id])
        rows = results.fetchall()
        col_names = self._get_col_names_from_cursor(results)
        results.close()

        barcode_info = [dict(zip(col_names, row)) for row in rows]

        return barcode_info

def updateBarcodeStatus(self, status, postmark, scan_date, barcode,
                            biomass_remaining, sequencing_status, obsolete):
        """ Updates a barcode's status
        """
        sql = """update  barcode
        set     status = %s,
            sample_postmark_date = %s,
            scan_date = %s,
            biomass_remaining = %s,
            sequencing_status = %s,
            obsolete = %s
        where   barcode = %s"""
        cursor = self.get_cursor()
        cursor.execute(sql, [status, postmark, scan_date, biomass_remaining,
                             sequencing_status, obsolete, barcode])
        self.connection.commit()
        cursor.close() 

def setBarcodeProjType(self, project, barcode):
        """sets the project type of the barcodel

            project is the project name from the project table
            barcode is the barcode
        """
        sql = """update project_barcode set project_id =
                (select project_id from project where project = %s)
                where barcode = %s"""
        result = self.get_cursor()
        cursor = self.get_cursor()
        cursor.execute(sql, [project, barcode])
        self.connection.commit()
        cursor.close()

def get_barcode_details(self, barcode):
        """
        Returns the genral barcode details for a barcode
        """
        sql = """select  create_date_time, status, scan_date,
                  sample_postmark_date,
                  biomass_remaining, sequencing_status, obsolete
                  from    barcode
                  where barcode = %s"""
        cursor = self.get_cursor()
        cursor.execute(sql, [barcode])
        col_names = [x[0] for x in cursor.description]
        results = [dict(zip(col_names, row)) for row in cursor.fetchall()]
        cursor.close()
        if results:
            return results[0]
        else:
            return {}

    def get_plate_for_barcode(self, barcode):
        """
        Gets the sequencing plates a barcode is on
        """
        sql = """select  p.plate, p.sequence_date
                 from    plate p inner join plate_barcode pb on
                 pb.plate_id = p.plate_id \
                where   pb.barcode = %s"""
        cursor = self.get_cursor()
        cursor.execute(sql, [barcode])
        col_names = [x[0] for x in cursor.description]
        results = [dict(zip(col_names, row)) for row in cursor.fetchall()]
        cursor.close()
        return results

    def getBarcodeProjType(self, barcode):
        """ Get the project type of the barcode.
            Return a tuple of project and project type.
        """
        sql = """select p.project from project p inner join
                 project_barcode pb on (pb.project_id = p.project_id)
                 where pb.barcode = %s"""
        cursor = self.get_cursor()
        cursor.execute(sql, [barcode])
        results = cursor.fetchone()
        proj = results[0]
        #this will get changed to get the project type from the db
        if proj in ('American Gut Project', 'ICU Microbiome', 'Handout Kits',
                    'Office Succession Study',
                    'American Gut Project: Functional Feces',
                    'Down Syndrome Microbiome', 'Beyond Bacteria',
                    'All in the Family', 'American Gut Handout kit',
                    'Personal Genome Project', 'Sleep Study',
                    'Anxiety/Depression cohort', 'Alzheimers Study'):
            proj_type = 'American Gut'
        else:
            proj_type = proj
        return (proj, proj_type)

def get_barcode_results(self, supplied_kit_id):
        sql = """select akb.barcode, akb.participant_name
                 from ag_kit_barcodes akb
                 inner join ag_kit agk  on akb.ag_kit_id = agk.ag_kit_id
                 where agk.supplied_kit_id =  %s and akb.results_ready = 'Y'"""
        cursor = self.get_cursor()
        cursor.execute(sql, [supplied_kit_id])
        results = cursor.fetchall()
        col_names = self._get_col_names_from_cursor(cursor)
        return [dict(zip(col_names, row)) for row in results]

def updateAKB(self, barcode, moldy, overloaded, other, other_text,
                  date_of_last_email):
        """ Update ag_kit_barcodes table.
        """
        self.get_cursor().callproc('update_akb', [barcode, moldy,
                                                  overloaded, other,
                                                  other_text,
                                                  date_of_last_email])
        self.connection.commit()

def check_access(self, user, barcode):
        """Check if the user has access to the barcode

        Parameters
        ----------
        user : str
            The user's supplied kit ID
        barcode : str
            The barcode to check access for

        Returns
        -------
        boolean
            True if the user can access the barcode, False otherwise
        """
        cursor = self.get_cursor()
        cursor.execute("""SELECT EXISTS (
                              SELECT barcode
                              FROM ag.ag_login
                              INNER JOIN ag.ag_kit USING (ag_login_id)
                              FULL OUTER JOIN ag.ag_kit_barcodes USING(ag_kit_id)
                              WHERE supplied_kit_id=%s AND
                                    barcode=%s)""", [user, barcode])
        return cursor.fetchone()[0]

    def checkBarcode(self, barcode):
        # return a tuple consists of:
        # site_sampled, sample_date, sample_time, participant_name,
        # environment_sampled, notes, etc (please refer to
        # ag_check_barcode_status.sql).
        results = self._sql.execute_proc_return_cursor(
            'ag_check_barcode_status', [barcode])
        row = results.fetchone()
        col_names = self._get_col_names_from_cursor(results)
        results.close()

        barcode_details = {}
        if row:
            barcode_details = dict(zip(col_names, row))

        return barcode_details

def getAGBarcodeDetails(self, barcode):
        results = self._sql.execute_proc_return_cursor(
            'ag_get_barcode_details', [barcode])
        barcode_details = results.fetchone()
        col_names = self._get_col_names_from_cursor(results)
        results.close()

        row_dict = {}
        if barcode_details:
            row_dict = dict(zip(col_names, barcode_details))

        return row_dict

def getNextAGBarcode(self):
        results = self._sql.execute_proc_return_cursor('ag_get_next_barcode',
                                                       [])
        next_barcode = results.fetchone()[0]
        text_barcode = '{0}'.format(str(next_barcode))
        # Pad out the barcode until it's 9 digits long
        while len(text_barcode) < 9:
            text_barcode = '0{0}'.format(text_barcode)

        results.close()
        return next_barcode, text_barcode

    def reassignAGBarcode(self, ag_kit_id, barcode):
        self.get_cursor().callproc('ag_reassign_barcode', [ag_kit_id,
                                                           barcode])
        self.connection.commit()

    def addAGBarcode(self, ag_kit_id, barcode):
        """
        return values
        1:  success
        -1: insert failed due to IntegrityError
        """
        try:
            self.get_cursor().callproc('ag_insert_barcode',
                                       [ag_kit_id, barcode])
            self.connection.commit()
        except psycopg2.IntegrityError:
            logging.exception('Error on barcode %s:' % barcode)
            self.connection.rollback()
            return -1
        return 1

    def updateAGBarcode(self, barcode, ag_kit_id, site_sampled,
                        environment_sampled, sample_date, sample_time,
                        participant_name, notes, refunded, withdrawn):
        self.get_cursor().callproc('ag_update_barcode',
                                   [barcode, ag_kit_id, site_sampled,
                                    environment_sampled,
                                    sample_date, sample_time,
                                    participant_name, notes,
                                    refunded, withdrawn])
        self.connection.commit()

def deleteSample(self, barcode, ag_login_id):
        """
        Strictly speaking the ag_login_id isn't needed but it makes it really
        hard to hack the function when you would need to know someone else's
        login id (a GUID) to delete something maliciously
        """
        self.get_cursor().callproc('ag_delete_sample',
                                   [barcode, ag_login_id])

def AGGetBarcodeMetadata(self, barcode):
        results = self._sql.execute_proc_return_cursor(
            'ag_get_barcode_metadata', [barcode])
        rows = results.fetchall()
        col_names = self._get_col_names_from_cursor(results)
        results.close()

        return_res = [dict(zip(col_names, row)) for row in rows]

        return return_res

    def AGGetBarcodeMetadataAnimal(self, barcode):
        results = self._sql.execute_proc_return_cursor(
            'ag_get_barcode_md_animal', [barcode])
        col_names = self._get_col_names_from_cursor(results)
        return_res = [dict(zip(col_names, row)) for row in results]
        results.close()
        return return_res

