###############################################################
# Module to centralise and unify external database lookups
#
# new_object = lookup_by_id('hgnc', 1101)
# or
# new_object = lookup_hgnc(1101)
#
# if new_object:
#     print new_object.name
# >> BRCA2 DNA repair associated
#
# Similarly for chebi
# new_object = lookup_by_id('chebi', 88852)
# or
# new_object = lookup_chebi(88852)
#
# print new_object.name
# >> 3,4-Dimethylcyclohexanol)
#
# Again for pubchem.
#
# lookups take an optional argument of synonym to set wether we
# want these aswell. It takes more time hence optional, no need
# grabbing stuff we do not need and wasting time.
#
# NOTE: for OMIM we need the env OMIM_KEY set to get the api key
#
###############################################################
#
# COSMIC https://cancer.sanger.ac.uk/cosmic/search?q=KMT2A
# GHR_gene https://ghr.nlm.nih.gov/search?query=TBC1D24
# external api's
from bioservices import HGNC
import pubchempy

# general imports
import logging
import json
import requests
from retry import retry
from os import getenv
from typing import Union

# url imports for omim
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError

log = logging.getLogger(__name__)
# Stop bioservices from outputting tons of unnecessary info in DEBUG mode.
logging.getLogger("suds").setLevel(logging.INFO)

MAX_TRIES = 5
SLEEP_TIME = 5

db_alias = {'omim_phenotype': 'omim'}


class ExternalLookup:
    def __init__(self, dbname: str, external_id: Union[int, str] = 0, name: str = "",
                 get_synonyms: bool = False, inchikey: str = None):
        log.debug('Initializing Lookup object.')
        self.external_id = external_id
        self.dbname = dbname.lower()
        self.name = name
        self.description = None
        self.inchikey = inchikey
        self.error = ""
        self.get_synonyms = get_synonyms
        self.synonyms: list = []
        ############################################
        # Set up how to get each type id external db
        ############################################
        self.id_dict = {'hgnc': self._lookup_hgnc_id,
                        'chebi': self._lookup_chebi_id,
                        'pubchem': self._lookup_pubchem_id,
                        'pubchem_sid': self._lookup_by_pubchem_substance_id,
                        'omim': self._lookup_omim_id,
                        'doid': self._lookup_doid_id}

        self.name_dict = {'pubchem': self._lookup_pubchem_name}
        self.inchikey_dict = {'pubchem': self._lookup_pubchem_inchikey}

    @classmethod
    def lookup_by_id(cls, dbname: str, external_id: Union[int, str] = 0, synonyms: bool = False):
        #
        # Will throw error if fails to connect after all tries
        #
        dbname = dbname.lower()
        if dbname in db_alias:
            dbname = db_alias[dbname]
        new_instance = cls(dbname, external_id=external_id, get_synonyms=synonyms)
        if not external_id:
            new_instance.error = "No Accession supplied"
            return new_instance
        if dbname not in new_instance.id_dict:
            new_instance.error = "Dbname {}. Not found in list {}".format(dbname, new_instance.id_dict.keys())
            return new_instance
        return new_instance.id_dict[dbname]()

    @classmethod
    def lookup_by_name(cls, dbname, name=None, synonyms=False):
        #
        # Will throw error if fails to connect after all tries
        #
        dbname = dbname.lower()
        new_instance = cls(dbname, name=name, get_synonyms=synonyms)
        if not name:
            new_instance.error = "No Name supplied"
            return new_instance
        if dbname not in new_instance.name_dict:
            new_instance.error = "Dbname {}. Not found in list {}".format(dbname, new_instance.name_dict.keys())
            return new_instance
        return new_instance.name_dict[dbname]()

    @classmethod
    def lookup_by_inchikey(cls, dbname, inchikey=None, synonyms=False):
        #
        # Will throw error if fails to connect after all tries
        #
        dbname = dbname.lower()
        new_instance = cls(dbname, inchikey=inchikey, get_synonyms=synonyms)
        if not inchikey:
            new_instance.error = "No Inchikey supplied"
            return new_instance
        if dbname not in new_instance.inchikey_dict:
            new_instance.error = "Dbname {}. Not found in list {}".format(dbname, new_instance.inchikey_dict.keys())
            return new_instance
        return new_instance.inchikey_dict[dbname]()

    ###############
    # HGNC methods.
    ###############
    @classmethod
    def lookup_hgnc(cls, external_id=None, synonyms=False):
        new_instance = cls('hgnc', external_id, get_synonyms=synonyms)
        if not external_id:
            new_instance.error = "No Accession supplied"
            return new_instance
        return new_instance._lookup_hgnc_id()

    @retry(tries=MAX_TRIES, delay=SLEEP_TIME, logger=log)
    def _lookup_hgnc_id(self):
        hgnc_web = HGNC()
        hgnc = hgnc_web.fetch('hgnc_id', self.external_id)
        if hgnc['response']['numFound'] == 1:
            self.name = hgnc['response']['docs'][0]['symbol']
            self.description = hgnc['response']['docs'][0]['name']
            # Get synonyms if requested.
            if self.get_synonyms:
                for item in hgnc['response']['docs'][0]['alias_symbol']:
                    self.synonyms.append(item)
        elif hgnc['response']['numFound'] == 0:
            self.error = "No results found when querying HGNC for {}".format(self.external_id)
        return self

    ################
    # ChEBI methods.
    ################
    @classmethod
    def lookup_chebi(cls, external_id=None, synonyms=False):
        new_instance = cls('chebi', external_id, get_synonyms=synonyms)
        if not external_id:
            new_instance.error = "No Accession supplied"
            return new_instance
        return new_instance._lookup_chebi_id()

    @retry(tries=MAX_TRIES, delay=SLEEP_TIME, logger=log)
    def _lookup_chebi_id(self):
        lookup_id = str(self.external_id)
        if lookup_id.startswith("CHEBI:"):
            lookup_id = lookup_id[6:]  # Remove CHEBI: prefix for EBI Search API

        # Use EBI Search REST API instead of SOAP service
        url = f'https://www.ebi.ac.uk/ebisearch/ws/rest/chebi/entry/{lookup_id}?format=json&fields=id%2Cname%2Cdescription%2Csynonyms%2Cinchikey'

        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                self.error = "No results found when querying ChEBI for {}".format(self.external_id)
                return self

            data = response.json()
            if not data.get('entries'):
                self.error = "No results found when querying ChEBI for {}".format(self.external_id)
                return self

            entry = data['entries'][0]
            fields = entry.get('fields', {})

            # Name
            if 'name' in fields and fields['name']:
                self.name = fields['name'][0]
            else:
                self.error = "No name found for ChEBI entry {}".format(self.external_id)
                return self

            # Description
            if 'description' in fields and fields['description']:
                self.description = fields['description'][0]

            # InChIKey
            if 'inchikey' in fields and fields['inchikey']:
                self.inchikey = fields['inchikey'][0]

            # Synonyms (if requested)
            if self.get_synonyms and 'synonyms' in fields and fields['synonyms']:
                seen_it = set()
                for synonym in fields['synonyms']:
                    if synonym and synonym not in seen_it:
                        self.synonyms.append(synonym)
                        seen_it.add(synonym)

        except requests.RequestException as e:
            self.error = f"Error connecting to ChEBI service: {e}"
            return self
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            self.error = f"Error parsing ChEBI response: {e}"
            return self

        return self

    #################
    # Pubchem methods
    #################
    @classmethod
    def lookup_pubchem(cls, external_id=None, synonyms=False):
        new_instance = cls('pubchem', external_id, get_synonyms=synonyms)
        if not external_id:
            new_instance.error = "No Accession supplied"
            return new_instance
        return new_instance._lookup_pubchem_id()

    def pubchem_get_details_from_id(self):
        #
        # From the pubchem id get the description, title (stored as name) and inchikey
        # Optional get the synonyms too.

        #####################
        # Get the description
        #####################
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

        ###########################
        # Get synonyms if requested
        ###########################
        try:
            if self.get_synonyms:
                syn = pubchempy.request(self.external_id, operation='synonyms')
                raw_data = syn.read()
                encoding = syn.info().get_content_charset('utf8')  # JSON default
                syn_data = json.loads(raw_data.decode(encoding))
                for synonym_item in syn_data['InformationList']['Information']:
                    if 'Synonym' in synonym_item.keys():
                        self.synonyms = synonym_item['Synonym']
        except Exception as e:
            self.synonyms = []

        ##################
        # Get the inchikey
        ##################
        results = pubchempy.Compound.from_cid(self.external_id)
        inchikey = results.to_dict(properties=['inchikey'])
        if 'inchikey' in inchikey:
            self.inchikey = inchikey['inchikey']

    @retry(tries=MAX_TRIES, delay=SLEEP_TIME, logger=log)
    def _lookup_by_pubchem_substance_id(self):
        try:
            substance = pubchempy.Substance.from_sid(self.external_id)
        except pubchempy.BadRequestError:
            self.error = "No results found when querying pubchem for substance {}".format(self.external_id)
        self.name = substance.sid
        self.inchikey = None
        self.description = None
        self.synonyms = substance.synonyms[0:10]  # Top 10 will do.
        return self

    @retry(tries=MAX_TRIES, delay=SLEEP_TIME, logger=log)
    def _lookup_pubchem_id(self):
        try:
            self.pubchem_get_details_from_id()
        except pubchempy.BadRequestError:
            self.error = "No results found when querying pubchem id for {}".format(self.external_id)
        return self

    @retry(tries=MAX_TRIES, delay=SLEEP_TIME, logger=log)
    def _lookup_pubchem_name(self):
        try:
            results = pubchempy.get_compounds(self.name, 'name')
            if results:
                self.external_id = results[0].to_dict(properties=['cid'])['cid']
                self.pubchem_get_details_from_id()
            else:
                self.error = "No results found when querying pubchem for name {}".format(self.name)
        except pubchempy.BadRequestError as e:
            self.error = f"No results found when querying pubchem for {self.name} Error:{e}"
        return self

    @retry(tries=MAX_TRIES, delay=SLEEP_TIME, logger=log)
    def _lookup_pubchem_inchikey(self):
        try:
            results = pubchempy.get_compounds(self.inchikey, 'inchikey')
            if results:
                self.external_id = results[0].to_dict(properties=['cid'])['cid']
                self.pubchem_get_details_from_id()
            else:
                self.error = "No results found when querying pubchem for inchikey {}".format(self.inchikey)
        except pubchempy.BadRequestError as e:
            self.error = f"No results found when querying pubchem for {self.inchikey} Error:{e}"
        return self

    ##############
    # OMIM methods
    ##############
    @classmethod
    def lookup_omim(cls, external_id=None, synonyms=False):
        new_instance = cls('omim', external_id, get_synonyms=synonyms)
        if not external_id:
            new_instance.error = "No Accession supplied"
            return new_instance
        return new_instance._lookup_omim_id()

    @retry(tries=MAX_TRIES, delay=SLEEP_TIME, logger=log)
    def _lookup_omim_id(self):

        api_key = getenv('OMIM_KEY')
        if not api_key:
            self.error = "OMIM_KEY env NOT set"
            return self

        request_data = {}
        request_data['apiKey'] = api_key
        request_data['format'] = 'json'
        request_data['mimNumber'] = self.external_id

        url = 'https://api.omim.org/api/entry'
        # add parameters to url string
        url_values = urlencode(request_data)
        url = url + '?' + url_values
        # query OMIM
        try:
            response = urlopen(url)
        except HTTPError as err:
            if err.code == 403:  # forbidden: BAD KEY
                self.error = "Failed to access OMIM API, may be time to register for a new key"
                return self
            elif err.code == 400:
                self.error = "No results found when querying OMIM for {}".format(self.external_id)
            return self

        # read in response
        result = json.loads(response.read())
        try:
            self.description = result['omim']['entryList'][0]['entry']['titles']['preferredTitle']
        except KeyError:
            self.error = "No results found when querying OMIM for {}".format(self.external_id)
        except IndexError:
            self.error = "No results found when querying OMIM for {}".format(self.external_id)
        return self

    ##############
    # DOID methods
    ##############
    @classmethod
    def lookup_doid(cls, external_id=None, synonyms=False):
        #
        # Lookup merere tests it exists and does not load descriptions etc
        #
        new_instance = cls('doid', external_id, get_synonyms=synonyms)
        if not external_id:
            new_instance.error = "No Accession supplied"
            return new_instance
        return new_instance._lookup_doid_id()

    @retry(tries=MAX_TRIES, delay=SLEEP_TIME, logger=log)
    def _lookup_doid_id(self):
        lookup_id = str(self.external_id)
        if not lookup_id.startswith("DOID:"):
            lookup_id = "DOID:{}".format(self.external_id)
        url = 'https://www.ebi.ac.uk/ols/api/terms?id={}'.format(lookup_id)
        headers = {'Accept': 'application/json'}

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            self.error = "No results found when querying DOID for {}".format(self.external_id)
            return self
        result = response.json()
        try:
            self.description = result['_embedded']['terms'][0]['label']
        except KeyError:
            self.error = "No results found when querying DOID for {}".format(self.external_id)
        return self


##########
# Examples
##########
if __name__ == '__main__':  # noqa: C901
    for hg_id in [1101, 111111]:
        print("\n\nProcessing hgnc {}".format(hg_id))
        hgnc = ExternalLookup.lookup_by_id('HGNC', hg_id)
        if hgnc.error:
            print("\t Error: {}".format(hgnc.error))
        else:
            print("\tname: {}".format(hgnc.name))
            print("\tdesc: {}".format(hgnc.description))

    for hg_id in [1103]:
        print("\n\nProcessing hgnc {}".format(hg_id))
        hgnc = ExternalLookup.lookup_hgnc(hg_id, synonyms=True)
        if hgnc.error:
            print("\t Error: {}".format(hgnc.error))
        else:
            print("\tname: {}".format(hgnc.name))
            print("\tdesc: {}".format(hgnc.description))
            print("\tsynonyms: {}".format(hgnc.synonyms))

    for chem_id in ['CHEBI:32140', 32140, 'CHEBI:99999999', 99999999]:
        print("\n\nProcessing chebi {}".format(chem_id))
        hgnc = ExternalLookup.lookup_by_id('CHEBI', chem_id, synonyms=True)  # type ignore
        if hgnc.error:
            print("\t Error: {}".format(hgnc.error))
        else:
            print("\tname: {}".format(hgnc.name))
            print("\tdesc: {}".format(hgnc.description))
            print("\tsynonyms: {}".format(hgnc.synonyms))

    for pub_id in [23669229, 12345678910]:
        print("\n\nProcessing pubchem id {}".format(pub_id))
        hgnc = ExternalLookup.lookup_by_id('pubchem', pub_id)
        if hgnc.error:
            print("\t Error: {}".format(hgnc.error))
        else:
            print("\tname: {}".format(hgnc.name))
            print("\tinchikey: {}".format(hgnc.inchikey))
            print("\tdesc: {}".format(hgnc.description))

    for pub_name in ['Ecdysone', '3,4-Dimethylcyclohexanol', '12345678910', 'sodium caffeine benzoate']:
        print("\n\nProcessing pubchem name {}".format(pub_name))
        hgnc = ExternalLookup.lookup_by_name('pubchem', pub_name)
        if hgnc.error:
            print("\t Error: {}".format(hgnc.error))
        else:
            print("\tname: {}".format(hgnc.name))
            print("\tinchikey: {}".format(hgnc.inchikey))
            print("\tdesc: {}".format(hgnc.description))
            print("\tsynonyms: {}".format(hgnc.synonyms))

    # also get synonyms
    for pub_name in ['sodium caffeine benzoate']:
        print("\n\nProcessing pubchem name {}".format(pub_name))
        hgnc = ExternalLookup.lookup_by_name('pubchem', pub_name, synonyms=True)
        if hgnc.error:
            print("\t Error: {}".format(hgnc.error))
        else:
            print("\tname: {}".format(hgnc.name))
            print("\tinchikey: {}".format(hgnc.inchikey))
            print("\tdesc: {}".format(hgnc.description))
            print("\tsynonyms: {}".format(hgnc.synonyms))

    for omim_id in [100100, 123456789]:
        print("\n\nProcessing omim id {}".format(omim_id))
        hgnc = ExternalLookup.lookup_by_id('omim', omim_id, synonyms=True)
        if hgnc.error:
            print("\t Error: {}".format(hgnc.error))
        else:
            print("\tname: {}".format(hgnc.name))
            print("\tinchikey: {}".format(hgnc.inchikey))
            print("\tdesc: {}".format(hgnc.description))
            print("\tsynonyms: {}".format(hgnc.synonyms))

    for doid_id in ['0001816', '1234567890123']:
        print("\n\nProcessing doid id {}".format(doid_id))
        hgnc = ExternalLookup.lookup_by_id('doid', doid_id)
        if hgnc.error:
            print("\t Error: {}".format(hgnc.error))
        else:
            print("\tdescription: {}".format(hgnc.description))

    for sid in ['348274211']:
        print("\n\nProcessing PubChem_sid id {}".format(sid))
        hgnc = ExternalLookup.lookup_by_id('PubChem_SID', sid)
        if hgnc.error:
            print("\t Error: {}".format(hgnc.error))
        else:
            print("\tdescription: {}".format(hgnc.description))
            print("\tname: {}".format(hgnc.name))
            print("\tinchikey: {}".format(hgnc.inchikey))
            print("\tdesc: {}".format(hgnc.description))
            print("\tsynonyms: {}".format(hgnc.synonyms))
