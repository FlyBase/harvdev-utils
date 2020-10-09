"""Chado Object Classes.

:synopsis: Chado Object Classes.

:moduleauthor: Christopher Tabone <ctabone@morgan.harvard.edu>, Ian Longden <ilongden@morgan.harvard.edu>

Produced originally from production_gen_init.py

NOTE: If you run this again do not overwrite, instead do a diff.
      many __str__ methods have been added to this file and this will be removed if overwritten.

"""
from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, Float, ForeignKey, Index, Integer, SmallInteger, String, Table, Text, UniqueConstraint, text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata


t_af_type = Table(
    'af_type', metadata,
    Column('feature_id', Integer),
    Column('name', String(255)),
    Column('uniquename', Text),
    Column('dbxref_id', Integer),
    Column('type', String(1024)),
    Column('residues', Text),
    Column('seqlen', Integer),
    Column('md5checksum', String(32)),
    Column('type_id', Integer),
    Column('organism_id', Integer),
    Column('analysis_id', Integer),
    Column('timeaccessioned', DateTime),
    Column('timelastmodified', DateTime)
)


t_alignment_evidence = Table(
    'alignment_evidence', metadata,
    Column('alignment_evidence_id', Text),
    Column('feature_id', Integer),
    Column('evidence_id', Integer),
    Column('analysis_id', Integer)
)


class Analysis(Base):
    __tablename__ = 'analysis'
    __table_args__ = (
        UniqueConstraint('program', 'programversion', 'sourcename'),
    )

    analysis_id = Column(Integer, primary_key=True, server_default=text("nextval('analysis_analysis_id_seq'::regclass)"))
    name = Column(String(255))
    description = Column(Text)
    program = Column(String(255), nullable=False)
    programversion = Column(String(255), nullable=False)
    algorithm = Column(String(255))
    sourcename = Column(String(255), index=True)
    sourceversion = Column(String(255))
    sourceuri = Column(Text)
    timeexecuted = Column(DateTime, nullable=False, server_default=text("('now'::text)::timestamp(6) with time zone"))

    def __str__(self):
        """Over write the default output."""
        return "Analysis id={}:  program:'{}' sourcename:'{}'".format(self.analysis_id, self.program, self.sourcename)


class Analysisfeature(Base):
    __tablename__ = 'analysisfeature'
    __table_args__ = (
        UniqueConstraint('feature_id', 'analysis_id'),
    )

    analysisfeature_id = Column(Integer, primary_key=True, server_default=text("nextval('analysisfeature_analysisfeature_id_seq'::regclass)"))
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    analysis_id = Column(ForeignKey('analysis.analysis_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    rawscore = Column(Float(53))
    normscore = Column(Float(53))
    significance = Column(Float(53))
    identity = Column(Float(53))

    analysis = relationship('Analysis')
    feature = relationship('Feature')

    def __str__(self):
        """Over write the default output."""
        return "AnalysisFeat id={}:\n\tAnalysis:({})\n\tFeature:({})".format(self.analysisfeature_id, self.analysis, self.feature)


class Analysisgrp(Base):
    __tablename__ = 'analysisgrp'
    __table_args__ = (
        UniqueConstraint('analysis_id', 'grp_id'),
    )

    analysisgrp_id = Column(Integer, primary_key=True, server_default=text("nextval('analysisgrp_analysisgrp_id_seq'::regclass)"))
    rawscore = Column(Float(53))
    normscore = Column(Float(53))
    significance = Column(Float(53))
    identity = Column(Float(53))
    analysis_id = Column(ForeignKey('analysis.analysis_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    grp_id = Column(ForeignKey('grp.grp_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    analysis = relationship('Analysis')
    grp = relationship('Grp')

    def __str__(self):
        """Over write the default output."""
        return "Analysisgrp id={}:\n\tAnalysis:({})\n\tGrp:({})".format(self.analysisgrp_id, self.analysis, self.grp)


class Analysisgrpmember(Base):
    __tablename__ = 'analysisgrpmember'
    __table_args__ = (
        UniqueConstraint('analysis_id', 'grpmember_id'),
    )

    analysisgrpmember_id = Column(Integer, primary_key=True, server_default=text("nextval('analysisgrpmember_analysisgrpmember_id_seq'::regclass)"))
    rawscore = Column(Float(53))
    normscore = Column(Float(53))
    significance = Column(Float(53))
    identity = Column(Float(53))
    analysis_id = Column(ForeignKey('analysis.analysis_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    grpmember_id = Column(ForeignKey('grpmember.grpmember_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    analysis = relationship('Analysis')
    grpmember = relationship('Grpmember')


class Analysisprop(Base):
    __tablename__ = 'analysisprop'
    __table_args__ = (
        UniqueConstraint('analysis_id', 'type_id', 'value'),
    )

    analysisprop_id = Column(Integer, primary_key=True, server_default=text("nextval('analysisprop_analysisprop_id_seq'::regclass)"))
    analysis_id = Column(ForeignKey('analysis.analysis_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)

    analysis = relationship('Analysis')
    type = relationship('Cvterm')


t_audit_chado = Table(
    'audit_chado', metadata,
    Column('audit_transaction', String(1), nullable=False),
    Column('transaction_timestamp', DateTime, nullable=False),
    Column('userid', String(255), nullable=False),
    Column('audited_table', String(255), nullable=False),
    Column('record_pkey', Integer, nullable=False),
    Column('record_ukey_cols', String, nullable=False),
    Column('record_ukey_vals', Text, nullable=False),
    Column('audited_cols', Text, nullable=False),
    Column('audited_vals', Text, nullable=False),
    Index('audit_idx1', 'audited_table', 'record_pkey')
)


class CellLine(Base):
    __tablename__ = 'cell_line'
    __table_args__ = (
        UniqueConstraint('uniquename', 'organism_id'),
    )

    cell_line_id = Column(Integer, primary_key=True, server_default=text("nextval('cell_line_cell_line_id_seq'::regclass)"))
    name = Column(String(255))
    uniquename = Column(String(255), nullable=False)
    organism_id = Column(ForeignKey('organism.organism_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    timeaccessioned = Column(DateTime, nullable=False, server_default=text("now()"))
    timelastmodified = Column(DateTime, nullable=False, server_default=text("now()"))

    organism = relationship('Organism')

    def __str__(self):
        """Over write the default output."""
        return "CellLine id={}: uniquename:'{}' name:'{}' organism:({})".format(self.cell_line_id, self.uniquename, self.name, self.organism)


class CellLineCvterm(Base):
    __tablename__ = 'cell_line_cvterm'
    __table_args__ = (
        UniqueConstraint('cell_line_id', 'cvterm_id', 'pub_id', 'rank'),
    )

    cell_line_cvterm_id = Column(Integer, primary_key=True, server_default=text("nextval('cell_line_cvterm_cell_line_cvterm_id_seq'::regclass)"))
    cell_line_id = Column(ForeignKey('cell_line.cell_line_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    cvterm_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    cell_line = relationship('CellLine')
    cvterm = relationship('Cvterm')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "CellLineCvterm id={}:\n\tcellline:({})\n\tcvterm:({})\n\tpub:({})".format(self.cell_line_cvterm_id, self.cell_line, self.cvterm, self.pub)


class CellLineCvtermprop(Base):
    __tablename__ = 'cell_line_cvtermprop'
    __table_args__ = (
        UniqueConstraint('cell_line_cvterm_id', 'type_id', 'rank'),
    )

    cell_line_cvtermprop_id = Column(Integer, primary_key=True, server_default=text("nextval('cell_line_cvtermprop_cell_line_cvtermprop_id_seq'::regclass)"))
    cell_line_cvterm_id = Column(ForeignKey('cell_line_cvterm.cell_line_cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    cell_line_cvterm = relationship('CellLineCvterm')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "CellLineCvtermprop id={}: value:'{}' type:({}) clc:({})".\
            format(self.cell_line_cvtermprop_id, self.value, self.type, self.cell_line_cvterm)


class CellLineDbxref(Base):
    __tablename__ = 'cell_line_dbxref'
    __table_args__ = (
        UniqueConstraint('cell_line_id', 'dbxref_id'),
    )

    cell_line_dbxref_id = Column(Integer, primary_key=True, server_default=text("nextval('cell_line_dbxref_cell_line_dbxref_id_seq'::regclass)"))
    cell_line_id = Column(ForeignKey('cell_line.cell_line_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    dbxref_id = Column(ForeignKey('dbxref.dbxref_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    is_current = Column(Boolean, nullable=False, server_default=text("true"))

    cell_line = relationship('CellLine')
    dbxref = relationship('Dbxref')

    def __str__(self):
        """Over write the default output."""
        return "CellLineDbxref id={}: CellLine:({}) dbxef:({}) current:{}".\
            format(self.cell_line_dbxref_id, self.cell_line, self.dbxef)


class CellLineFeature(Base):
    __tablename__ = 'cell_line_feature'
    __table_args__ = (
        UniqueConstraint('cell_line_id', 'feature_id', 'pub_id'),
    )

    cell_line_feature_id = Column(Integer, primary_key=True, server_default=text("nextval('cell_line_feature_cell_line_feature_id_seq'::regclass)"))
    cell_line_id = Column(ForeignKey('cell_line.cell_line_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    cell_line = relationship('CellLine')
    feature = relationship('Feature')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "CellLineFeature id={}:\n\tcell line:({})\n\tfeature:({})\n\tpub:({})".\
            format(self.cell_line_feature_id, self.cell_line, self.feature, self.pub)


class CellLineLibrary(Base):
    __tablename__ = 'cell_line_library'
    __table_args__ = (
        UniqueConstraint('cell_line_id', 'library_id', 'pub_id'),
    )

    cell_line_library_id = Column(Integer, primary_key=True, server_default=text("nextval('cell_line_library_cell_line_library_id_seq'::regclass)"))
    cell_line_id = Column(ForeignKey('cell_line.cell_line_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    library_id = Column(ForeignKey('library.library_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    cell_line = relationship('CellLine')
    library = relationship('Library')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "CellLineLibrary id={}:\n\tcell line:({})\n\tlibrary:({})\n\tpub:({})".\
            format(self.cell_line_library_id, self.cell_line, self.library, self.pub)


class CellLineLibraryprop(Base):
    __tablename__ = 'cell_line_libraryprop'
    __table_args__ = (
        UniqueConstraint('cell_line_library_id', 'type_id', 'rank'),
    )

    cell_line_libraryprop_id = Column(Integer, primary_key=True, server_default=text("nextval('cell_line_libraryprop_cell_line_libraryprop_id_seq'::regclass)"))
    cell_line_library_id = Column(ForeignKey('cell_line_library.cell_line_library_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    cell_line_library = relationship('CellLineLibrary')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "CellLineLibraryprop id={}: value:{} rank:{}\n\tLibrary:({})\n\tType:({})".\
            format(self.cell_line_libraryprop_id, self.value, self.rank, self.cell_line_library, self.type)


class CellLinePub(Base):
    __tablename__ = 'cell_line_pub'
    __table_args__ = (
        UniqueConstraint('cell_line_id', 'pub_id'),
    )

    cell_line_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('cell_line_pub_cell_line_pub_id_seq'::regclass)"))
    cell_line_id = Column(ForeignKey('cell_line.cell_line_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    cell_line = relationship('CellLine')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "CellLinePub id={}:\n\tcell line:({})\n\tpub:({})".\
            format(self.cell_line_pub_id, self.cell_line, self.pub)


class CellLineRelationship(Base):
    __tablename__ = 'cell_line_relationship'
    __table_args__ = (
        UniqueConstraint('subject_id', 'object_id', 'type_id'),
    )

    cell_line_relationship_id = Column(Integer, primary_key=True, server_default=text("nextval('cell_line_relationship_cell_line_relationship_id_seq'::regclass)"))
    subject_id = Column(ForeignKey('cell_line.cell_line_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    object_id = Column(ForeignKey('cell_line.cell_line_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    object = relationship('CellLine', primaryjoin='CellLineRelationship.object_id == CellLine.cell_line_id')
    subject = relationship('CellLine', primaryjoin='CellLineRelationship.subject_id == CellLine.cell_line_id')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "CellLineRelationship id={}:\n\tObject:({})\n\tSubject:({})\n\tType({})".\
            format(self.cell_line_relationship_id, self.object, self.subject, self.type)


class CellLineStrain(Base):
    __tablename__ = 'cell_line_strain'
    __table_args__ = (
        UniqueConstraint('strain_id', 'cell_line_id', 'pub_id'),
    )

    cell_line_strain_id = Column(Integer, primary_key=True, server_default=text("nextval('cell_line_strain_cell_line_strain_id_seq'::regclass)"))
    strain_id = Column(ForeignKey('strain.strain_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    cell_line_id = Column(ForeignKey('cell_line.cell_line_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    cell_line = relationship('CellLine')
    pub = relationship('Pub')
    strain = relationship('Strain')

    def __str__(self):
        """Over write the default output."""
        return "CellLineStrain id={}:\n\tcell line:({})\n\tstrain:({})\n\tpub:({})".\
            format(self.cell_line_strain_id, self.cell_line, self.strain, self.pub)


class CellLineStrainprop(Base):
    __tablename__ = 'cell_line_strainprop'
    __table_args__ = (
        UniqueConstraint('cell_line_strain_id', 'type_id', 'rank'),
    )

    cell_line_strainprop_id = Column(Integer, primary_key=True, server_default=text("nextval('cell_line_strainprop_cell_line_strainprop_id_seq'::regclass)"))
    cell_line_strain_id = Column(ForeignKey('cell_line_strain.cell_line_strain_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    cell_line_strain = relationship('CellLineStrain')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "CellLineStrainprop id={}: value:'{}' rank:'{}'\n\tcell line strain:({})\n\tType:({})".\
            format(self.cell_line_strainprop_id, self.value, self.rank, self.cell_line_strain, self.type)


class CellLineSynonym(Base):
    __tablename__ = 'cell_line_synonym'
    __table_args__ = (
        UniqueConstraint('synonym_id', 'cell_line_id', 'pub_id'),
    )

    cell_line_synonym_id = Column(Integer, primary_key=True, server_default=text("nextval('cell_line_synonym_cell_line_synonym_id_seq'::regclass)"))
    cell_line_id = Column(ForeignKey('cell_line.cell_line_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    synonym_id = Column(ForeignKey('synonym.synonym_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    is_current = Column(Boolean, nullable=False, server_default=text("false"))
    is_internal = Column(Boolean, nullable=False, server_default=text("false"))

    cell_line = relationship('CellLine')
    pub = relationship('Pub')
    synonym = relationship('Synonym')

    def __str__(self):
        """Over write the default output."""
        return "CellLineSynonym id={}: is_current:{} is_internal:{}\n\tcell line:({})\n\tsynonym:({})\n\tpub:({})".\
            format(self.cell_line_synonym_id, self.is_current, self.is_internal, self.cell_line, self.synonym, self.pub)


class CellLineprop(Base):
    __tablename__ = 'cell_lineprop'
    __table_args__ = (
        UniqueConstraint('cell_line_id', 'type_id', 'rank'),
    )

    cell_lineprop_id = Column(Integer, primary_key=True, server_default=text("nextval('cell_lineprop_cell_lineprop_id_seq'::regclass)"))
    cell_line_id = Column(ForeignKey('cell_line.cell_line_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    cell_line = relationship('CellLine')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "CellLineprop id={}: value:'{}' rank:'{}'\n\tcell line:({})\n\ttype::({})".\
            format(self.cell_lineprop_id, self.value, self.rank, self.cell_line, self.type)


class CellLinepropPub(Base):
    __tablename__ = 'cell_lineprop_pub'
    __table_args__ = (
        UniqueConstraint('cell_lineprop_id', 'pub_id'),
    )

    cell_lineprop_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('cell_lineprop_pub_cell_lineprop_pub_id_seq'::regclass)"))
    cell_lineprop_id = Column(ForeignKey('cell_lineprop.cell_lineprop_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    cell_lineprop = relationship('CellLineprop')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "CellLineproppub id={}:\n\tcell line prop:({})\n\tpub:{})".\
            format(self.cell_lineprop_pub_id, self.cell_lineprop, self.pub)


class Contact(Base):
    __tablename__ = 'contact'

    contact_id = Column(Integer, primary_key=True, server_default=text("nextval('contact_contact_id_seq'::regclass)"))
    description = Column(String(255))
    name = Column(String(30), nullable=False, unique=True)


class Cv(Base):
    __tablename__ = 'cv'

    cv_id = Column(Integer, primary_key=True, server_default=text("nextval('cv_cv_id_seq'::regclass)"))
    name = Column(String(255), nullable=False, unique=True)
    definition = Column(Text)

    def __str__(self):
        """Over write the default output."""
        return "Cv id={}: name:'{}'".format(self.cv_id, self.name)


class Cvterm(Base):
    __tablename__ = 'cvterm'
    __table_args__ = (
        UniqueConstraint('cv_id', 'name', 'is_obsolete'),
    )

    cvterm_id = Column(Integer, primary_key=True, server_default=text("nextval('cvterm_cvterm_id_seq'::regclass)"))
    cv_id = Column(ForeignKey('cv.cv_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    definition = Column(Text)
    dbxref_id = Column(ForeignKey('dbxref.dbxref_id', ondelete='SET NULL'), nullable=False, unique=True)
    is_obsolete = Column(Integer, nullable=False, server_default=text("0"))
    is_relationshiptype = Column(Integer, nullable=False, server_default=text("0"))
    name = Column(String(1024), nullable=False, index=True)

    cv = relationship('Cv')
    dbxref = relationship('Dbxref', uselist=False)

    def __str__(self):
        """Over write the default output."""
        return "Cvterm id={}: name:'{}' cv:({})".format(self.cvterm_id, self.name, self.cv)


class CvtermDbxref(Base):
    __tablename__ = 'cvterm_dbxref'
    __table_args__ = (
        UniqueConstraint('cvterm_id', 'dbxref_id'),
    )

    cvterm_dbxref_id = Column(Integer, primary_key=True, server_default=text("nextval('cvterm_dbxref_cvterm_dbxref_id_seq'::regclass)"))
    cvterm_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    dbxref_id = Column(ForeignKey('dbxref.dbxref_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    is_for_definition = Column(Integer, nullable=False, server_default=text("0"))

    cvterm = relationship('Cvterm')
    dbxref = relationship('Dbxref')

    def __str__(self):
        """Over write the default output."""
        return "CvtermDbxref id={}: is_for_definition:{}\n\tcvterm:({})\n\tdbxref:({})".\
            format(self.cvterm_dbxref_id, self.is_for_definition, self.cvterm, self.dbxref)


class CvtermRelationship(Base):
    __tablename__ = 'cvterm_relationship'
    __table_args__ = (
        UniqueConstraint('type_id', 'subject_id', 'object_id'),
    )

    cvterm_relationship_id = Column(Integer, primary_key=True, server_default=text("nextval('cvterm_relationship_cvterm_relationship_id_seq'::regclass)"))
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    subject_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    object_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    object = relationship('Cvterm', primaryjoin='CvtermRelationship.object_id == Cvterm.cvterm_id')
    subject = relationship('Cvterm', primaryjoin='CvtermRelationship.subject_id == Cvterm.cvterm_id')
    type = relationship('Cvterm', primaryjoin='CvtermRelationship.type_id == Cvterm.cvterm_id')

    def __str__(self):
        """Over write the default output."""
        return "CvtermRelationship id={}:\n\tobject:({})\n\tsubject:({})\n\ttype:({})".\
            format(self.cvterm_relationship_id, self.object, self.subject, self.type)


t_cvterm_type = Table(
    'cvterm_type', metadata,
    Column('cvterm_id', Integer),
    Column('name', String(1024)),
    Column('termtype', String(255))
)


class Cvtermpath(Base):
    __tablename__ = 'cvtermpath'
    __table_args__ = (
        UniqueConstraint('subject_id', 'object_id'),
    )

    cvtermpath_id = Column(Integer, primary_key=True, server_default=text("nextval('cvtermpath_cvtermpath_id_seq'::regclass)"))
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='SET NULL'), index=True)
    subject_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    object_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    cv_id = Column(Integer, nullable=False, index=True)
    pathdistance = Column(Integer)

    object = relationship('Cvterm', primaryjoin='Cvtermpath.object_id == Cvterm.cvterm_id')
    subject = relationship('Cvterm', primaryjoin='Cvtermpath.subject_id == Cvterm.cvterm_id')
    type = relationship('Cvterm', primaryjoin='Cvtermpath.type_id == Cvterm.cvterm_id')


class Cvtermprop(Base):
    __tablename__ = 'cvtermprop'
    __table_args__ = (
        UniqueConstraint('cvterm_id', 'type_id', 'value', 'rank'),
    )

    cvtermprop_id = Column(Integer, primary_key=True, server_default=text("nextval('cvtermprop_cvtermprop_id_seq'::regclass)"))
    cvterm_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text, nullable=False, server_default=text("''::text"))
    rank = Column(Integer, nullable=False, server_default=text("0"))

    cvterm = relationship('Cvterm', primaryjoin='Cvtermprop.cvterm_id == Cvterm.cvterm_id')
    type = relationship('Cvterm', primaryjoin='Cvtermprop.type_id == Cvterm.cvterm_id')


class Cvtermsynonym(Base):
    __tablename__ = 'cvtermsynonym'
    __table_args__ = (
        UniqueConstraint('cvterm_id', 'name'),
    )

    cvtermsynonym_id = Column(Integer, primary_key=True, server_default=text("nextval('cvtermsynonym_cvtermsynonym_id_seq'::regclass)"))
    cvterm_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    name = Column(String(1024), nullable=False)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'))

    cvterm = relationship('Cvterm', primaryjoin='Cvtermsynonym.cvterm_id == Cvterm.cvterm_id')
    type = relationship('Cvterm', primaryjoin='Cvtermsynonym.type_id == Cvterm.cvterm_id')


class Db(Base):
    __tablename__ = 'db'

    db_id = Column(Integer, primary_key=True, server_default=text("nextval('db_db_id_seq'::regclass)"))
    name = Column(String(255), nullable=False, unique=True)
    contact_id = Column(ForeignKey('contact.contact_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'))
    description = Column(String(255))
    urlprefix = Column(String(255))
    url = Column(String(255))

    contact = relationship('Contact')

    def __str__(self):
        """Over write the default output."""
        return "Db id={}: name:'{}'".format(self.db_id, self.name)


class Dbxref(Base):
    __tablename__ = 'dbxref'
    __table_args__ = (
        UniqueConstraint('db_id', 'accession', 'version'),
    )

    dbxref_id = Column(Integer, primary_key=True, server_default=text("nextval('dbxref_dbxref_id_seq'::regclass)"))
    db_id = Column(ForeignKey('db.db_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    accession = Column(String(255), nullable=False, index=True)
    version = Column(String(255), nullable=False, index=True, server_default=text("''::character varying"))
    description = Column(Text)
    url = Column(String(255))

    db = relationship('Db')

    def __str__(self):
        """Over write the default output."""
        return "Dbxref id={}: acc:'{}' Db:({})".format(self.dbxref_id, self.accession, self.db)


class Dbxrefprop(Base):
    __tablename__ = 'dbxrefprop'
    __table_args__ = (
        UniqueConstraint('dbxref_id', 'type_id', 'rank'),
    )

    dbxrefprop_id = Column(Integer, primary_key=True, server_default=text("nextval('dbxrefprop_dbxrefprop_id_seq'::regclass)"))
    dbxref_id = Column(ForeignKey('dbxref.dbxref_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text, nullable=False, server_default=text("''::text"))
    rank = Column(Integer, nullable=False, server_default=text("0"))

    dbxref = relationship('Dbxref')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "Dbxrefprop id={}: value:'{}' rank:'{}'\n\tdbxref:({})\n\ttype:({})".\
            format(self.dbxrefprop_id, self.value, self.rank, self.dbxref, self.type)


class Eimage(Base):
    __tablename__ = 'eimage'

    eimage_id = Column(Integer, primary_key=True, server_default=text("nextval('eimage_eimage_id_seq'::regclass)"))
    eimage_data = Column(Text)
    eimage_type = Column(String(255), nullable=False)
    image_uri = Column(String(255))


class Environment(Base):
    __tablename__ = 'environment'

    environment_id = Column(Integer, primary_key=True, server_default=text("nextval('environment_environment_id_seq'::regclass)"))
    uniquename = Column(Text, nullable=False, unique=True)
    description = Column(Text)

    def __str__(self):
        """Over write the default output."""
        return "environment_id id={}: uniquename:'{}' desc:'{}'".\
            format(self.environment_id, self.uniquename, self.description)


class EnvironmentCvterm(Base):
    __tablename__ = 'environment_cvterm'
    __table_args__ = (
        UniqueConstraint('environment_id', 'cvterm_id'),
    )

    environment_cvterm_id = Column(Integer, primary_key=True, server_default=text("nextval('environment_cvterm_environment_cvterm_id_seq'::regclass)"))
    environment_id = Column(ForeignKey('environment.environment_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    cvterm_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    cvterm = relationship('Cvterm')
    environment = relationship('Environment')


class Expression(Base):
    __tablename__ = 'expression'

    expression_id = Column(Integer, primary_key=True, server_default=text("nextval('expression_expression_id_seq'::regclass)"))
    uniquename = Column(Text, nullable=False, unique=True)
    md5checksum = Column(String(32))
    description = Column(Text)

    def __str__(self):
        """Over write the default output."""
        return "Expression id={}: uniquename:{} description:{}".format(self.expression_id, self.uniquename, self.description)


class ExpressionCvterm(Base):
    __tablename__ = 'expression_cvterm'
    __table_args__ = (
        UniqueConstraint('expression_id', 'cvterm_id', 'rank', 'cvterm_type_id'),
    )

    expression_cvterm_id = Column(Integer, primary_key=True, server_default=text("nextval('expression_cvterm_expression_cvterm_id_seq'::regclass)"))
    expression_id = Column(ForeignKey('expression.expression_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    cvterm_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    rank = Column(Integer, nullable=False, server_default=text("0"))
    cvterm_type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    cvterm = relationship('Cvterm', primaryjoin='ExpressionCvterm.cvterm_id == Cvterm.cvterm_id')
    cvterm_type = relationship('Cvterm', primaryjoin='ExpressionCvterm.cvterm_type_id == Cvterm.cvterm_id')
    expression = relationship('Expression')

    def __str__(self):
        """Over write the default output."""
        return "ExpressionCvterm id={}: rank:'{}'\n\tcvterm:({})\n\ttype:({})\n\texpression:({})".\
            format(self.expression_cvterm_id, self.rank, self.cvterm, self.cvterm_type, self.expression)


class ExpressionCvtermprop(Base):
    __tablename__ = 'expression_cvtermprop'
    __table_args__ = (
        UniqueConstraint('expression_cvterm_id', 'type_id', 'rank'),
    )

    expression_cvtermprop_id = Column(Integer, primary_key=True, server_default=text("nextval('expression_cvtermprop_expression_cvtermprop_id_seq'::regclass)"))
    expression_cvterm_id = Column(ForeignKey('expression_cvterm.expression_cvterm_id', ondelete='CASCADE'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    expression_cvterm = relationship('ExpressionCvterm')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "ExpressionCvtermprop id={}: value:'{}' rank:'{}'\n\texp_cvt:({})\n\ttype:({})".\
            format(self.expression_cvtermprop_id, self.value, self.rank, self.expression_cvterm, self.type)


class ExpressionImage(Base):
    __tablename__ = 'expression_image'
    __table_args__ = (
        UniqueConstraint('expression_id', 'eimage_id'),
    )

    expression_image_id = Column(Integer, primary_key=True, server_default=text("nextval('expression_image_expression_image_id_seq'::regclass)"))
    expression_id = Column(ForeignKey('expression.expression_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    eimage_id = Column(ForeignKey('eimage.eimage_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    eimage = relationship('Eimage')
    expression = relationship('Expression')


class ExpressionPub(Base):
    __tablename__ = 'expression_pub'
    __table_args__ = (
        UniqueConstraint('expression_id', 'pub_id'),
    )

    expression_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('expression_pub_expression_pub_id_seq'::regclass)"))
    expression_id = Column(ForeignKey('expression.expression_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    expression = relationship('Expression')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "ExpressionPub id={}:\n\texpression:({})\n\tpub:({})".\
            format(self.expression_pub_id, self.expression, self.pub)


class Expressionprop(Base):
    __tablename__ = 'expressionprop'
    __table_args__ = (
        UniqueConstraint('expression_id', 'type_id', 'rank'),
    )

    expressionprop_id = Column(Integer, primary_key=True, server_default=text("nextval('expressionprop_expressionprop_id_seq'::regclass)"))
    expression_id = Column(ForeignKey('expression.expression_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    expression = relationship('Expression')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "Expressionprop id={}: value:'{}' rank:'{}'\n\texpression:({})\n\ttype:({})".\
            format(self.expressionprop_id, self.expression, self.type)


t_f_loc = Table(
    'f_loc', metadata,
    Column('feature_id', Integer),
    Column('name', String(255)),
    Column('dbxref_id', Integer),
    Column('fmin', Integer),
    Column('fmax', Integer),
    Column('strand', SmallInteger)
)


t_f_type = Table(
    'f_type', metadata,
    Column('feature_id', Integer),
    Column('name', String(255)),
    Column('uniquename', Text),
    Column('dbxref_id', Integer),
    Column('type', String(1024)),
    Column('residues', Text),
    Column('seqlen', Integer),
    Column('md5checksum', String(32)),
    Column('type_id', Integer),
    Column('organism_id', Integer),
    Column('is_analysis', Boolean),
    Column('timeaccessioned', DateTime),
    Column('timelastmodified', DateTime)
)


class Feature(Base):
    __tablename__ = 'feature'
    __table_args__ = (
        UniqueConstraint('organism_id', 'uniquename', 'type_id'),
    )

    feature_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_feature_id_seq'::regclass)"))
    dbxref_id = Column(ForeignKey('dbxref.dbxref_id', ondelete='SET NULL'), index=True)
    organism_id = Column(ForeignKey('organism.organism_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    name = Column(String(255), index=True)
    uniquename = Column(Text, nullable=False, index=True)
    residues = Column(Text)
    seqlen = Column(Integer)
    md5checksum = Column(String(32))
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    is_analysis = Column(Boolean, nullable=False, server_default=text("false"))
    timeaccessioned = Column(DateTime, nullable=False, server_default=text("('now'::text)::timestamp(6) with time zone"))
    timelastmodified = Column(DateTime, nullable=False, server_default=text("('now'::text)::timestamp(6) with time zone"))
    is_obsolete = Column(Boolean, nullable=False, server_default=text("false"))

    dbxref = relationship('Dbxref')
    organism = relationship('Organism')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        # ? add dbxref org?
        return "Feature id={}: uniquename:'{}' name:'{}' obsolete:{} type:({})".\
            format(self.feature_id, self.uniquename, self.name, self.is_obsolete, self.type)


class FeatureCvterm(Base):
    __tablename__ = 'feature_cvterm'
    __table_args__ = (
        UniqueConstraint('feature_id', 'cvterm_id', 'pub_id'),
    )

    feature_cvterm_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_cvterm_feature_cvterm_id_seq'::regclass)"))
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    cvterm_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    is_not = Column(Boolean, nullable=False, server_default=text("false"))

    cvterm = relationship('Cvterm')
    feature = relationship('Feature')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "FeatureCvterm id={}: is_not={}\n\tcvterm:({})\n\tfeature:({})\n\tpub:({})".\
            format(self.feature_cvterm_id, self.is_not, self.cvterm, self.feature, self.pub)


class FeatureCvtermDbxref(Base):
    __tablename__ = 'feature_cvterm_dbxref'
    __table_args__ = (
        UniqueConstraint('feature_cvterm_id', 'dbxref_id'),
    )

    feature_cvterm_dbxref_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_cvterm_dbxref_feature_cvterm_dbxref_id_seq'::regclass)"))
    feature_cvterm_id = Column(ForeignKey('feature_cvterm.feature_cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    dbxref_id = Column(ForeignKey('dbxref.dbxref_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    dbxref = relationship('Dbxref')
    feature_cvterm = relationship('FeatureCvterm')

    def __str__(self):
        """Over write the default output."""
        return "FeatureCvtermDbxref id={}:\n\tdbxref:({})\n\tfeat_cvterm:({})".\
            format(self.feature_cvterm_dbxref_id, self.dbxref, self.feature_cvterm)


class FeatureCvtermprop(Base):
    __tablename__ = 'feature_cvtermprop'
    __table_args__ = (
        UniqueConstraint('feature_cvterm_id', 'type_id', 'rank'),
    )

    feature_cvtermprop_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_cvtermprop_feature_cvtermprop_id_seq'::regclass)"))
    feature_cvterm_id = Column(ForeignKey('feature_cvterm.feature_cvterm_id', ondelete='CASCADE'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    feature_cvterm = relationship('FeatureCvterm')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "FeatureCvtermprop id={}: value='{}' rank='{}'\n\tfeat_cvterm:({})\n\ttype:({})".\
            format(self.feature_cvtermprop_id, self.value, self.rank, self.feature_cvterm, self.type)


class FeatureDbxref(Base):
    __tablename__ = 'feature_dbxref'
    __table_args__ = (
        UniqueConstraint('feature_id', 'dbxref_id'),
    )

    feature_dbxref_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_dbxref_feature_dbxref_id_seq'::regclass)"))
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    dbxref_id = Column(ForeignKey('dbxref.dbxref_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    is_current = Column(Boolean, nullable=False, server_default=text("true"))

    dbxref = relationship('Dbxref')
    feature = relationship('Feature')

    def __str__(self):
        """Over write the default output."""
        return "FeatureDbxref id={}: is_current:{}\n\tdbxref:({})\n\tfeature:({})".\
            format(self.feature_dbxref_id, self.is_current, self.dbxref, self.feature)


class FeatureExpression(Base):
    __tablename__ = 'feature_expression'
    __table_args__ = (
        UniqueConstraint('expression_id', 'feature_id', 'pub_id'),
    )

    feature_expression_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_expression_feature_expression_id_seq'::regclass)"))
    expression_id = Column(ForeignKey('expression.expression_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    expression = relationship('Expression')
    feature = relationship('Feature')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "FeatureExpression id={}:\n\texpression:({})\n\tfeature:({})\n\tpub:({})".\
            format(self.feature_expression_id, self.expression, self.feature, self.pub)


class FeatureExpressionprop(Base):
    __tablename__ = 'feature_expressionprop'
    __table_args__ = (
        UniqueConstraint('feature_expression_id', 'type_id', 'rank'),
    )

    feature_expressionprop_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_expressionprop_feature_expressionprop_id_seq'::regclass)"))
    feature_expression_id = Column(ForeignKey('feature_expression.feature_expression_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    feature_expression = relationship('FeatureExpression')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "FeatureExpressionprop id={}: value:'{}' rank:'{}'\n\tfeat exp:({})\n\ttype:({})".\
            format(self.feature_expressionprop_id, self.value, self.rank, self.feature_expression, self.type)


class FeatureGenotype(Base):
    __tablename__ = 'feature_genotype'
    __table_args__ = (
        UniqueConstraint('feature_id', 'genotype_id', 'cvterm_id', 'chromosome_id', 'rank', 'cgroup'),
    )

    feature_genotype_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_genotype_feature_genotype_id_seq'::regclass)"))
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    genotype_id = Column(ForeignKey('genotype.genotype_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    chromosome_id = Column(ForeignKey('feature.feature_id', ondelete='SET NULL'))
    rank = Column(Integer, nullable=False)
    cgroup = Column(Integer, nullable=False)
    cvterm_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    chromosome = relationship('Feature', primaryjoin='FeatureGenotype.chromosome_id == Feature.feature_id')
    cvterm = relationship('Cvterm')
    feature = relationship('Feature', primaryjoin='FeatureGenotype.feature_id == Feature.feature_id')
    genotype = relationship('Genotype')

    def __str__(self):
        """Over write the default output."""
        return "FeatureGenotype id={}: rank:'{}' cgroup:'{}'\n\tchrom:({})\n\tfeat:({})\n\tgenotype:({})\n\tcvterm:({})".\
            format(self.feature_genotype_id, self.rank, self.cgroup, self.chromosome, self.feature, self.genotype, self.cvterm)



class FeatureGrpmember(Base):
    __tablename__ = 'feature_grpmember'
    __table_args__ = (
        UniqueConstraint('grpmember_id', 'feature_id'),
    )

    feature_grpmember_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_grpmember_feature_grpmember_id_seq'::regclass)"))
    grpmember_id = Column(ForeignKey('grpmember.grpmember_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    feature = relationship('Feature')
    grpmember = relationship('Grpmember')

    def __str__(self):
        """Over write the default output."""
        return "FeatureGrpmember id={}:\n\tfeature({})\n\tgrpmember:({})".\
            format(self.feature_grpmember_id, self.feature, self.grpmember)


class FeatureGrpmemberPub(Base):
    __tablename__ = 'feature_grpmember_pub'
    __table_args__ = (
        UniqueConstraint('pub_id', 'feature_grpmember_id'),
    )

    feature_grpmember_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_grpmember_pub_feature_grpmember_pub_id_seq'::regclass)"))
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    feature_grpmember_id = Column(ForeignKey('feature_grpmember.feature_grpmember_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    feature_grpmember = relationship('FeatureGrpmember')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "FeatureGrpmemberPub id={}:\n\tfeature_grpmember:({})\n\tpub({})".\
            format(self.feature_grpmember_pub_id, self.feature_grpmember, self.pub)


class FeatureHumanhealthDbxref(Base):
    __tablename__ = 'feature_humanhealth_dbxref'
    __table_args__ = (
        UniqueConstraint('humanhealth_dbxref_id', 'feature_id', 'pub_id'),
    )

    feature_humanhealth_dbxref_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_humanhealth_dbxref_feature_humanhealth_dbxref_id_seq'::regclass)"))
    humanhealth_dbxref_id = Column(ForeignKey('humanhealth_dbxref.humanhealth_dbxref_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    feature = relationship('Feature')
    humanhealth_dbxref = relationship('HumanhealthDbxref')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "FeatureHumanhealthDbxref id={}:\n\tfeature:({})\n\thh_dbxref:({})\n\tpub:({})".\
            format(self.feature_humanhealth_dbxref_id, self.feature, self.humanhealth_dbxref, self.pub)


class FeatureInteraction(Base):
    __tablename__ = 'feature_interaction'
    __table_args__ = (
        UniqueConstraint('feature_id', 'interaction_id', 'role_id'),
    )

    feature_interaction_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_interaction_feature_interaction_id_seq'::regclass)"))
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    interaction_id = Column(ForeignKey('interaction.interaction_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    role_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    feature = relationship('Feature')
    interaction = relationship('Interaction')
    role = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "FeatureInteraction id={}: rank:'{}'\n\tfeature:({})\n\tinteraction:({})\n\trole:({})".\
            format(self.feature_interaction_id, self.rank, self.feature, self.interaction, self.role)


class FeatureInteractionPub(Base):
    __tablename__ = 'feature_interaction_pub'
    __table_args__ = (
        UniqueConstraint('feature_interaction_id', 'pub_id'),
    )

    feature_interaction_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_interaction_pub_feature_interaction_pub_id_seq'::regclass)"))
    feature_interaction_id = Column(ForeignKey('feature_interaction.feature_interaction_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    feature_interaction = relationship('FeatureInteraction')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "FeatureInteractionPub id={}:\n\tFI:({})\n\tPub:({})".\
            format(self.feature_interaction_pub_id, self.feature_interaction, self.pub)


class FeatureInteractionprop(Base):
    __tablename__ = 'feature_interactionprop'
    __table_args__ = (
        UniqueConstraint('feature_interaction_id', 'type_id', 'rank'),
    )

    feature_interactionprop_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_interactionprop_feature_interactionprop_id_seq'::regclass)"))
    feature_interaction_id = Column(ForeignKey('feature_interaction.feature_interaction_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    feature_interaction = relationship('FeatureInteraction')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "FeatureInteractionprop id={}: value:'{}' rank:'{}'\n\tFI:({})\n\ttype:({})".\
            format(self.feature_interactionprop_id, self.value, self.rank, self.feature_interaction, self.type)


class FeaturePhenotype(Base):
    __tablename__ = 'feature_phenotype'
    __table_args__ = (
        UniqueConstraint('feature_id', 'phenotype_id'),
    )

    feature_phenotype_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_phenotype_feature_phenotype_id_seq'::regclass)"))
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    phenotype_id = Column(ForeignKey('phenotype.phenotype_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    feature = relationship('Feature')
    phenotype = relationship('Phenotype')

    def __str__(self):
        """Over write the default output."""
        return "FeaturePhenotype id={}:\n\tFeat:({})\n\tPhenotype:({})".\
            format(self.feature_phenotype_id, self.feature, self.type)


class FeaturePub(Base):
    __tablename__ = 'feature_pub'
    __table_args__ = (
        UniqueConstraint('feature_id', 'pub_id'),
    )

    feature_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_pub_feature_pub_id_seq'::regclass)"))
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    feature = relationship('Feature')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "FeaturePub id={}:\n\tFeat:({})\n\tPub:({})".\
            format(self.feature_pub_id, self.feature, self.pub)


class FeaturePubprop(Base):
    __tablename__ = 'feature_pubprop'
    __table_args__ = (
        UniqueConstraint('feature_pub_id', 'type_id', 'rank'),
    )

    feature_pubprop_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_pubprop_feature_pubprop_id_seq'::regclass)"))
    feature_pub_id = Column(ForeignKey('feature_pub.feature_pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    feature_pub = relationship('FeaturePub')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "FeaturePubprop id={}: value:'{}' rank:'{}'\nFeatPub:({})\n\ttype:({})".\
            format(self.feature_pubprop_id, self.value, self.rank, self.feature_pub, self.type)


class FeatureRelationship(Base):
    __tablename__ = 'feature_relationship'
    __table_args__ = (
        UniqueConstraint('subject_id', 'object_id', 'type_id', 'rank'),
    )

    feature_relationship_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_relationship_feature_relationship_id_seq'::regclass)"))
    subject_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    object_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    rank = Column(Integer, nullable=False, server_default=text("0"))
    value = Column(Text)

    object = relationship('Feature', primaryjoin='FeatureRelationship.object_id == Feature.feature_id')
    subject = relationship('Feature', primaryjoin='FeatureRelationship.subject_id == Feature.feature_id')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "FeatureRelationship id={}: value:'{}' rank:'{}'\n\tObj:({})\n\tSub:({})\n\ttype:({})".\
            format(self.feature_relationship_id, self.value, self.rank, self.object, self.subject, self.type)


class FeatureRelationshipPub(Base):
    __tablename__ = 'feature_relationship_pub'
    __table_args__ = (
        UniqueConstraint('feature_relationship_id', 'pub_id'),
    )

    feature_relationship_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_relationship_pub_feature_relationship_pub_id_seq'::regclass)"))
    feature_relationship_id = Column(ForeignKey('feature_relationship.feature_relationship_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    feature_relationship = relationship('FeatureRelationship')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "FeatureRelationshipPub id={}:\n\tFR:({})\n\tPub:({})".\
            format(self.feature_relationship_pub_id, self.feature_relationship, self.pub)


class FeatureRelationshipprop(Base):
    __tablename__ = 'feature_relationshipprop'
    __table_args__ = (
        UniqueConstraint('feature_relationship_id', 'type_id', 'rank'),
    )

    feature_relationshipprop_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_relationshipprop_feature_relationshipprop_id_seq'::regclass)"))
    feature_relationship_id = Column(ForeignKey('feature_relationship.feature_relationship_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    feature_relationship = relationship('FeatureRelationship')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "FeatureRelationshipprop id={}: value:'{}' rank: '{}' \n\tFR:({})\n\ttype:({})".\
            format(self.feature_relationshipprop_id, self.value, self.rank, self.feature_relationship, self.type)


class FeatureRelationshippropPub(Base):
    __tablename__ = 'feature_relationshipprop_pub'
    __table_args__ = (
        UniqueConstraint('feature_relationshipprop_id', 'pub_id'),
    )

    feature_relationshipprop_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_relationshipprop_pub_feature_relationshipprop_pub_i_seq'::regclass)"))
    feature_relationshipprop_id = Column(ForeignKey('feature_relationshipprop.feature_relationshipprop_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    feature_relationshipprop = relationship('FeatureRelationshipprop')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "FeatureRelationshipproPub id={}:\n\tFRP:({})\n\tpub:({})".\
            format(self.feature_relationshipprop_pub_id, self.feature_relationshipprop, self.pub)


class FeatureSynonym(Base):
    __tablename__ = 'feature_synonym'
    __table_args__ = (
        UniqueConstraint('synonym_id', 'feature_id', 'pub_id'),
    )

    feature_synonym_id = Column(Integer, primary_key=True, server_default=text("nextval('feature_synonym_feature_synonym_id_seq'::regclass)"))
    synonym_id = Column(ForeignKey('synonym.synonym_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    is_current = Column(Boolean, nullable=False, server_default=text("true"))
    is_internal = Column(Boolean, nullable=False, server_default=text("false"))

    feature = relationship('Feature')
    pub = relationship('Pub')
    synonym = relationship('Synonym')

    def __str__(self):
        """Over write the default output."""
        return "FeatureSynonym id={}: is_current:'{}' is_internal:'{}'\n\tFeat:({})\n\tSyn:({})\n\tPub:({})".\
            format(self.feature_synonym_id, self.is_current, self.is_internal, self.feature, self.synonym, self.pub)


class Featureloc(Base):
    __tablename__ = 'featureloc'
    __table_args__ = (
        CheckConstraint('fmin <= fmax'),
        UniqueConstraint('feature_id', 'locgroup', 'rank'),
        Index('featureloc_idx3', 'srcfeature_id', 'fmin', 'fmax')
    )

    featureloc_id = Column(Integer, primary_key=True, server_default=text("nextval('featureloc_featureloc_id_seq'::regclass)"))
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    srcfeature_id = Column(ForeignKey('feature.feature_id', ondelete='SET NULL'), index=True)
    fmin = Column(Integer, index=True)
    is_fmin_partial = Column(Boolean, nullable=False, server_default=text("false"))
    fmax = Column(Integer, index=True)
    is_fmax_partial = Column(Boolean, nullable=False, server_default=text("false"))
    strand = Column(SmallInteger)
    phase = Column(Integer)
    residue_info = Column(Text)
    locgroup = Column(Integer, nullable=False, server_default=text("0"))
    rank = Column(Integer, nullable=False, server_default=text("0"))

    feature = relationship('Feature', primaryjoin='Featureloc.feature_id == Feature.feature_id')
    srcfeature = relationship('Feature', primaryjoin='Featureloc.srcfeature_id == Feature.feature_id')

    def __str__(self):
        """Over write the default output."""
        return "Featureloc id={}:fmin:'{}' fmax:'{}' is_fmin_partial:'{}' is_fmax_partial:'{}' strand:'{}' phase:'{}' residue_info:'{}' locgroup:'{}' rank:'{}'\n\tFeat:({})\n\tsrcfeat:({})".\
            format(self.featureloc_id, self.fmin, self.fmax, self.is_fmin_partial, self.is_fmax_partial, self.strand, self.phase, self.residue_info, self.locgroup, self.rank, self.feature, self.srcfeature)


t_featureloc_allcoords = Table(
    'featureloc_allcoords', metadata,
    Column('featureloc_id', Integer),
    Column('feature_id', Integer),
    Column('srcfeature_id', Integer),
    Column('fmin', Integer),
    Column('is_fmin_partial', Boolean),
    Column('fmax', Integer),
    Column('is_fmax_partial', Boolean),
    Column('strand', SmallInteger),
    Column('phase', Integer),
    Column('residue_info', Text),
    Column('locgroup', Integer),
    Column('rank', Integer),
    Column('gbeg', Integer),
    Column('gend', Integer),
    Column('nbeg', Integer),
    Column('nend', Integer)
)


class FeaturelocPub(Base):
    __tablename__ = 'featureloc_pub'
    __table_args__ = (
        UniqueConstraint('featureloc_id', 'pub_id'),
    )

    featureloc_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('featureloc_pub_featureloc_pub_id_seq'::regclass)"))
    featureloc_id = Column(ForeignKey('featureloc.featureloc_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    featureloc = relationship('Featureloc')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "FeaturelocPub id={}:\n\tFL:({})\n\tPub:({})".\
            format(self.featureloc_pub_id, self.featureloc, self.pub)

class Featuremap(Base):
    __tablename__ = 'featuremap'

    featuremap_id = Column(Integer, primary_key=True, server_default=text("nextval('featuremap_featuremap_id_seq'::regclass)"))
    name = Column(String(255), unique=True)
    description = Column(Text)
    unittype_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'))

    unittype = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "Featuremap id={}: name:'{}' description:'{}'\n\ttype:({})".\
            format(self.featuremap_id, self.name, self.description, self.unittype)


class FeaturemapPub(Base):
    __tablename__ = 'featuremap_pub'

    featuremap_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('featuremap_pub_featuremap_pub_id_seq'::regclass)"))
    featuremap_id = Column(ForeignKey('featuremap.featuremap_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    featuremap = relationship('Featuremap')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "FeaturemapPub id={}:\n\tFm:({})\n\tPub:({})".\
            format(self.featuremap_pub_id, self.featuremap, self.pub)


class Featurepo(Base):
    __tablename__ = 'featurepos'

    featurepos_id = Column(Integer, primary_key=True, server_default=text("nextval('featurepos_featurepos_id_seq'::regclass)"))
    featuremap_id = Column(ForeignKey('featuremap.featuremap_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True, server_default=text("nextval('featurepos_featuremap_id_seq'::regclass)"))
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    map_feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    mappos = Column(Float(53), nullable=False)

    feature = relationship('Feature', primaryjoin='Featurepo.feature_id == Feature.feature_id')
    featuremap = relationship('Featuremap')
    map_feature = relationship('Feature', primaryjoin='Featurepo.map_feature_id == Feature.feature_id')

    def __str__(self):
        """Over write the default output."""
        return "Not used in flybase"


class Featureprop(Base):
    __tablename__ = 'featureprop'
    __table_args__ = (
        UniqueConstraint('feature_id', 'type_id', 'rank'),
    )

    featureprop_id = Column(Integer, primary_key=True, server_default=text("nextval('featureprop_featureprop_id_seq'::regclass)"))
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    feature = relationship('Feature')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "Featureprop id={}: value:'{}' rank:'{}'\n\tfeat:({})\n\ttype:({})".\
            format(self.featureprop_id, self.value, self.rank, self.feature, self.type)


class FeaturepropPub(Base):
    __tablename__ = 'featureprop_pub'
    __table_args__ = (
        UniqueConstraint('featureprop_id', 'pub_id'),
    )

    featureprop_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('featureprop_pub_featureprop_pub_id_seq'::regclass)"))
    featureprop_id = Column(ForeignKey('featureprop.featureprop_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    featureprop = relationship('Featureprop')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "FeaturepropPub id={}:\n\tfeatprop:({})\n\tpub:({})".\
            format(self.featureprop_pub_id, self.featureprop, self.pub)


class Featurerange(Base):
    __tablename__ = 'featurerange'

    featurerange_id = Column(Integer, primary_key=True, server_default=text("nextval('featurerange_featurerange_id_seq'::regclass)"))
    featuremap_id = Column(ForeignKey('featuremap.featuremap_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    leftstartf_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    leftendf_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), index=True)
    rightstartf_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), index=True)
    rightendf_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    rangestr = Column(String(255))

    feature = relationship('Feature', primaryjoin='Featurerange.feature_id == Feature.feature_id')
    featuremap = relationship('Featuremap')
    leftendf = relationship('Feature', primaryjoin='Featurerange.leftendf_id == Feature.feature_id')
    leftstartf = relationship('Feature', primaryjoin='Featurerange.leftstartf_id == Feature.feature_id')
    rightendf = relationship('Feature', primaryjoin='Featurerange.rightendf_id == Feature.feature_id')
    rightstartf = relationship('Feature', primaryjoin='Featurerange.rightstartf_id == Feature.feature_id')


t_fnr_type = Table(
    'fnr_type', metadata,
    Column('feature_id', Integer),
    Column('name', String(255)),
    Column('uniquename', Text),
    Column('dbxref_id', Integer),
    Column('type', String(1024)),
    Column('residues', Text),
    Column('seqlen', Integer),
    Column('md5checksum', String(32)),
    Column('type_id', Integer),
    Column('organism_id', Integer),
    Column('timeaccessioned', DateTime),
    Column('timelastmodified', DateTime)
)


t_fp_key = Table(
    'fp_key', metadata,
    Column('featureprop_id', Integer),
    Column('feature_id', Integer),
    Column('type', String(1024)),
    Column('value', Text)
)


class Genotype(Base):
    __tablename__ = 'genotype'

    genotype_id = Column(Integer, primary_key=True, server_default=text("nextval('genotype_genotype_id_seq'::regclass)"))
    uniquename = Column(Text, nullable=False, unique=True)
    description = Column(String(255))
    name = Column(Text, index=True)

    def __str__(self):
        """Over write the default output."""
        return "Genotype id ={}: uniquename:'{}' name:'{}' description:'{}'".\
            format(self.genotype_id, self.uniquename, self.name, self.description)


t_gffatts_slim = Table(
    'gffatts_slim', metadata,
    Column('feature_id', Integer),
    Column('type', String),
    Column('attribute', Text)
)


t_gffatts_slpar = Table(
    'gffatts_slpar', metadata,
    Column('feature_id', Integer),
    Column('type', String),
    Column('attribute', Text)
)


class Grp(Base):
    __tablename__ = 'grp'
    __table_args__ = (
        UniqueConstraint('uniquename', 'type_id'),
    )

    grp_id = Column(Integer, primary_key=True, server_default=text("nextval('grp_grp_id_seq'::regclass)"))
    name = Column(String(255), index=True)
    uniquename = Column(Text, nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    is_analysis = Column(Boolean, nullable=False, server_default=text("false"))
    is_obsolete = Column(Boolean, nullable=False, server_default=text("false"))

    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "Grp id={}: uniquename:'{}' name:'{}' is_analysis:'{}' is_obsolete:'{}'\n\ttype:({})".\
            format(self.grp_id, self.uniquename, self.name, self.is_analysis, self.is_obsolete, self.type)


class GrpCvterm(Base):
    __tablename__ = 'grp_cvterm'
    __table_args__ = (
        UniqueConstraint('cvterm_id', 'grp_id', 'pub_id'),
    )

    grp_cvterm_id = Column(Integer, primary_key=True, server_default=text("nextval('grp_cvterm_grp_cvterm_id_seq'::regclass)"))
    is_not = Column(Boolean, nullable=False, server_default=text("false"))
    cvterm_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    grp_id = Column(ForeignKey('grp.grp_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    cvterm = relationship('Cvterm')
    grp = relationship('Grp')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "GrpCvterm id={}: is_not:'{}'\n\tgrp:({})\n\tcvterm:({})\n\tpub:({})".\
            format(self.grp_cvterm_id, self.is_not, self.grp, self.cvterm,self.pub)


class GrpDbxref(Base):
    __tablename__ = 'grp_dbxref'
    __table_args__ = (
        UniqueConstraint('dbxref_id', 'grp_id'),
    )

    grp_dbxref_id = Column(Integer, primary_key=True, server_default=text("nextval('grp_dbxref_grp_dbxref_id_seq'::regclass)"))
    is_current = Column(Boolean, nullable=False, server_default=text("true"))
    dbxref_id = Column(ForeignKey('dbxref.dbxref_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    grp_id = Column(ForeignKey('grp.grp_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    dbxref = relationship('Dbxref')
    grp = relationship('Grp')

    def __str__(self):
        """Over write the default output."""
        return "GrpDbxref id={}: is_current:'{}'\n\tgrp:({})\n\tdbxref:({})".\
            format(self.grp_dbxref_id, self.is_current, self.grp, self.dbxref)


class GrpPub(Base):
    __tablename__ = 'grp_pub'
    __table_args__ = (
        UniqueConstraint('pub_id', 'grp_id'),
    )

    grp_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('grp_pub_grp_pub_id_seq'::regclass)"))
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    grp_id = Column(ForeignKey('grp.grp_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    grp = relationship('Grp')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "GrpPub id={}:\n\tgrp:({})\n\tpub:({})".\
            format(self.grp_pub_id, self.grp, self.pub)


class GrpPubprop(Base):
    __tablename__ = 'grp_pubprop'
    __table_args__ = (
        UniqueConstraint('rank', 'type_id', 'grp_pub_id'),
    )

    grp_pubprop_id = Column(Integer, primary_key=True, server_default=text("nextval('grp_pubprop_grp_pubprop_id_seq'::regclass)"))
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    grp_pub_id = Column(ForeignKey('grp_pub.grp_pub_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    grp_pub = relationship('GrpPub')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "GrpPubprop id={}: value:'{}' rank:'{}'\n\tgrp_pub:({})\n\ttype:({})".\
            format(self.grp_pubprop_id, self.value, self.rank, self.grp_pub, self.type)


class GrpRelationship(Base):
    __tablename__ = 'grp_relationship'
    __table_args__ = (
        UniqueConstraint('rank', 'type_id', 'subject_id', 'object_id'),
    )

    grp_relationship_id = Column(Integer, primary_key=True, server_default=text("nextval('grp_relationship_grp_relationship_id_seq'::regclass)"))
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    subject_id = Column(ForeignKey('grp.grp_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    object_id = Column(ForeignKey('grp.grp_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    object = relationship('Grp', primaryjoin='GrpRelationship.object_id == Grp.grp_id')
    subject = relationship('Grp', primaryjoin='GrpRelationship.subject_id == Grp.grp_id')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "GrpRelationship id={}: value:'{}' rank:'{}'\n\tObj:({})\n\tSub:({})\n\ttype:({})".\
            format(self.grp_relationship_id, self.value, self.rank, self.object, self.subject, self.type)


class GrpRelationshipPub(Base):
    __tablename__ = 'grp_relationship_pub'
    __table_args__ = (
        UniqueConstraint('pub_id', 'grp_relationship_id'),
    )

    grp_relationship_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('grp_relationship_pub_grp_relationship_pub_id_seq'::regclass)"))
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    grp_relationship_id = Column(ForeignKey('grp_relationship.grp_relationship_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    grp_relationship = relationship('GrpRelationship')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "GrpRelationshipPub id={}:\n\tGR:({})\n\tPub:({})".\
            format(self.grp_relationship_pub_id, self.grp_relationship, self.pub)


class GrpRelationshipprop(Base):
    __tablename__ = 'grp_relationshipprop'
    __table_args__ = (
        UniqueConstraint('rank', 'type_id', 'grp_relationship_id'),
    )

    grp_relationshipprop_id = Column(Integer, primary_key=True, server_default=text("nextval('grp_relationshipprop_grp_relationshipprop_id_seq'::regclass)"))
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    grp_relationship_id = Column(ForeignKey('grp_relationship.grp_relationship_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    grp_relationship = relationship('GrpRelationship')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "GrpRelationshipprop id={}: value:'{}' rank:'{}' \n\tGR:({})\n\ttype:({})".\
            format(self.grp_relationshipprop_id, self.value, self.rank, self.grp_relationship, self.type)


class GrpSynonym(Base):
    __tablename__ = 'grp_synonym'
    __table_args__ = (
        UniqueConstraint('synonym_id', 'grp_id', 'pub_id'),
    )

    grp_synonym_id = Column(Integer, primary_key=True, server_default=text("nextval('grp_synonym_grp_synonym_id_seq'::regclass)"))
    synonym_id = Column(ForeignKey('synonym.synonym_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    grp_id = Column(ForeignKey('grp.grp_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    is_current = Column(Boolean, nullable=False, server_default=text("false"))
    is_internal = Column(Boolean, nullable=False, server_default=text("false"))

    grp = relationship('Grp')
    pub = relationship('Pub')
    synonym = relationship('Synonym')


class Grpmember(Base):
    __tablename__ = 'grpmember'
    __table_args__ = (
        UniqueConstraint('rank', 'type_id', 'grp_id'),
    )

    grpmember_id = Column(Integer, primary_key=True, server_default=text("nextval('grpmember_grpmember_id_seq'::regclass)"))
    rank = Column(Integer, nullable=False, server_default=text("0"))
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    grp_id = Column(ForeignKey('grp.grp_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    grp = relationship('Grp')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "Grpmember id={}: rank:'{}'\n\tgrp:({})\n\ttype:({})".\
            format(self.grpmember_id, self.rank, self.grp, self.type)


class GrpmemberCvterm(Base):
    __tablename__ = 'grpmember_cvterm'
    __table_args__ = (
        UniqueConstraint('cvterm_id', 'grpmember_id', 'pub_id'),
    )

    grpmember_cvterm_id = Column(Integer, primary_key=True, server_default=text("nextval('grpmember_cvterm_grpmember_cvterm_id_seq'::regclass)"))
    is_not = Column(Boolean, nullable=False, server_default=text("false"))
    cvterm_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    grpmember_id = Column(ForeignKey('grpmember.grpmember_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    cvterm = relationship('Cvterm')
    grpmember = relationship('Grpmember')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "GrpmemberCvterm id={}: is_not:'{}'\n\tGrpmem:({})\n\ttype:({})\n\tpub:({})".\
            format(self.grpmember_cvterm_id, self.is_not, self.grpmember, self.cvterm, self.pub)


class GrpmemberPub(Base):
    __tablename__ = 'grpmember_pub'
    __table_args__ = (
        UniqueConstraint('pub_id', 'grpmember_id'),
    )

    grpmember_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('grpmember_pub_grpmember_pub_id_seq'::regclass)"))
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    grpmember_id = Column(ForeignKey('grpmember.grpmember_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    grpmember = relationship('Grpmember')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "GrpmemberPub id={}:\n\tGrpmem:({})\n\tGrpMemPub:({})\n\tPub:({})".\
            format(self.grpmember_pub_id, self.grpmember, self.pub)


class Grpmemberprop(Base):
    __tablename__ = 'grpmemberprop'
    __table_args__ = (
        UniqueConstraint('rank', 'type_id', 'grpmember_id'),
    )

    grpmemberprop_id = Column(Integer, primary_key=True, server_default=text("nextval('grpmemberprop_grpmemberprop_id_seq'::regclass)"))
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    grpmember_id = Column(ForeignKey('grpmember.grpmember_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    grpmember = relationship('Grpmember')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "Grpmemberprop id={}: vlaue:'{}' rank:'{}' GrpMem:({})\n\ttype:({})".\
            format(self.grpmemberprop_id. self.value, self.rank, self.grpmember, self.type)


class GrpmemberpropPub(Base):
    __tablename__ = 'grpmemberprop_pub'
    __table_args__ = (
        UniqueConstraint('pub_id', 'grpmemberprop_id'),
    )

    grpmemberprop_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('grpmemberprop_pub_grpmemberprop_pub_id_seq'::regclass)"))
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    grpmemberprop_id = Column(ForeignKey('grpmemberprop.grpmemberprop_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    grpmemberprop = relationship('Grpmemberprop')
    pub = relationship('Pub')


class Grpprop(Base):
    __tablename__ = 'grpprop'
    __table_args__ = (
        UniqueConstraint('rank', 'type_id', 'grp_id'),
    )

    grpprop_id = Column(Integer, primary_key=True, server_default=text("nextval('grpprop_grpprop_id_seq'::regclass)"))
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    grp_id = Column(ForeignKey('grp.grp_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    grp = relationship('Grp')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "Grpprop id={}: value:'{}' rank:'{}'\n\tGrp:({})\n\ttype:({})".\
            format(self.grpprop_id, self.value, self.rank, self.grp, self.type)


class GrppropPub(Base):
    __tablename__ = 'grpprop_pub'
    __table_args__ = (
        UniqueConstraint('pub_id', 'grpprop_id'),
    )

    grpprop_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('grpprop_pub_grpprop_pub_id_seq'::regclass)"))
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    grpprop_id = Column(ForeignKey('grpprop.grpprop_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    grpprop = relationship('Grpprop')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "GrppropPub id={}:\n\tgrpprop:({})\n\tPub:({})".\
            format(self.grpprop_pub_id, self.grpprop, self.pub)


class Humanhealth(Base):
    __tablename__ = 'humanhealth'
    __table_args__ = (
        UniqueConstraint('organism_id', 'uniquename'),
    )

    humanhealth_id = Column(Integer, primary_key=True, server_default=text("nextval('humanhealth_humanhealth_id_seq'::regclass)"))
    name = Column(String(255), index=True)
    uniquename = Column(Text, nullable=False, index=True)
    organism_id = Column(ForeignKey('organism.organism_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    dbxref_id = Column(ForeignKey('dbxref.dbxref_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'))
    is_obsolete = Column(Boolean, nullable=False, server_default=text("false"))

    dbxref = relationship('Dbxref')
    organism = relationship('Organism')

    def __str__(self):
        """Over write the default output."""
        return "Humanhealth id={}: uniquename:'{}' name:'{}' is_obsolete:'{}'\n\rorg:({})\n\tdbxref:({})".\
            format(self.humanhealth_id, self.uniquename, self.name, self.is_obsolete, self.organism, self.dbxref)

class HumanhealthCvterm(Base):
    __tablename__ = 'humanhealth_cvterm'
    __table_args__ = (
        UniqueConstraint('humanhealth_id', 'cvterm_id', 'pub_id'),
    )

    humanhealth_cvterm_id = Column(Integer, primary_key=True, server_default=text("nextval('humanhealth_cvterm_humanhealth_cvterm_id_seq'::regclass)"))
    humanhealth_id = Column(ForeignKey('humanhealth.humanhealth_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    cvterm_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    cvterm = relationship('Cvterm')
    humanhealth = relationship('Humanhealth')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "HumanhealthCvterm id={}:\n\tHH:({})\n\tcvterm:({})\n\tPub:({})".\
            format(self.humanhealth_cvterm_id, self.humanhealth, self.cvterm, self.pub)


class HumanhealthCvtermprop(Base):
    __tablename__ = 'humanhealth_cvtermprop'
    __table_args__ = (
        UniqueConstraint('humanhealth_cvterm_id', 'type_id', 'rank'),
    )

    humanhealth_cvtermprop_id = Column(Integer, primary_key=True, server_default=text("nextval('humanhealth_cvtermprop_humanhealth_cvtermprop_id_seq'::regclass)"))
    humanhealth_cvterm_id = Column(ForeignKey('humanhealth_cvterm.humanhealth_cvterm_id', ondelete='CASCADE'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    humanhealth_cvterm = relationship('HumanhealthCvterm')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "HumanhealthCvtermprop id={}: value:'{}' rank:'{}'\n\tHHcvterm:({})\n\ttype:({})".\
            format(self.humanhealth_cvtermprop_id, self.value, self.rank, self.humanhealth_cvterm, self.type)


class HumanhealthDbxref(Base):
    __tablename__ = 'humanhealth_dbxref'
    __table_args__ = (
        UniqueConstraint('humanhealth_id', 'dbxref_id'),
    )

    humanhealth_dbxref_id = Column(Integer, primary_key=True, server_default=text("nextval('humanhealth_dbxref_humanhealth_dbxref_id_seq'::regclass)"))
    humanhealth_id = Column(ForeignKey('humanhealth.humanhealth_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    dbxref_id = Column(ForeignKey('dbxref.dbxref_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    is_current = Column(Boolean, nullable=False, server_default=text("true"))

    dbxref = relationship('Dbxref')
    humanhealth = relationship('Humanhealth')

    def __str__(self):
        """Over write the default output."""
        return "HumanhealthDbxref id={}: is_current:'{}'\n\thh:({})\n\tdbxref:({})".\
            format(self.humanhealth_dbxref_id, self.is_current, self.humanhealth, self.dbxref)


class HumanhealthDbxrefprop(Base):
    __tablename__ = 'humanhealth_dbxrefprop'
    __table_args__ = (
        UniqueConstraint('humanhealth_dbxref_id', 'type_id', 'rank'),
    )

    humanhealth_dbxrefprop_id = Column(Integer, primary_key=True, server_default=text("nextval('humanhealth_dbxrefprop_humanhealth_dbxrefprop_id_seq'::regclass)"))
    humanhealth_dbxref_id = Column(ForeignKey('humanhealth_dbxref.humanhealth_dbxref_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    humanhealth_dbxref = relationship('HumanhealthDbxref')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "HumanhealthDbxrefprop id={}: value:'{}' rank:'{}'\n\tHHDnxref:({})\n\ttype:({})".\
            format(self.humanhealth_dbxrefprop_id, self.value, self.rank, self.humanhealth_dbxref, self.type)


class HumanhealthDbxrefpropPub(Base):
    __tablename__ = 'humanhealth_dbxrefprop_pub'
    __table_args__ = (
        UniqueConstraint('humanhealth_dbxrefprop_id', 'pub_id'),
    )

    humanhealth_dbxrefprop_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('humanhealth_dbxrefprop_pub_humanhealth_dbxrefprop_pub_id_seq'::regclass)"))
    humanhealth_dbxrefprop_id = Column(ForeignKey('humanhealth_dbxrefprop.humanhealth_dbxrefprop_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    humanhealth_dbxrefprop = relationship('HumanhealthDbxrefprop')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "HumanhealthDbxrefpropPub id={}:\n\tHHDp:({})\n\tPub:({})".\
            format(self.humanhealth_dbxrefprop_pub_id, self.humanhealth_dbxrefprop, self.pub)


class HumanhealthFeature(Base):
    __tablename__ = 'humanhealth_feature'
    __table_args__ = (
        UniqueConstraint('humanhealth_id', 'feature_id', 'pub_id'),
    )

    humanhealth_feature_id = Column(Integer, primary_key=True, server_default=text("nextval('humanhealth_feature_humanhealth_feature_id_seq'::regclass)"))
    humanhealth_id = Column(ForeignKey('humanhealth.humanhealth_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    feature = relationship('Feature')
    humanhealth = relationship('Humanhealth')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "HumanhealthFeature id={}:\n\tHH:({})\n\tFeat:({})\n\tpub:({})".\
            format(self.humanhealth_feature_id, self.humanhealth, self.feature, self.pub)


class HumanhealthFeatureprop(Base):
    __tablename__ = 'humanhealth_featureprop'
    __table_args__ = (
        UniqueConstraint('humanhealth_feature_id', 'type_id', 'rank'),
    )

    humanhealth_featureprop_id = Column(Integer, primary_key=True, server_default=text("nextval('humanhealth_featureprop_humanhealth_featureprop_id_seq'::regclass)"))
    humanhealth_feature_id = Column(ForeignKey('humanhealth_feature.humanhealth_feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    humanhealth_feature = relationship('HumanhealthFeature')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "HumanhealthFeatureprop id={}: value:'{} rank:'{}'\n\tHHF:({})\n\ttype:({})".\
            format(self.humanhealth_featureprop_id, self.value, self.rank, self.humanhealth_feature, self.type)


class HumanhealthPhenotype(Base):
    __tablename__ = 'humanhealth_phenotype'
    __table_args__ = (
        UniqueConstraint('humanhealth_id', 'phenotype_id', 'pub_id'),
    )

    humanhealth_phenotype_id = Column(Integer, primary_key=True, server_default=text("nextval('humanhealth_phenotype_humanhealth_phenotype_id_seq'::regclass)"))
    humanhealth_id = Column(ForeignKey('humanhealth.humanhealth_id', ondelete='CASCADE'), nullable=False, index=True)
    phenotype_id = Column(ForeignKey('phenotype.phenotype_id', ondelete='CASCADE'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    humanhealth = relationship('Humanhealth')
    phenotype = relationship('Phenotype')
    pub = relationship('Pub')


class HumanhealthPhenotypeprop(Base):
    __tablename__ = 'humanhealth_phenotypeprop'
    __table_args__ = (
        UniqueConstraint('humanhealth_phenotype_id', 'type_id', 'rank'),
    )

    humanhealth_phenotypeprop_id = Column(Integer, primary_key=True, server_default=text("nextval('humanhealth_phenotypeprop_humanhealth_phenotypeprop_id_seq'::regclass)"))
    humanhealth_phenotype_id = Column(ForeignKey('humanhealth_phenotype.humanhealth_phenotype_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    humanhealth_phenotype = relationship('HumanhealthPhenotype')
    type = relationship('Cvterm')


class HumanhealthPub(Base):
    __tablename__ = 'humanhealth_pub'
    __table_args__ = (
        UniqueConstraint('humanhealth_id', 'pub_id'),
    )

    humanhealth_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('humanhealth_pub_humanhealth_pub_id_seq'::regclass)"))
    humanhealth_id = Column(ForeignKey('humanhealth.humanhealth_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    humanhealth = relationship('Humanhealth')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "HumanhealthPub id={}:\n\tHH:({})\n\tPub:({})".\
            format(self.humanhealth_pub_id, self.humanhealth, self.pub)


class HumanhealthPubprop(Base):
    __tablename__ = 'humanhealth_pubprop'
    __table_args__ = (
        UniqueConstraint('rank', 'type_id', 'humanhealth_pub_id'),
    )

    humanhealth_pubprop_id = Column(Integer, primary_key=True, server_default=text("nextval('humanhealth_pubprop_humanhealth_pubprop_id_seq'::regclass)"))
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    humanhealth_pub_id = Column(ForeignKey('humanhealth_pub.humanhealth_pub_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    humanhealth_pub = relationship('HumanhealthPub')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "HumanhealthPubprop id={}: value:'{}' rank:'{}'\n\tHHpub:({})\n\ttype:({})".\
            format(self.humanhealth_pubprop_id, self.value, self.rank, self.humanhealth_pub, self.type)


class HumanhealthRelationship(Base):
    __tablename__ = 'humanhealth_relationship'
    __table_args__ = (
        UniqueConstraint('subject_id', 'object_id', 'type_id', 'rank'),
    )

    humanhealth_relationship_id = Column(Integer, primary_key=True, server_default=text("nextval('humanhealth_relationship_humanhealth_relationship_id_seq'::regclass)"))
    subject_id = Column(ForeignKey('humanhealth.humanhealth_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    object_id = Column(ForeignKey('humanhealth.humanhealth_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    object = relationship('Humanhealth', primaryjoin='HumanhealthRelationship.object_id == Humanhealth.humanhealth_id')
    subject = relationship('Humanhealth', primaryjoin='HumanhealthRelationship.subject_id == Humanhealth.humanhealth_id')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "HumanhealthRelationship id={}: value:'{}' rank:'{}'\n\tObj:({})\n\tSub:({})\n\ttype:({})".\
            format(self.humanhealth_relationship_id, self.value, self.rank, self.object, self.subject, self.type)


class HumanhealthRelationshipPub(Base):
    __tablename__ = 'humanhealth_relationship_pub'
    __table_args__ = (
        UniqueConstraint('humanhealth_relationship_id', 'pub_id'),
    )

    humanhealth_relationship_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('humanhealth_relationship_pub_humanhealth_relationship_pub_i_seq'::regclass)"))
    humanhealth_relationship_id = Column(ForeignKey('humanhealth_relationship.humanhealth_relationship_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    humanhealth_relationship = relationship('HumanhealthRelationship')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "HumanhealthRelationshipPub id={}:\n\tHHR:({})\n\tPun:({})".\
            format(self.humanhealth_relationship_pub_id, self.humanhealth_relationship, self.pub)


class HumanhealthSynonym(Base):
    __tablename__ = 'humanhealth_synonym'
    __table_args__ = (
        UniqueConstraint('synonym_id', 'humanhealth_id', 'pub_id'),
    )

    humanhealth_synonym_id = Column(Integer, primary_key=True, server_default=text("nextval('humanhealth_synonym_humanhealth_synonym_id_seq'::regclass)"))
    humanhealth_id = Column(ForeignKey('humanhealth.humanhealth_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    synonym_id = Column(ForeignKey('synonym.synonym_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    is_current = Column(Boolean, nullable=False, server_default=text("false"))
    is_internal = Column(Boolean, nullable=False, server_default=text("false"))

    humanhealth = relationship('Humanhealth')
    pub = relationship('Pub')
    synonym = relationship('Synonym')

    def __str__(self):
        """Over write the default output."""
        return "HumanhealthSynonym id={}: is_current:'{}' is_internal:'{}'\n\tHH:({})\n\tSyn:({})\n\tPub:({})".\
            format(self.humanhealth_synonym_id, self.is_current, self.is_internal, self.humanhealth, self.synonym, self.pub)


class Humanhealthprop(Base):
    __tablename__ = 'humanhealthprop'
    __table_args__ = (
        UniqueConstraint('humanhealth_id', 'type_id', 'rank'),
    )

    humanhealthprop_id = Column(Integer, primary_key=True, server_default=text("nextval('humanhealthprop_humanhealthprop_id_seq'::regclass)"))
    humanhealth_id = Column(ForeignKey('humanhealth.humanhealth_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    humanhealth = relationship('Humanhealth')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "Humanhealthprop id={}: value:'{}' rank:'{}'\n\tHH:({})\n\ttype:({})".\
            format(self.humanhealthprop_id, self.value, self.rank, self.humanhealth, self.type)

class HumanhealthpropPub(Base):
    __tablename__ = 'humanhealthprop_pub'
    __table_args__ = (
        UniqueConstraint('humanhealthprop_id', 'pub_id'),
    )

    humanhealthprop_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('humanhealthprop_pub_humanhealthprop_pub_id_seq'::regclass)"))
    humanhealthprop_id = Column(ForeignKey('humanhealthprop.humanhealthprop_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    humanhealthprop = relationship('Humanhealthprop')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "HumanhealthpropPub id={}:\n\tHHprop:({}) Pub:({})".\
            format(self.humanhealthprop_pub_id, self.humanhealthprop, self.pub)


class Interaction(Base):
    __tablename__ = 'interaction'
    __table_args__ = (
        UniqueConstraint('uniquename', 'type_id'),
    )

    interaction_id = Column(Integer, primary_key=True, server_default=text("nextval('interaction_interaction_id_seq'::regclass)"))
    uniquename = Column(Text, nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    description = Column(Text)
    is_obsolete = Column(Boolean, nullable=False, server_default=text("false"))

    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "Interaction id={}: uniquename:'{}' is_obsolte:'{}', description:'{}'\n\ttype:({})".\
            format(self.interaction_id, self.uniquename, self.is_obsolete, self.description, self.type)


class InteractionCellLine(Base):
    __tablename__ = 'interaction_cell_line'
    __table_args__ = (
        UniqueConstraint('cell_line_id', 'interaction_id', 'pub_id'),
    )

    interaction_cell_line_id = Column(Integer, primary_key=True, server_default=text("nextval('interaction_cell_line_interaction_cell_line_id_seq'::regclass)"))
    cell_line_id = Column(ForeignKey('cell_line.cell_line_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    interaction_id = Column(ForeignKey('interaction.interaction_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    cell_line = relationship('CellLine')
    interaction = relationship('Interaction')
    pub = relationship('Pub')

    def __str__(self):
        """Over write the default output."""
        return "InteractionCellLine id={}:\n\tInteraction:({})\n\tCell line:({})\n\tPub:({})".\
            format(self.interaction_cell_line_id, self.interaction, cell_line, self.pub)


class InteractionCvterm(Base):
    __tablename__ = 'interaction_cvterm'
    __table_args__ = (
        UniqueConstraint('interaction_id', 'cvterm_id'),
    )

    interaction_cvterm_id = Column(Integer, primary_key=True, server_default=text("nextval('interaction_cvterm_interaction_cvterm_id_seq'::regclass)"))
    interaction_id = Column(ForeignKey('interaction.interaction_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    cvterm_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    cvterm = relationship('Cvterm')
    interaction = relationship('Interaction')


class InteractionCvtermprop(Base):
    __tablename__ = 'interaction_cvtermprop'
    __table_args__ = (
        UniqueConstraint('interaction_cvterm_id', 'type_id', 'rank'),
    )

    interaction_cvtermprop_id = Column(Integer, primary_key=True, server_default=text("nextval('interaction_cvtermprop_interaction_cvtermprop_id_seq'::regclass)"))
    interaction_cvterm_id = Column(ForeignKey('interaction_cvterm.interaction_cvterm_id', ondelete='CASCADE'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    interaction_cvterm = relationship('InteractionCvterm')
    type = relationship('Cvterm')


class InteractionExpression(Base):
    __tablename__ = 'interaction_expression'
    __table_args__ = (
        UniqueConstraint('expression_id', 'interaction_id', 'pub_id'),
    )

    interaction_expression_id = Column(Integer, primary_key=True, server_default=text("nextval('interaction_expression_interaction_expression_id_seq'::regclass)"))
    expression_id = Column(ForeignKey('expression.expression_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    interaction_id = Column(ForeignKey('interaction.interaction_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    expression = relationship('Expression')
    interaction = relationship('Interaction')
    pub = relationship('Pub')


class InteractionExpressionprop(Base):
    __tablename__ = 'interaction_expressionprop'
    __table_args__ = (
        UniqueConstraint('interaction_expression_id', 'type_id', 'rank'),
    )

    interaction_expressionprop_id = Column(Integer, primary_key=True, server_default=text("nextval('interaction_expressionprop_interaction_expressionprop_id_seq'::regclass)"))
    interaction_expression_id = Column(ForeignKey('interaction_expression.interaction_expression_id', ondelete='CASCADE'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    interaction_expression = relationship('InteractionExpression')
    type = relationship('Cvterm')


class InteractionGroup(Base):
    __tablename__ = 'interaction_group'

    interaction_group_id = Column(Integer, primary_key=True, server_default=text("nextval('interaction_group_interaction_group_id_seq'::regclass)"))
    uniquename = Column(Text, nullable=False, unique=True)
    is_obsolete = Column(Boolean, nullable=False, server_default=text("false"))
    description = Column(Text)


class InteractionGroupFeatureInteraction(Base):
    __tablename__ = 'interaction_group_feature_interaction'
    __table_args__ = (
        UniqueConstraint('interaction_group_id', 'feature_interaction_id', 'rank'),
    )

    interaction_group_feature_interaction_id = Column(Integer, primary_key=True, server_default=text("nextval('interaction_group_feature_int_interaction_group_feature_int_seq'::regclass)"))
    interaction_group_id = Column(ForeignKey('interaction_group.interaction_group_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    feature_interaction_id = Column(ForeignKey('feature_interaction.feature_interaction_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    rank = Column(Integer, nullable=False, server_default=text("0"))
    ftype = Column(String(255))

    feature_interaction = relationship('FeatureInteraction')
    interaction_group = relationship('InteractionGroup')


class InteractionPub(Base):
    __tablename__ = 'interaction_pub'
    __table_args__ = (
        UniqueConstraint('interaction_id', 'pub_id'),
    )

    interaction_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('interaction_pub_interaction_pub_id_seq'::regclass)"))
    interaction_id = Column(ForeignKey('interaction.interaction_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    interaction = relationship('Interaction')
    pub = relationship('Pub')


class Interactionprop(Base):
    __tablename__ = 'interactionprop'
    __table_args__ = (
        UniqueConstraint('interaction_id', 'type_id', 'rank'),
    )

    interactionprop_id = Column(Integer, primary_key=True, server_default=text("nextval('interactionprop_interactionprop_id_seq'::regclass)"))
    interaction_id = Column(ForeignKey('interaction.interaction_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    interaction = relationship('Interaction')
    type = relationship('Cvterm')


class InteractionpropPub(Base):
    __tablename__ = 'interactionprop_pub'
    __table_args__ = (
        UniqueConstraint('interactionprop_id', 'pub_id'),
    )

    interactionprop_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('interactionprop_pub_interactionprop_pub_id_seq'::regclass)"))
    interactionprop_id = Column(ForeignKey('interactionprop.interactionprop_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    interactionprop = relationship('Interactionprop')
    pub = relationship('Pub')


class Library(Base):
    __tablename__ = 'library'
    __table_args__ = (
        UniqueConstraint('organism_id', 'uniquename', 'type_id'),
    )

    library_id = Column(Integer, primary_key=True, server_default=text("nextval('library_library_id_seq'::regclass)"))
    organism_id = Column(ForeignKey('organism.organism_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    name = Column(String(255), index=True)
    uniquename = Column(Text, nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    is_obsolete = Column(Boolean, nullable=False, server_default=text("false"))
    timeaccessioned = Column(DateTime, nullable=False, server_default=text("now()"))
    timelastmodified = Column(DateTime, nullable=False, server_default=text("now()"))

    organism = relationship('Organism')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "Library id={}: uniquename:{} name:{} obsolete:{}\n\torg:({})\n\ttype:({})".\
            format(self.library_id, self.uniquename, self.name, self.is_obsolete, self.organism, self.type)


class LibraryCvterm(Base):
    __tablename__ = 'library_cvterm'
    __table_args__ = (
        UniqueConstraint('library_id', 'cvterm_id', 'pub_id'),
    )

    library_cvterm_id = Column(Integer, primary_key=True, server_default=text("nextval('library_cvterm_library_cvterm_id_seq'::regclass)"))
    library_id = Column(ForeignKey('library.library_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    cvterm_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    cvterm = relationship('Cvterm')
    library = relationship('Library')
    pub = relationship('Pub')


class LibraryCvtermprop(Base):
    __tablename__ = 'library_cvtermprop'
    __table_args__ = (
        UniqueConstraint('library_cvterm_id', 'type_id', 'rank'),
    )

    library_cvtermprop_id = Column(Integer, primary_key=True, server_default=text("nextval('library_cvtermprop_library_cvtermprop_id_seq'::regclass)"))
    library_cvterm_id = Column(ForeignKey('library_cvterm.library_cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    library_cvterm = relationship('LibraryCvterm')
    type = relationship('Cvterm')


class LibraryDbxref(Base):
    __tablename__ = 'library_dbxref'
    __table_args__ = (
        UniqueConstraint('library_id', 'dbxref_id'),
    )

    library_dbxref_id = Column(Integer, primary_key=True, server_default=text("nextval('library_dbxref_library_dbxref_id_seq'::regclass)"))
    library_id = Column(ForeignKey('library.library_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    dbxref_id = Column(ForeignKey('dbxref.dbxref_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    is_current = Column(Boolean, nullable=False, server_default=text("true"))

    dbxref = relationship('Dbxref')
    library = relationship('Library')


class LibraryDbxrefprop(Base):
    __tablename__ = 'library_dbxrefprop'
    __table_args__ = (
        UniqueConstraint('library_dbxref_id', 'type_id', 'rank'),
    )

    library_dbxrefprop_id = Column(Integer, primary_key=True, server_default=text("nextval('library_dbxrefprop_library_dbxrefprop_id_seq'::regclass)"))
    library_dbxref_id = Column(ForeignKey('library_dbxref.library_dbxref_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    library_dbxref = relationship('LibraryDbxref')
    type = relationship('Cvterm')


class LibraryExpression(Base):
    __tablename__ = 'library_expression'
    __table_args__ = (
        UniqueConstraint('expression_id', 'library_id', 'pub_id'),
    )

    library_expression_id = Column(Integer, primary_key=True, server_default=text("nextval('library_expression_library_expression_id_seq'::regclass)"))
    expression_id = Column(ForeignKey('expression.expression_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    library_id = Column(ForeignKey('library.library_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    expression = relationship('Expression')
    library = relationship('Library')
    pub = relationship('Pub')


class LibraryExpressionprop(Base):
    __tablename__ = 'library_expressionprop'
    __table_args__ = (
        UniqueConstraint('library_expression_id', 'type_id', 'rank'),
    )

    library_expressionprop_id = Column(Integer, primary_key=True, server_default=text("nextval('library_expressionprop_library_expressionprop_id_seq'::regclass)"))
    library_expression_id = Column(ForeignKey('library_expression.library_expression_id', ondelete='CASCADE'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    library_expression = relationship('LibraryExpression')
    type = relationship('Cvterm')


class LibraryFeature(Base):
    __tablename__ = 'library_feature'
    __table_args__ = (
        UniqueConstraint('library_id', 'feature_id'),
    )

    library_feature_id = Column(Integer, primary_key=True, server_default=text("nextval('library_feature_library_feature_id_seq'::regclass)"))
    library_id = Column(ForeignKey('library.library_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    feature = relationship('Feature')
    library = relationship('Library')

    def __str__(self):
        """Over write the default output."""
        return "LibraryFeature id={}:\n\tLibrary:({})\n\tFeature:({})".\
            format(self.library_feature_id, self.library, self.feature)

class LibraryFeatureprop(Base):
    __tablename__ = 'library_featureprop'
    __table_args__ = (
        UniqueConstraint('library_feature_id', 'type_id', 'rank'),
    )

    library_featureprop_id = Column(Integer, primary_key=True, server_default=text("nextval('library_featureprop_library_featureprop_id_seq'::regclass)"))
    library_feature_id = Column(ForeignKey('library_feature.library_feature_id', ondelete='CASCADE'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    library_feature = relationship('LibraryFeature')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "LibraryFeatureprop id={}: value={} rank={}\n\ttype=({})\n\tLibraryFeature:({})".\
            format(self.library_featureprop_id, self.value, self.rank, self.type, self.library_feature)

class LibraryGrpmember(Base):
    __tablename__ = 'library_grpmember'
    __table_args__ = (
        UniqueConstraint('grpmember_id', 'library_id'),
    )

    library_grpmember_id = Column(Integer, primary_key=True, server_default=text("nextval('library_grpmember_library_grpmember_id_seq'::regclass)"))
    grpmember_id = Column(ForeignKey('grpmember.grpmember_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    library_id = Column(ForeignKey('library.library_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    grpmember = relationship('Grpmember')
    library = relationship('Library')


class LibraryHumanhealth(Base):
    __tablename__ = 'library_humanhealth'
    __table_args__ = (
        UniqueConstraint('humanhealth_id', 'library_id', 'pub_id'),
    )

    library_humanhealth_id = Column(Integer, primary_key=True, server_default=text("nextval('library_humanhealth_library_humanhealth_id_seq'::regclass)"))
    humanhealth_id = Column(ForeignKey('humanhealth.humanhealth_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    library_id = Column(ForeignKey('library.library_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    humanhealth = relationship('Humanhealth')
    library = relationship('Library')
    pub = relationship('Pub')


class LibraryHumanhealthprop(Base):
    __tablename__ = 'library_humanhealthprop'
    __table_args__ = (
        UniqueConstraint('library_humanhealth_id', 'type_id', 'rank'),
    )

    library_humanhealthprop_id = Column(Integer, primary_key=True, server_default=text("nextval('library_humanhealthprop_library_humanhealthprop_id_seq'::regclass)"))
    library_humanhealth_id = Column(ForeignKey('library_humanhealth.library_humanhealth_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    library_humanhealth = relationship('LibraryHumanhealth')
    type = relationship('Cvterm')


class LibraryInteraction(Base):
    __tablename__ = 'library_interaction'
    __table_args__ = (
        UniqueConstraint('interaction_id', 'library_id', 'pub_id'),
    )

    library_interaction_id = Column(Integer, primary_key=True, server_default=text("nextval('library_interaction_library_interaction_id_seq'::regclass)"))
    interaction_id = Column(ForeignKey('interaction.interaction_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    library_id = Column(ForeignKey('library.library_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    interaction = relationship('Interaction')
    library = relationship('Library')
    pub = relationship('Pub')


class LibraryPub(Base):
    __tablename__ = 'library_pub'
    __table_args__ = (
        UniqueConstraint('library_id', 'pub_id'),
    )

    library_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('library_pub_library_pub_id_seq'::regclass)"))
    library_id = Column(ForeignKey('library.library_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    library = relationship('Library')
    pub = relationship('Pub')


class LibraryRelationship(Base):
    __tablename__ = 'library_relationship'
    __table_args__ = (
        UniqueConstraint('subject_id', 'object_id', 'type_id'),
    )

    library_relationship_id = Column(Integer, primary_key=True, server_default=text("nextval('library_relationship_library_relationship_id_seq'::regclass)"))
    subject_id = Column(ForeignKey('library.library_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    object_id = Column(ForeignKey('library.library_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    object = relationship('Library', primaryjoin='LibraryRelationship.object_id == Library.library_id')
    subject = relationship('Library', primaryjoin='LibraryRelationship.subject_id == Library.library_id')
    type = relationship('Cvterm')


class LibraryRelationshipPub(Base):
    __tablename__ = 'library_relationship_pub'
    __table_args__ = (
        UniqueConstraint('library_relationship_id', 'pub_id'),
    )

    library_relationship_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('library_relationship_pub_library_relationship_pub_id_seq'::regclass)"))
    library_relationship_id = Column(ForeignKey('library_relationship.library_relationship_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    library_relationship = relationship('LibraryRelationship')
    pub = relationship('Pub')


class LibraryStrain(Base):
    __tablename__ = 'library_strain'
    __table_args__ = (
        UniqueConstraint('strain_id', 'library_id', 'pub_id'),
    )

    library_strain_id = Column(Integer, primary_key=True, server_default=text("nextval('library_strain_library_strain_id_seq'::regclass)"))
    strain_id = Column(ForeignKey('strain.strain_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    library_id = Column(ForeignKey('library.library_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    library = relationship('Library')
    pub = relationship('Pub')
    strain = relationship('Strain')


class LibraryStrainprop(Base):
    __tablename__ = 'library_strainprop'
    __table_args__ = (
        UniqueConstraint('library_strain_id', 'type_id', 'rank'),
    )

    library_strainprop_id = Column(Integer, primary_key=True, server_default=text("nextval('library_strainprop_library_strainprop_id_seq'::regclass)"))
    library_strain_id = Column(ForeignKey('library_strain.library_strain_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    library_strain = relationship('LibraryStrain')
    type = relationship('Cvterm')


class LibrarySynonym(Base):
    __tablename__ = 'library_synonym'
    __table_args__ = (
        UniqueConstraint('synonym_id', 'library_id', 'pub_id'),
    )

    library_synonym_id = Column(Integer, primary_key=True, server_default=text("nextval('library_synonym_library_synonym_id_seq'::regclass)"))
    synonym_id = Column(ForeignKey('synonym.synonym_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    library_id = Column(ForeignKey('library.library_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    is_current = Column(Boolean, nullable=False, server_default=text("true"))
    is_internal = Column(Boolean, nullable=False, server_default=text("false"))

    library = relationship('Library')
    pub = relationship('Pub')
    synonym = relationship('Synonym')


class Libraryprop(Base):
    __tablename__ = 'libraryprop'
    __table_args__ = (
        UniqueConstraint('library_id', 'type_id', 'rank'),
    )

    libraryprop_id = Column(Integer, primary_key=True, server_default=text("nextval('libraryprop_libraryprop_id_seq'::regclass)"))
    library_id = Column(ForeignKey('library.library_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    library = relationship('Library')
    type = relationship('Cvterm')


class LibrarypropPub(Base):
    __tablename__ = 'libraryprop_pub'
    __table_args__ = (
        UniqueConstraint('libraryprop_id', 'pub_id'),
    )

    libraryprop_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('libraryprop_pub_libraryprop_pub_id_seq'::regclass)"))
    libraryprop_id = Column(ForeignKey('libraryprop.libraryprop_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    libraryprop = relationship('Libraryprop')
    pub = relationship('Pub')


class Lock(Base):
    __tablename__ = 'lock'
    __table_args__ = (
        UniqueConstraint('lockname', 'lockrank', 'locktype'),
    )

    lock_id = Column(Integer, primary_key=True, server_default=text("nextval('lock_lock_id_seq'::regclass)"))
    username = Column(String(20), nullable=False, server_default=text("'administrator'::character varying"))
    locktype = Column(String(20), nullable=False, server_default=text("'write'::character varying"))
    lockname = Column(String(100), nullable=False)
    lockrank = Column(Integer, nullable=False, server_default=text("0"))
    lockstatus = Column(Boolean, nullable=False, server_default=text("false"))
    timeaccessioend = Column(DateTime, nullable=False, server_default=text("now()"))
    timelastmodified = Column(DateTime, nullable=False, server_default=text("now()"))
    chadoxmlfile = Column(String(100))
    comment = Column(String(100))
    task = Column(String(50), nullable=False, server_default=text("'modify gene model'::character varying"))


class Organism(Base):
    __tablename__ = 'organism'
    __table_args__ = (
        UniqueConstraint('genus', 'species'),
    )

    organism_id = Column(Integer, primary_key=True, server_default=text("nextval('organism_organism_id_seq'::regclass)"))
    abbreviation = Column(String(255))
    genus = Column(String(255), nullable=False)
    species = Column(String(255), nullable=False)
    common_name = Column(String(255))
    comment = Column(Text)

    def __str__(self):
        """Over write the default output."""
        return "Organism id={}: abbr:'{}' genus:'{}' species:'{}'".\
            format(self.organism_id, self.abbreviation, self.genus, self.species)


class OrganismCvterm(Base):
    __tablename__ = 'organism_cvterm'
    __table_args__ = (
        UniqueConstraint('organism_id', 'cvterm_id', 'pub_id', 'rank'),
    )

    organism_cvterm_id = Column(Integer, primary_key=True, server_default=text("nextval('organism_cvterm_organism_cvterm_id_seq'::regclass)"))
    organism_id = Column(ForeignKey('organism.organism_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    cvterm_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    rank = Column(Integer, nullable=False, server_default=text("0"))
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    cvterm = relationship('Cvterm')
    organism = relationship('Organism')
    pub = relationship('Pub')


class OrganismCvtermprop(Base):
    __tablename__ = 'organism_cvtermprop'
    __table_args__ = (
        UniqueConstraint('organism_cvterm_id', 'type_id', 'rank'),
    )

    organism_cvtermprop_id = Column(Integer, primary_key=True, server_default=text("nextval('organism_cvtermprop_organism_cvtermprop_id_seq'::regclass)"))
    organism_cvterm_id = Column(ForeignKey('organism_cvterm.organism_cvterm_id', ondelete='CASCADE'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    organism_cvterm = relationship('OrganismCvterm')
    type = relationship('Cvterm')


class OrganismDbxref(Base):
    __tablename__ = 'organism_dbxref'
    __table_args__ = (
        UniqueConstraint('organism_id', 'dbxref_id'),
    )

    organism_dbxref_id = Column(Integer, primary_key=True, server_default=text("nextval('organism_dbxref_organism_dbxref_id_seq'::regclass)"))
    organism_id = Column(ForeignKey('organism.organism_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    dbxref_id = Column(ForeignKey('dbxref.dbxref_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    is_current = Column(Boolean, nullable=False, server_default=text("true"))

    dbxref = relationship('Dbxref')
    organism = relationship('Organism')


class OrganismGrpmember(Base):
    __tablename__ = 'organism_grpmember'
    __table_args__ = (
        UniqueConstraint('grpmember_id', 'organism_id'),
    )

    organism_grpmember_id = Column(Integer, primary_key=True, server_default=text("nextval('organism_grpmember_organism_grpmember_id_seq'::regclass)"))
    grpmember_id = Column(ForeignKey('grpmember.grpmember_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    organism_id = Column(ForeignKey('organism.organism_id', ondelete='CASCADE', onupdate='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    grpmember = relationship('Grpmember')
    organism = relationship('Organism')


class OrganismLibrary(Base):
    __tablename__ = 'organism_library'
    __table_args__ = (
        UniqueConstraint('organism_id', 'library_id'),
    )

    organism_library_id = Column(Integer, primary_key=True, server_default=text("nextval('organism_library_organism_library_id_seq'::regclass)"))
    organism_id = Column(ForeignKey('organism.organism_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    library_id = Column(ForeignKey('library.library_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    library = relationship('Library')
    organism = relationship('Organism')


class OrganismPub(Base):
    __tablename__ = 'organism_pub'
    __table_args__ = (
        UniqueConstraint('organism_id', 'pub_id'),
    )

    organism_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('organism_pub_organism_pub_id_seq'::regclass)"))
    organism_id = Column(ForeignKey('organism.organism_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    organism = relationship('Organism')
    pub = relationship('Pub')


class Organismprop(Base):
    __tablename__ = 'organismprop'
    __table_args__ = (
        UniqueConstraint('organism_id', 'type_id', 'rank'),
    )

    organismprop_id = Column(Integer, primary_key=True, server_default=text("nextval('organismprop_organismprop_id_seq'::regclass)"))
    organism_id = Column(ForeignKey('organism.organism_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    organism = relationship('Organism')
    type = relationship('Cvterm')


class OrganismpropPub(Base):
    __tablename__ = 'organismprop_pub'
    __table_args__ = (
        UniqueConstraint('organismprop_id', 'pub_id'),
    )

    organismprop_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('organismprop_pub_organismprop_pub_id_seq'::regclass)"))
    organismprop_id = Column(ForeignKey('organismprop.organismprop_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    organismprop = relationship('Organismprop')
    pub = relationship('Pub')


class Phendesc(Base):
    __tablename__ = 'phendesc'
    __table_args__ = (
        UniqueConstraint('genotype_id', 'environment_id', 'type_id', 'pub_id'),
    )

    phendesc_id = Column(Integer, primary_key=True, server_default=text("nextval('phendesc_phendesc_id_seq'::regclass)"))
    genotype_id = Column(ForeignKey('genotype.genotype_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    environment_id = Column(ForeignKey('environment.environment_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    description = Column(Text, nullable=False)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    environment = relationship('Environment')
    genotype = relationship('Genotype')
    pub = relationship('Pub')
    type = relationship('Cvterm')


class Phenotype(Base):
    __tablename__ = 'phenotype'

    phenotype_id = Column(Integer, primary_key=True, server_default=text("nextval('phenotype_phenotype_id_seq'::regclass)"))
    uniquename = Column(Text, nullable=False, unique=True)
    observable_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), index=True)
    attr_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='SET NULL'), index=True)
    value = Column(Text)
    cvalue_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='SET NULL'), index=True)
    assay_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='SET NULL'))

    assay = relationship('Cvterm', primaryjoin='Phenotype.assay_id == Cvterm.cvterm_id')
    attr = relationship('Cvterm', primaryjoin='Phenotype.attr_id == Cvterm.cvterm_id')
    cvalue = relationship('Cvterm', primaryjoin='Phenotype.cvalue_id == Cvterm.cvterm_id')
    observable = relationship('Cvterm', primaryjoin='Phenotype.observable_id == Cvterm.cvterm_id')

    def __str__(self):
        """Over write the default output."""
        return "Phenotype id={}: uniquename:'{}' value:({})\n\tassay:({})\n\tattr:({})\n\tcvalue:({})\n\tobs:({})".\
            format(self.phenotype_id, self.uniquename, self.value, self.assay, self.attr, self.cvalue, self.observable)

class PhenotypeComparison(Base):
    __tablename__ = 'phenotype_comparison'
    __table_args__ = (
        UniqueConstraint('genotype1_id', 'environment1_id', 'genotype2_id', 'environment2_id', 'phenotype1_id', 'pub_id'),
    )

    phenotype_comparison_id = Column(Integer, primary_key=True, server_default=text("nextval('phenotype_comparison_phenotype_comparison_id_seq'::regclass)"))
    genotype1_id = Column(ForeignKey('genotype.genotype_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    environment1_id = Column(ForeignKey('environment.environment_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    genotype2_id = Column(ForeignKey('genotype.genotype_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    environment2_id = Column(ForeignKey('environment.environment_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    phenotype1_id = Column(ForeignKey('phenotype.phenotype_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    phenotype2_id = Column(ForeignKey('phenotype.phenotype_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'))
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    organism_id = Column(ForeignKey('organism.organism_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    environment1 = relationship('Environment', primaryjoin='PhenotypeComparison.environment1_id == Environment.environment_id')
    environment2 = relationship('Environment', primaryjoin='PhenotypeComparison.environment2_id == Environment.environment_id')
    genotype1 = relationship('Genotype', primaryjoin='PhenotypeComparison.genotype1_id == Genotype.genotype_id')
    genotype2 = relationship('Genotype', primaryjoin='PhenotypeComparison.genotype2_id == Genotype.genotype_id')
    organism = relationship('Organism')
    phenotype1 = relationship('Phenotype', primaryjoin='PhenotypeComparison.phenotype1_id == Phenotype.phenotype_id')
    phenotype2 = relationship('Phenotype', primaryjoin='PhenotypeComparison.phenotype2_id == Phenotype.phenotype_id')
    pub = relationship('Pub')


class PhenotypeComparisonCvterm(Base):
    __tablename__ = 'phenotype_comparison_cvterm'
    __table_args__ = (
        UniqueConstraint('phenotype_comparison_id', 'cvterm_id'),
    )

    phenotype_comparison_cvterm_id = Column(Integer, primary_key=True, server_default=text("nextval('phenotype_comparison_cvterm_phenotype_comparison_cvterm_id_seq'::regclass)"))
    phenotype_comparison_id = Column(ForeignKey('phenotype_comparison.phenotype_comparison_id', ondelete='CASCADE'), nullable=False, index=True)
    cvterm_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE'), nullable=False, index=True)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    cvterm = relationship('Cvterm')
    phenotype_comparison = relationship('PhenotypeComparison')


class PhenotypeCvterm(Base):
    __tablename__ = 'phenotype_cvterm'
    __table_args__ = (
        UniqueConstraint('phenotype_id', 'cvterm_id', 'rank'),
    )

    phenotype_cvterm_id = Column(Integer, primary_key=True, server_default=text("nextval('phenotype_cvterm_phenotype_cvterm_id_seq'::regclass)"))
    phenotype_id = Column(ForeignKey('phenotype.phenotype_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    cvterm_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    cvterm = relationship('Cvterm')
    phenotype = relationship('Phenotype')


class Phenstatement(Base):
    __tablename__ = 'phenstatement'
    __table_args__ = (
        UniqueConstraint('genotype_id', 'phenotype_id', 'environment_id', 'type_id', 'pub_id'),
    )

    phenstatement_id = Column(Integer, primary_key=True, server_default=text("nextval('phenstatement_phenstatement_id_seq'::regclass)"))
    genotype_id = Column(ForeignKey('genotype.genotype_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    environment_id = Column(ForeignKey('environment.environment_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    phenotype_id = Column(ForeignKey('phenotype.phenotype_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    environment = relationship('Environment')
    genotype = relationship('Genotype')
    phenotype = relationship('Phenotype')
    pub = relationship('Pub')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "Phenstatement id={}\n\tgenotype:'{}'\n\tphenotype: {}\n\tenvironment:'{}'\n\ttype{}\n\tpub:{}".\
            format(self.phenstatement_id, self.genotype, self.phenotype, self.environment, self.type, self.pub)


t_prediction_evidence = Table(
    'prediction_evidence', metadata,
    Column('prediction_evidence_id', Text),
    Column('feature_id', Integer),
    Column('evidence_id', Integer),
    Column('analysis_id', Integer)
)


class Project(Base):
    __tablename__ = 'project'

    project_id = Column(Integer, primary_key=True, server_default=text("nextval('project_project_id_seq'::regclass)"))
    name = Column(String(255), nullable=False, unique=True)
    description = Column(String(255), nullable=False)


class Pub(Base):
    __tablename__ = 'pub'

    pub_id = Column(Integer, primary_key=True, server_default=text("nextval('pub_pub_id_seq'::regclass)"))
    title = Column(Text)
    volumetitle = Column(Text)
    volume = Column(String(255))
    series_name = Column(String(255))
    issue = Column(String(255))
    pyear = Column(String(255))
    pages = Column(String(255))
    miniref = Column(String(255))
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    is_obsolete = Column(Boolean, server_default=text("false"))
    publisher = Column(String(255))
    pubplace = Column(String(255))
    uniquename = Column(Text, nullable=False, unique=True)

    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "Pub id={}: uniquename:{} title:'{}' miniref:'{}' type:({}) obsolete:'{}'".\
            format(self.pub_id, self.uniquename, self.title, self.miniref, self.type, self.is_obsolete)


class PubDbxref(Base):
    __tablename__ = 'pub_dbxref'
    __table_args__ = (
        UniqueConstraint('pub_id', 'dbxref_id'),
    )

    pub_dbxref_id = Column(Integer, primary_key=True, server_default=text("nextval('pub_dbxref_pub_dbxref_id_seq'::regclass)"))
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    dbxref_id = Column(ForeignKey('dbxref.dbxref_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    is_current = Column(Boolean, nullable=False, server_default=text("true"))

    dbxref = relationship('Dbxref')
    pub = relationship('Pub')


class PubRelationship(Base):
    __tablename__ = 'pub_relationship'
    __table_args__ = (
        UniqueConstraint('subject_id', 'object_id', 'type_id'),
    )

    pub_relationship_id = Column(Integer, primary_key=True, server_default=text("nextval('pub_relationship_pub_relationship_id_seq'::regclass)"))
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    subject_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    object_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    object = relationship('Pub', primaryjoin='PubRelationship.object_id == Pub.pub_id')
    subject = relationship('Pub', primaryjoin='PubRelationship.subject_id == Pub.pub_id')
    type = relationship('Cvterm')


class Pubauthor(Base):
    __tablename__ = 'pubauthor'
    __table_args__ = (
        UniqueConstraint('pub_id', 'rank'),
    )

    pubauthor_id = Column(Integer, primary_key=True, server_default=text("nextval('pubauthor_pubauthor_id_seq'::regclass)"))
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    rank = Column(Integer, nullable=False)
    editor = Column(Boolean, server_default=text("false"))
    surname = Column(String(100), nullable=False)
    givennames = Column(String(100))
    suffix = Column(String(100))

    pub = relationship('Pub')


class Pubprop(Base):
    __tablename__ = 'pubprop'
    __table_args__ = (
        UniqueConstraint('pub_id', 'type_id', 'rank'),
    )

    pubprop_id = Column(Integer, primary_key=True, server_default=text("nextval('pubprop_pubprop_id_seq'::regclass)"))
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text, nullable=False)
    rank = Column(Integer)

    pub = relationship('Pub')
    type = relationship('Cvterm')


class Strain(Base):
    __tablename__ = 'strain'
    __table_args__ = (
        UniqueConstraint('organism_id', 'uniquename'),
    )

    strain_id = Column(Integer, primary_key=True, server_default=text("nextval('strain_strain_id_seq'::regclass)"))
    name = Column(String(255), index=True)
    uniquename = Column(Text, nullable=False, index=True)
    organism_id = Column(ForeignKey('organism.organism_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    dbxref_id = Column(ForeignKey('dbxref.dbxref_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'))
    is_obsolete = Column(Boolean, nullable=False, server_default=text("false"))

    dbxref = relationship('Dbxref')
    organism = relationship('Organism')

    def __str__(self):
       """Dump data."""
       return "Strain id={}: name={}, uniquename={}, is_obsolete={}\n\tDbxref:({})\n\tOrg:({})".\
            format(self.strain_id, self.name, self.uniquename, self.is_obsolete, self.dbxref, self.organism)

class StrainCvterm(Base):
    __tablename__ = 'strain_cvterm'
    __table_args__ = (
        UniqueConstraint('strain_id', 'cvterm_id', 'pub_id'),
    )

    strain_cvterm_id = Column(Integer, primary_key=True, server_default=text("nextval('strain_cvterm_strain_cvterm_id_seq'::regclass)"))
    strain_id = Column(ForeignKey('strain.strain_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    cvterm_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    cvterm = relationship('Cvterm')
    pub = relationship('Pub')
    strain = relationship('Strain')

    def __str__(self):
        """Over write the default output."""
        return "StrainCvterm id={}:\n\tcvterm:({})\n\tstrain:({})\n\tpub:({})".\
            format(self.strain_cvterm_id, self.cvterm, self.strain, self.pub)


class StrainCvtermprop(Base):
    __tablename__ = 'strain_cvtermprop'
    __table_args__ = (
        UniqueConstraint('strain_cvterm_id', 'type_id', 'rank'),
    )

    strain_cvtermprop_id = Column(Integer, primary_key=True, server_default=text("nextval('strain_cvtermprop_strain_cvtermprop_id_seq'::regclass)"))
    strain_cvterm_id = Column(ForeignKey('strain_cvterm.strain_cvterm_id', ondelete='CASCADE'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    strain_cvterm = relationship('StrainCvterm')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "StrainCvtermprop id={}: value='{}' rank='{}'\n\tstrain_cvterm:({})\n\ttype:({})".\
            format(self.strain_cvtermprop_id, self.value, self.rank, self.strain_cvterm, self.type)


class StrainDbxref(Base):
    __tablename__ = 'strain_dbxref'
    __table_args__ = (
        UniqueConstraint('strain_id', 'dbxref_id'),
    )

    strain_dbxref_id = Column(Integer, primary_key=True, server_default=text("nextval('strain_dbxref_strain_dbxref_id_seq'::regclass)"))
    strain_id = Column(ForeignKey('strain.strain_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    dbxref_id = Column(ForeignKey('dbxref.dbxref_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    is_current = Column(Boolean, nullable=False, server_default=text("true"))

    dbxref = relationship('Dbxref')
    strain = relationship('Strain')

    def __str__(self):
        """Over write the default output."""
        return "StrainDbxref id={}: is_current:{}\n\tdbxref:({})\n\tstrain:({})".\
            format(self.strain_dbxref_id, self.is_current, self.dbxref, self.strain)


class StrainFeature(Base):
    __tablename__ = 'strain_feature'
    __table_args__ = (
        UniqueConstraint('strain_id', 'feature_id', 'pub_id'),
    )

    strain_feature_id = Column(Integer, primary_key=True, server_default=text("nextval('strain_feature_strain_feature_id_seq'::regclass)"))
    strain_id = Column(ForeignKey('strain.strain_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    feature_id = Column(ForeignKey('feature.feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    feature = relationship('Feature')
    pub = relationship('Pub')
    strain = relationship('Strain')

    def __str__(self):
        """Over write the default output."""
        return "StrainFeature id={}: \nStrain:({})\n\tFeature:({})\n\tpub:{}".\
            format(self.strain_feature_id, self.strain, self.feature, self.pub)

class StrainFeatureprop(Base):
    __tablename__ = 'strain_featureprop'
    __table_args__ = (
        UniqueConstraint('strain_feature_id', 'type_id', 'rank'),
    )

    strain_featureprop_id = Column(Integer, primary_key=True, server_default=text("nextval('strain_featureprop_strain_featureprop_id_seq'::regclass)"))
    strain_feature_id = Column(ForeignKey('strain_feature.strain_feature_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    strain_feature = relationship('StrainFeature')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "StrainFeatureprop id={}: value:'{}' rank:'{}'\nStrainFeature:({})\n\ttype:({})".\
            format(self.strain_featureprop_id, self.value, self.rank, self.strain_feature, self.type)

class StrainPhenotype(Base):
    __tablename__ = 'strain_phenotype'
    __table_args__ = (
        UniqueConstraint('strain_id', 'phenotype_id', 'pub_id'),
    )

    strain_phenotype_id = Column(Integer, primary_key=True, server_default=text("nextval('strain_phenotype_strain_phenotype_id_seq'::regclass)"))
    strain_id = Column(ForeignKey('strain.strain_id', ondelete='CASCADE'), nullable=False, index=True)
    phenotype_id = Column(ForeignKey('phenotype.phenotype_id', ondelete='CASCADE'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)

    phenotype = relationship('Phenotype')
    pub = relationship('Pub')
    strain = relationship('Strain')

    def __str__(self):
        """Over write the default output."""
        return "StrainPhenotype id={}:\n\tStrain:({})\n\tPhenotype:({})".\
            format(self.strain_phenotype_id, self.strain, self.phenotype)


class StrainPhenotypeprop(Base):
    __tablename__ = 'strain_phenotypeprop'
    __table_args__ = (
        UniqueConstraint('strain_phenotype_id', 'type_id', 'rank'),
    )

    strain_phenotypeprop_id = Column(Integer, primary_key=True, server_default=text("nextval('strain_phenotypeprop_strain_phenotypeprop_id_seq'::regclass)"))
    strain_phenotype_id = Column(ForeignKey('strain_phenotype.strain_phenotype_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    strain_phenotype = relationship('StrainPhenotype')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "StrainPhenotypeprop id={}: value:'{}' rank:'{}'\nStrainPhenotype:({})\n\ttype:({})".\
            format(self.strain_phenotypeprop_id, self.value, self.rank, self.strain_phenotype, self.type)


class StrainPub(Base):
    __tablename__ = 'strain_pub'
    __table_args__ = (
        UniqueConstraint('strain_id', 'pub_id'),
    )

    strain_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('strain_pub_strain_pub_id_seq'::regclass)"))
    strain_id = Column(ForeignKey('strain.strain_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    pub = relationship('Pub')
    strain = relationship('Strain')

    def __str__(self):
        """Over write the default output."""
        return "StrainPub id={}:\n\tStrain:({})\n\tPub:({})".\
            format(self.strain_pub_id, self.strain, self.pub)


class StrainRelationship(Base):
    __tablename__ = 'strain_relationship'
    __table_args__ = (
        UniqueConstraint('subject_id', 'object_id', 'type_id', 'rank'),
    )

    strain_relationship_id = Column(Integer, primary_key=True, server_default=text("nextval('strain_relationship_strain_relationship_id_seq'::regclass)"))
    subject_id = Column(ForeignKey('strain.strain_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    object_id = Column(ForeignKey('strain.strain_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    object = relationship('Strain', primaryjoin='StrainRelationship.object_id == Strain.strain_id')
    subject = relationship('Strain', primaryjoin='StrainRelationship.subject_id == Strain.strain_id')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "StrainRelationship id={}: value:'{}' rank:'{}'\n\tObj:({})\n\tSub:({})\n\ttype:({})".\
            format(self.strain_relationship_id, self.value, self.rank, self.object, self.subject, self.type)


class StrainRelationshipPub(Base):
    __tablename__ = 'strain_relationship_pub'
    __table_args__ = (
        UniqueConstraint('strain_relationship_id', 'pub_id'),
    )

    strain_relationship_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('strain_relationship_pub_strain_relationship_pub_id_seq'::regclass)"))
    strain_relationship_id = Column(ForeignKey('strain_relationship.strain_relationship_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    pub = relationship('Pub')
    strain_relationship = relationship('StrainRelationship')

    def __str__(self):
        """Over write the default output."""
        return "StrainRelationshipPub id={}:\n\tSR:({})\n\tPub:({})".\
            format(self.strain_relationship_pub_id, self.strain_relationship, self.pub)


class StrainSynonym(Base):
    __tablename__ = 'strain_synonym'
    __table_args__ = (
        UniqueConstraint('synonym_id', 'strain_id', 'pub_id'),
    )

    strain_synonym_id = Column(Integer, primary_key=True, server_default=text("nextval('strain_synonym_strain_synonym_id_seq'::regclass)"))
    strain_id = Column(ForeignKey('strain.strain_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    synonym_id = Column(ForeignKey('synonym.synonym_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    is_current = Column(Boolean, nullable=False, server_default=text("false"))
    is_internal = Column(Boolean, nullable=False, server_default=text("false"))

    pub = relationship('Pub')
    strain = relationship('Strain')
    synonym = relationship('Synonym')

    def __str__(self):
        """Over write the default output."""
        return "StrainSynonym id={}: is_current:'{}' is_internal:'{}'\n\tStrain:({})\n\tSyn:({})\n\tPub:({})".\
            format(self.strain_synonym_id, self.is_current, self.is_internal, self.strain, self.synonym, self.pub)


class Strainprop(Base):
    __tablename__ = 'strainprop'
    __table_args__ = (
        UniqueConstraint('strain_id', 'type_id', 'rank'),
    )

    strainprop_id = Column(Integer, primary_key=True, server_default=text("nextval('strainprop_strainprop_id_seq'::regclass)"))
    strain_id = Column(ForeignKey('strain.strain_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    value = Column(Text)
    rank = Column(Integer, nullable=False, server_default=text("0"))

    strain = relationship('Strain')
    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "Strainprop id={}: value:'{}' rank:'{}'\n\tstrain:({})\n\ttype:({})".\
            format(self.strainprop_id, self.value, self.rank, self.strain, self.type)


class StrainpropPub(Base):
    __tablename__ = 'strainprop_pub'
    __table_args__ = (
        UniqueConstraint('strainprop_id', 'pub_id'),
    )

    strainprop_pub_id = Column(Integer, primary_key=True, server_default=text("nextval('strainprop_pub_strainprop_pub_id_seq'::regclass)"))
    strainprop_id = Column(ForeignKey('strainprop.strainprop_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    pub_id = Column(ForeignKey('pub.pub_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)

    pub = relationship('Pub')
    strainprop = relationship('Strainprop')

    def __str__(self):
        """Over write the default output."""
        return "StrainpropPub id={}:\n\tstrainprop:({})\n\tpub:({})".\
            format(self.strainprop_pub_id, self.strainprop, self.pub)


class Synonym(Base):
    __tablename__ = 'synonym'
    __table_args__ = (
        UniqueConstraint('name', 'type_id', 'synonym_sgml'),
    )

    synonym_id = Column(Integer, primary_key=True, server_default=text("nextval('synonym_synonym_id_seq'::regclass)"))
    name = Column(String(255), nullable=False, index=True)
    type_id = Column(ForeignKey('cvterm.cvterm_id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), nullable=False, index=True)
    synonym_sgml = Column(String(255), nullable=False, index=True)

    type = relationship('Cvterm')

    def __str__(self):
        """Over write the default output."""
        return "Synonym id={}: name:'{}' synonym_sgml:'{}'\n\ttype:({})".\
            format(self.synonym_id, self.name, self.synonym_sgml, self.type)


class Tableinfo(Base):
    __tablename__ = 'tableinfo'

    tableinfo_id = Column(Integer, primary_key=True, server_default=text("nextval('tableinfo_tableinfo_id_seq'::regclass)"))
    name = Column(String(30), nullable=False, unique=True)
    primary_key_column = Column(String(30))
    is_view = Column(Integer, nullable=False, server_default=text("0"))
    view_on_table_id = Column(Integer)
    superclass_table_id = Column(Integer)
    is_updateable = Column(Integer, nullable=False, server_default=text("1"))
    modification_date = Column(Date, nullable=False, server_default=text("now()"))


class UpdateTrack(Base):
    __tablename__ = 'update_track'

    update_track_id = Column(Integer, primary_key=True, server_default=text("nextval('update_track_update_track_id_seq'::regclass)"))
    release = Column(String(20), nullable=False)
    fbid = Column(String(50), nullable=False)
    time_update = Column(DateTime, nullable=False, server_default=text("now()"))
    author = Column(String(20), nullable=False)
    statement = Column(String(255), nullable=False)
    comment = Column(Text, nullable=False, server_default=text("''::text"))
    annotation_id = Column(String(50))
