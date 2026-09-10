# !/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Utilities for processing genotypes.

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu

Notes:
    A GenotypeAnnotation object will check for data problems with a genotype,
    and, if there are no issues, find an existing genotype in chado, or create
    one. Creating a new genotype in chado involves not just adding to the
    genotype table, but also assigning an ID (genotype_dbxref), a current
    symbol (genotype_synonym), and the components (feature_genotype).
    While these objects can write directly to chado, they should be controlled
    by handlers that have a postgres Session object.

    A genotype can be given to a GenotypeAnnotation in either of two ways.

    1. As a name: a string of component SGML symbols (but using square
    brackets for sub/superscript) for alleles, aberrations, balancers (and
    rarely, constructs and insertions): e.g., &agr;Tub67C[3] (Greeks in sgml,
    superscript using square brackets). Features may also include internal
    "bogus symbol" features typically meant to represent an unspecified
    wildtype allele: e.g., "wg[+]". Components at the same locus should be
    separated by a "/" character, with spaces separating different loci. See
    curation rules for more details. This is the form curators type, and the
    form disease annotation proformae carry, so it is what those callers use.

    2. As components: cgroup-keyed lists of feature.feature_ids, straight from
    the feature_genotype table of a genotype already in chado. Callers
    re-assessing chado genotypes should use this form. Parsing a genotype's
    uniquename back into features is both slow (a symbol has to be looked up
    to get back to the feature_id that feature_genotype already holds) and
    ambiguous (a "/" in a component's own symbol is indistinguishable from
    the "/" that separates components at a locus).

    Both forms are checked and transformed by the same code once components
    have been identified: only the identification step differs.

    The per-component chado lookups live in component_lookup.py. Pass a
    PrefetchedComponentLookup when processing many genotypes; the default
    ComponentLookup queries chado per component, which is cheaper for one-offs
    but far too slow for a whole-database pass.

"""

import re
from collections import defaultdict
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from harvdev_utils.production import (
    Cv, Cvterm, Db, Dbxref, FeatureGenotype, Genotype, GenotypeCvterm,
    GenotypeDbxref, GenotypeSynonym, Pub, Synonym
)
from harvdev_utils.chado_functions import get_or_create
from harvdev_utils.char_conversions import sgml_to_plain_text, sub_sup_to_sgml
from harvdev_utils.genotype_utilities.component_lookup import (
    ComponentLookup, FeatureRef, FBAB_REGEX, FBAL_REGEX, FBBA_REGEX,
    FBGN_REGEX, FBGO_REGEX, FBTI_REGEX, FBTP_REGEX,
    FEATURE_UNIQUENAME_REGEX
)

# Names re-exported for callers that used to import them from this module.
__all__ = [
    'ChadoCache', 'ComplementationGroup', 'GenotypeAnnotation',
    'FBAB_REGEX', 'FBAL_REGEX', 'FBBA_REGEX', 'FBGN_REGEX', 'FBGO_REGEX',
    'FBTI_REGEX', 'FBTP_REGEX', 'FEATURE_UNIQUENAME_REGEX',
]


class ChadoCache:
    """Cache commonly used Chado DB objects to reduce repeated queries."""
    def __init__(self, session):
        """Create a ChadoCache object."""
        self.session = session
        self._flybase_db = None
        self._pub_unattributed = None
        self._synonym_symbol_cvterm = None
        self._alliance_compliant_cvterm = None

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

    @property
    def alliance_compliant_cvterm(self):
        """The "alliance_compliant" CV term from the "genotype characteristics" CV."""
        if self._alliance_compliant_cvterm is None:
            self._alliance_compliant_cvterm = (
                self.session.query(Cvterm)
                .join(Cv, Cv.cv_id == Cvterm.cv_id)
                .filter(Cvterm.name == 'alliance_compliant', Cv.name == 'genotype characteristics')
                .one()
            )
        return self._alliance_compliant_cvterm


class GenotypeAnnotation(object):
    """A genotype, its related data, and quality-check attributes."""
    def __init__(self, input_genotype_name, session, log, pub_id, input_components=None, lookup=None, cache=None):
        """Create a base GenotypeAnnotation from a genotype name, or from its components.

        Args:
            input_genotype_name (str): A string of component SGML symbols. When
                input_components is given this string is used only as a label
                for logging, so the chado genotype's uniquename is a good value.
            session (Session): SQLAlchemy session for the database from which to query and export.
            log (Logger): The logging object to use.
            pub_id (int): The relevant pub.pub_id; may be used for disambiguation.
            input_components (dict): Optional cgroup-keyed lists of feature.feature_ids,
                each list ordered by feature_genotype.rank. When given, the genotype is
                built from these rather than from input_genotype_name.
            lookup (ComponentLookup): Optional shared source of per-component chado facts.
            cache (ChadoCache): Optional shared cache of common chado objects.

        Returns:
            An object of the GenotypeAnnotation class.

        """
        self.input_genotype_name = input_genotype_name
        self.input_components = input_components    # Cgroup-keyed lists of feature_ids, when built from feature_genotype.
        self.log = log              # From a script using this class.
        self.pub_id = pub_id        # The pub.pub_id to be used for disambiguation.
        self.lookup = lookup if lookup is not None else ComponentLookup(log)
        self.cache = cache if cache is not None else ChadoCache(session)
        self.features = {}          # Feature_id-keyed dict of public features.
        self.input_features_replaced = {}    # Will be old FBal/FBtp ID to new FBti ID list of replacements.
        self.cgroup_list = []       # A list of ComplementationGroup objects derived from the input genotype.
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
        self.log.debug(f'Parse {self} into ComplementationGroups.')
        if self.input_components is not None:
            if not self.input_components:
                self.errors.append('Genotype has no feature_genotype components')
                self.log.error(f'For {self}, found no feature_genotype components.')
                return
            for cgroup_number in sorted(self.input_components.keys()):
                cgroup = ComplementationGroup.from_feature_ids(self.input_components[cgroup_number], self.log, self.pub_id, self.lookup)
                cgroup.process_cgroup(session)
                self.cgroup_list.append(cgroup)
        else:
            cgroup_symbols = self.input_genotype_name.split(' ')
            # self.log.debug(f'Found these cgroups: {cgroup_symbols}')
            for cgroup_symbol in cgroup_symbols:
                if cgroup_symbol != '':
                    cgroup = ComplementationGroup(cgroup_symbol, self.log, self.pub_id, self.lookup)
                    cgroup.process_cgroup(session)
                    self.cgroup_list.append(cgroup)
        for cgroup in self.cgroup_list:
            for feature_dict in cgroup.features:
                if feature_dict['feature_id'] is not None and feature_dict['type'] != 'bogus symbol':
                    self.features[feature_dict['feature_id']] = feature_dict
        return

    def _propagate_cgroup_notes_and_errors(self):
        """Propagate cgroup notes, warnings, and errors up to the genotype."""
        for cgroup in self.cgroup_list:
            self.notes.extend(cgroup.notes)
            self.warnings.extend(cgroup.warnings)
            self.errors.extend(cgroup.errors)
            for feature_dict in cgroup.features:
                for old_id, new_id in feature_dict['input_features_replaced'].items():
                    self.input_features_replaced[old_id] = new_id
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
            compatible_fbgn_ids = self.lookup.possible_genes_for_insertion(session, public_feature_ids[0])
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
        # The pair's components have already been identified, mapped and flagged, so the combined
        # cgroup reuses those feature dicts. Rebuilding it from a "donor/receptor" symbol string
        # would re-do all that work, and would split a component symbol that contains a "/".
        for donor_desc, receptor_desc in final_matches.items():
            donor_cgroup = cgroup_desc_dict[donor_desc]
            donor_feature = [i for i in donor_cgroup.features if i['uniquename'] and i['uniquename'].startswith('FBti')][0]
            receptor_cgroup = cgroup_desc_dict[receptor_desc]
            receptor_feature = [i for i in receptor_cgroup.features if i['uniquename'] and i['type'] != 'bogus symbol'][0]
            msg = f'Created new combined cgroup: {donor_feature["input_symbol"]}/{receptor_feature["input_symbol"]}'
            self.log.debug(msg)
            new_cgroup = ComplementationGroup.from_feature_dicts([donor_feature, receptor_feature], self.log, self.pub_id, self.lookup)
            new_cgroup.process_cgroup(session)
            new_cgroup_list.append(new_cgroup)
        self.cgroup_list = new_cgroup_list
        return

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
                self.log.warning(msg)
                self.warnings.append(msg)
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
        """Find a corresponding genotype in chado.

        The genotype.description is the match key: it is built from the FlyBase IDs of the
        genotype's components, so unlike genotype.uniquename it does not go stale when a
        component is renamed. check_genotypes.py derives it from feature_genotype and merges
        genotypes that share one, so it identifies a genotype.
        """
        if self.errors:
            return
        try:
            known_genotype = self.lookup.genotype_by_description(session, self.description)
        except MultipleResultsFound:
            msg = f'Many current genotypes with FBgo IDs have the description {self.description}'
            self.errors.append(msg)
            self.log.error(msg)
            return
        if known_genotype is None:
            self.is_new = True
            self.log.debug(f'Genotype {self} not found in chado.')
            return
        self.curie = known_genotype.curie
        self.genotype_id = known_genotype.genotype_id
        self.is_new = False
        self.log.debug(f'{self} matches {known_genotype.uniquename} (genotype_id={self.genotype_id}, {self.curie})')
        # The uniquename is the genotype's current symbol, and is what XORT matches on, so a
        # disagreement is worth seeing. It is not a reason to reject the match, though: it is
        # check_genotypes.py that recalculates uniquenames, and it may not have run since the
        # component was renamed. Recorded as a note so that it does not gate callers that stop
        # on warnings.
        if known_genotype.uniquename != self.uniquename:
            msg = f'Uniquename mismatch: chado_uniquename={known_genotype.uniquename}, calc_uniquename={self.uniquename}'
            self.notes.append(msg)
            self.log.warning(msg)
        self._mark_as_alliance_compliant(session)

    def _create_new_genotype(self, session):
        """Create a new entry in the chado genotype table."""
        if self.errors or not self.is_new:
            return
        # genotype.uniquename is unique, so check before inserting: a uniquename held by a
        # genotype with some other description would otherwise abort the whole transaction.
        uniquename_holder = self.lookup.genotype_by_uniquename(session, self.uniquename)
        if uniquename_holder is not None and uniquename_holder[1] != self.description:
            msg = f'Uniquename "{self.uniquename}" belongs to genotype_id={uniquename_holder[0]}, '
            msg += f'whose description is "{uniquename_holder[1]}", not "{self.description}"'
            self.errors.append(msg)
            self.log.error(msg)
            return
        new_chado_genotype, created = get_or_create(session, Genotype, uniquename=self.uniquename, description=self.description)
        if created is False:
            self.errors.append(f'Thought to be new, but corresponds to genotype_id={new_chado_genotype.genotype_id}')
            self.log.error(f'For {self}, initial attempt to find chado genotype missed this existing one: genotype_id={new_chado_genotype.genotype_id}')
            return
        else:
            geno_desc = f'genotype_id={new_chado_genotype.genotype_id}; uniquename="{new_chado_genotype.uniquename}"'
            geno_desc += f'; description="{new_chado_genotype.description}"'
            self.log.debug(f'For {self}, made this genotype: {geno_desc}')
        self.genotype_id = new_chado_genotype.genotype_id
        return

    def _assign_genotype_curie(self, session):
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
            db_id=self.cache.flybase_db.db_id,
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
        # Make the new genotype findable, so that a later genotype deriving to it is mapped
        # onto it rather than colliding with it.
        self.lookup.register_genotype(self.description, self.uniquename, self.genotype_id, self.curie)
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

    def _assign_genotype_symbol(self, session):
        """Assign the genotype a current symbol."""
        if self.errors or not self.is_new:
            return
        new_symbol, _ = get_or_create(
            session,
            Synonym,
            type_id=self.cache.synonym_symbol_cvterm.cvterm_id,
            name=self.uniquename,
            synonym_sgml=self.uniquename
        )
        get_or_create(
            session,
            GenotypeSynonym,
            genotype_id=self.genotype_id,
            synonym_id=new_symbol.synonym_id,
            pub_id=self.cache.pub_unattributed.pub_id
        )
        return

    def _mark_as_alliance_compliant(self, session):
        """Mark the genotype as Alliance compliant."""
        if self.errors:
            return
        # Many genotypes derive to the same compliant genotype, so check before writing.
        if self.lookup.is_alliance_compliant(session, self.genotype_id):
            return
        get_or_create(
            session,
            GenotypeCvterm,
            genotype_id=self.genotype_id,
            cvterm_id=self.cache.alliance_compliant_cvterm.cvterm_id,
            pub_id=self.cache.pub_unattributed.pub_id
        )
        self.lookup.register_alliance_compliant(self.genotype_id)
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
        self.log.debug('Done initial parsing of genotype.')
        return

    def get_known_or_create_new_genotype(self, session):
        """Find an existing genotype, or, create a new genotype plus a new ID, component entries, and a current symbol."""
        # Identify if the genotype is already in chado.
        self._find_known_genotype(session)
        # If not found in chado, create a new genotype in chado.
        if self.is_new is True:
            self._create_new_genotype(session)
            self._assign_genotype_curie(session)
            self._create_genotype_component_associations(session)
            self._assign_genotype_symbol(session)
            self._mark_as_alliance_compliant(session)
        return


class ComplementationGroup(object):
    """A complementation group of features that is part of a genotype."""
    def __init__(self, input_cgroup_str, log, pub_id, lookup=None):
        """Create a base ComplementationGroup.

        Args:
            input_cgroup_str (str): The components of the cgroup: e.g., "wg[1]/Df(2L)x".
            log (Logger): The logging object to use.
            pub_id (int): The pub.pub_id to use for disambiguation.
            lookup (ComponentLookup): Optional shared source of per-component chado facts.

        Returns:
            An object of the ComplementationGroup class.

        """
        self.input_cgroup_str = input_cgroup_str
        self.log = log                   # From a script using this class.
        self.pub_id = pub_id             # The pub.pub_id to use for disambiguation.
        self.lookup = lookup if lookup is not None else ComponentLookup(log)
        self.input_feature_ids = None    # Rank-ordered feature_ids, if the cgroup came from feature_genotype.
        self.preset_features = None      # Feature dicts, if the cgroup was made by combining two other cgroups.
        self.features = []               # Will be dicts with relevant feature info.
        self.feature_replaced = False    # Change to True if an input allele/construct is converted to an insertion.
        self.at_locus = False            # Change to True if there are at_locus features present.
        self.rank_dict = {}              # Will be rank-keyed feature dicts.
        self.cgroup_name = None          # Will be "correct" symbol for the cgroup from its components.
        self.cgroup_desc = None          # Will be sorted concatenation of component IDs.
        self.gene_locus_id = None        # Will be FBgn ID of gene if cgroup represents classical/insertion alleles of a gene.
        self.notes = []                  # Notes on mapping of specified feature to one more appropriate for Alliance submission.
        self.warnings = []               # Warnings about the cgroup.
        self.errors = []                 # Error messages: if any, the cgroup (and related genotype) should not be processed.

    @classmethod
    def from_feature_ids(cls, feature_ids, log, pub_id, lookup):
        """Create a ComplementationGroup from feature_genotype components.

        Args:
            feature_ids (list): feature.feature_ids of the cgroup's components, ordered by feature_genotype.rank.
            log (Logger): The logging object to use.
            pub_id (int): The pub.pub_id to use for disambiguation.
            lookup (ComponentLookup): The source of per-component chado facts.

        Returns:
            An object of the ComplementationGroup class.

        """
        cgroup = cls('', log, pub_id, lookup)
        cgroup.input_feature_ids = list(feature_ids)
        return cgroup

    @classmethod
    def from_feature_dicts(cls, feature_dicts, log, pub_id, lookup):
        """Create a ComplementationGroup from components already identified in other cgroups.

        Args:
            feature_dicts (list): Feature dicts from cgroups that have already been processed.
            log (Logger): The logging object to use.
            pub_id (int): The pub.pub_id to use for disambiguation.
            lookup (ComponentLookup): The source of per-component chado facts.

        Returns:
            An object of the ComplementationGroup class.

        """
        cgroup = cls('', log, pub_id, lookup)
        cgroup.preset_features = list(feature_dicts)
        return cgroup

    #####################
    # Internal Methods
    #####################

    @staticmethod
    def _new_feature_dict(input_symbol, input_name):
        """Make the dict in which everything known about one component is collected."""
        return {
            'input_symbol': input_symbol,
            'input_name': input_name,                          # Expected to match the feature.name of a feature in chado.
            'input_mapped_feature_id': None,                   # The feature_id for the feature that corresponds to the input feature symbol.
            'input_uniquename': None,                          # The uniquename for the feature that corresponds to the input feature symbol.
            'input_features_replaced': {},                     # Old ID - new ID replacement tracking.
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

    def _identify_feature(self, session):
        """Identify the chado feature for each symbol given in a complementation group."""
        input_feature_symbols = self.input_cgroup_str.split('/')
        self.log.debug(f'Found these component symbols: {input_feature_symbols}.')
        for input_symbol in input_feature_symbols:
            feature_dict = self._new_feature_dict(input_symbol, sgml_to_plain_text(input_symbol))
            # The dict is appended by reference here, then filled in by the steps below.
            self.features.append(feature_dict)
            # 1. Find the chado feature corresponding to the input symbol.
            # A "bogus symbol" is an option only here, when the input symbol matches no chado feature at all.
            try:
                initial_feature = self.lookup.feature_by_name(session, feature_dict['input_name'])
            except NoResultFound:
                self._map_to_bogus_symbol(session, feature_dict)
                continue
            except MultipleResultsFound:
                self.errors.append(f'"{input_symbol}" has MANY features in chado')
                self.log.error(f'For "{input_symbol}", found MANY chado features.')
                continue
            self._map_and_describe_feature(session, initial_feature, feature_dict)
        return

    def _identify_features_by_id(self, session):
        """Identify the chado feature for each component given as a feature_genotype feature_id."""
        self.log.debug(f'Found these component feature_ids: {self.input_feature_ids}.')
        for feature_id in self.input_feature_ids:
            feature_dict = self._new_feature_dict('', '')
            # The dict is appended by reference here, then filled in by the steps below.
            self.features.append(feature_dict)
            # 1. Get the details of the component feature that feature_genotype names.
            try:
                basics = self.lookup.component_basics(session, feature_id)
            except NoResultFound:
                self.errors.append(f'feature_id={feature_id} is not a feature that can be a genotype component')
                self.log.error(f'For feature_id={feature_id}, found no current feature that can be a genotype component.')
                continue
            except MultipleResultsFound:
                self.errors.append(f'feature_id={feature_id} has MANY current symbols in chado')
                self.log.error(f'For feature_id={feature_id}, found many current symbols.')
                continue
            feature_dict['input_symbol'] = basics['current_symbol']
            feature_dict['input_name'] = basics['name']
            # A "bogus symbol" component is reported as it is: there is nothing to map it to.
            if basics['type'] == 'bogus symbol':
                feature_dict['feature_id'] = feature_id
                feature_dict['current_symbol'] = basics['current_symbol']
                feature_dict['uniquename'] = basics['uniquename']
                feature_dict['type'] = basics['type']
                self.log.debug(f'feature_id={feature_id} is bogus symbol {basics["uniquename"]}.')
                continue
            initial_feature = FeatureRef(feature_id, basics['uniquename'], basics['name'])
            self._map_and_describe_feature(session, initial_feature, feature_dict)
        # Note the cgroup's components, for the messages that the check methods build.
        self.input_cgroup_str = '/'.join([i['input_symbol'] for i in self.features])
        return

    def _map_and_describe_feature(self, session, initial_feature, feature_dict):
        """Map an identified component to the feature to report, then describe that feature."""
        input_symbol = feature_dict['input_symbol']
        # 1. Map the identified feature to the feature to be reported.
        # A component that does correspond to a chado feature is never sent to _map_to_bogus_symbol(): if
        # the mapping fails, the component is left unmapped (feature_dict['feature_id'] stays None).
        try:
            self._map_to_public_feature(session, initial_feature, feature_dict)
        except NoResultFound:
            self.errors.append(f'"{input_symbol}" ({initial_feature.uniquename}) has NO feature to which it can be mapped')
            self.log.error(f'For "{input_symbol}" ({initial_feature.uniquename}), found NO feature to map it to.')
            return
        except MultipleResultsFound:
            self.errors.append(f'"{input_symbol}" ({initial_feature.uniquename}) maps to MANY features')
            self.log.error(f'For "{input_symbol}" ({initial_feature.uniquename}), found MANY features to map it to.')
            return
        # 2. Get details for the feature to be reported.
        try:
            self._get_basic_feature_info(session, feature_dict)
        except NoResultFound:
            self.errors.append(f'"{input_symbol}" maps to a feature having NO current symbol in chado')
            self.log.error(f'For "{input_symbol}", found no current symbol for feature_id={feature_dict["feature_id"]}.')
        except MultipleResultsFound:
            self.errors.append(f'"{input_symbol}" maps to a feature having MANY current symbols in chado')
            self.log.error(f'For "{input_symbol}", found many current symbols for feature_id={feature_dict["feature_id"]}.')
        return

    def _adopt_preset_features(self):
        """Take on components that were identified, mapped and flagged in other cgroups."""
        self.features = self.preset_features
        for feature_dict in self.features:
            if feature_dict['input_features_replaced']:
                self.feature_replaced = True
        self.input_cgroup_str = '/'.join([i['input_symbol'] for i in self.features])
        self.log.debug(f'Built cgroup "{self.input_cgroup_str}" from components of other cgroups.')
        return

    def _map_to_bogus_symbol(self, session, feature_dict):
        """Map the input symbol to a bogus symbol feature."""
        # For bogus symbols, keep SGML Greek representations.
        input_symbol = feature_dict['input_symbol']
        feature_dict['input_name'] = input_symbol
        if input_symbol == '+' or input_symbol.endswith('[+]') or input_symbol.endswith('[-]'):
            self.log.debug(f'Look for an internal "bogus symbol" feature for "{input_symbol}".')
            bogus_feature, is_new = self.lookup.bogus_feature(session, input_symbol)
            feature_dict['current_symbol'] = sub_sup_to_sgml(feature_dict['input_name'])
            feature_dict['feature_id'] = bogus_feature.feature_id
            feature_dict['uniquename'] = bogus_feature.uniquename
            feature_dict['type'] = 'bogus symbol'
            if is_new is True:
                feature_dict['is_new'] = True
                self.log.warning(f'No existing feature for bogus symbol {feature_dict["input_symbol"]}, so one was created.')
            else:
                self.log.debug(f'"{input_symbol}" corresponds to bogus symbol {feature_dict["uniquename"]}.')
        else:
            self.errors.append(f'"{input_symbol}" is NOT in chado, and no "bogus symbol" feature could be made for it')
            self.log.error(f'For "{input_symbol}", found no chado feature, and the symbol is not of a form for which a "bogus symbol" feature can be made.')
        return

    def _map_to_public_feature(self, session, initial_feature, feature_dict):
        """Map the input feature to one that should be used for Alliance export."""
        feature_dict['input_mapped_feature_id'] = initial_feature.feature_id
        feature_dict['input_uniquename'] = initial_feature.uniquename
        # 1. Convert FBtp to associated insertion.
        if initial_feature.uniquename.startswith('FBtp'):
            ins_to_report = self.lookup.construct_unspecified_insertion(session, initial_feature.feature_id)
            feature_dict['feature_id'] = ins_to_report.feature_id
            feature_dict['input_features_replaced'][feature_dict['input_uniquename']] = ins_to_report.uniquename
            self.feature_replaced = True
            feature_dict['at_locus'] = False
            msg = f'Convert "{initial_feature.name}" ({initial_feature.uniquename}) to "{ins_to_report.name}" ({ins_to_report.uniquename})'
            self.log.debug(msg)
            self.notes.append(msg)
            return
        # 2a. Convert FBba balancer to its parent FBab aberration.
        # Only FBba features flagged as usable balancers are mappable.
        elif initial_feature.uniquename.startswith('FBba'):
            aberr_to_report = self.lookup.balancer_aberration(session, initial_feature, feature_dict['input_symbol'])
            feature_dict['feature_id'] = aberr_to_report.feature_id
            feature_dict['input_features_replaced'][feature_dict['input_uniquename']] = aberr_to_report.uniquename
            self.feature_replaced = True
            msg = f'Convert "{initial_feature.name}" ({initial_feature.uniquename}) to "{aberr_to_report.name}" ({aberr_to_report.uniquename})'
            self.log.debug(msg)
            self.notes.append(msg)
            return
        # 2b. For non-FBal, non-FBba (balancer) features, just use the initial feature found.
        elif not initial_feature.uniquename.startswith('FBal'):
            feature_dict['feature_id'] = initial_feature.feature_id
            return
        # 3. For an FBal feature, look for an at-locus insertion.
        ins_to_report = self.lookup.alliance_insertion(session, initial_feature.feature_id)
        if ins_to_report:
            feature_dict['feature_id'] = ins_to_report.feature_id
            feature_dict['input_features_replaced'][feature_dict['input_uniquename']] = ins_to_report.uniquename
            self.feature_replaced = True
            msg = f'Convert "{initial_feature.name}" ({initial_feature.uniquename}) to "{ins_to_report.name}" ({ins_to_report.uniquename})'
            self.log.debug(msg)
            self.notes.append(msg)
            return
        # 4. For an FBal feature, look for a single unspecified insertion for an associated construct.
        cons_ins_dict = self.lookup.allele_construct_insertions(session, initial_feature.feature_id)
        # 4a. If no construct-associated insertions, report the original allele.
        if len(cons_ins_dict.keys()) == 0:
            feature_dict['feature_id'] = initial_feature.feature_id
            return
        # 4b. If a single construct-associated insertion, report that insertion.
        elif len(cons_ins_dict.keys()) == 1:
            feature_dict['at_locus'] = False
            ins_to_report = list(cons_ins_dict.values())[0]
            feature_dict['feature_id'] = ins_to_report.feature_id
            feature_dict['input_features_replaced'][feature_dict['input_uniquename']] = ins_to_report.uniquename
            self.feature_replaced = True
            msg = f'Convert "{initial_feature.name}" ({initial_feature.uniquename}) to "{ins_to_report.name}" ({ins_to_report.uniquename})'
            self.log.debug(msg)
            self.notes.append(msg)
            return
        else:
            feature_dict['at_locus'] = False
            pub_asso_cons_ids = self.lookup.constructs_for_pub(session, cons_ins_dict.keys(), self.pub_id)
            # 4c. If a single construct associated with the pub, report that insertion.
            if len(pub_asso_cons_ids) == 1:
                specific_cons_id = pub_asso_cons_ids[0]
                ins_to_report = cons_ins_dict[specific_cons_id]
                feature_dict['feature_id'] = ins_to_report.feature_id
                feature_dict['input_features_replaced'][feature_dict['input_uniquename']] = ins_to_report.uniquename
                self.feature_replaced = True
                msg = f'Convert "{initial_feature.name}" ({initial_feature.uniquename}) to "{ins_to_report.name}" ({ins_to_report.uniquename})'
                self.log.debug(msg)
                self.notes.append(msg)
                return
            # 4d. Do not map if there are many allele-associated constructs for the given pub.
            else:
                msg = f'{initial_feature.name} ({initial_feature.uniquename}) has ambiguous mapping to many constructs'
                self.log.warning(msg)
                self.warnings.append(msg)
                return

    def _get_basic_feature_info(self, session, feature_dict):
        if feature_dict['feature_id'] is None:
            return
        basics = self.lookup.feature_basics(session, feature_dict['feature_id'])
        feature_dict['current_symbol'] = basics['current_symbol']
        feature_dict['uniquename'] = basics['uniquename']
        feature_dict['type'] = basics['type']
        feature_dict['org_abbr'] = basics['org_abbr']
        self.log.debug(f'Input "{feature_dict["input_symbol"]}" corresponds to {feature_dict["uniquename"]}.')
        return

    def _get_parental_genes(self, session):
        """Get parental Drosophilid genes for each allele specified."""
        # Note - get the parental gene for the input allele, even if the allele is converted to an insertion in the output genotype.
        # self.log.debug(f'Getting parental gene(s) for this cgroup: "{self.input_cgroup_str}".')
        for feature_dict in self.features:
            # Skip undetermined features.
            if not feature_dict['input_uniquename'] or not feature_dict['uniquename']:
                continue
            # Skip non-at-locus or non-FBal features.
            if not feature_dict['at_locus'] or not feature_dict['input_uniquename'].startswith('FBal'):
                continue
            input_symbol = feature_dict['input_symbol']
            try:
                parent_gene = self.lookup.parental_gene(session, feature_dict['input_mapped_feature_id'])
                feature_dict['parental_gene_feature_id'] = parent_gene.feature_id
                feature_dict['parental_gene_uniquename'] = parent_gene.uniquename
                feature_dict['parental_gene_name'] = parent_gene.name
                self.log.debug(f'For "{input_symbol}", found this parental gene: {parent_gene.name} ({parent_gene.uniquename}).')
            except NoResultFound:
                # This only occurs for non-Drosophilid genes, for which we do not want the parental gene.
                pass
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
                if self.lookup.is_in_vitro(session, feature_dict['input_mapped_feature_id']):
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
                if self.lookup.is_misexpression_element(session, feature_dict['input_mapped_feature_id']):
                    feature_dict['misexpression_element'] = True
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
            self.warnings.append(f'For "{self.input_cgroup_str}", classical alleles of many different genes share a cgroup.')
            self.log.warning('Alleles of many different genes share a cgroup.')
        return

    def _check_cgroup_for_mix_of_classical_and_transgenic_alleles(self):
        """Check that a cgroup does not mix classical and transgenic alleles."""
        at_locus = False
        not_at_locus = False
        for feature_dict in self.features:
            if feature_dict['feature_id'] and feature_dict['at_locus'] is True and feature_dict['type'] != 'bogus symbol':
                at_locus = True
            elif feature_dict['feature_id'] and feature_dict['at_locus'] is False:
                not_at_locus = True
        if at_locus is True and not_at_locus is True:
            self.warnings.append(f'For "{self.input_cgroup_str}", have a mix of classical and transgenic alleles.')
            self.log.warning('Locus contains a mix of classical and transgenic alleles.')
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
            self.warnings.append(f'For "{self.input_cgroup_str}", bogus symbol does not match paired allele')
            self.log.warning('Bogus symbol does not match paired allele.')
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
        if self.preset_features is not None:
            # These components carry the flags they were given in the cgroups they came from.
            self._adopt_preset_features()
        else:
            if self.input_feature_ids is not None:
                self._identify_features_by_id(session)
            else:
                self._identify_feature(session)
            self._flag_in_vitro_alleles(session)
            self._flag_misexpression_elements(session)
            self._get_parental_genes(session)
        self._assess_single_group_alleles()
        self._check_cgroup_feature_count()
        self._check_cgroup_gene_count()
        self._check_cgroup_for_mix_of_classical_and_transgenic_alleles()
        self._check_cgroup_bogus_symbol_count()
        self._check_bogus_symbol_matches_gene()
        self._rank_cgroups()
        self.log.debug('Done initial parsing of cgroup.')
        return
