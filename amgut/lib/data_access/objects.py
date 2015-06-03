#!/usr/bin/env python
from __future__ import division

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, event, DDL, Column, Table, ForeignKey
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import String, DateTime
from sqlalchemy.dialects.postgresql import (
    ARRAY, BIGINT, BIT, BOOLEAN, BYTEA, CHAR, CIDR, DATE,
    DOUBLE_PRECISION, ENUM, FLOAT, HSTORE, INET, INTEGER,
    INTERVAL, JSON, JSONB, MACADDR, NUMERIC, OID, REAL, SMALLINT, TEXT,
    TIME, TIMESTAMP, UUID, VARCHAR, INT4RANGE, INT8RANGE, NUMRANGE,
    DATERANGE, TSRANGE, TSTZRANGE, TSVECTOR)

from amgut.lib.config_manager import AMGUT_CONFIG

Base = declarative_base()
event.listen(Base.metadata, 'before_create', DDL(
    "CREATE SCHEMA IF NOT EXISTS ag"))
event.listen(Base.metadata, 'before_create', DDL(
    "CREATE SCHEMA IF NOT EXISTS barcodes"))

# ---------- GENERIC BARCODE TABLES ----------


class Barcode(Base):
    __tablename__ = 'barcode'
    __table_args__ = {'schema': 'barcodes'}
    __mapper_args__ = {'polymorphic_identity': 'barcode'}

    barcode = Column(String(), primary_key=True)
    create_date_time = Column(DateTime, default=func.now())
    status = Column(String(100))
    scan_date = Column(String(20))
    sample_postmark_date = Column(String(20))
    biomass_remaining = Column(String(1))
    sequencing_status = Column(ENUM(
        'WAITING', 'SUCCESS', 'FAILED_SEQUENCING', 'FAILED_SEQUENCING_1',
        'FAILED_SEQUENCING_2', 'FAILED_SEQUENCING_3', name='seq_status'))
    obsolete = Column(String(1))

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
    barcodes = relationship("Barcode", secondary=plate_association_table,
                            backref="plates")

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
    project = Column(String(200))
    barcodes = relationship("Barcode", secondary=project_association_table,
                            backref="projects")


# ---------- AG SPECIFIC TABLES ----------


class AGBarcode(Barcode):
    __tablename__ = 'barcode'
    __table_args__ = {'schema': 'ag'}
    __mapper_args__ = {'polymorphic_identity': 'ag_barcode'}

    kit_id = Column(UUID, ForeignKey('ag.kit.id'), primary_key=True)
    barcode = Column(String(), ForeignKey('barcodes.barcode.barcode'),
                     primary_key=True)
    survey_id = Column(String())
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


class Kit(Base):
    __tablename__ = 'kit'
    __table_args__ = {'schema': 'ag'}

    id = Column(UUID, default=func.uuid_generate_v4(), primary_key=True)
    ag_login_id = Column(UUID, ForeignKey('ag.login.id'), nullable=False)
    supplied_kit_id = Column(String(50), nullable=False)
    kit_password = Column(String(50))
    swabs_per_kit = Column(BIGINT, nullable=False)
    kit_verification_code = Column(String(50))
    kit_verified = Column(BOOLEAN, default=False)
    verification_email_sent = Column(BOOLEAN, default=False)
    pass_reset_code = Column(String(20))
    pass_reset_time = Column(DateTime())
    print_results = Column(BOOLEAN, default=False)
    barcodes = relationship("AGBarcode", backref="kit")


class Login(Base):
    __tablename__ = 'login'
    __table_args__ = {'schema': 'ag'}

    id = Column(UUID, default=func.uuid_generate_v4(), primary_key=True)
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
    kits = relationship("Kit", backref="login")

# ---------- BUILD THE TABLES AND ORM ----------

engine = create_engine("postgresql://%s:%s@%s:%d/%s" %
                       (AMGUT_CONFIG.user, AMGUT_CONFIG.password,
                        AMGUT_CONFIG.host, AMGUT_CONFIG.port,
                        AMGUT_CONFIG.database))
Base.metadata.create_all(engine)
session = Session(bind=engine)
