# !/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Utilities for processing genotypes.

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu

Notes:
    Given a genotype name (a string of feature SGML symbols), a
    GenotypeAnnotation object is created that will check for data problems
    with the genotype, if there are no issues, it can find an existing
    genotype in chado, or, create one. The genotype input name should consist
    of SGML symbols (but using square brackets for sub/superscript) for
    alleles, aberrations, balancers (and rarely, constructs and insertions):
    e.g., &agr;Tub67C[3] (Greeks in sgml, superscript using square brackets).
    Features may also include internal "bogus symbol" features typically
    meant to represent an unspecified wildtype allele: e.g., "wg[+]".
    Components at the same locus should be separated by a "/" character, with
    spaces separating different loci. FeSee curation rules for more details.
    Creating a new genotype in chado involves not just adding to the genotype
    table, but also assigning an ID (genotype_dbxref), a current symbol
    (genotype_synonym), and the components (feature_genotype).
    While these objects can write directly to chado, they should be
    controlled by handlers that have a postgress Session object.

"""

import re
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from collections import defaultdict
from harvdev_utils.production import (
    Cv, Cvterm, Db, Dbxref, Feature, FeatureCvterm, FeatureCvtermprop,
    FeatureGenotype, FeatureRelationship, FeatureRelationshipPub, FeaturePub,
    FeatureSynonym, Genotype, GenotypeDbxref, GenotypeSynonym, Organism,
    Organismprop, Pub, Synonym
)
from harvdev_utils.chado_functions import get_or_create
from harvdev_utils.char_conversions import sgml_to_plain_text, greek_to_sgml


# Regex patterns as constants (easier to maintain/change if needed)
FEATURE_UNIQUENAME_REGEX = r'^FB(al|ab|ba|ti|tp)[0-9]{7}$'
FBAL_REGEX = r'^FBal[0-9]{7}$'
FBGO_REGEX = r'^FBgo[0-9]{7}$'
FBTP_REGEX = r'^FBtp[0-9]{7}$'
FBTI_REGEX = r'^FBti[0-9]{7}$'
FBGN_REGEX = r'^FBgn[0-9]{7}$'


class ChadoCache:
    """Cache commonly used Chado DB objects to reduce repeated queries."""
    def __init__(self, session):
        """Create a ChadoCache object."""
        self.session = session
        self._flybase_db = None
        self._pub_unattributed = None
        self._synonym_symbol_cvterm = None

    @property
    def flybase_db(self):
        """Get FlyBase db.db_id."""
        if self._flybase_db is None:
            self._flybase_db = self.session.query(Db).filter(Db.name == 'FlyBase').one()
        return self._flybase_db

    @property
    def pub_unattributed(self):
        """Get FlyBase pub.pub_id for unattributed pub."""
        if self._pub_unattributed is None:
            self._pub_unattributed = self.session.query(Pub).filter(Pub.uniquename == 'unattributed').one()
        return self._pub_unattributed

    @property
    def synonym_symbol_cvterm(self):
        """Synonym CV term for 'symbol' from the 'synonym type' CV."""
        if self._synonym_symbol_cvterm is None:
            self._synonym_symbol_cvterm = (
                self.session.query(Cvterm)
                .join(Cv, Cv.cv_id == Cvterm.cv_id)
                .filter(Cvterm.name == 'symbol', Cv.name == 'synonym type')
                .one()
            )
        return self._synonym_symbol_cvterm


class GenotypeAnnotation(object):
    """A genotype, its related data, and quality-check attributes."""
    def __init__(self, input_genotype_name, session, log, pub_id):
        """Create a base GenotypeAnnotation from a genotype name.

        Args:
            input_genotype_name (str): A string of component SGML symbols.
            session (Session): SQLAlchemy session for the database from which to query and export.
            log (Logger): The logging object to use.
            pub_id (int): The relevant pub.pub_id; may be used for disambiguation.

        Returns:
            An object of the GenotypeAnnotation class.

        """
        self.input_genotype_name = input_genotype_name
        self.log = log              # From a script using this class.
        self.pub_id = pub_id        # The pub.pub_id to be used for disambiguation.
        self.features = {}          # Feature_id-keyed dict of public features.
        self.cgroup_list = []       # A list of ComplementationGroup objects derived from the input_genotype_name.
        self.cgroup_dict = {}       # Cgroup-keyed ComplementationGroups.
        self.uniquename = None      # Recomputed uniquename (symbols sorted).
        self.description = None     # Description based on feature IDs.
        self.curie = None           # FBgo ID (existing or created anew).
        self.genotype_id = None     # genotype.genotype_id (existing or new).
        self.is_new = None          # Becomes False if in chado, True if not.
        self.warnings = []          # Warnings about the genotype.
        self.notes = []             # Notes regarding transformation of input genotype.
        self.errors = []            # Errors (QC fails) that stop processing.
        # Process the input genotype.
        self.process_genotype_annotation(session)

    def __str__(self):
        """Informative string for this genotype for logging purposes."""
        return self.input_genotype_name

    #####################
    # Internal Methods
    #####################

    def _parse_cgroups(self, session):
        """Parse the input genotype into ComplementationGroups."""
        self.log.debug(f'Parse {self} into ComplementationGroups.\n')
        cgroup_symbols = self.input_genotype_name.split(' ')
        # self.log.debug(f'Found these cgroups: {cgroup_symbols}')
        for cgroup_symbol in cgroup_symbols:
            if cgroup_symbol != '':
                cgroup = ComplementationGroup(cgroup_symbol, self.log, self.pub_id)
                cgroup.process_cgroup(session)
                self.cgroup_list.append(cgroup)
        for cgroup in self.cgroup_list:
            for feature_dict in cgroup.features:
                if feature_dict['feature_id'] is not None and feature_dict['type'] != 'bogus symbol':
                    self.features[feature_dict['feature_id']] = feature_dict
        return

    def _propagate_cgroup_notes_and_errors(self):
        """Propagate cgroup notes and errors up to the genotype."""
        for cgroup in self.cgroup_list:
            self.notes.extend(cgroup.notes)
            self.errors.extend(cgroup.errors)
        return

    def _remove_redundant_cgroups(self):
        """For cgroups that have had allele replacements, assess for redundancy."""
        if self.errors:
            return
        transformed_cgroup_descs = {}
        for cgroup in self.cgroup_list:
            try:
                transformed_cgroup_descs[cgroup.cgroup_desc].append(cgroup)
            except KeyError:
                transformed_cgroup_descs[cgroup.cgroup_desc] = [cgroup]
        non_redundant_cgroup_list = []
        for cgroup_list in transformed_cgroup_descs.values():
            non_redundant_cgroup_list.append(cgroup_list[0])
        self.cgroup_list = non_redundant_cgroup_list
        return

    def _remove_less_informative_cgroups(self):
        """Remove FBti-containing cgroups if more informative cgroups exist."""
        if self.errors:
            return
        cgroup_descs = [i.cgroup_desc for i in self.cgroup_list if i.cgroup_desc]
        new_cgroup_list = []
        for this_cgroup in self.cgroup_list:
            if not re.match(FBTI_REGEX, this_cgroup.cgroup_desc):
                new_cgroup_list.append(this_cgroup)
            # Assess cgroups representing a single FBti insertion further
            else:
                more_informative_cgroup_exists = False
                for other_desc in cgroup_descs:
                    if this_cgroup.cgroup_desc in other_desc and this_cgroup.cgroup_desc != other_desc:
                        msg = f'cgroup "{this_cgroup.cgroup_desc}" is less informative than other cgroup "{other_desc}"'
                        self.notes.append(msg)
                        self.log.debug(msg)
                        more_informative_cgroup_exists = True
                if more_informative_cgroup_exists is False:
                    new_cgroup_list.append(this_cgroup)
                else:
                    msg = f'cgroup "{this_cgroup.cgroup_desc}" has been removed'
                    self.notes.append(msg)
                    self.log.debug(msg)
        self.cgroup_list = new_cgroup_list
        return

    def _reassign_insertions_to_classical_cgroups(self, session):
        """Look for FBti cgroups that can be combined with another cgroup."""
        if self.errors:
            return
        cgroup_desc_dict = {}    # cgroup_desc-keyed cgroups
        receptor_cgroups = {}    # keys are cgroups of single classical allele with open cgroup slot: each value a list of compatible donor cgroups
        donor_cgroups = {}       # keys are cgroups with single FBti that might get moved to another cgroup: each value a list of compatible receptor cgroups
        final_matches = {}       # A 1:1 donor-receptor match (using cgroup descs).
        new_cgroup_list = []
        # 1. Check for potential donor cgroups (must be a single at-locus FBti, not assigned to a Dros gene by curation).
        for cgroup in self.cgroup_list:
            # self.log.debug(f'Assess donor-potential of cgroup {cgroup.cgroup_desc}')
            if cgroup.at_locus is False or cgroup.gene_locus_id or 'FBti' not in cgroup.cgroup_desc:
                # self.log.debug(f'The cgroup {cgroup.cgroup_desc} is NOT a potential donor.')
                continue
            else:
                # self.log.debug(f'Check cgroup {cgroup.cgroup_desc} as a potential donor.')
                pass
            public_uniquenames = [i['uniquename'] for i in cgroup.features if i['uniquename'] and i['type'] != 'bogus symbol']
            # self.log.debug(f'Have these public uniquenames: {public_uniquenames}')
            # Must be a cgroup with only one FBti in the cgroup (ignore bogus symbols).
            if len(public_uniquenames) == 1:
                donor_cgroups[cgroup.cgroup_desc] = []
                # self.log.debug(f'The cgroup {cgroup.cgroup_desc} IS a potential donor.')
        if not donor_cgroups:
            # self.log.debug('Found no donor cgroups.')
            return
        # 2. Check for potential receptor cgroups (must have been assigned to a Dros gene by curation of FBal classical/insertion allele).
        for cgroup in self.cgroup_list:
            # self.log.debug(f'Assess acceptor-potential of cgroup {cgroup.cgroup_desc}')
            if cgroup.at_locus is False or cgroup.gene_locus_id is None:
                # self.log.debug(f'The cgroup {cgroup.cgroup_desc} is NOT a potential acceptor.')
                continue
            else:
                # self.log.debug(f'Check cgroup {cgroup.cgroup_desc} as a potential acceptor.')
                pass
            public_uniquenames = [i['uniquename'] for i in cgroup.features if i['uniquename'] and i['type'] != 'bogus symbol']
            # self.log.debug(f'Have these public uniquenames: {public_uniquenames}')
            # Must be a cgroup with an open spot (ignore bogus symbols).
            if len(public_uniquenames) == 1:
                receptor_cgroups[cgroup.cgroup_desc] = []
                # self.log.debug(f'The cgroup {cgroup.cgroup_desc} IS a potential acceptor.')
        if not receptor_cgroups:
            # self.log.debug('Found no acceptor cgroups.')
            return
        # Make a cgroup_desc-keyed dict of cgroups.
        for cgroup in self.cgroup_list:
            cgroup_desc_dict[cgroup.cgroup_desc] = cgroup
        # 3. Look for compatible donor/acceptor cgroups: the two sets should be non-overlapping.
        for donor_desc in donor_cgroups.keys():
            donor = cgroup_desc_dict[donor_desc]
            public_feature_ids = [i['feature_id'] for i in donor.features if i['feature_id'] and i['uniquename'].startswith('FBti')]
            compatible_fbgn_ids = self._find_possible_genes_for_insertion(session, public_feature_ids[0])
            # self.log.debug(f'For {donor_desc}, found these compatible FBgn IDs: {compatible_fbgn_ids}')
            for receptor_desc in receptor_cgroups.keys():
                receptor = cgroup_desc_dict[receptor_desc]
                # self.log.debug(f'For {receptor_desc}, found this FBgn ID locus: {receptor.gene_locus_id}')
                if receptor.gene_locus_id in compatible_fbgn_ids:
                    donor_cgroups[donor_desc].append(receptor_desc)
                    receptor_cgroups[receptor_desc].append(donor_desc)
                    msg = f'Might be possible to combine {donor_desc} with {receptor_desc} at {receptor.gene_locus_id} locus'
                    self.notes.append(msg)
                    self.log.debug(msg)
        # 4. Find one-to-one donor/receptor pairs (ignore cases of many-to-one or many-to-many).
        for donor_desc, receptor_list in donor_cgroups.items():
            if len(receptor_list) == 1:
                receptor_desc = receptor_list[0]
                if donor_desc in receptor_cgroups[receptor_desc] and len(receptor_cgroups[receptor_desc]) == 1:
                    final_matches[donor_desc] = receptor_desc
        for k, v in final_matches.items():
            self.log.debug(f'Found complementary cgroups: {k} and {v}')
        # 5. Move non-donor/receptor cgroups to the final list.
        cgroups_to_edit = list(final_matches.keys())
        cgroups_to_edit.extend(list(final_matches.values()))
        for cgroup in self.cgroup_list:
            if cgroup.cgroup_desc not in cgroups_to_edit:
                new_cgroup_list.append(cgroup)
        # 6. Combine the donor/receptor pairs and add them to the final list of cgroups.
        for donor_desc, receptor_desc in final_matches.items():
            donor_cgroup = cgroup_desc_dict[donor_desc]
            donor_symbol = [i['input_symbol'] for i in donor_cgroup.features if i['uniquename'].startswith('FBti')][0]
            receptor_cgroup = cgroup_desc_dict[receptor_desc]
            receptor_symbol = [i['input_symbol'] for i in receptor_cgroup.features if i['uniquename'] and i['type'] != 'bogus symbol'][0]
            new_input_cgroup_symbol = f'{donor_symbol}/{receptor_symbol}'
            # self.log.debug(f'Create new combined cgroup: {new_input_cgroup_symbol}')
            new_cgroup = ComplementationGroup(new_input_cgroup_symbol, self.log, self.pub_id)
            new_cgroup.process_cgroup(session)
            new_cgroup_list.append(new_cgroup)
        self.cgroup_list = new_cgroup_list
        return

    def _find_possible_genes_for_insertion(self, session, insertion_feature_id):
        """Find possible Dros genes for an at-locus FBti insertion via alleles."""
        fbgn_id_list = []
        gene = aliased(Feature, name='gene')
        allele = aliased(Feature, name='allele')
        ag_rel = aliased(FeatureRelationship, name='ag_rel')
        ai_rel = aliased(FeatureRelationship, name='ai_rel')
        ag_rel_type = aliased(Cvterm, name='ag_rel_type')
        ai_rel_type = aliased(Cvterm, name='ai_rel_type')
        filters = (
            ai_rel.object_id == insertion_feature_id,
            allele.is_obsolete.is_(False),
            allele.uniquename.op('~')(FBAL_REGEX),
            gene.is_obsolete.is_(False),
            gene.uniquename.op('~')(FBGN_REGEX),
            ai_rel_type.name == 'associated_with',
            ag_rel_type.name == 'alleleof',
            Organismprop.value == 'drosophilid',
        )
        results = session.query(gene).\
            select_from(gene).\
            join(Organismprop, (Organismprop.organism_id == gene.organism_id)).\
            join(ag_rel, (ag_rel.object_id == gene.feature_id)).\
            join(ag_rel_type, (ag_rel_type.cvterm_id == ag_rel.type_id)).\
            join(allele, (allele.feature_id == ag_rel.subject_id)).\
            join(ai_rel, (ai_rel.subject_id == allele.feature_id)).\
            join(ai_rel_type, (ai_rel_type.cvterm_id == ai_rel.type_id)).\
            filter(*filters).\
            distinct()
        for result in results:
            fbgn_id_list.append(result.uniquename)
        return fbgn_id_list

    def _check_multi_cgroup_genes(self):
        """Look for genes of "single_cgroup" features in many cgroups."""
        GENE_NAME = 0
        GENE_CURIE = 1
        gene_cgroup_counter = {}
        for cgroup in self.cgroup_list:
            cgroup_genes = {
                (feature_dict['parental_gene_name'], feature_dict['parental_gene_uniquename'])
                for feature_dict in cgroup.features
                if feature_dict['at_locus'] and feature_dict['parental_gene_feature_id']
            }
            for cgroup_gene in cgroup_genes:
                try:
                    gene_cgroup_counter[cgroup_gene] += 1
                except KeyError:
                    gene_cgroup_counter[cgroup_gene] = 1
        for gene, count in gene_cgroup_counter.items():
            if count > 1:
                msg = f'Classical alleles for {gene[GENE_NAME]} '
                msg += f'({gene[GENE_CURIE]}) '
                msg += f'are listed in {count} different cgroups'
                self.log.error(msg)
                self.errors.append(msg)
        return

    def _calculate_genotype_uniquename(self):
        """Calculate the genotype uniquename."""
        if self.errors:
            return
        cgroups_by_name = defaultdict(list)
        for cgroup in self.cgroup_list:
            cgroups_by_name[cgroup.cgroup_name].append(cgroup)
        sorted_cgroup_names = sorted(cgroups_by_name.keys())
        cgroup_number = 0
        for cgroup_name in sorted_cgroup_names:
            for cgroup in cgroups_by_name[cgroup_name]:
                self.cgroup_dict[cgroup_number] = cgroup
                cgroup_number += 1
        self.uniquename = ' '.join(sorted_cgroup_names)
        self.log.debug(f'Genotype {self} has this uniquename: {self.uniquename}')
        return

    def _calculate_genotype_desc(self):
        """Calculate the genotype description."""
        if self.errors:
            return
        cgroup_descs = sorted([i.cgroup_desc for i in self.cgroup_list])
        self.description = '_'.join(cgroup_descs)
        self.log.debug(f'Calculated this description: {self.description}')
        return

    def _find_known_genotype(self, session):
        """Find a corresponding genotype in chado."""
        if self.errors:
            return
        filters = (
            Genotype.uniquename == self.uniquename,
            Genotype.is_obsolete.is_(False),
            GenotypeDbxref.is_current.is_(True),
            Dbxref.accession.op('~')(FBGO_REGEX),
            Db.name == 'FlyBase',
        )
        chado_genotype = session.query(Genotype, Dbxref).\
            select_from(Genotype).\
            join(GenotypeDbxref, (GenotypeDbxref.genotype_id == Genotype.genotype_id)).\
            join(Dbxref, (Dbxref.dbxref_id == GenotypeDbxref.dbxref_id)).\
            join(Db, (Db.db_id == Dbxref.db_id)).\
            filter(*filters).\
            one_or_none()
        if chado_genotype:
            self.log.debug(f'{self} matches {chado_genotype.Genotype.uniquename} (genotype_id={chado_genotype.Genotype.genotype_id})')
            if chado_genotype.Genotype.description == self.description:
                self.curie = chado_genotype.Dbxref.accession
                self.genotype_id = chado_genotype.Genotype.genotype_id
                self.is_new = False
                self.log.debug(f'The descriptions for the curated and chado genotype are identical: {self.description}.')
            else:
                msg = f'Description mismatch: chado_desc={chado_genotype.Genotype.description}, calc_desc={self.description}'
                self.errors.append(msg)
                self.log.error(msg)
        else:
            self.is_new = True
            self.log.debug(f'Genotype {self} not found in chado.')

    def _create_new_genotype(self, session):
        """Create a new entry in the chado genotype table."""
        if self.errors or not self.is_new:
            return
        new_chado_genotype, created = get_or_create(session, Genotype, uniquename=self.uniquename, description=self.description)
        if created is False:
            self.errors.append(f'Thought to be new, but corresponds to genotype_id={new_chado_genotype.genotype_id}')
            self.log.error(f'For {self}, initial attempt to find chado genotype missed this existing one: genotype_id={new_chado_genotype.genotype_id}')
            return
        else:
            self.log.debug(f'For {self}, made this genotype: {new_chado_genotype}')
        self.genotype_id = new_chado_genotype.genotype_id
        return

    def _assign_genotype_curie(self, session, cache):
        """Assign a FlyBase curie to the genotype."""
        if self.errors or not self.is_new:
            return
        # Generate a new FBgo ID from the sequence.
        new_fbgo_query = "SELECT nextval('genotype_curie_seq');"
        new_fbgo_int = session.execute(new_fbgo_query).scalar()
        new_fbgo_id = f'FBgo{str(new_fbgo_int).zfill(7)}'
        # Create the new FBgo ID in chado.
        new_xref, created = get_or_create(
            session,
            Dbxref,
            db_id=cache.flybase_db.db_id,
            accession=new_fbgo_id
        )
        if not created:
            msg = f'{new_xref.accession} should be new, but it already exists. ID minting is malfunctioning.'
            self.log.error(msg)
            raise ValueError(msg)
        get_or_create(
            session,
            GenotypeDbxref,
            genotype_id=self.genotype_id,
            dbxref_id=new_xref.dbxref_id
        )
        self.curie = new_xref.accession
        self.log.debug(f'For {self}, assigned new ID: {self.curie}')
        return

    def _create_genotype_component_associations(self, session):
        """Create genotype component entries."""
        if self.errors or not self.is_new:
            return
        for cgroup_number, cgroup in self.cgroup_dict.items():
            for feat_rank, feature_dict in cgroup.rank_dict.items():
                _, created = get_or_create(session, FeatureGenotype, genotype_id=self.genotype_id, feature_id=feature_dict['feature_id'],
                                           cgroup=cgroup_number, rank=feat_rank, cvterm_id=60468, chromosome_id=23159230)
        return

    def _assign_genotype_symbol(self, session, cache):
        """Assign the genotype a current symbol."""
        if self.errors or not self.is_new:
            return
        new_symbol, _ = get_or_create(
            session,
            Synonym,
            type_id=cache.synonym_symbol_cvterm.cvterm_id,
            name=self.uniquename,
            synonym_sgml=self.uniquename
        )
        get_or_create(
            session,
            GenotypeSynonym,
            genotype_id=self.genotype_id,
            synonym_id=new_symbol.synonym_id,
            pub_id=cache.pub_unattributed.pub_id
        )
        return

    ###############################
    # Public Methods (Entry Point)
    ###############################

    def process_genotype_annotation(self, session):
        """Run various GenotypeAnnotation methods in sequence."""
        self.log.debug(f'Processing input genotype {self.input_genotype_name}.')
        self._parse_cgroups(session)
        self._propagate_cgroup_notes_and_errors()
        self._remove_less_informative_cgroups()
        self._remove_redundant_cgroups()
        self._reassign_insertions_to_classical_cgroups(session)
        self._check_multi_cgroup_genes()
        self._calculate_genotype_uniquename()
        self._calculate_genotype_desc()
        self.log.debug('Done initial parsing of genotype.\n\n\n')
        return

    def get_known_or_create_new_genotype(self, session):
        """Find an existing genotype, or, create a new genotype plus a new ID, component entries, and a current symbol."""
        # We create a cache object once, then reuse it.
        cache = ChadoCache(session)
        # Identify if the genotype is already in chado.
        self._find_known_genotype(session)
        # If not found in chado, create a new genotype in chado.
        if self.is_new is True:
            self._create_new_genotype(session)
            self._assign_genotype_curie(session, cache)
            self._create_genotype_component_associations(session)
            self._assign_genotype_symbol(session, cache)
        return


class ComplementationGroup(object):
    """A complementation group of features that is part of a genotype."""
    def __init__(self, input_cgroup_str, log, pub_id):
        """Create a base ComplementationGroup.

        Args:
            input_cgroup_str (str): The components of the cgroup: e.g., "wg[1]/Df(2L)x".
            log (Logger): The logging object to use.
            pub_id (int): The pub.pub_id to use for disambiguation.

        Returns:
            An object of the ComplementationGroup class.

        """
        self.input_cgroup_str = input_cgroup_str
        self.log = log                   # From a script using this class.
        self.pub_id = pub_id             # The pub.pub_id to use for disambiguation.
        self.features = []               # Will be dicts with relevant feature info.
        self.feature_replaced = False    # Change to True if an input allele/construct is converted to an insertion.
        self.at_locus = False            # Change to True if there are at_locus features present.
        self.rank_dict = {}              # Will be rank-keyed feature dicts.
        self.cgroup_name = None          # Will be "correct" symbol for the cgroup from its components.
        self.cgroup_desc = None          # Will be sorted concatenation of component IDs.
        self.gene_locus_id = None        # Will be FBgn ID of gene if cgroup represents classical/insertion alleles of a gene.
        self.notes = []                  # Notes on mapping of specified feature to one more appropriate for Alliance submission.
        self.errors = []                 # Error messages: if any, the cgroup (and related genotype) should not be processed.

    #####################
    # Internal Methods
    #####################

    def _identify_feature(self, session):
        """Identify the chado feature for each symbol given in a complementation group."""
        input_feature_symbols = self.input_cgroup_str.split('/')
        self.log.debug(f'Found these component symbols: {input_feature_symbols}.')
        for input_symbol in input_feature_symbols:
            feature_dict = {
                'input_symbol': input_symbol,
                'input_name': sgml_to_plain_text(input_symbol),    # Expected to match the feature.name of a feature in chado.
                'input_mapped_feature_id': None,                   # The feature_id for the feature that corresponds to the input feature symbol.
                'input_uniquename': None,                          # The uniquename for the feature that corresponds to the input feature symbol.
                'input_feature_replaced': False,                   # True if input allele replaced with an insertion.
                'at_locus': True,                                  # True if the feature can share a cgroup with a classical allele (so False for transgenic).
                'single_cgroup': True,                             # True if the feature should occupy only one cgroup (False for transgenic and aberrations).
                'feature_id': None,                                # The feature.feature_id for the component to report.
                'current_symbol': None,                            # The current symbol synonym.synonym_sgml (in SGML, Greeks converted to &agr; style).
                'uniquename': None,                                # The FlyBase ID for the component.
                'type': None,                                      # The CV term for the feature type.
                'org_abbr': None,                                  # The organism.abbreviation for the feature.
                'parental_gene_feature_id': None,                  # The feature.feature_id for the parental gene, if the feature is an FBal allele.
                'parental_gene_uniquename': None,                  # The FBgn ID for the parental gene, if the feature is an FBal allele.
                'parental_gene_name': None,                        # The feature.name for the parental gene.
                'is_new': False,                                   # True if the feature is a bogus symbol made by this script.
                'misexpression_element': False,                    # True if allele is a misexpression element.
            }
            filters = (
                Feature.is_obsolete.is_(False),
                Feature.is_analysis.is_(False),
                Feature.uniquename.op('~')(FEATURE_UNIQUENAME_REGEX),
                Feature.name == feature_dict['input_name'],
            )
            try:
                feature_result = session.query(Feature).filter(*filters).one()
                self._map_to_public_feature(session, feature_result, feature_dict)
                self._get_basic_feature_info(session, feature_dict)
            except NoResultFound:
                self._map_to_bogus_symbol(session, feature_dict)
            except MultipleResultsFound:
                self.errors.append(f'"{input_symbol}" has MANY features in chado')
                self.log.error(f'For "{input_symbol}", found MANY chado features.')
            self.features.append(feature_dict)
        return

    def _map_to_bogus_symbol(self, session, feature_dict):
        """Map the input symbol to a bogus symbol feature."""
        input_symbol = feature_dict["input_symbol"]
        if input_symbol == '+' or input_symbol.endswith('[+]') or input_symbol.endswith('[-]'):
            self.log.debug(f'Look for an internal "bogus symbol" feature for "{input_symbol}".')
            filters = (
                Feature.is_obsolete.is_(False),
                Feature.is_analysis.is_(False),
                Feature.name == feature_dict['input_name'],
                Feature.uniquename == Feature.name,
                Cvterm.name == 'bogus symbol',
            )
            try:
                component_result = session.query(Feature).\
                    select_from(Feature).\
                    join(Cvterm, (Cvterm.cvterm_id == Feature.type_id)).\
                    filter(*filters).\
                    one()
                feature_dict['current_symbol'] = feature_dict['input_name'].replace('<up>', '[').replace('</up>', ']')
                feature_dict['feature_id'] = component_result.feature_id
                feature_dict['uniquename'] = component_result.uniquename
                feature_dict['type'] = 'bogus symbol'
                self.log.debug(f'"{input_symbol}" corresponds to {feature_dict["uniquename"]}.')
            except NoResultFound:
                # Make a new bogus symbol feature if needed.
                # self.log.warning(f'No existing bogus symbol feature found; create one for "{input_symbol}".')
                org_id = 1
                if input_symbol == '+':
                    org_id = '1367'    # Corresponds to Unknown, which is what the old perl parser did.
                name_to_use = feature_dict['input_name']
                bogus_feature, _ = get_or_create(session, Feature, type_id=60494, organism_id=org_id, name=name_to_use, uniquename=input_symbol)
                feature_dict['current_symbol'] = feature_dict['input_name'].replace('<up>', '[').replace('</up>', ']')
                feature_dict['feature_id'] = bogus_feature.feature_id
                feature_dict['uniquename'] = feature_dict['input_name']
                feature_dict['type'] = 'bogus symbol'
                feature_dict['is_new'] = True
                self.log.warning(f'No existing feature for "bogus symbol" {input_symbol}", so one was created.')
        else:
            self.errors.append(f'"{input_symbol}" NOT in chado')
            self.log.error(f'For "{input_symbol}", could not find an existing chado feature or create a "bogus symbol" feature.')
        return

    def _map_to_public_feature(self, session, initial_feature, feature_dict):
        """Map the input feature to one that should be used for Alliance export."""
        feature_dict['input_mapped_feature_id'] = initial_feature.feature_id
        feature_dict['input_uniquename'] = initial_feature.uniquename
        # 1. Convert FBtp to associated insertion.
        if initial_feature.uniquename.startswith('FBtp'):
            construct = aliased(Feature, name='construct')
            insertion = aliased(Feature, name='insertion')
            filters = (
                construct.feature_id == feature_dict['input_mapped_feature_id'],
                insertion.is_obsolete.is_(False),
                insertion.uniquename.op('~')(FBTI_REGEX),
                insertion.is_analysis.is_(False),
                insertion.name.op('~')('unspecified$'),
                Cvterm.name == 'producedby',
                Pub.uniquename == 'FBrf0262355',
            )
            ins_to_report = session.query(insertion).\
                select_from(construct).\
                join(FeatureRelationship, (FeatureRelationship.object_id == construct.feature_id)).\
                join(insertion, (insertion.feature_id == FeatureRelationship.subject_id)).\
                join(Cvterm, (Cvterm.cvterm_id == FeatureRelationship.type_id)).\
                join(FeatureRelationshipPub, (FeatureRelationshipPub.feature_relationship_id == FeatureRelationship.feature_relationship_id)).\
                join(Pub, (Pub.pub_id == FeatureRelationshipPub.pub_id)).\
                filter(*filters).\
                one()
            feature_dict['feature_id'] = ins_to_report.feature_id
            feature_dict['input_feature_replaced'] = True
            self.feature_replaced = True
            feature_dict['at_locus'] = False
            msg = f'Convert "{initial_feature.name}" ({initial_feature.uniquename}) to "{ins_to_report.name}" ({ins_to_report.uniquename})'
            self.log.debug(msg)
            self.notes.append(msg)
            return
        # 2. For non-FBal features, just use the initial feature found.
        elif not initial_feature.uniquename.startswith('FBal'):
            feature_dict['feature_id'] = initial_feature.feature_id
            return
        # 3. For an FBal feature, look for an at-locus insertion.
        allele = aliased(Feature, name='allele')
        insertion = aliased(Feature, name='insertion')
        filters = (
            allele.feature_id == initial_feature.feature_id,
            insertion.is_obsolete.is_(False),
            insertion.uniquename.op('~')(FBTI_REGEX),
            insertion.is_analysis.is_(False),
            Cvterm.name == 'is_represented_at_alliance_as',
        )
        ins_to_report = session.query(insertion).\
            select_from(allele).\
            join(FeatureRelationship, (FeatureRelationship.subject_id == allele.feature_id)).\
            join(insertion, (insertion.feature_id == FeatureRelationship.object_id)).\
            join(Cvterm, (Cvterm.cvterm_id == FeatureRelationship.type_id)).\
            filter(*filters).\
            one_or_none()
        if ins_to_report:
            feature_dict['feature_id'] = ins_to_report.feature_id
            feature_dict['input_feature_replaced'] = True
            self.feature_replaced = True
            msg = f'Convert "{initial_feature.name}" ({initial_feature.uniquename}) to "{ins_to_report.name}" ({ins_to_report.uniquename})'
            self.log.debug(msg)
            self.notes.append(msg)
            return
        # 4. For an FBal feature, look for a single unspecified insertion for an associated construct.
        allele = aliased(Feature, name='allele')
        construct = aliased(Feature, name='construct')
        insertion = aliased(Feature, name='insertion')
        ac_rel_type = aliased(Cvterm, name='ac_rel_type')
        ic_rel_type = aliased(Cvterm, name='ic_rel_type')
        ac_rel = aliased(FeatureRelationship, name='ac_rel')
        ic_rel = aliased(FeatureRelationship, name='ic_rel')
        filters = (
            allele.feature_id == initial_feature.feature_id,
            construct.is_obsolete.is_(False),
            construct.uniquename.op('~')(FBTP_REGEX),
            construct.is_analysis.is_(False),
            insertion.is_obsolete.is_(False),
            insertion.uniquename.op('~')(FBTI_REGEX),
            insertion.is_analysis.is_(False),
            insertion.name.op('~')('unspecified$'),
            ac_rel_type.name == 'associated_with',
            ic_rel_type.name == 'producedby',
            Pub.uniquename == 'FBrf0262355',
        )
        results = session.query(construct, insertion).\
            select_from(allele).\
            join(ac_rel, (ac_rel.subject_id == allele.feature_id)).\
            join(construct, (construct.feature_id == ac_rel.object_id)).\
            join(ac_rel_type, (ac_rel_type.cvterm_id == ac_rel.type_id)).\
            join(ic_rel, (ic_rel.object_id == construct.feature_id)).\
            join(insertion, (insertion.feature_id == ic_rel.subject_id)).\
            join(ic_rel_type, (ic_rel_type.cvterm_id == ic_rel.type_id)).\
            join(FeatureRelationshipPub, (FeatureRelationshipPub.feature_relationship_id == ic_rel.feature_relationship_id)).\
            join(Pub, (Pub.pub_id == FeatureRelationshipPub.pub_id)).\
            filter(*filters).\
            distinct()
        cons_ins_dict = {}
        for result in results:
            cons_ins_dict[result.construct.feature_id] = result.insertion
        # 4a. If no construct-associated insertions, report the original allele.
        if len(cons_ins_dict.keys()) == 0:
            feature_dict['feature_id'] = initial_feature.feature_id
            return
        # 4b. If a single construct-associated insertion, report that insertion.
        elif len(cons_ins_dict.keys()) == 1:
            ins_to_report = list(cons_ins_dict.values())[0]
            feature_dict['feature_id'] = ins_to_report.feature_id
            feature_dict['input_feature_replaced'] = True
            self.feature_replaced = True
            feature_dict['at_locus'] = False
            msg = f'Convert "{initial_feature.name}" ({initial_feature.uniquename}) to "{ins_to_report.name}" ({ins_to_report.uniquename})'
            self.log.debug(msg)
            self.notes.append(msg)
            return
        else:
            filters = (
                Feature.feature_id.in_((cons_ins_dict.keys())),
                Pub.pub_id == self.pub_id
            )
            pub_asso_cons = session.query(Feature).\
                select_from(Feature).\
                join(FeaturePub, (FeaturePub.feature_id == Feature.feature_id)).\
                join(Pub, (Pub.pub_id == FeaturePub.pub_id)).\
                filter(*filters).\
                distinct()
            pub_asso_cons_ids = [i.feature_id for i in pub_asso_cons]
            # 4c. If a single construct associated with the pub, report that insertion.
            if len(pub_asso_cons_ids) == 1:
                specific_cons_id = pub_asso_cons_ids[0]
                ins_to_report = cons_ins_dict[specific_cons_id]
                feature_dict['feature_id'] = ins_to_report.feature_id
                feature_dict['input_feature_replaced'] = True
                self.feature_replaced = True
                feature_dict['at_locus'] = False
                msg = f'Convert "{initial_feature.name}" ({initial_feature.uniquename}) to "{ins_to_report.name}" ({ins_to_report.uniquename})'
                self.log.debug(msg)
                self.notes.append(msg)
                return
            # 4d. Do not map if there are many allele-associated constructs for the given pub.
            else:
                msg = f'{initial_feature.name} ({initial_feature.uniquename}) has ambiguous mapping to many constructs'
                self.log.debug(msg)
                self.errors.append(msg)
                return

    def _get_basic_feature_info(self, session, feature_dict):
        feature_type = aliased(Cvterm, name='feature_type')
        synonym_type = aliased(Cvterm, name='synonym_type')
        filters = (
            Feature.is_obsolete.is_(False),
            Feature.is_analysis.is_(False),
            Feature.uniquename.op('~')(FEATURE_UNIQUENAME_REGEX),
            Feature.feature_id == feature_dict['feature_id'],
            FeatureSynonym.is_current.is_(True),
            synonym_type.name == 'symbol',
        )
        component_result = session.query(Feature, feature_type, Organism, Synonym).\
            select_from(Feature).\
            join(Organism, (Organism.organism_id == Feature.organism_id)).\
            join(feature_type, (feature_type.cvterm_id == Feature.type_id)).\
            join(FeatureSynonym, (FeatureSynonym.feature_id == Feature.feature_id)).\
            join(Synonym, (Synonym.synonym_id == FeatureSynonym.synonym_id)).\
            join(synonym_type, (synonym_type.cvterm_id == Synonym.type_id)).\
            filter(*filters).\
            one()
        feature_dict['current_symbol'] = greek_to_sgml(component_result.Synonym.synonym_sgml)
        feature_dict['feature_id'] = component_result.Feature.feature_id
        feature_dict['uniquename'] = component_result.Feature.uniquename
        feature_dict['type'] = component_result.feature_type.name
        feature_dict['org_abbr'] = component_result.Organism.abbreviation
        self.log.debug(f'Input "{feature_dict["input_symbol"]}" corresponds to {feature_dict["uniquename"]}.')
        return

    def _get_parental_genes(self, session):
        """Get parental Drosophilid genes for each allele specified."""
        # Note - get the gene for the input allele, even if the allele is reported as an insertion.
        # self.log.debug(f'Getting parental gene(s) for this cgroup: "{self.input_cgroup_str}".')
        rel_type = aliased(Cvterm, name='rel_type')
        org_prop_type = aliased(Cvterm, name='org_prop_type')
        for feature_dict in self.features:
            if not feature_dict['input_uniquename']:
                continue
            input_symbol = feature_dict['input_symbol']
            if feature_dict['at_locus'] and feature_dict['input_uniquename'].startswith('FBal'):
                try:
                    filters = (
                        FeatureRelationship.subject_id == feature_dict['input_mapped_feature_id'],
                        rel_type.name == 'alleleof',
                        Feature.is_obsolete.is_(False),
                        Feature.is_analysis.is_(False),
                        Feature.uniquename.op('~')(FBGN_REGEX),
                        org_prop_type.name == 'taxgroup',
                        Organismprop.value == 'drosophilid',

                    )
                    gene_result = session.query(Feature).\
                        select_from(Feature).\
                        join(Organismprop, (Organismprop.organism_id == Feature.organism_id)).\
                        join(org_prop_type, (org_prop_type.cvterm_id == Organismprop.type_id)).\
                        join(FeatureRelationship, (FeatureRelationship.object_id == Feature.feature_id)).\
                        join(rel_type, (rel_type.cvterm_id == FeatureRelationship.type_id)).\
                        filter(*filters).\
                        one()
                    feature_dict['parental_gene_feature_id'] = gene_result.feature_id
                    feature_dict['parental_gene_uniquename'] = gene_result.uniquename
                    feature_dict['parental_gene_name'] = gene_result.name
                    self.log.debug(f'For "{input_symbol}", found this parental gene: {gene_result.name} ({gene_result.uniquename}).')
                except NoResultFound:
                    self.log.warning(f'Found NO parental genes for "{input_symbol}".')
                except MultipleResultsFound:
                    self.log.warning(f'Found MANY parental genes for "{input_symbol}".')
        return

    def _flag_in_vitro_alleles(self, session):
        """Flag in vitro alleles."""
        # self.log.debug(f'Flag alleles with "in vitro construct" annotations for this cgroup: "{self.input_cgroup_str}".')
        for feature_dict in self.features:
            if not feature_dict['feature_id']:
                continue
            input_symbol = feature_dict['input_symbol']
            # Skip assessment of feature already known to have an associated construct.
            if feature_dict['at_locus'] is False:
                continue
            if feature_dict['input_uniquename'] and feature_dict['input_uniquename'].startswith('FBal'):
                filters = (
                    FeatureCvterm.feature_id == feature_dict['input_mapped_feature_id'],
                    Cvterm.name == 'in vitro construct',
                )
                results = session.query(Cvterm).\
                    select_from(FeatureCvterm).\
                    join(Cvterm, (Cvterm.cvterm_id == FeatureCvterm.cvterm_id)).\
                    filter(*filters).\
                    distinct()
                for _ in results:
                    feature_dict['at_locus'] = False
            if feature_dict['at_locus'] is False:
                self.log.debug(f'Allele "{input_symbol}" has "in vitro construct" annotation.')
        return

    def _flag_misexpression_elements(self, session):
        """Flag misexpression alleles."""
        # self.log.debug(f'Flag misexpression alleles for this cgroup: "{self.input_cgroup_str}".')
        for feature_dict in self.features:
            if not feature_dict['feature_id']:
                continue
            input_symbol = feature_dict['input_symbol']
            if feature_dict['input_uniquename'] and feature_dict['input_uniquename'].startswith('FBal'):
                allele_feature = aliased(Feature, name='allele_feature')
                construct_feature = aliased(Feature, name='construct_feature')
                insertion_feature = aliased(Feature, name='insertion_feature')
                allele_insertion_rel = aliased(FeatureRelationship, name='allele_insertion_rel')
                insertion_construct_rel = aliased(FeatureRelationship, name='insertion_construct_rel')
                ai_rel_type = aliased(Cvterm, name='ai_rel_type')
                ic_rel_type = aliased(Cvterm, name='ic_rel_type')
                tool_type = aliased(Cvterm, name='tool_type')
                tool_rel = aliased(Cvterm, name='tool_rel')
                filters = (
                    allele_feature.feature_id == feature_dict['input_mapped_feature_id'],
                    construct_feature.uniquename.op('~')(FBTP_REGEX),
                    construct_feature.is_obsolete.is_(False),
                    insertion_feature.uniquename.op('~')(FBTI_REGEX),
                    insertion_feature.is_obsolete.is_(False),
                    ai_rel_type.name == 'associated_with',
                    ic_rel_type.name == 'producedby',
                    tool_type.name == 'misexpression element',
                    tool_rel.name == 'tool_uses'
                )
                results = session.query(allele_feature).\
                    select_from(allele_feature).\
                    join(allele_insertion_rel, (allele_insertion_rel.subject_id == allele_feature.feature_id)).\
                    join(insertion_feature, (insertion_feature.feature_id == allele_insertion_rel.object_id)).\
                    join(ai_rel_type, (ai_rel_type.cvterm_id == allele_insertion_rel.type_id)).\
                    join(insertion_construct_rel, (insertion_construct_rel.subject_id == insertion_feature.feature_id)).\
                    join(construct_feature, (construct_feature.feature_id == insertion_construct_rel.object_id)).\
                    join(ic_rel_type, (ic_rel_type.cvterm_id == insertion_construct_rel.type_id)).\
                    join(FeatureCvterm, (FeatureCvterm.feature_id == construct_feature.feature_id)).\
                    join(tool_type, (tool_type.cvterm_id == FeatureCvterm.cvterm_id)).\
                    join(FeatureCvtermprop, (FeatureCvtermprop.feature_cvterm_id == FeatureCvterm.feature_cvterm_id)).\
                    join(tool_rel, (tool_rel.cvterm_id == FeatureCvtermprop.type_id)).\
                    filter(*filters).\
                    distinct()
                for _ in results:
                    feature_dict['misexpression_element'] = True
                if feature_dict['misexpression_element'] is True:
                    self.log.debug(f'Allele "{input_symbol}" is a misexpression element.')
        return

    def _assess_single_group_alleles(self):
        """Assess genotype components that should be restricted to a single cgroup."""
        # self.log.debug(f'Assess genotype components that should be restricted to a single cgroup for this cgroup: "{self.input_cgroup_str}".')
        for feature_dict in self.features:
            if not feature_dict['feature_id']:
                continue
            input_symbol = feature_dict['input_symbol']
            if feature_dict['type'] == 'chromosome_structure_variation':
                feature_dict['single_cgroup'] = False
            elif feature_dict['at_locus'] is False:
                feature_dict['single_cgroup'] = False
            if feature_dict['single_cgroup'] is False:
                self.log.debug(f'"{input_symbol}" is allowed to occupy many complementation groups.')
        return

    def _check_cgroup_feature_count(self):
        """Check that a cgroup has only one or two associated features."""
        if len(self.features) > 2:
            self.errors.append(f'For "{self.input_cgroup_str}", more than the max of two features given for one cgroup')
            self.log.error(f'For "{self.input_cgroup_str}", more than the max of two features given for one cgroup.')
        verified_feature_ids = [i['feature_id'] for i in self.features if i['feature_id'] is not None]
        if len(verified_feature_ids) < len(self.features):
            self.errors.append(f'For "{self.input_cgroup_str}", could not verify all features given')
            self.log.error('Could not verify all features given.')
        return

    def _check_cgroup_gene_count(self):
        """Check that a cgroup contains alleles of only one gene."""
        cgroup_parental_genes = []
        for feature_dict in self.features:
            if feature_dict['parental_gene_feature_id']:
                self.gene_locus_id = feature_dict['parental_gene_uniquename']
                cgroup_parental_genes.append(feature_dict['parental_gene_uniquename'])
        cgroup_parental_genes = set(cgroup_parental_genes)
        if len(cgroup_parental_genes) > 1:
            self.gene_locus_id = None
            self.errors.append(f'For "{self.input_cgroup_str}", classical alleles of many different genes share a cgroup.')
            self.log.error('Alleles of many different genes share a cgroup.')
        return

    def _check_cgroup_for_mix_of_classical_and_transgenic_alleles(self):
        """Check that a cgroup does not mix classical and transgenic alleles."""
        at_locus = False
        not_at_locus = False
        for feature_dict in self.features:
            if feature_dict['feature_id'] and feature_dict['at_locus'] is True:
                at_locus = True
            elif feature_dict['feature_id'] and feature_dict['at_locus'] is False:
                not_at_locus = True
        if at_locus is True and not_at_locus is True:
            self.errors.append(f'For "{self.input_cgroup_str}", have a mix of classical and transgenic alleles.')
            self.log.error('Locus contains a mix of classical and transgenic alleles.')
        elif at_locus is True:
            self.at_locus = True
        return

    def _check_cgroup_bogus_symbol_count(self):
        """Check that a cgroup has a max of one bogus symbol feature."""
        bogus_symbols = []
        for feature_dict in self.features:
            if feature_dict['feature_id'] and feature_dict['type'] == 'bogus symbol':
                bogus_symbols.append(feature_dict['feature_id'])
        if len(bogus_symbols) > 1:
            self.errors.append(f'For "{self.input_cgroup_str}", more than one bogus symbol feature given')
            self.log.error('More than one bogus symbol feature given.')
        return

    def _check_bogus_symbol_matches_gene(self):
        """Check that a bogus symbol matches the locus of the classical allele."""
        allele_gene_name = None
        bogus_symbol_gene_name = None
        for feature_dict in self.features:
            if feature_dict['feature_id'] and feature_dict['type'] == 'bogus symbol':
                if feature_dict['input_name'].endswith('[+]'):
                    bogus_symbol_gene_name = feature_dict['input_name'].replace('[+]', '')
                elif feature_dict['input_name'].endswith('[-]'):
                    bogus_symbol_gene_name = feature_dict['input_name'].replace('[-]', '')
            elif feature_dict['feature_id'] and feature_dict['parental_gene_feature_id']:
                allele_gene_name = feature_dict['parental_gene_name']
        if allele_gene_name and bogus_symbol_gene_name and allele_gene_name != bogus_symbol_gene_name:
            self.errors.append(f'For "{self.input_cgroup_str}", bogus symbol does not match paired allele')
            self.log.error('Bogus symbol does not match paired allele.')
        return

    def _rank_cgroups(self):
        """Order cgroups."""
        # Skip problematic cgroups.
        if self.errors:
            return
        # Handle single feature cgroups.
        if len(self.features) == 1:
            self.rank_dict[0] = self.features[0]
            self.cgroup_name = self.rank_dict[0]['current_symbol']
            self.cgroup_desc = self.rank_dict[0]['uniquename']
            self.log.debug(f'cgroup_name="{self.cgroup_name}"')
            self.log.debug(f'cgroup_desc="{self.cgroup_desc}"')
            return
        # Handle two feature cgroups: homozygous.
        if self.features[0]['feature_id'] == self.features[1]['feature_id']:
            self.rank_dict[0] = self.features[0]
            self.rank_dict[1] = self.features[1]
        # Handle two feature cgroups: heterozygous.
        else:
            symbol_sorted_features = {}
            for feature_dict in self.features:
                symbol_sorted_features[feature_dict['current_symbol']] = feature_dict
            if self.features[0]['type'] == 'bogus symbol':
                self.rank_dict[0] = self.features[1]
                self.rank_dict[1] = self.features[0]
            elif self.features[1]['type'] == 'bogus symbol':
                self.rank_dict[0] = self.features[0]
                self.rank_dict[1] = self.features[1]
            else:
                sorted_symbols = sorted(symbol_sorted_features.keys())
                self.rank_dict[0] = symbol_sorted_features[sorted_symbols[0]]
                self.rank_dict[1] = symbol_sorted_features[sorted_symbols[1]]
        self.cgroup_name = f'{self.rank_dict[0]["current_symbol"]}/{self.rank_dict[1]["current_symbol"]}'
        self.cgroup_desc = '|'.join(sorted([i['uniquename'] for i in self.features]))
        self.log.debug(f'cgroup_name="{self.cgroup_name}"')
        self.log.debug(f'cgroup_desc="{self.cgroup_desc}"')
        return

    ###############################
    # Public Methods (Entry Point)
    ###############################

    def process_cgroup(self, session):
        """Run various ComplementationGroup methods in sequence."""
        self.log.debug(f'Processing cgroup {self.input_cgroup_str}')
        self._identify_feature(session)
        self._get_parental_genes(session)
        self._flag_in_vitro_alleles(session)
        self._flag_misexpression_elements(session)
        self._assess_single_group_alleles()
        self._check_cgroup_feature_count()
        self._check_cgroup_gene_count()
        self._check_cgroup_for_mix_of_classical_and_transgenic_alleles()
        self._check_cgroup_bogus_symbol_count()
        self._check_bogus_symbol_matches_gene()
        self._rank_cgroups()
        self.log.debug('Done initial parsing of cgroup.\n')
        return
