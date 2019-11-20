###############################################################
# Module to centralise and unify external database lookups
#
# new_object = check_id('hgnc', 1101)
# or
# new_object = check_hgnc(1101)
#
# if new_object:
#     print new_object.name
# >> BRCA2 DNA repair associated
#
# Similarly for chebi
# new_object = check_id('chebi', 88852)
# or
# new_object = check_chebi(88852)
#
# print new_object.name
# >> 3,4-Dimethylcyclohexanol)
###############################################################

# external api's
from bioservices import ChEBI, HGNC
import pubchempy

# general imports
import logging
import json
from retry import retry

log = logging.getLogger(__name__)
# Stop bioservices from outputting tons of unnecessary info in DEBUG mode.
logging.getLogger("suds").setLevel(logging.INFO)

MAX_TRIES = 5
SLEEP_TIME = 5


class ExternalLookup:
    def __init__(self, dbname, external_id=None, name=None):
        log.info('Initializing Lookup object.')
        self.external_id = external_id
        self.dbname = dbname.lower()
        self.name = name
        self.description = None
        self.error = None
        ############################################
        # Set up how to get each type id external db
        ############################################
        self.id_dict = {'hgnc': self._lookup_hgnc_id,
                        'chebi': self._lookup_chebi_id,
                        'pubchem': self._lookup_pubchem_id}

        self.name_dict = {'pubchem': self._lookup_pubchem_name}

    @classmethod
    def check_id(cls, dbname, external_id=None):
        #
        # Will throw error if fails to connect after all tries
        #
        dbname = dbname.lower()
        new_instance = cls(dbname, external_id=external_id)
        if not external_id:
            new_instance.error = "No Accession supplied"
            return new_instance
        if dbname not in new_instance.id_dict:
            new_instance.error = "Dbname {}. Not found in list {}".format(dbname, new_instance.id_dict.keys())
            return new_instance
        return new_instance.id_dict[dbname]()

    @classmethod
    def check_name(cls, dbname, name=None):
        #
        # Will throw error if fails to connect after all tries
        #
        dbname = dbname.lower()
        new_instance = cls(dbname, name=name)
        if not name:
            new_instance.error = "No Name supplied"
            return new_instance
        if dbname not in new_instance.name_dict:
            new_instance.error = "Dbname {}. Not found in list {}".format(dbname, new_instance.name_dict.keys())
            return new_instance
        return new_instance.name_dict[dbname]()

    ###############
    # HGNC methods.
    ###############
    @classmethod
    def get_hgnc(cls, external_id=None):
        new_instance = cls('hgnc', external_id)
        if not external_id:
            new_instance.error = "No Accession supplied"
            return new_instance
        return new_instance._lookup_hgnc()

    @retry(tries=MAX_TRIES, delay=SLEEP_TIME, logger=log)
    def _lookup_hgnc_id(self):
        hgnc_web = HGNC()
        hgnc = hgnc_web.fetch('hgnc_id', self.external_id)
        if hgnc['response']['numFound'] == 1:
            self.name = hgnc['response']['docs'][0]['symbol']
            self.description = hgnc['response']['docs'][0]['name']
        elif hgnc['response']['numFound'] == 0:
            self.error = "No results found when querying HGNC for {}".format(self.external_id)
        return self

    ################
    # ChEBI methods.
    ################
    @classmethod
    def get_chebi(cls, external_id=None):
        new_instance = cls('chebi', external_id)
        if not external_id:
            new_instance.error = "No Accession supplied"
            return new_instance
        return new_instance._lookup_chebi()

    @retry(tries=MAX_TRIES, delay=SLEEP_TIME, logger=log)
    def _lookup_chebi_id(self):
        chebi_web = ChEBI()
        lookup_id = str(self.external_id)
        if not lookup_id.startswith("CHEBI:"):
            lookup_id = "CHEBI:{}".format(self.external_id)
        chebi = chebi_web.getCompleteEntity(lookup_id)
        if not chebi:
            self.error = "No results found when querying ChEBI for {}".format(self.external_id)
            return self
        self.name = chebi.chebiAsciiName
        try:
            self.inchikey = chebi.inchiKey
        except AttributeError:
            self.error = 'No InChIKey found for entry: {}'.format(self.external_id)
        return self

    #################
    # Pubchem methods
    #################
    @classmethod
    def get_pubchem(cls, external_id=None):
        new_instance = cls('pubchem', external_id)
        if not external_id:
            new_instance.error = "No Accession supplied"
            return new_instance
        return new_instance._lookup_pubchem()

    def pubchem_get_details_from_id(self):
        #
        # From the pubchem id get the description, title (stored as name) and inchikey
        #
        description = pubchempy.request(self.external_id, operation='description')
        raw_data = description.read()
        encoding = description.info().get_content_charset('utf8')  # JSON default
        description_data = json.loads(raw_data.decode(encoding))
        string_to_add_for_description = ""
        for description_item in description_data['InformationList']['Information']:
            if 'Description' in description_item.keys() and 'DescriptionSourceName' in description_item.keys():
                formatted_string = '{}: {}'.format(description_item['DescriptionSourceName'],
                                                   description_item['Description'])
                string_to_add_for_description += formatted_string
            elif 'Title' in description_item.keys():
                self.name = description_item['Title']

        self.description = string_to_add_for_description

        results = pubchempy.Compound.from_cid(self.external_id)
        inchikey = results.to_dict(properties=['inchikey'])
        if 'inchikey' in inchikey:
            self.inchikey = inchikey['inchikey']

    @retry(tries=MAX_TRIES, delay=SLEEP_TIME, logger=log)
    def _lookup_pubchem_id(self):
        try:
            self.pubchem_get_details_from_id()
        except pubchempy.BadRequestError:
            self.error = "No results found when querying pubchem for {}".format(self.external_id)
        return self

    @retry(tries=MAX_TRIES, delay=SLEEP_TIME, logger=log)
    def _lookup_pubchem_name(self):
        try:
            results = pubchempy.get_compounds(self.name, 'name')
            if results:
                self.external_id = results[0].to_dict(properties=['cid'])['cid']
                self.pubchem_get_details_from_id()
            else:
                self.error = "No results found when querying pubchem for {}".format(self.name)
        except pubchempy.BadRequestError:
            self.error = "No results found when querying pubchem for {}".format(self.name)
        return self

# test examples
# for hg_id in [1101, 111111]:
#     print("\n\nProcessing hgnc {}".format(hg_id))
#     hgnc = ExternalLookup.check_id('HGNC', hg_id)
#     if hgnc.error:
#         print("\t Error: {}".format(hgnc.error))
#     else:
#         print("\tname: {}".format(hgnc.name))
#         print("\tdesc: {}".format(hgnc.description))

# for chem_id in ['CHEBI:32140', 32140, 'CHEBI:99999999', 99999999]:
#     print("\n\nProcessing chebi {}".format(chem_id))
#     hgnc = ExternalLookup.check_id('CHEBI', chem_id)
#     if hgnc.error:
#         print("\t Error: {}".format(hgnc.error))
#     else:
#         print("\tname: {}".format(hgnc.name))
#         print("\tdesc: {}".format(hgnc.description))

# for pub_id in [23669229, 12345678910]:
#     print("\n\nProcessing pubchem id {}".format(pub_id))
#     hgnc = ExternalLookup.check_id('pubchem', pub_id)
#     if hgnc.error:
#         print("\t Error: {}".format(hgnc.error))
#     else:
#         print("\tname: {}".format(hgnc.name))
#         print("\tinchikey: {}".format(hgnc.inchikey))
#         print("\tdesc: {}".format(hgnc.description))

# for pub_name in ['Ecdysone', '3,4-Dimethylcyclohexanol', '12345678910']:
#     print("\n\nProcessing pubchem name {}".format(pub_name))
#     hgnc = ExternalLookup.check_name('pubchem', pub_name)
#     if hgnc.error:
#         print("\t Error: {}".format(hgnc.error))
#     else:
#         print("\tname: {}".format(hgnc.name))
#         print("\tinchikey: {}".format(hgnc.inchikey))
#         print("\tdesc: {}".format(hgnc.description))
