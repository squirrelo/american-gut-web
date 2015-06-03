def getProjectNames(self):
        """Returns a list of project names
        """
        sql = """select project from project"""
        result = self.get_cursor()
        cursor = self.get_cursor()
       cursor.execute(sql)
        results = cursor.fetchall()
        return [x[0] for x in results]

def search_handout_kits(self, term):
        sql = """select kit_id, password, barcode, verification_code
                 from ag_handout_kits where kit_id like %s
                 or barcode like %s"""
        cursor = self.get_cursor()
        liketerm = '%%' + term + '%%'
        cursor.execute(sql, [liketerm, liketerm])
        col_names = [x[0] for x in cursor.description]
        results = [dict(zip(col_names, row)) for row in cursor.fetchall()]
        cursor.close()
        return results

def search_barcodes(self, term):
        sql = """select  cast(ak.ag_login_id as varchar(100)) as ag_login_id
                 from    ag_kit ak
                 inner join ag_kit_barcodes akb
                 on ak.ag_kit_id = akb.ag_kit_id
                 where   barcode like %s or lower(participant_name) like
                 %s or lower(notes) like %s"""
        cursor = self.get_cursor()
        liketerm = '%%' + term + '%%'
        cursor.execute(sql, [liketerm, liketerm, liketerm])
        results = cursor.fetchall()
        cursor.close()
        return [x[0] for x in results]

def search_kits(self, term):
        sql = """ select  cast(ag_login_id as varchar(100)) as ag_login_id
                 from    ag_kit
                 where   lower(supplied_kit_id) like %s or
                 lower(kit_password) like %s or
                 lower(kit_verification_code) = %s"""
        cursor = self.get_cursor()
        liketerm = '%%' + term + '%%'
        cursor.execute(sql, [liketerm, liketerm, term])
        results = cursor.fetchall()
        cursor.close()
        return [x[0] for x in results]

def search_participants(self, term):
    sql = """ select  cast(ag_login_id as varchar(100)) as ag_login_id
             from    ag_consent
             where   lower(participant_name) like %s or
             lower(participant_email) like %s"""
    conn_handler = SQLConnectionHandler()
    liketerm = '%%' + term + '%%'
    return [x[0] for x in conn_handler.execute_fetchall(
        sql, [liketerm, liketerm])]

def search_participant_info(self, term):
        sql = """select   cast(ag_login_id as varchar(100)) as ag_login_id
                 from    ag_login al
                 where   lower(email) like %s or lower(name) like
                 %s or lower(address) like %s"""
        cursor = self.get_cursor()
        liketerm = '%%' + term + '%%'
        cursor.execute(sql, [liketerm, liketerm, liketerm])
        results = cursor.fetchall()
        cursor.close()
        return [x[0] for x in results]