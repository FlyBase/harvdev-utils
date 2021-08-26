from harvdev_utils.production.production import CellLineLibraryprop
from base import BaseObject
from harvdev_utils.production import (
    CellLine, CellLinePub, CellLineprop, CellLinepropPub,
    CellLineCvterm, CellLineCvtermprop, CellLineDbxref, CellLineSynonym,
    CellLineRelationship, CellLineFeature, CellLineLibrary, CellLineStrain,
    CellLineStrainprop
)

import logging

log = logging.getLogger(__name__)


class CellLineReport(BaseObject):
    """Process the Cell line lookup.

    public | cell_line_cvterm                                                | table    | go
        public | cell_line_cvtermprop                                            | table    | go
    public | cell_line_dbxref                                                | table    | go
    public | cell_line_feature                                               | table    | go
    public | cell_line_library                                               | table    | go
        public | cell_line_libraryprop                                           | table    | go
    public | cell_line_pub                                                   | table    | go
    public | cell_line_relationship                                          | table    | go
    public | cell_line_Strain                                                | table    | go
        public | cell_line_Strainprop                                            | table    | go
    public | cell_line_synonym                                               | table    | go
    public | cell_lineprop                                                   | table    | go
        public | cell_lineprop_pub                                               | table    | go

    """

    def __init__(self, params):
        """Initialise the chado object."""
        log.debug('Initializing ChadoGrp object.')

        # Initiate the parent.
        super(CellLineReport, self).__init__(params)
        print("params are {}".format(params))
        ##################################################################################
        # table_info
        # is a list of tuples.
        # first item of tuple is the database table class
        # second is a list of dicts, each dict must have a related_class and related_id_name
        # this can alos be an empty list if there are no secondarys.
        ##################################################################################
        self.table_info = [(CellLineSynonym, []),
                           (CellLinePub, []),
                           (CellLineDbxref, []),
                           (CellLineprop, [{"related_class": CellLinepropPub, "related_id_name": 'cell_lineprop_id'}]),
                           (CellLineCvterm, [{"related_class": CellLineCvtermprop, "related_id_name": 'cell_line_cvterm_id'}]),
                           (CellLineFeature, []),
                           (CellLineLibrary, [{"related_class": CellLineLibraryprop, "related_id_name": 'cell_line_library_id'}]),
                           (CellLineStrain, [{"related_class": CellLineStrainprop, "related_id_name": 'cell_line_strain_id'}])]
        self.relationship = (CellLineRelationship, [])
        self.chado_object = CellLine
        self.primary_key_name = 'cell_line_id'  # primary id.
        self.chado_object = self.get_object(params.get('name'), params.get('lookup_by'))
