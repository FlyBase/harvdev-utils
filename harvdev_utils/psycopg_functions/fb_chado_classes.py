"""Module:: fb_chado_classes.

Synopsis:
    FlyBase chado objects (non-feature).

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu

"""

import logging
import re
import datetime
import strict_rfc3339
from harvdev_utils.char_conversions import sub_sup_sgml_to_html, sgml_to_unicode

log = logging.getLogger(__name__)


# Classes
class Author(object):
    """Define a FlyBase Author object."""

    def __init__(self, pubauthor_id, pub_id, rank, editor, surname, givennames, suffix):
        """Initialize a FlyBase Author Class object.

        Args:
            arg1 (int): The chado pubauthor.pubauthor_id.
            arg2 (int): The chado pubauthor.pub_id.
            arg3 (int): The chado pubauthor.rank.
            arg4 (bool): The chado pubauthor.editor.
            arg5 (str): The chado pubauthor.surname (max 255 char).
            arg6 (str): The chado pubauthor.givennames (max 255 char).
            arg7 (str): The chado pubauthor.suffix (max 255 char).

        Returns:
            Author: A FlyBase "Author" object.

        """
        self.pubauthor_id = pubauthor_id
        self.pub_id = pub_id
        self.rank = rank
        self.editor = editor
        self.surname = surname
        self.givennames = givennames
        self.suffix = suffix
        # Additional author attributes to be retrieved from FlyBase chado.
        self.pub_uniquename = None    # This will be the uniquename of the related pub (if applicable).
        self.pubmed_id = None         # The PubMed ID for the pub, if available.
        # AGR attributes.
        self.agr_author = None         # Author info transformed into AGR format.

    def make_agr_author(self):
        """Convert FlyBase pubauthor info into AGR authorReference.json spec."""
        # Perform only if pubauthor has pub corresponding to a current FBrf pub.
        if self.pub_uniquename is None:
            return
        else:
            agr_author_dict = {}

        # Pick the best ID.
        if self.pubmed_id is not None:
            agr_author_dict['referenceId'] = 'PMID:' + self.pubmed_id
        elif self.pub_uniquename is not None:
            agr_author_dict['referenceId'] = 'FB:' + self.pub_uniquename

        # Construct the author name.
        # If givennames are null or unknown, don't break out the name into components.
        # This will include consortia like "FlyBase", "Bloomington Drosophila Stock Center".
        if self.givennames is None or self.givennames == '?.':
            agr_author_dict['name'] = self.surname
        # Having givennames, we can break out name components.
        # Givennames should be initials (with periods): e.g., "H.A." or "W.M."
        else:
            agr_author_dict['name'] = self.givennames + ' ' + self.surname
            agr_author_dict['lastName'] = self.surname
            agr_author_dict['firstName'] = self.givennames.split('.')[0] + '.'
            # If givennames has anything after a period, we have to process middle initials.
            if re.search(r'\..+', self.givennames):
                # Names like "da Silva" appear has " da S." in pubauthor.givennames - just strip leading space.
                # Otherwise, split at ".", ignore first element and last empty element after last "."
                middle_inits = [i.lstrip(' ') + '.' for i in self.givennames.split('.')[1:-1]]
                agr_author_dict['middleNames'] = middle_inits

        self.agr_author = agr_author_dict

        return


class Pub(object):
    """Define a FlyBase Pub object."""

    def __init__(self, pub_id, title, volumetitle, volume, series_name, issue, pyear, pages, miniref, type_id, is_obsolete, publisher, pubplace, uniquename):
        """Initialize a FlyBase Pub Class object.

        Args:
            arg1 (int): The chado pub.pub_id.
            arg2 (str): The chado pub.title.
            arg3 (str): The chado pub.volumetitle.
            arg4 (str): The chado pub.volume (max 255 char).
            arg5 (str): The chado pub.series_name (max 255 char).
            arg6 (str): The chado pub.issue (max 255 char).
            arg7 (str): The chado pub.pyear (max 255 char).
            arg8 (str): The chado pub.pages (max 255 char).
            arg9 (str): The chado pub.miniref (max 255 char).
            arg10 (int): The chado pub.type_id.
            arg11 (bool): The chado pub.is_obsolete.
            arg12 (str): The chado pub.publisher (max 255 char).
            arg13 (str): The chado pub.pubplace (max 255 char).
            arg14 (str): The chado pub.uniquename, which should match '^multipub_[0-9]{1,5}$' regex.

        Returns:
            Pub: A FlyBase "Pub" object.

        """
        self.pub_id = pub_id
        self.title = title
        self.volumetitle = volumetitle
        self.volume = volume
        self.series_name = series_name
        self.issue = issue
        self.pyear = pyear
        self.pages = pages
        self.miniref = miniref
        self.type_id = type_id
        self.is_obsolete = is_obsolete
        self.publisher = publisher
        self.pubplace = pubplace
        self.uniquename = uniquename

    # pub.pub_id must be an integer
    def _get_pub_id(self):
        return self.__pub_id

    def _set_pub_id(self, value):
        if isinstance(value, int):
            self.__pub_id = value
        else:
            raise TypeError('The "pub_id" must be an integer.')

    pub_id = property(_get_pub_id, _set_pub_id)

    # pub.is_obsolete must be boolean
    def _get_obsolete(self):
        return self.__is_obsolete

    def _set_obsolete(self, value):
        if isinstance(value, bool):
            self.__is_obsolete = value
        else:
            raise TypeError('The "is_obsolete" value must be boolean.')

    obsolete = property(_get_obsolete, _set_obsolete)


class Reference(Pub):
    """Define a FlyBase Reference object."""

    def __init__(self, pub_id, title, volumetitle, volume, series_name, issue, pyear, pages, miniref, type_id, is_obsolete, publisher, pubplace, uniquename):
        """Initialize a FlyBase Reference Class object. See Pub Class for details.

        This Class is limited to chado pub entries corresponding to publications, which have "FBrf"-type IDs.
        Excluded are ~10K "resources" (journals, books and compendiums), which have "multipub"-type uniquenames.
        Excluded are ~50 "internal" pubs, which have non-"FBrf"/"multipub"-type IDs (e.g., "unattributed", "gadfly3").

        """
        Pub.__init__(self, pub_id, title, volumetitle, volume, series_name, issue, pyear, pages, miniref, type_id, is_obsolete, publisher, pubplace, uniquename)
        # Additional attributes to be retrieved from FlyBase chado.
        self.pubmed_id = None                    # A string of type '^PMID:[0-9]{1,}$' corresponding to the PubMed ID.
        self.pub_type = None                     # The cvterm.name corresponding to pub.type_id.
        self.pubauthor_ids = []                  # The pubauthor entries (IDs) for the pub.
        self.pubmed_abstract = []                # pubprop of type "pubmed_abstract".
        self.not_drospub = None                  # Will be "y" if not a Dros pub.
        self.resource_abbr = None                # The abbreviation for the resource in which the Reference was published.
        self.pub_timelastmodified = None         # Last audit_chado timestamp for "pub" table.
        self.author_timelastmodified = None      # Last audit_chado timestamp for "pubauthor" table.
        self.abstract_timelastmodified = None    # Last audit_chado timestamp for "pubprop" (abstract).
        self.pmid_timelastmodified = None        # Last audit_chado timestamp for "pub_dbxref" (PMID).
        self.journal_timelastmodified = None     # Last audit_chado timestamp for "pub_relationship" (journal).
        # Additional intermediate attributes to be synthesized from FlyBase Reference info.
        self.processing_errors = []            # A list of errors that prevent export of FB reference to AGR.
        self.processing_warnings = []          # A list of warnings that don't prevent export but should be logged.
        self.is_for_agr_export = None          # Boolean that reports if Reference is to be exported.
        self.export_description = None         # A string that identifies the pub for logging.
        # Below are attributes to be used for export to AGR.
        # If attribute is required, value can't be none: either hold from export, or fill in value with a placeholder.
        # Required AGR attributes for BOTH reference.json and referenceExchange.json formats.
        self.agr_category = None               # Need a dict of FB-to-AGR types.
        # Required attributes for ONLY reference.json.
        self.agr_primary_id = None             # Use PMID, then FBrf if no PMID.
        self.agr_title = None                  # FB title, but with FB-idiosyncratic chars converted (e.g., "</up>").
        self.agr_date_published = None         # Need to convert chado string (variable) into strict_rfc type timestamp?
        self.agr_citation = None               # Should be miniref, with handling for NULL minirefs, possibly odd chars.
        # Required attributes for ONLY referenceExchange.json
        self.agr_pubmed_id = None              # The PMID.
        # Optional AGR attributes for BOTH reference.json and referenceExchange.json formats.
        self.agr_mod_reference_types = None    # MOD ref type.
        self.agr_date_last_modified = None     # TO DO: Find most recent date for all pub datestamps.
        self.agr_tags = None                   # Will be a list of AGR tags. All FBrfs are "inCorpus"; some are "notRelevant" to fly researchers.
        # Optional AGR attributes for ONLY reference.json.
        self.agr_abstract = None               # Convert odd chars/tags.
        self.agr_publisher = None              # Will be publisher, and if present, pubplace.
        self.agr_resource_abbr = None          # Abbreviation for any related journal/book/compendium.
        self.agr_volume = None                 # Same as volume.
        self.agr_issue_name = None             # Using pub.issue for this.
        self.agr_pages = None                  # Need to handle lots of different syntax. Is there decided-upon AGR syntax? (e.g., convert FB "--" to "-")?
        self.agr_xrefs = None                  # xref back to FB Reference report.
        self.agr_authors = []                  # List of pubauthor entries for the pub.
        # Optional AGR attributes for ONLY referenceExchange.json.
        self.agr_mod_id = None                 # Will be the MOD ID.
        # AGR attribute for reporting pub as evidence.
        self.agr_pub_evidence = None
        # Ignoring these AGR reference.json attributes: dateArrivedPubMed, keywords, pubMedType, issueDate, meshTerms.

    # pub.uniquename must be "FBrf"-type.
    uniquename_regex = r'^FBrf[0-9]{7}$'

    def _get_uniquename(self):
        return self.__uniquename

    def _set_uniquename(self, value):
        regex = self.uniquename_regex
        if re.search(regex, value):
            self.__uniquename = value
        else:
            raise TypeError('The "uniquename" must match this regex: {}'.format(regex))

    uniquename = property(_get_uniquename, _set_uniquename)

    # Various methods for synthesizing and converting Reference attributes.
    def get_timelastmodified(self):
        """Collect all timestamps for the Reference object, take the latest, and convert to AGR spec."""
        timestamp_list = []
        attribute_list = self.__dict__.keys()
        for attribute in attribute_list:
            if attribute.endswith('timelastmodified') and getattr(self, attribute) is not None:
                timestamp_list.append(getattr(self, attribute))
        # Sort the timestamps and take the last one (i.e., the latest timestamp).
        max_timestamp = sorted(timestamp_list)[-1]
        # Convert datetime to strict_rfc3339 (via timestamp).
        self.agr_date_last_modified = strict_rfc3339.timestamp_to_rfc3339_localoffset(datetime.datetime.timestamp(max_timestamp))

        return

    def get_agr_primary_id(self):
        """Pick primary ID for AGR reporting of references or evidence supporting other submitted data."""
        if self.pubmed_id is not None:
            self.agr_pubmed_id = 'PMID:' + self.pubmed_id
            self.agr_primary_id = self.agr_pubmed_id
            self.agr_pub_evidence = {
                'publicationId': self.agr_primary_id,
                'crossReference': {
                    'id': 'FB:' + self.uniquename,
                    'pages': ['reference']
                }
            }
        else:
            self.agr_primary_id = 'FB:' + self.uniquename
            self.agr_pub_evidence = {
                'publicationId': self.agr_primary_id
            }

        return

    def get_agr_title(self):
        """Convert chars and sub/superscript tags in FlyBase title for AGR export."""
        # First determine if there's any title and/or volumetitle.
        if self.title is None:
            self.processing_warnings.append('No pub.title available.')
            title_to_use = 'No title available.'
        elif self.volumetitle is None:
            title_to_use = self.title
        else:
            title_to_use = self.title + ' ' + self.volumetitle
        # Next convert, handling odd chars that will raise error in "sgml_to_unicode" function.
        title_to_use = sub_sup_sgml_to_html(title_to_use)
        try:
            title_to_use = sgml_to_unicode(title_to_use)
        except KeyError:
            self.processing_warnings.append('Atypical sgml character(s) in title.')
        self.agr_title = title_to_use

        return

    def get_agr_date_published(self):
        """Convert FlyBase pub.pyear into AGR-compliant "datePublished" string."""
        # pub.pyear should be in one of six formats.
        # Not modifying or excluding outliers, but listing them here for future reference.
        # 1. YYYY (year, e.g, "1993", n = 180,653).
        # 2. YYYY- (year started for a living doc, e.g., "2000-", n = 69).
        # 3. YYYY-YYYY (year range, e.g., "1989-2000", n = 129).
        # 4. YYYY-M(M) (year-month, e.g., "2000-03", n = 235).
        # 5. YYYY-M(M)-D(D) (year-month-day, e.g., "2000-03-19", n = 49,441).
        # 6. YY(YY)?(?) (ambituity, e.g., "19??" or "1955?", n = 101).
        if self.pyear is None:
            self.processing_warnings.append('No pub.pyear available.')
            self.agr_date_published = 'No publication date available.'
        else:
            self.agr_date_published = self.pyear

        return

    def get_agr_citation(self):
        """Convert chars and sub/superscript tags in FlyBase miniref for AGR export."""
        if self.miniref is None:
            self.processing_warnings.append('No pub.miniref available.')
            self.agr_citation = 'No citation available.'
        else:
            converted_miniref = sgml_to_unicode(self.miniref)
            self.agr_citation = sub_sup_sgml_to_html(converted_miniref)

        return

    def get_agr_category(self):
        """Map FlyBase pub type to AGR pub type."""
        pub_type_fb_to_agr_mapping = {
            'abstract': 'Conference Publication',
            'autobiography': 'Other',
            'bibliographic list': 'Other',
            'biography': 'Other',
            'book': 'Book',
            'book review': 'Other',
            'conference report': 'Conference Publication',
            'curated genome annotation': 'Internal Process Reference',
            'database': 'Other',
            'DNA/RNA sequence record': 'Internal Process Reference',
            'edited book': 'Book',
            'editorial': 'Other',
            'erratum': 'Research Article',
            'film': 'Other',
            'FlyBase analysis': 'Internal Process Reference',
            'interview': 'Other',
            'letter': 'Other',
            'micropublication': 'Research Article',
            'news article': 'Other',
            'note': 'Other',
            'obituary': 'Other',
            'paper': 'Research Article',
            'patent': 'Other',
            'personal communication to FlyBase': 'Personal Communication',
            'poem': 'Other',
            'poster': 'Conference Publication',
            'preprint': 'Preprint',
            'press release': 'Other',
            'protein sequence record': 'Internal Process Reference',
            'retraction': 'Retraction',
            'review': 'Review Article',
            'species list': 'Direct Data Submission',
            'spoof': 'Other',
            'stock list': 'Direct Data Submission',
            'supplementary material': 'Research Article',
            'teaching note': 'Other',
            'thesis': 'Thesis',
            'unpublished': 'Preprint',
            'website': 'Other',
            'white paper': 'Other'}
        try:
            self.agr_category = pub_type_fb_to_agr_mapping[self.pub_type]
        except KeyError:
            self.processing_warnings.append('Pub type has no AGR mapping.')
            self.agr_category = 'Other'

        return

    def get_agr_abstract(self):
        """Convert chars and sub/superscript tags in FlyBase abstract for AGR export."""
        if self.pubmed_abstract != []:
            if len(self.pubmed_abstract) > 1:
                self.processing_warnings.append('Pub has many abstracts ({}). Using the first one.')
            abstract_to_use = sub_sup_sgml_to_html(self.pubmed_abstract[0])
            try:
                abstract_to_use = sgml_to_unicode(abstract_to_use)
            except KeyError:
                self.processing_warnings.append('Atypical sgml character(s) in abstract.')
            self.agr_abstract = abstract_to_use

        return

    def get_agr_tags(self):
        """Add AGR pub tags."""
        self.agr_tags = [{'referenceId': 'FB:' + self.uniquename,
                          'tagName': 'inCorpus',
                          'tagSource': 'FB'}]
        if self.not_drospub == 'y':
            not_relevant_tag = {'referenceId': 'FB:' + self.uniquename,
                                'tagName': 'notRelevant',
                                'tagSource': 'FB'}
            self.agr_tags.append(not_relevant_tag)

        return

    def get_agr_publisher(self):
        """Combine publisher with pubplace, if needed."""
        if self.publisher is not None and self.pubplace is not None:
            self.agr_publisher = '{} ({})'.format(self.publisher, self.pubplace)
        elif self.publisher is not None:
            self.agr_publisher = self.publisher

        return

    def process_for_agr_export(self):
        """Run set of simple methods for conversion of FB info into AGR format."""
        self.get_timelastmodified()
        self.get_agr_primary_id()
        self.get_agr_title()
        self.get_agr_date_published()
        self.get_agr_citation()
        self.get_agr_category()
        self.get_agr_abstract()
        self.get_agr_tags()
        self.get_agr_publisher()
        # No special conversion required for these attributes, yet.
        self.agr_mod_id = 'FB:' + self.uniquename
        self.agr_resource_abbr = self.resource_abbr
        self.agr_volume = self.volume
        self.agr_issue_name = self.issue
        self.agr_pages = self.pages
        self.agr_mod_reference_types = [{'source': 'FB', 'referenceType': self.pub_type}]
        self.agr_xrefs = [{'id': 'FB:' + self.uniquename, 'pages': ['reference']}]
        # Determine exportability.
        if self.processing_errors == []:
            self.is_for_agr_export = True
        else:
            self.is_for_agr_export = False
        # Generate a string that summarizes Reference AGR export issues for logging.
        export_description = 'Exported? {}. {}: {}. {}. '.format(self.is_for_agr_export, self.uniquename, self.miniref, self.title)
        if self.processing_errors != []:
            error_messages = 'ERRORS: ' + ' '.join(self.processing_errors)
            export_description = export_description + error_messages
        if self.processing_warnings != []:
            warning_messages = 'WARNINGS: ' + ' '.join(self.processing_warnings)
            export_description = export_description + warning_messages
        self.export_description = export_description

        return


class Resource(Pub):
    """Define a FlyBase Resource object."""

    def __init__(self, pub_id, title, volumetitle, volume, series_name, issue, pyear, pages, miniref, type_id, is_obsolete, publisher, pubplace, uniquename):
        """Initialize a FlyBase Resource Class object. See Pub Class for details.

        This Class is limited to current chado pub entries corresponding to books, journals and compendia, which have "multipub_"-type IDs.

        """
        Pub.__init__(self, pub_id, title, volumetitle, volume, series_name, issue, pyear, pages, miniref, type_id, is_obsolete, publisher, pubplace, uniquename)
        # Additional attributes to be retrieved from FlyBase chado.
        self.isbn_ids = []                # 0-many. 1320/9913 resources have ISBN (db.name = 'isbn').
        self.issn_ids = []                # 0-many. 4729/9913 resources have ISSN (db.name = 'issn'), print or online.
        self.pubauthor_ids = []           # 0-many. 1970/9913 resources have pubauthor (editor) entries.
        # Additional intermediate attributes to be synthesized from FlyBase Reference info.
        self.processing_errors = []       # A list of errors that prevent export of FB reference to AGR.
        self.processing_warnings = []     # A list of warnings that don't prevent export but should be logged.
        self.is_for_agr_export = None     # Boolean that reports if Reference is to be exported.
        self.export_description = None    # A string that identifies the pub for logging.
        # If attribute is required, value can't be none: either hold from export, or fill in value with a placeholder.
        # Required AGR attributes for resource.json.
        self.agr_primary_id = None        # NLM, MOD or ISBN ID.
        self.agr_title = None             # Title of resource.
        self.agr_iso_abbr = None          # ISO abbreviation. ISSUE - I don't know if FB abbr are MedLine or ISO.
        self.agr_medline_abbr = None      # MedLine abbreviation. ISSUE - I don't know if FB abbr are MedLine or ISO.
        # Optional AGR attributes for resource.json.
        self.agr_publisher = None              # Will be publisher, and if present, pubplace.
        self.agr_volumes = None                # ISSUE - Must be an array. Request string.
        self.agr_pages = None                  # ISSUE - Must be number. Request string.
        self.agr_editors = []                  # List of pubauthor (editor) entries for the pub.
        # Ignoring these AGR resource.json attributes: titleSynonyms, copyrightDate, abstractOrSummary.
        # Ignoring these AGR resource.json attributes: crossReferences (because we have no pages for resources).
        # Ignoring these AGR resource.json attributes: onlineISSN, printISSN (don't distinguish them in chado).

    # pub.uniquename must be "multipub_"-type.
    uniquename_regex = r'^multipub_[0-9]{1,5}$'

    def _get_uniquename(self):
        return self.__uniquename

    def _set_uniquename(self, value):
        regex = self.uniquename_regex
        if re.search(regex, value):
            self.__uniquename = value
        else:
            raise TypeError('The "uniquename" must match this regex: {}'.format(regex))

    uniquename = property(_get_uniquename, _set_uniquename)

    # Various methods for synthesizing and converting Reference attributes.
    def get_agr_primary_id(self):
        """Pick primary ID for AGR reporting."""
        self.agr_primary_id = 'FB:' + self.uniquename

        return

    def get_agr_title(self):
        """Convert chars and sub/superscript tags in FlyBase title for AGR export."""
        # First determine if there's any title and/or volumetitle.
        if self.title is None:
            self.processing_warnings.append('No pub.title available.')
            title_to_use = 'No title available.'
        elif self.volumetitle is None:
            title_to_use = self.title
        else:
            title_to_use = self.title + ' ' + self.volumetitle
        # Next convert, handling odd chars that will raise error in "sgml_to_unicode" function.
        title_to_use = sub_sup_sgml_to_html(title_to_use)
        try:
            title_to_use = sgml_to_unicode(title_to_use)
        except KeyError:
            self.processing_warnings.append('Atypical sgml character(s) in title.')
        self.agr_title = title_to_use

        return

    def get_agr_iso_abbr(self):
        """Check miniref and use as abbreviation if present."""
        if self.miniref is not None:
            self.agr_iso_abbr = self.miniref
        else:
            self.agr_iso_abbr = 'isoAbbreviation unavailable.'

        return

    def get_agr_medline_abbr(self):
        """Check miniref and use as abbreviation if present."""
        if self.miniref is not None:
            self.agr_medline_abbr = self.miniref
        else:
            self.agr_medline_abbr = 'medlineAbbreviation unavailable.'

        return

    def get_agr_publisher(self):
        """Combine publisher with pubplace, if needed."""
        if self.publisher is not None and self.pubplace is not None:
            self.agr_publisher = '{} ({})'.format(self.publisher, self.pubplace)
        elif self.publisher is not None:
            self.agr_publisher = self.publisher

        return

    def process_for_agr_export(self):
        """Run set of simple methods for conversion of FB info into AGR format."""
        self.get_agr_primary_id()
        self.get_agr_title()
        self.get_agr_iso_abbr()
        self.get_agr_medline_abbr()
        self.get_agr_publisher()
        # No special conversion required for these attributes, yet.
        # self.agr_volumes = self.volume
        self.agr_volumes = ['bob']    # TEMP - to pass spec for now.
        # self.agr_pages = self.pages
        self.agr_pages = 99                 # TEMP - to pass spec for now.
        # Determine exportability.
        if self.processing_errors == []:
            self.is_for_agr_export = True
        else:
            self.is_for_agr_export = False
        # Generate a string that summarizes Reference AGR export issues for logging.
        export_description = 'Exported? {}. {}: {}. {}. '.format(self.is_for_agr_export, self.uniquename, self.miniref, self.title)
        if self.processing_errors != []:
            error_messages = 'ERRORS: ' + ' '.join(self.processing_errors)
            export_description = export_description + error_messages
        if self.processing_warnings != []:
            warning_messages = 'WARNINGS: ' + ' '.join(self.processing_warnings)
            export_description = export_description + warning_messages
        self.export_description = export_description

        return


class Cvterm(object):
    """Define a FlyBase Cvterm object."""

    def __init__(self, cvterm_id, cv_id, definition, dbxref_id, is_obsolete, is_relationshiptype, name):
        """Initialize a FlyBase Cvterm Class object.

        Args:
            arg1 (int): The chado cvterm.cvterm_id.
            arg2 (int): The chado cvterm.cv_id.
            arg3 (str): The chado cvterm.definition. Can be NULL.
            arg4 (int): The chado cvterm.dbxref_id.
            arg5 (int): The chado cvterm.is_obsolete (0 or 1).
            arg6 (int): The chado cvterm.is_relationshiptype (0 or 1).
            arg7 (str): The chado cvterm.name.

        Returns:
            Cvterm: A FlyBase "Cvterm" object.

        """
        self.cvterm_id = cvterm_id
        self.cv_id = cv_id
        self.definition = definition
        self.dbxref_id = dbxref_id
        self.is_obsolete = is_obsolete
        self.is_relationshiptype = is_relationshiptype
        self.name = name
        # Additional attributes to be retrieved from FlyBase chado.
        self.cv_name = None             # Name of the CV for the CV term.
        self.dbxref_accession = None    # The dbxref.accession corresponding to cvterm.dbxref_id.
        self.db_name = None             # The db.name corresponding to the cvterm.dbxref_id.
        # Additional intermediate attributes to be synthesized from FlyBase Reference info.
        self.processing_errors = []       # A list of errors that prevent export of FB reference to AGR.
        self.processing_warnings = []     # A list of warnings that don't prevent export but should be logged.
        self.is_for_agr_export = None     # Boolean that reports if Reference is to be exported.
        self.export_description = None    # A string that identifies the pub for logging.
        # AGR attributes.
        self.agr_term_id = None           # Concatenation of the db.name and dbx.accession for a CV term's 1o ID.

    # cvterm.cvterm_id must be an integer
    def _get_cvterm_id(self):
        return self.__cvterm_id

    def _set_cvterm_id(self, value):
        if isinstance(value, int):
            self.__cvterm_id = value
        else:
            raise TypeError('The "cvterm_id" must be an integer.')

    cvterm_id = property(_get_cvterm_id, _set_cvterm_id)

    # cvterm.cv_id must be an integer
    def _get_cv_id(self):
        return self.__cv_id

    def _set_cv_id(self, value):
        if isinstance(value, int):
            self.__cv_id = value
        else:
            raise TypeError('The "cv_id" must be an integer.')

    cv_id = property(_get_cv_id, _set_cv_id)

    # cvterm.dbxref_id must be an integer
    def _get_dbxref_id(self):
        return self.__dbxref_id

    def _set_dbxref_id(self, value):
        if isinstance(value, int):
            self.__dbxref_id = value
        else:
            raise TypeError('The "dbxref_id" must be an integer.')

    dbxref_id = property(_get_dbxref_id, _set_dbxref_id)

    # cvterm.is_obsolete must an integer
    def _get_is_obsolete(self):
        return self.__is_obsolete

    def _set_is_obsolete(self, value):
        if isinstance(value, int):
            self.__is_obsolete = value
        else:
            raise TypeError('The "is_obsolete" value must an integer.')

    is_obsolete = property(_get_is_obsolete, _set_is_obsolete)

    # cvterm.is_relationshiptype must an integer
    def _get_is_relationshiptype(self):
        return self.__is_relationshiptype

    def _set_is_relationshiptype(self, value):
        if isinstance(value, int):
            self.__is_relationshiptype = value
        else:
            raise TypeError('The "is_relationshiptype" value must an integer.')

    is_obsolete = property(_get_is_relationshiptype, _set_is_relationshiptype)

    def get_agr_term_id(self):
        """Determine CV term ID for AGR export, if applicable."""
        exportable_cvterm_db_list = ['DOID', 'FBbt', 'FBcv', 'FBdv', 'GO', 'SO']
        if self.db_name in exportable_cvterm_db_list:
            self.agr_term_id = '{}:{}'.format(self.db_name, self.dbxref_accession)
        else:
            self.processing_errors.append('CV term not from a valid CV.')
        return

    def process_for_agr_export(self):
        """Run set of simple methods for conversion of FB info into AGR format."""
        self.get_agr_term_id()
        # Determine exportability.
        if self.processing_errors == []:
            self.is_for_agr_export = True
        else:
            self.is_for_agr_export = False
        # Generate a string that summarizes Reference AGR export issues for logging.
        export_description = 'Exported? {}. {} ({}:{}). '.format(self.is_for_agr_export, self.name, self.db_name, self.dbxref_accession)
        if self.processing_errors != []:
            error_messages = 'ERRORS: ' + ' '.join(self.processing_errors)
            export_description = export_description + error_messages
        if self.processing_warnings != []:
            warning_messages = 'WARNINGS: ' + ' '.join(self.processing_warnings)
            export_description = export_description + warning_messages
        self.export_description = export_description

        return



# Genotype, Environment, Phenotype, Phenstatement
