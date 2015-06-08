#!/usr/bin/env python
from __future__ import division

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, event, DDL, Column, Table, ForeignKey, text
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import or_, and_
from sqlalchemy.types import String, DateTime, Integer
from sqlalchemy.dialects.postgresql import (
    UUID, FLOAT, BOOLEAN, BIGINT, ENUM, DATE)

from amgut.lib.config_manager import AMGUT_CONFIG

Base = declarative_base()
event.listen(Base.metadata, 'before_create', DDL(
    'CREATE SCHEMA IF NOT EXISTS ag'))
event.listen(Base.metadata, 'before_create', DDL(
    'CREATE SCHEMA IF NOT EXISTS barcodes'))
event.listen(Base.metadata, 'before_create', DDL(
    'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
# add conditional foreign key restraint type trigger on survey response table
event.listen(Base.metadata, 'after_create', DDL(
    """CREATE OR REPLACE FUNCTION check_resp_func() RETURNS TRIGGER AS $BODY$
BEGIN
    IF (SELECT NOT EXISTS(SELECT answer FROM ag.survey_question_response
    WHERE response = NEW.response)) THEN
     RAISE EXCEPTION 'Unknown response: %', NEW.response
     USING ERRCODE = 'CONSTRAINT';
 END IF;
END;
$BODY$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS check_response ON ag.participant_responses;

CREATE TRIGGER check_response
BEFORE INSERT ON ag.participant_responses FOR EACH ROW
WHEN (NEW.free_response = False) EXECUTE PROCEDURE check_resp_func();"""))

# ---------- GENERIC BARCODE TABLES (barcodes schema) ----------


class Barcode(Base):
    __tablename__ = 'barcode'
    __table_args__ = {'schema': 'barcodes'}

    barcode = Column(String(), primary_key=True, unique=True)
    create_date_time = Column(DateTime, default=func.now())
    status = Column(String(100))
    scan_date = Column(String(20))
    sample_postmark_date = Column(String(20))
    biomass_remaining = Column(String(1))
    sequencing_status = Column(ENUM(
        'WAITING', 'SUCCESS', 'FAILED_SEQUENCING', 'FAILED_SEQUENCING_1',
        'FAILED_SEQUENCING_2', 'FAILED_SEQUENCING_3', name='seq_status'))
    obsolete = Column(String(1))

    __mapper_args__ = {'polymorphic_identity': 'barcode',
                       'polymorphic_on': barcode}

    @classmethod
    def get_all(cls):
        return session.query(Barcode).order_by(Barcode.barcode)

plate_association_table = Table(
    'plate_barcode', Base.metadata,
    Column('plate_id', BIGINT, ForeignKey('barcodes.plate.id'),
           nullable=False),
    Column('barcode', String(), ForeignKey('barcodes.barcode.barcode'),
           nullable=False), schema='barcodes')


class Plate(Base):
    __tablename__ = 'plate'
    __table_args__ = {'schema': 'barcodes'}

    id = Column(BIGINT, primary_key=True, nullable=False)
    plate = Column(String(50))
    sequence_date = Column(String(20))
    barcodes = relationship('Barcode', secondary=plate_association_table,
                            backref='plates')

    @classmethod
    def get_all(cls):
        return session.query(Plate).order_by(Plate.id)

project_association_table = Table(
    'project_barcode', Base.metadata,
    Column('project_id', BIGINT, ForeignKey('barcodes.project.id'),
           nullable=False),
    Column('barcode', String(), ForeignKey('barcodes.barcode.barcode'),
           nullable=False), schema='barcodes')


class Project(Base):
    __tablename__ = 'project'
    __table_args__ = {'schema': 'barcodes'}

    id = Column(BIGINT, primary_key=True, nullable=False)
    project = Column(String(200), unique=True)
    barcodes = relationship('Barcode', secondary=project_association_table,
                            backref='projects')

    @classmethod
    def get_all(cls):
        return session.query(Project).order_by(Project.id)


# ---------- AG SPECIFIC TABLES (ag schema) ----------
class Kit(Base):
    __tablename__ = 'kit'
    __table_args__ = {'schema': 'ag'}

    id = Column(UUID, server_default=text('uuid_generate_v4()'),
                primary_key=True, unique=True)
    login_id = Column(UUID, ForeignKey('ag.login.id'), nullable=False)
    supplied_kit_id = Column(String(9), nullable=False)
    kit_password = Column(String(50))
    swabs_per_kit = Column(BIGINT, nullable=False)
    kit_verification_code = Column(String(50))
    kit_verified = Column(BOOLEAN, default=False)
    verification_email_sent = Column(BOOLEAN, default=False)
    pass_reset_code = Column(String(20))
    pass_reset_time = Column(DateTime())
    print_results = Column(BOOLEAN, default=False)
    barcodes = relationship('AGBarcode', backref='kit')
    consents = relationship('Consent', backref='kit')

    @classmethod
    def get_all(cls):
        return session.query(Kit).order_by(Kit.id)

    @classmethod
    def search_skid(cls, search_str):
        cls.query.filter(cls.supplied_kit_id.like('%%s%' % search_str))


class HandoutKit(Base):
    __tablename__ = 'handout_kit'
    __table_args__ = {'schema': 'ag'}

    id = Column(String(9), primary_key=True, nullable=False, unique=True)
    password = Column(String(30))
    verification_code = Column(String(5))
    sample_barcode_file = Column(String(13))
    swabs_per_kit = Column(BIGINT, nullable=False)
    print_results = Column(BOOLEAN, default=False)
    barcodes = relationship('HandoutBarcode', backref='kit')

    @classmethod
    def get_all(cls):
        return session.query(HandoutKit).order_by(HandoutKit.id)

    @classmethod
    def search(cls, search_str):
        cls.query.filter(or_(cls.barcode.like('%%s%' % search_str),
                             cls.id.like('%%s%' % search_str)))


class AGBarcode(Barcode):
    __tablename__ = 'barcode'
    __table_args__ = {'schema': 'ag'}
    __mapper_args__ = {'polymorphic_identity': 'ag_barcode'}

    kit_id = Column(UUID, ForeignKey('ag.kit.id'), primary_key=True)
    barcode = Column(String(), ForeignKey('barcodes.barcode.barcode'),
                     primary_key=True, unique=True)
    survey_id = Column(String(), ForeignKey('ag.participant_survey.id'))
    sample_barcode_file = Column(String(500))
    sample_barcode_file_md5 = Column(String(50))
    site_sampled = Column(String(200))
    sample_date = Column(String(20))
    participant_name = Column(String(200))
    sample_time = Column(String(100))
    notes = Column(String(2000))
    environment_sampled = Column(String(100))
    moldy = Column(BOOLEAN, default=False)
    overloaded = Column(BOOLEAN, default=False)
    other = Column(BOOLEAN, default=False)
    other_text = Column(String(2000))
    date_of_last_email = Column(String(20))
    results_ready = Column(BOOLEAN, default=False)
    withdrawn = Column(BOOLEAN, default=False)
    refunded = Column(BOOLEAN, default=False)

    @classmethod
    def get_all(cls):
        return session.query(AGBarcode).order_by(AGBarcode.barcode)

    @classmethod
    def search(cls, search_str):
        cls.query.filter(cls.barcode.like('%%s%' % search_str))


class HandoutBarcode(Barcode):
    __tablename__ = 'handout_barcode'
    __table_args__ = {'schema': 'ag'}

    kit_id = Column(String(9), ForeignKey('ag.handout_kit.id'),
                    primary_key=True, nullable=False)
    barcode = Column(String(9), ForeignKey('barcodes.barcode.barcode'),
                     primary_key=True, nullable=False, unique=True)


class Login(Base):
    __tablename__ = 'login'
    __table_args__ = {'schema': 'ag'}

    id = Column(UUID, server_default=text('uuid_generate_v4()'),
                primary_key=True)
    email = Column(String(100))
    name = Column(String(200))
    address = Column(String(500))
    city = Column(String(100))
    state = Column(String(100))
    zipcode = Column(String(10))
    country = Column(String(10))
    latitude = Column(FLOAT)
    longitude = Column(FLOAT)
    cannot_geocode = Column(BOOLEAN)
    elevation = Column(FLOAT)
    kits = relationship('Kit', backref='login')
    consents = relationship('Consent', backref='login')

    @classmethod
    def get_all(cls):
        return session.query(Login).order_by(Login.id)

    @classmethod
    def search(cls, search_str):
        cls.query.filter(or_(cls.name.like('%%s%' % search_str),
                             cls.email.like('%%s%' % search_str)))


class Consent(Base):
    __tablename__ = 'consent'
    __table_args__ = {'schema': 'ag'}

    login_id = Column(UUID, ForeignKey('ag.login.id'), nullable=False,
                      primary_key=True)
    participant_name = Column(String(200), primary_key=True, nullable=False)
    participant_email = Column(String(200), nullable=False)
    is_juvenile = Column(BOOLEAN)
    parent_1_name = Column(String(200))
    parent_2_name = Column(String(200))
    deceased_parent = Column(String(10))
    date_signed = Column(DATE, default=func.now(), nullable=False)
    assent_obtainer = Column(String(200))
    age_range = Column(String(20))

    @classmethod
    def get_all(cls):
        return session.query(Consent).order_by(Consent.login_id)

# ------------ AG SURVEY & RESPONSE TABLES ----------


class ParticipantSurvey(Base):
    __tablename__ = 'participant_survey'
    __table_args__ = {'schema': 'ag'}

    id = Column(String(), nullable=False, primary_key=True)
    ag_login_id = Column(UUID, ForeignKey('ag.login.id'), nullable=False)
    participant_name = Column(String())
    vioscreen_status = Column(Integer)
    barcodes = relationship(Barcode, backref='survey')
    orig_version = Column(Integer, nullable=False)


questions_association_table = Table(
    'group_questions', Base.metadata,
    Column('survey_group_id', Integer, ForeignKey('ag.survey_group.id'),
           nullable=False, primary_key=True),
    Column('survey_question_id', Integer, ForeignKey('ag.survey_question.id'),
           nullable=False, primary_key=True),
    Column('display_index', Integer, nullable=False, primary_key=True),
    schema='ag')


class SurveyGroup(Base):
    __tablename__ = 'survey_group'
    __table_args__ = {'schema': 'ag'}

    id = Column(Integer, nullable=False, primary_key=True)
    american = Column(String(), nullable=False, unique=True)
    british = Column(String(), nullable=False, unique=True)
    display_index = Column(Integer, nullable=False)
    questions = relationship('Question', secondary=questions_association_table,
                             backref='groups', order_by='display_index')

responses_association_table = Table(
    'survey_question_response', Base.metadata,
    Column('survey_question_id', Integer, ForeignKey('ag.survey_question.id'),
           nullable=False, primary_key=True, unique=True),
    Column('response', String(), ForeignKey('ag.survey_response.american'),
           nullable=False, primary_key=True, unique=True),
    Column('display_index', Integer, nullable=False, primary_key=True),
    schema='ag')

class Question(Base):
    __tablename__ = 'survey_question'
    __table_args__ = {'schema': 'ag'}

    id = Column(BIGINT, nullable=False, unique=True, primary_key=True)
    question_shortname = Column(String(100), nullable=False, unique=True,
                                default='TODO')
    american = Column(String(), nullable=False, unique=True)
    british = Column(String(), unique=True)
    responses = relationship('Response', secondary=responses_association_table,
                             backref='questions', order_by='display_index')

class Response(Base):
    __tablename__ = 'survey_response'
    __table_args__ = {'schema': 'ag'}

    american = Column(String(), nullable=False, unique=True, primary_key=True)
    british = Column(String(), unique=True)


class Survey(Base):
    __tablename__ = 'surveys'
    __table_args__ = {'schema': 'ag'}

    id = Column(Integer, nullable=False, primary_key=True)
    survey_group = Column(Integer, ForeignKey('ag.survey_group.id'),
                          nullable=False, primary_key=True)
    groups = relationship('SurveyGroup', secondary=SurveyGroup,
                          backref='surveys', order_by='display_index')


class ParticipantResponse(Base):
    __tablename__ = 'participant_responses'
    __table_args__ = {'schema': 'ag'}

    survey_id = Column(String(), ForeignKey('ag.participant_survey.id'),
                       nullable=False, primary_key=True)
    survey_question_id = Column(
        String(), ForeignKey('ag.survey_question_response.response'),
        nullable=False, primary_key=True)
    response = Column(String(), nullable=False)
    free_response = Column(BOOLEAN, nullable=False, default=False)
    responses = relationship('Response')


# ---------- HELPER TABLES ----------

class Zipcode(Base):
    __tablename__ = 'zipcode'
    __table_args__ = {'schema': 'ag'}

    zipcode = Column(String(200), primary_key=True, nullable=False)
    state = Column(String(200))
    fips_regions = Column(String())
    city = Column(String(200))
    latitude = Column(FLOAT)
    longitude = Column(FLOAT)
    elevation = Column(FLOAT)
    cannot_geocode = Column(BOOLEAN)

# ---------- BUILD THE TABLES AND ORM ----------

engine = create_engine('postgresql://%s:%s@%s:%d/%s' %
                       (AMGUT_CONFIG.user, AMGUT_CONFIG.password,
                        AMGUT_CONFIG.host, AMGUT_CONFIG.port,
                        AMGUT_CONFIG.database))
Base.metadata.create_all(engine)
session = Session(bind=engine)
