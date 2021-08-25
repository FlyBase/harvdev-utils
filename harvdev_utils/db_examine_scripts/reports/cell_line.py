from base import BaseObject
from harvdev_utils.production import (
    CellLine, CellLinePub, CellLineprop, CellLinepropPub
    # CellLineCvterm, CellLineDbxref,CellLineSynonym,
    # CellLineRelationship
)

import logging

log = logging.getLogger(__name__)


class CellLineReport(BaseObject):
    """Process the Cell line lookup."""

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
        self.table_info = [(CellLinePub, []),
                           (CellLineprop, [{"related_class": CellLinepropPub, "related_id_name": 'cell_lineprop_id'}])]

        self.chado_object = CellLine
        self.primary_key_name = 'cell_line_id'  # primary id.
        self.chado_object = self.get_object(params.get('name'), params.get('lookup_by'))
