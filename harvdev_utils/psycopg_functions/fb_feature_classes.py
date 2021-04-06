"""Module:: fb_feature_classes.

Synopsis:
    FlyBase feature objects.

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu

"""

import logging
import re
from harvdev_utils.char_conversions import sub_sup_to_sgml, sub_sup_sgml_to_html, sgml_to_unicode

log = logging.getLogger(__name__)


# Parent Feature object.
class Feature(object):
    """Define a general FlyBase Feature object."""

    # Feature Class has the basic attributes of the chado feature table.
    def __init__(self, feature_id, organism_id, name, uniquename, feature_type, analysis, obsolete):
        """Initialize a FlyBase Feature class object.

        Args:
            arg1 (int): The feature.feature_id.
            arg2 (int): The feature.organism_id.
            arg3 (str): The feature.name.
            arg4 (str): The feature.uniquename; usually r'^FB[a-z]{2}[0-9]{7,10}$'.
            arg5 (str): The cvterm.name corresponding to feature.type_id.
            arg6 (bool): The feature.is_analysis value.
            arg7 (bool): The feature.is_obsolete value.

        Returns:
            Feature: A FlyBase "Feature" object.

        """
        self.feature_id = feature_id
        self.organism_id = organism_id
        self.name = name
        self.uniquename = uniquename
        self.feature_type = feature_type
        self.analysis = analysis
        self.obsolete = obsolete
        # Feature Class also has common stuff retrievable from other chado tables; set to None at outset.
        self.org_abbr = None               # The organism.abbreviation for the feature's organism.
        self.genus = None                  # The organism.genus for the feature's organism.
        self.symbol_sgml = None            # Current symbol synonym_sgml value.
        self.fullname_sgml = None          # Current fullname synonym_sgml value.
        self.agr_symbol = None             # For converted symbol_sgml (sub/superscript given in html).
        self.agr_symbol_text = None        # Demarcates allele superscript designation with chevrons.
        self.symbol_synonym_list = None    # List of symbol synonyms.
        self.fullname_synonym_list = None  # List of fullname synonyms.
        self.all_synonym_set = None        # List of all synonym types (should be uniqued).
        self.secondary_id_list = None      # List of dbxref.accession values.
        # Add bins to add warning and error messages.
        self.warnings = []         # Issues that prevent reporting of some info for this feature in some export file.
        self.errors = []           # Issues that prevent reporting of this feature in some export file.


    # feature.uniquename must be FB-type.
    uniquename_regex = r'^FB[a-z]{2}[0-9]{7,10}$'

    def _get_uniquename(self):
        return self.__uniquename

    def _set_uniquename(self, value):
        regex = self.uniquename_regex
        if re.search(regex, value):
            self.__uniquename = value
        else:
            raise TypeError('The "uniquename" must match this regex: {}'.format(regex))

    uniquename = property(_get_uniquename, _set_uniquename)

    # feature.feature_id must be an integer
    def _get_feature_id(self):
        return self.__feature_id

    def _set_feature_id(self, value):
        if isinstance(value, int):
            self.__feature_id = value
        else:
            raise TypeError('The "feature_id" must be an integer.')

    feature_id = property(_get_feature_id, _set_feature_id)

    # feature.is_analysis must be boolean
    def _get_analysis(self):
        return self.__analysis

    def _set_analysis(self, value):
        if isinstance(value, bool):
            self.__analysis = value
        else:
            raise TypeError('The "analysis" value must be boolean.')

    analysis = property(_get_analysis, _set_analysis)

    # feature.is_obsolete must be boolean
    def _get_obsolete(self):
        return self.__obsolete

    def _set_obsolete(self, value):
        if isinstance(value, bool):
            self.__obsolete = value
        else:
            raise TypeError('The "obsolete" value must be boolean.')

    obsolete = property(_get_obsolete, _set_obsolete)

    # Methods for converting FB sub/superscripts to html, uniquefying synonym/ID lists.
    def get_agr_symbol(self):
        """Convert FB symbol_sgml to AGR format (proper html sub/superscripts."""
        self.agr_symbol = self.symbol_sgml
        self.agr_symbol = sub_sup_sgml_to_html(self.symbol_sgml)
        return

    def convert_symbol_synonyms(self):
        """Convert all FB script designations in symbol synonyms to proper html."""
        if self.symbol_synonym_list is None:
            log.warning('Feature {} has no symbol_synonym_list to convert.'.format(self.uniquename))
            return
        else:
            self.symbol_synonym_list = [sub_sup_sgml_to_html(i) for i in self.symbol_synonym_list]
            return

    def convert_fullname_synonyms(self):
        """Convert all FB script designations in fullname synonyms to proper html."""
        if self.fullname_synonym_list is None:
            log.warning('Feature {} has no fullname_synonym_list to convert.'.format(self.uniquename))
            return
        else:
            self.fullname_synonym_list = [sub_sup_sgml_to_html(i) for i in self.fullname_synonym_list]
            return

    def unique_synonyms(self):
        """Make a unique set of symbol and fullname synonyms."""
        self.all_synonym_set = list(set(self.symbol_synonym_list + self.fullname_synonym_list))
        return

    def unique_secondary_ids(self):
        """Make unique set of secondary IDs."""
        if self.secondary_id_list is None:
            log.warning('Feature {} has no 2o ID info.'.format(self.uniquename))
        else:
            self.secondary_id_list = list(set(self.secondary_id_list))

    def agr_processing(self):
        """Run various methods for AGR processing."""
        self.get_agr_symbol()
        self.convert_symbol_synonyms()
        self.convert_fullname_synonyms()
        self.unique_synonyms()
        self.unique_secondary_ids()


# Children of Feature Object (alphabetically sorted).
class Allele(Feature):
    """Define a FlyBase Allele object."""

    # Inherit parental feature init.
    def __init__(self, feature_id, organism_id, name, uniquename, feature_type, analysis, obsolete):
        """Initialize a FlyBase Allele class object. See Feature for details."""
        Feature.__init__(self, feature_id, organism_id, name, uniquename, feature_type, analysis, obsolete)
        # Below are allele attributes that will be instantiated as "None" but given a value later.
        self.gene_id = None               # Will be one item.
        self.gene_symbol_sgml = None      # Will be one item.
        self.expresses = None             # If applicable, will match gene_id. Should be mutually exclusive with "targets".
        self.targets = None               # If applicable, will match gene_id. Should be mutually exclusive with "expresses".
        self.mut_origin = None            # Will be a list.
        self.fbtp_list = None             # Will be a list. Should have 'associated_with' rel type. Ignore rare FBmc and FBms.
        self.fbti_list = None             # Will be a list. Should only be Dmel insertions of 'associated_with. rel type.
        self.fbtp_via_fbti_list = None    # Will be a list. FBtp indirectly related to allele via FBti.
        self.has_reg_region = None        # Will be a list. FBal 'has_reg_region' FBto (f_r).
        self.tagged_with = None           # Will be a list. FBal 'tagged_with' FBto (f_r).
        self.encodes_tool = None          # Will be a list. FBal 'encodes_tool' FBto (f_r).
        self.carries_tool = None          # Will be a list. FBal 'carries_tool' FBto (f_r).
        self.molecular_info = None        # Will be a list. Eponymous featureprop.
        self.aminoacid_rep = None         # Will be a list. Eponymous featureprop.
        self.nucleotide_sub = None        # Will be a list. Eponymous featureprop.
        self.description = None           # Will be a string (concatenation of "nature_lesion" attribute values).
        self.insertion = None             # Will be a bool. Determined by "is_insertion" method.
        self.transgenic = None            # Will be a bool. Determined by "is_transgenic" method.
        self.in_dmel = None               # Will be a bool. Determined by "exists_in_dmel" method.
        self.drosophilidae = None         # Will be a bool. Allele of vinegar/fruit fly. Determined by "is_drosophilidae" method.
        self.classification = None        # AGR export classification
        self.crispr_ko_coll = None        # Will be a list. List of Crispr KO FBlc collections to which FBal indirectly belongs.
        self.gene_action = None           # For transgenic allele, determines if transgenic allele expresses or targets its gene.
        self.gene_for_agr_export = None   # Will be a bool. Obtained from related gene.
        self.for_agr_export = None        # Will be a bool.

    # feature.uniquename must be FBal-type.
    uniquename_regex = r'^FBal[0-9]{7}$'

    # This is a more sophisticated version of "get_agr_symbol_text()" method
    # It replaces ONLY the superscript designations around the superscripted allelic suffix, after the gene.
    # I want to keep this until I confirm exactly what symbolText should be.
    # def get_agr_symbol_text(self):
    #     """Replaces FB superscript around allele designation with chevrons."""
    #     if self.symbol_sgml is None:
    #         log.warning('Cannot get AGR symbolText for {} without symbol_sgml.'.format(self.uniquename))
    #         return
    #     if self.gene_symbol_sgml is None:
    #         log.warning('Cannot get AGR symbolText for {} without gene_symbol_sgml.'.format(self.uniquename))
    #         return
    #     gene_symbol = self.gene_symbol_sgml
    #     allele_symbol = self.symbol_sgml
    #     allele_superscript = allele_symbol.replace(gene_symbol, '')
    #     symbol_text = gene_symbol + allele_superscript.replace('<up>', '<').replace('</up>', '>')
    #     self.agr_symbol_text = symbol_text
    #     return

    def get_agr_symbol_text(self):
        """Replace all FB superscript with chevrons."""
        if self.symbol_sgml is None:
            log.warning('Cannot get AGR symbolText for {} without symbol_sgml.'.format(self.uniquename))
            return
        new_text = self.symbol_sgml
        new_text = new_text.replace('<up>', '<').replace('</up>', '>').replace('<down>', '<').replace('</down>', '>')
        self.agr_symbol_text = new_text
        return

    def make_description(self):
        """Concatenate "nature_lesion" strings into a description."""
        if self.molecular_info is None:
            log.warning('Allele {} missing "molecular_info" info for description.'.format(self.uniquename))
            self.description = None
        elif self.aminoacid_rep is None:
            log.warning('Allele {} missing "aminoacid_rep" info for description.'.format(self.uniquename))
            self.description = None
        elif self.nucleotide_sub is None:
            log.warning('Allele {} missing "nucleotide_sub" info for description.'.format(self.uniquename))
            self.description = None
        else:
            nature_lesion_list = []
            nature_lesion_list.extend(self.molecular_info)
            nature_lesion_list.extend(self.aminoacid_rep)
            nature_lesion_list.extend(self.nucleotide_sub)
        if len(nature_lesion_list) > 0:
            nature_lesion = ' '.join(nature_lesion_list)
            nature_lesion = nature_lesion.replace('@', '')
            nature_lesion = sub_sup_to_sgml(nature_lesion)         # Convert brackets into FB sub/superscript.
            nature_lesion = sub_sup_sgml_to_html(nature_lesion)    # Convert FB sub/superscript to html.
            nature_lesion = sgml_to_unicode(nature_lesion)         # Convert FB "&.gr;" Greeks to unicode.
            self.description = nature_lesion
        else:
            log.debug('Allele {} has no nature_lesion to report for description'.format(self.uniquename))
            self.description = None
        return

    def is_drosophilidae(self):
        """Determine if the feature is in some Drosophilidae species (vinegar/fruit fly)."""
        genus_list = ['Drosophila', 'Scaptomyza', 'Scaptodrosophila', 'Zaprionus', 'Chymomyza']
        if self.genus is None:
            log.warning('Feature {} lacks genus into to determine if Drosophilidae.'.format(self.uniquename))
        else:
            if self.genus in genus_list:
                self.drosophilidae = True
            else:
                self.drosophilidae = False
        return

    def is_transgenic(self):
        """Determine if allele is transgenic if "in vitro" term or FBtp found."""
        if self.mut_origin is None:
            log.warning('Allele {} has no cvterm info to make this determination.'.format(self.name))
            conclusion = None
        elif self.fbtp_list is None:
            log.warning('Allele {} has no FBtp info to make this determination.'.format(self.name))
            conclusion = None
        elif len(self.fbtp_list) > 0:
            conclusion = True
        elif type(self.mut_origin) == list:
            ivt_term_cnt = 0
            for term in self.mut_origin:
                if term.startswith('in vitro construct'):
                    ivt_term_cnt += 1
            if ivt_term_cnt > 0:
                conclusion = True
            else:
                conclusion = False
        else:
            conclusion = False
        self.transgenic = conclusion
        return

    def is_insertion(self):
        """Allele is insertion if has Dmel FBti."""
        if self.fbti_list is None:
            log.warning('Cannot determine if {} is insertion without FBti list.'.format(self.uniquename))
            conclusion = None
        elif len(self.fbti_list) == 0:
            conclusion = False
        elif len(self.fbti_list) > 0:
            conclusion = True
        self.insertion = conclusion
        return

    def exists_in_dmel(self):
        """Determine if this allele is carried in Dmel (regardless of allele's feature.orgnanism)."""
        if self.org_abbr is None:
            log.warning('Allele {} missing org_abbr to determine if it exists in Dmel.'.format(self.uniquename))
            conclusion = None
        elif self.org_abbr == 'Dmel':
            conclusion = True
        elif self.drosophilidae is None:
            log.warning('Allele {} missing drosophilidae to determine if it exists in Dmel.'.format(self.uniquename))
            conclusion = None
        # Non-Drosophilidae alleles (for Ecol\lacZ, Scer\GAL4, Hsap) presumed to exist in Dmel.
        elif self.drosophilidae is False:
            conclusion = True
        # At this point, allele must be non-Dmel Drosophilidae allele (e.g., Dana, Dsim). Special handling.
        else:
            if self.transgenic is None:
                log.warning('Allele {} lacks transgenic info to make Dmel/non-Dmel determination.'.format(self.name))
                conclusion = None
            elif self.transgenic is True:
                conclusion = True
            elif self.insertion is None:
                log.warning('Allele {} lacks insertion info to make Dmel/non-Dmel determination.'.format(self.name))
                conclusion = None
            elif self.insertion is True:    # Key point - self.insertion only counts insertions into Dmel.
                conclusion = True
            # At this point, we have non-Dmel Drosophilidae allele that's non-transgenic and lacks Dmel FBti.
            else:
                conclusion = False
        self.in_dmel = conclusion
        return

    def agr_allele_processing(self):
        """Run various methods for AGR processing."""
        self.agr_processing()
        self.get_agr_symbol_text()
        self.make_description()

    def classify_allele(self):
        """Classify allele into AGR export bins."""
        # Runs smaller methods to derive needed info for the decision.
        self.is_drosophilidae()
        self.is_transgenic()
        self.is_insertion()
        self.exists_in_dmel()    # Depends on is_drosophilidae() determination above.
        # Actual non-Dmel alleles in other Drosophilidae.
        if self.in_dmel is False:
            conclusion = 'non-dmel_allele'
        # Non-Dmel alleles that are actually carried in Dmel: transgenes and insertions.
        elif self.org_abbr != 'Dmel':
            # Non-Dmel alleles representing Dmel insertions: e.g., lacZ trap.
            if self.insertion is True:
                conclusion = 'insertion_non-dmel_gene'
            # Non-Dmel alleles representing Dmel transgenes: e.g., UAS-Hsap\p53.
            # For non-Dmel alleles, use more stringent criteria for "transgenicity" - must have FBtp.
            elif len(self.fbtp_list) > 0:
                conclusion = 'transgenic'
            # Non-Dmel alleles representing markers: e.g., Disc\RFP[3xP3.cUa] (FBal0320005).
            # Non-Dmel alleles with "in vitro construct" CV terms, but no FBtp: e.g., Avic\GFP[E.3xP3] (FBal0103092).
            else:
                conclusion = 'marker'
        # Here, dealing with 'Dmel' alleles.
        elif self.transgenic is False and self.insertion is False:
            conclusion = 'classical'
        elif self.transgenic is False and self.insertion is True:
            conclusion = 'insertion'
        elif self.transgenic is True:
            conclusion = 'transgenic'
        else:
            conclusion = 'undetermined'
        self.classification = conclusion
        return

    def determine_gene_action(self):
        """Determine if transgenic allele expresses, targets, or is_regulated_by its gene."""
        self.classify_allele()
        if self.classification == 'transgenic':
            if type(self.crispr_ko_coll) != list:
                log.warning('Allele {} needs "crispr_ko_coll" to determine "gene_action".'.format(self.uniquename))
            elif len(self.crispr_ko_coll) > 0:
                self.gene_action = 'targets'
                self.targets = self.gene_id
            elif type(self.mut_origin) != list:
                log.warning('Allele {} needs "mut_origin" CV terms to determine "gene_action".'.format(self.uniquename))
            else:
                cvterm_counter = 0
                for term in self.mut_origin:
                    if term in ['in vitro construct - RNAi']:
                        cvterm_counter += 1
                if cvterm_counter > 0:
                    self.gene_action = 'targets'
                    self.targets = self.gene_id
                else:
                    self.gene_action = 'expresses'
                    self.expresses = self.gene_id
        return

    def is_for_agr_export(self):
        """Considers allele type and related gene type to determine if allele is for export."""
        self.classify_allele()
        allele_type_filter_1 = ['classical', 'insertion']
        allele_type_filter_2 = ['undetermined', 'marker', 'non-dmel_allele']
        if self.gene_for_agr_export is None:
            raise ValueError('Cannot determine if allele is for agr export with "gene_for_agr_export" info.')
        elif self.classification is None:
            raise ValueError('Cannot determine if allele is for agr export with "classification" info.')
        elif self.gene_for_agr_export is False and self.classification in allele_type_filter_1:
            self.for_agr_export = False
        elif self.classification in allele_type_filter_2:
            self.for_agr_export = False
        else:
            self.for_agr_export = True
        return


class Construct(Feature):
    """Define a FlyBase Construct object."""

    # Inherit parental feature init.
    def __init__(self, feature_id, organism_id, name, uniquename, feature_type, analysis, obsolete):
        """Initialize a FlyBase Construct class object. See Feature for details."""
        Feature.__init__(self, feature_id, organism_id, name, uniquename, feature_type, analysis, obsolete)
        # Below are construct attributes that will be instantiated as "None" but given a value later.
        self.fbal_list = None             # Will be a list. FBal 'associated_with' FBtp.
        self.fbti_list = None             # Will be a list. Dmel FBti 'producedby' FBtp.
        self.has_reg_region = None        # Will be a list. FBal 'has_reg_region' FB(gn|to) (f_r).
        self.tagged_with = None           # Will be a list. FBal 'tagged_with' FBto (f_r).
        self.encodes_tool = None          # Will be a list. FBal 'encodes_tool' FBto (f_r).
        self.carries_tool = None          # Will be a list. FBal 'carries_tool' FBto (f_r).
        self.expresses_list = None          # Will be a list of FBgn IDs, via FBal. Expect no overlap with "target_list".
        self.targets_list = None            # Will be a list of FBgn IDs, via FBal. Expect no overlap with "expresses_list".

    # feature.uniquename must be FBtp-type.
    uniquename_regex = r'^FBtp[0-9]{7}$'


class Gene(Feature):
    """Define a FlyBase Gene object."""

    # Inherit parental feature init.
    def __init__(self, feature_id, organism_id, name, uniquename, feature_type, analysis, obsolete):
        """Initialize a FlyBase Gene class object. See Feature for details."""
        Feature.__init__(self, feature_id, organism_id, name, uniquename, feature_type, analysis, obsolete)
        # Below are gene attributes that will be instantiated as "None" but given a value later.
        self.hgnc_id_list = None          # Will be a list. All xrefs for Hsap genes where db = 'HGNC'.
        self.mod_id_list = None           # Will be a list. All xrefs where db in ('SGD', 'WormBase', 'ZFIN', 'RGD', 'MGI').
        self.agr_gene_id = None           # Will be unique. The ID to use for reporting genes to AGR.
        self.promoted_gene_type = None    # Will be unique. Eponymous featureprop.
        self.for_agr_export = None        # Will be boolean.

    # feature.uniquename must be FBgn-type.
    uniquename_regex = r'^FBgn[0-9]{7}$'

    def pick_gene_id(self):
        """Pick between FB, HGNC or other MOD ID to report."""
        # Start with FB ID as default.
        self.agr_gene_id = 'FB:{}'.format(self.uniquename)
        # Now look for a more appropriate ID.
        if type(self.hgnc_id_list) != list:
            log.warning('Gene {} should have "hgnc_id_list" to pick an ID.'.format(self.uniquename))
        elif len(self.hgnc_id_list) > 0:
            self.agr_gene_id = self.hgnc_id_list[0]
            if len(self.hgnc_id_list) > 1:
                log.warning('Gene {} has multiple HGNC IDs'.format(self.uniquename))
        elif type(self.mod_id_list) != list:
            log.warning('Gene {} should have "mod_id_list" to pick an ID.'.format(self.uniquename))
        elif len(self.mod_id_list) > 0:
            self.agr_gene_id = self.mod_id_list[0]
            if len(self.mod_id_list) > 1:
                log.warning('Gene {} has multiple MOD IDs'.format(self.uniquename))
        self.agr_gene_id = self.agr_gene_id.replace('WormBase:', 'WB:').replace('MGI:MGI:', 'MGI:')
        return

    def is_for_agr_export(self):
        """Assess organism and gene type to determine if gene is for AGR export."""
        # Post-SO-update
        exportable_gene_types = [
            '@SO0001217:protein_coding_gene@',
            '@SO0001263:ncRNA_gene@',
            '@SO0000336:pseudogene@',
            '@SO0000087:nuclear_gene@',
            '@SO0001265:miRNA_gene@',
            '@SO0001637:rRNA_gene@',
            '@SO0001267:snoRNA_gene@',
            '@SO0001268:snRNA_gene@',
            '@SO0001272:tRNA_gene@',
            '@SO0000704:gene@',
            '@SO0001269:SRP_RNA_gene@',
            '@SO0001639:RNase_P_RNA_gene@',
            '@SO0001640:RNase_MRP_RNA_gene@',
            '@SO0002127:lncRNA_gene@',
            '@SO0002182:antisense_lncRNA_gene@',
            '@SO0002236:rRNA_18S_gene@',
            '@SO0002238:rRNA_5S_gene@',
            '@SO0002239:rRNA_28S_gene@',
            '@SO0002240:rRNA_5_8S_gene@',
            '@SO0000010:protein_coding_gene@',        # Pre-SO-update term needed when querying older db.
            '@SO0000011:non_protein_coding_gene@',    # Pre-SO-update term needed when querying older db.
            '@SO0000042:pseudogene_attribute@',       # Pre-SO-update term needed when querying older db.
            '@SO0000571:miRNA_gene@',                 # Pre-SO-update term needed when querying older db.
            '@SO0000573:rRNA_gene@',                  # Pre-SO-update term needed when querying older db.
            '@SO0000578:snoRNA_gene@',                # Pre-SO-update term needed when querying older db.
            '@SO0000623:snRNA_gene@',                 # Pre-SO-update term needed when querying older db.
            '@SO0000663:tRNA_gene@'                   # Pre-SO-update term needed when querying older db.
        ]
        self.for_agr_export = False
        if self.org_abbr is None:
            log.warning('Gene {} should have "org_abbr" to determine exportability'.format(self.uniquename))
        elif self.promoted_gene_type is None:
            log.debug('Gene {} has no "promoted_gene_type" to determine exportability'.format(self.uniquename))
        elif self.org_abbr == 'Dmel':
            if self.promoted_gene_type in exportable_gene_types:
                self.for_agr_export = True
        return


class SeqFeat(Feature):
    """Define a FlyBase SeqFeat object."""

    # Inherit parental feature init.
    def __init__(self, feature_id, organism_id, name, uniquename, feature_type, analysis, obsolete):
        """Initialize a FlyBase SeqFeat class object. See Feature for details."""
        Feature.__init__(self, feature_id, organism_id, name, uniquename, feature_type, analysis, obsolete)

    # feature.uniquename must be FBsf-type.
    uniquename_regex = r'^FBsf[0-9]{10}$'


class Tool(Feature):
    """Define a FlyBase Tool object."""

    # Inherit parental feature init.
    def __init__(self, feature_id, organism_id, name, uniquename, feature_type, analysis, obsolete):
        """Make a FlyBase Tool class object. See Feature for details."""
        Feature.__init__(self, feature_id, organism_id, name, uniquename, feature_type, analysis, obsolete)
        # Below are tool attributes that will be instantiated as "None" but given a value later.
        self.originates_from = None    # Will be a list one FBgn IDs.

    # feature.uniquename must be FBto-type.
    uniquename_regex = r'^FBto[0-9]{7}$'
