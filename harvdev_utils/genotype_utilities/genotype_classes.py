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
    alleles, aberrations, balancers (and rarely, constructs and insertions).
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

from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from harvdev_utils.production import (
    Cv, Cvterm, Db, Dbxref, Feature, FeatureCvterm, FeatureCvtermprop,
    FeatureGenotype, FeatureRelationship, FeatureSynonym, Genotype,
    GenotypeDbxref, GenotypeSynonym, Organism, Pub, Synonym
)
from harvdev_utils.chado_functions import get_or_create
from harvdev_utils.char_conversions import sgml_to_plain_text, greek_to_sgml


class GenotypeAnnotation(object):
    """A genotype, its related data, and quality-check attributes."""
    global log

    def __init__(self, input_genotype_name):
        """Create a base GenotypeAnnotation from a genotype name.

        Args:
            input_genotype_name (str): A string of component SGML symbols.

        Returns:
            An object of the GenotypeAnnotation class.

        """
        self.input_genotype_name = input_genotype_name
        self.features = {}          # Feature_id-keyed dict of component info.
        self.cgroup_list = []       # A list of ComplementationGroup objects.
        self.cgroup_dict = {}       # Cgroup-keyed ComplementationGroups.
        self.uniquename = None      # Recomputed uniquename (symbols sorted).
        self.description = None     # Description based on feature IDs.
        self.curie = None           # FBgo ID (existing or created anew).
        self.genotype_id = None     # genotype.genotype_id (existing or new).
        self.is_new = None          # Becomes False if in chado, True if not.
        self.warnings = []          # Warnings about the genotype.
        self.errors = []            # Errors (QC fails) that stop processing.

    def _parse_cgroups(self, session):
        """Parse the input genotype into ComplementationGroups."""
        log.debug(f'BOB: Parse {self} into ComplementationGroups.\n')
        cgroup_symbols = self.input_genotype_name.split(' ')
        # log.debug(f'Found these cgroups: {cgroup_symbols}')
        for cgroup_symbol in cgroup_symbols:
            if cgroup_symbol != '':
                cgroup = ComplementationGroup(cgroup_symbol)
                cgroup.process_cgroup(session)
                self.cgroup_list.append(cgroup)
        for cgroup in self.cgroup_list:
            for feature_dict in cgroup.features:
                if feature_dict['feature_id'] is not None:
                    self.features['feature_id'] = feature_dict
        return

    def _check_multi_cgroup_genes(self):
        """Look for genes of "single_cgroup" features in many cgroups."""
        GENE_NAME = 0
        GENE_CURIE = 1
        gene_cgroup_counter = {}
        for cgroup in self.cgroup_list:
            cgroup_genes = []
            for feature_dict in cgroup.features:
                if feature_dict['single_cgroup'] is True:
                    if feature_dict['parental_gene_feature_id'] is not None:
                        gene_name = feature_dict['parental_gene_name']
                        gene_curie = feature_dict['parental_gene_curie']
                        cgroup_rank_gene = (gene_name, gene_curie)
                        cgroup_genes.append(cgroup_rank_gene)
            cgroup_genes = set(cgroup_genes)
            for cgroup_gene in cgroup_genes:
                try:
                    gene_cgroup_counter[cgroup_gene] += 1
                except KeyError:
                    gene_cgroup_counter[cgroup_gene] = 1
        # log.debug(f'{self}, have parental genes: {gene_cgroup_counter}')
        for gene, count in gene_cgroup_counter.items():
            if count > 1:
                msg = f'Classical alleles for {gene[GENE_NAME]} '
                msg += f'({gene[GENE_CURIE]}) '
                msg += f'are listed in {count} different cgroups'
                log.error(msg)
                self.errors.append(msg)
        return

    def _propagate_cgroup_errors(self):
        """Propagate cgroup errors up to the genotype."""
        for cgroup in self.cgroup_list:
            self.errors.extend(cgroup.errors)
        return

    def _calculate_genotype_uniquename(self):
        """Calculate the genotype uniquename."""
        if not self.errors:
            cgroups_by_name = {}
            for cgroup in self.cgroup_list:
                try:
                    cgroups_by_name[cgroup.cgroup_name].append(cgroup)
                except KeyError:
                    cgroups_by_name[cgroup.cgroup_name] = [cgroup]
            sorted_cgroup_names = sorted(cgroups_by_name.keys())
            cgroup_number = 0
            for cgroup_name in sorted_cgroup_names:
                for cgroup in cgroups_by_name[cgroup_name]:
                    self.cgroup_dict[cgroup_number] = cgroup
                    cgroup_number += 1
            self.uniquename = ' '.join(sorted_cgroup_names)
            log.debug(f'{self}, have this cgroup ordering.')
            for cgroup_number, cgroup in self.cgroup_dict.items():
                log.debug(f'cgroup={cgroup_number}, name={cgroup.cgroup_name}')
            log.debug(f'Calculated this uniquename: {self.uniquename}')
        return

    def _calculate_genotype_desc(self):
        """Calculate the genotype description."""
        if not self.errors:
            cgroup_descs = sorted([i.cgroup_desc for i in self.cgroup_list])
            self.description = '_'.join(cgroup_descs)
            log.debug(f'Calculated this description: {self.description}')
        return

    def process_genotype_annotation(self, session):
        """Run various GenotypeAnnotation methods in the correct order."""
        log.debug(f'Processing input genotype {self.input_genotype_name}.')
        self._parse_cgroups(session)
        self._check_multi_cgroup_genes()
        self._propagate_cgroup_errors()
        self._calculate_genotype_uniquename()
        self._calculate_genotype_desc()
        log.debug('Done initial parsing of genotype.\n\n\n')
        return

    def _find_known_genotype(self, session):
        """Find a corresponding genotype in chado."""
        if self.errors:
            return
        filters = (
            Genotype.uniquename == self.uniquename,
            Genotype.is_obsolete.is_(False),
            GenotypeDbxref.is_current.is_(True),
            Dbxref.accession.op('~')(r'^FBgo[0-9]{7}$'),
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
            log.debug(f'{self} matches {chado_genotype.Genotype.uniquename} (genotype_id={chado_genotype.Genotype.genotype_id})')
            if chado_genotype.Genotype.description == self.description:
                self.curie = chado_genotype.Dbxref.accession
                self.genotype_id = chado_genotype.Genotype.genotype_id
                self.is_new = False
                log.debug(f'The descriptions for the curated and chado genotype are identical: {self.description}.')
            else:
                self.errors.append(f'Description mismatch: chado_desc={chado_genotype.Genotype.description}, calc_desc={self.description}.')
                log.error(f'Description mismatch: chado_desc={chado_genotype.Genotype.description}, calc_desc={self.description}.')
        else:
            self.is_new = True
            log.debug(f'Could not find genotype {self} in chado.')

    def _create_new_genotype(self, session):
        """Create a new entry in the chado genotype table."""
        if self.errors or self.is_new is False or self.is_new is None:
            return
        new_chado_genotype, created = get_or_create(session, Genotype, uniquename=self.uniquename, description=self.description)
        if created is False:
            self.errors.append(f'Thought to be new, but corresponds to genotype_id={new_chado_genotype.genotype_id}')
            log.error(f'For {self}, initial attempt to find chado genotype missed this existing one: genotype_id={new_chado_genotype.genotype_id}')
            return
        else:
            log.debug(f'For {self}, made this genotype: {new_chado_genotype}')
        self.genotype_id = new_chado_genotype.genotype_id
        return

    def _assign_genotype_curie(self, session):
        """Assign a FlyBase curie to the genotype."""
        filters = (
            Db.name == 'FlyBase',
        )
        flybase_db = session.query(Db).filter(*filters).one()
        new_fbgo_query = "SELECT nextval('genotype_curie_seq');"
        new_fbgo_int = session.execute(new_fbgo_query).one()[0]
        new_fbgo_id = f'FBgo{str(new_fbgo_int).zfill(7)}'
        new_xref, created = get_or_create(session, Dbxref, db_id=flybase_db.db_id, accession=new_fbgo_id)
        if created is False:
            log.error(f'{new_xref.accession} should be new, but it already exists? ID minting is malfunctioning.')
            raise Exception
        log.debug(f'For {self}, reserved new ID: {new_xref.accession}')
        _, _ = get_or_create(session, GenotypeDbxref, genotype_id=self.genotype_id, dbxref_id=new_xref.dbxref_id)
        self.curie = new_xref.accession
        return

    def _create_genotype_component_associations(self, session):
        """Create genotype component entries."""
        for cgroup_number, cgroup in self.cgroup_dict.items():
            for feat_rank, feature_dict in cgroup.rank_dict.items():
                _, created = get_or_create(session, FeatureGenotype, genotype_id=self.genotype_id, feature_id=feature_dict['feature_id'],
                                           cgroup=cgroup_number, rank=feat_rank, cvterm_id=60468, chromosome_id=23159230)
        return

    def _assign_genotype_symbol(self, session):
        """Assign the genotype a current symbol."""
        # Record the official symbol synonym.
        filters = (Pub.uniquename == 'unattributed', )
        unattr_pub = session.query(Pub).filter(*filters).one()
        filters = (
            Cvterm.name == 'symbol',
            Cv.name == 'synonym type',
        )
        synonym_cvterm = session.query(Cvterm).\
            select_from(Cvterm).\
            join(Cv, (Cv.cv_id == Cvterm.cv_id)).\
            filter(*filters).\
            one()
        new_symbol, _ = get_or_create(session, Synonym, type_id=synonym_cvterm.cvterm_id, name=self.uniquename, synonym_sgml=self.uniquename)
        _, _ = get_or_create(session, GenotypeSynonym, genotype_id=self.genotype_id, synonym_id=new_symbol.synonym_id, pub_id=unattr_pub.pub_id)
        return

    def get_known_or_create_new_genotype(self, session):
        """Find an existing genotype, or, create a new genotype plus a new ID, component entries, and a current symbol."""
        self._find_known_genotype(session)
        self._create_new_genotype(session)
        self._assign_genotype_curie(session)
        self._create_genotype_component_associations(session)
        self._assign_genotype_symbol(session)
        return

    def __str__(self):
        """Informative string for this genotype for logging purposes."""
        return self.input_genotype_name


class ComplementationGroup(object):
    """A complementation group of features that is part of a genotype."""
    global log

    def __init__(self, input_cgroup_str):
        """Create a base ComplementationGroup.

        Args:
            input_cgroup_str (str): The components of the cgroup: e.g., "wg[1]/Df(2L)x".

        Returns:
            An object of the ComplementationGroup class.

        """
        self.input_cgroup_str = input_cgroup_str
        self.features = []         # Will be dicts with relevant feature info.
        self.rank_dict = {}        # Will be rank-keyed feature dicts.
        self.cgroup_name = None    # Will be "correct" symbol for the cgroup from its components.
        self.cgroup_desc = None    # Will be sorted concatenation of component IDs.
        self.errors = []           # Error messages: if any, the cgroup (and related genotype) should not be processed.

    def _get_feature_info(self, session):
        """Query chado for relevant feature info given a symbol."""
        input_feature_symbols = self.input_cgroup_str.split('/')
        log.debug(f'Found these component symbols: {input_feature_symbols}.')
        for input_symbol in input_feature_symbols:
            feature_dict = {
                'input_symbol': input_symbol,
                'name': sgml_to_plain_text(input_symbol),    # Expected to match the feature.name of a feature in chado.
                'current_symbol': None,                      # The current symbol synonym.synonym_sgml in chado.
                'feature_id': None,                          # The feature.feature_id for the component.
                'uniquename': None,                          # The FlyBase ID for the component.
                'type': None,                                # The CV term for the feature type.
                'org_abbr': None,                            # The organism.abbreviation for the feature.
                'parental_gene_feature_id': None,            # The feature.feature_id for the parental gene, if the feature is an FBal allele.
                'parental_gene_curie': None,                 # The FBgn ID for the parental gene, if the feature is an FBal allele.
                'parental_gene_name': None,                  # The feature.name for the parental gene.
                'is_new': False,                             # True if the feature is a bogus symbol made by this script.
                'has_constructs': False,                     # True if allele has related FBtp.
                'in_vitro': False,                           # True if allele has "in vitro construct" annotation.
                'binary_driver': False,                      # True if allele is a binary driver.
                'misexpression_element': False,              # True if allele is a misexpression element.
                'single_cgroup': True,                       # False if the component can be present in many cgroups.
                'has_pub_association': None,                 # True or False; left as None for internal bogus symbol features.
            }
            # First, identify a public feature (allele, aberration, balancer, construct or insertion).
            feature_type = aliased(Cvterm, name='feature_type')
            synonym_type = aliased(Cvterm, name='synonym_type')
            filters = (
                Feature.is_obsolete.is_(False),
                Feature.is_analysis.is_(False),
                Feature.uniquename.op('~')(r'^FB(al|ab|ba|ti|tp)[0-9]{7}$'),
                Feature.name == feature_dict['name'],
                FeatureSynonym.is_current.is_(True),
                synonym_type.name == 'symbol',
            )
            try:
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
                log.debug(f'"{input_symbol}" corresponds to {feature_dict["uniquename"]}.')
            except NoResultFound:
                # log.debug(f'Could not find a current public feature for "{input_symbol}".')
                # Second, if no public feature, look for a bogus symbol feature, if applicable.
                if input_symbol == '+' or input_symbol.endswith('[+]') or input_symbol.endswith('[-]'):
                    log.debug(f'Look for an internal "bogus symbol" feature for "{input_symbol}".')
                    filters = (
                        Feature.is_obsolete.is_(False),
                        Feature.is_analysis.is_(False),
                        Feature.name == feature_dict['input_symbol'],
                        Feature.uniquename == Feature.name,
                        Cvterm.name == 'bogus symbol',
                    )
                    try:
                        component_result = session.query(Feature).\
                            select_from(Feature).\
                            join(Cvterm, (Cvterm.cvterm_id == Feature.type_id)).\
                            filter(*filters).\
                            one()
                        feature_dict['name'] = input_symbol
                        feature_dict['current_symbol'] = input_symbol.replace('[', '<up>').replace(']', '</up>')
                        feature_dict['feature_id'] = component_result.feature_id
                        feature_dict['uniquename'] = component_result.uniquename
                        feature_dict['type'] = 'bogus symbol'
                        log.debug(f'"{input_symbol}" corresponds to {feature_dict["uniquename"]}.')
                    except NoResultFound:
                        # Third, make a new bogus symbol feature if needed.
                        # log.warning(f'No existing bogus symbol feature found; create one for "{input_symbol}".')
                        org_id = 1
                        if input_symbol == '+':
                            org_id = '1367'    # Corresponds to Unknown, which is what the old perl parser did.
                        bogus_feature, _ = get_or_create(session, Feature, type_id=60494, organism_id=org_id, name=input_symbol, uniquename=input_symbol)
                        feature_dict['name'] = input_symbol
                        feature_dict['current_symbol'] = input_symbol.replace('[', '<up>').replace(']', '</up>')
                        feature_dict['feature_id'] = bogus_feature.feature_id
                        feature_dict['uniquename'] = input_symbol
                        feature_dict['type'] = 'bogus symbol'
                        feature_dict['is_new'] = True
                        log.warning(f'No existing feature for "bogus symbol" {input_symbol}", so one was created.')
                # Fourth, if no feature found, note this in the errors list.
                else:
                    self.errors.append(f'"{input_symbol}" NOT in chado')
                    log.error(f'For "{input_symbol}", could not find an existing chado feature or create a "bogus symbol" feature.')
            self.features.append(feature_dict)
        return

    def _get_parental_genes(self, session):
        """Get parental genes for alleles."""
        # log.debug(f'Getting parental gene(s) for this cgroup: "{self.input_cgroup_str}".')
        for feature_dict in self.features:
            input_symbol = feature_dict['input_symbol']
            if feature_dict['uniquename'] and feature_dict['uniquename'].startswith('FBal'):
                try:
                    filters = (
                        Feature.is_obsolete.is_(False),
                        Feature.is_analysis.is_(False),
                        Feature.uniquename.op('~')(r'^FBgn[0-9]{7}$'),
                        Cvterm.name == 'alleleof',
                        FeatureRelationship.subject_id == feature_dict['feature_id'],
                    )
                    gene_result = session.query(Feature).\
                        select_from(Feature).\
                        join(FeatureRelationship, (FeatureRelationship.object_id == Feature.feature_id)).\
                        join(Cvterm, (Cvterm.cvterm_id == FeatureRelationship.type_id)).\
                        filter(*filters).\
                        one()
                    feature_dict['parental_gene_feature_id'] = gene_result.feature_id
                    feature_dict['parental_gene_curie'] = gene_result.uniquename
                    feature_dict['parental_gene_name'] = gene_result.name
                    log.debug(f'For "{input_symbol}", found this parental gene: {gene_result.name} ({gene_result.uniquename}).')
                except NoResultFound:
                    log.warning(f'Found NO parental genes for "{input_symbol}".')
                except MultipleResultsFound:
                    log.warning(f'Found MANY parental genes for "{input_symbol}".')
        return

    def _flag_transgenic_alleles(self, session):
        """Flag transgenic alleles."""
        # log.debug(f'Flag alleles related to constructs for this cgroup: "{self.input_cgroup_str}".')
        for feature_dict in self.features:
            if feature_dict['feature_id'] and feature_dict['uniquename'].startswith('FBal'):
                input_symbol = feature_dict['input_symbol']
                filters = (
                    FeatureRelationship.subject_id == feature_dict['feature_id'],
                    Feature.is_obsolete.is_(False),
                    Feature.is_analysis.is_(False),
                    Feature.uniquename.op('~')(r'^FBtp[0-9]{7}$'),
                    Cvterm.name == 'associated_with',
                )
                results = session.query(Feature).\
                    select_from(Feature).\
                    join(FeatureRelationship, (FeatureRelationship.object_id == Feature.feature_id)).\
                    join(Cvterm, (Cvterm.cvterm_id == FeatureRelationship.type_id)).\
                    filter(*filters).\
                    distinct()
                for _ in results:
                    feature_dict['has_constructs'] = True
            if feature_dict['has_constructs'] is True:
                log.debug(f'Allele "{input_symbol}" has associated constructs.')
        return

    def _flag_in_vitro_alleles(self, session):
        """Flag in vitro alleles."""
        # log.debug(f'Flag alleles with "in vitro construct" annotations for this cgroup: "{self.input_cgroup_str}".')
        for feature_dict in self.features:
            if feature_dict['feature_id'] and feature_dict['uniquename'].startswith('FBal'):
                input_symbol = feature_dict['input_symbol']
                filters = (
                    Feature.uniquename == feature_dict['uniquename'],
                    Cvterm.name == 'in vitro construct',
                )
                results = session.query(Cvterm).\
                    select_from(Feature).\
                    join(FeatureCvterm, (FeatureCvterm.feature_id == Feature.feature_id)).\
                    join(Cvterm, (Cvterm.cvterm_id == FeatureCvterm.cvterm_id)).\
                    filter(*filters).\
                    distinct()
                for _ in results:
                    feature_dict['in_vitro'] = True
            if feature_dict['in_vitro'] is True:
                log.debug(f'Allele "{input_symbol}" has "in vitro construct" annotation.')
        return

    def _flag_binary_drivers(self, session):
        """Flag drivers, like GAL4."""
        # log.debug(f'Flag drivers, like GAL4, for this cgroup: "{self.input_cgroup_str}".')
        for feature_dict in self.features:
            if feature_dict['uniquename'] and feature_dict['uniquename'].startswith('FBal'):
                if not feature_dict['parental_gene_feature_id']:
                    continue
                input_symbol = feature_dict['input_symbol']
                filters = (
                    FeatureCvterm.feature_id == feature_dict['parental_gene_feature_id'],
                    Cvterm.name.op('~')(r'^binary expression system.+driver$'),
                )
                results = session.query(Cvterm).\
                    select_from(FeatureCvterm).\
                    join(Cvterm, Cvterm.cvterm_id == FeatureCvterm.cvterm_id).\
                    filter(*filters).\
                    distinct()
                for _ in results:
                    feature_dict['binary_driver'] = True
            if feature_dict['binary_driver'] is True:
                log.debug(f'Allele "{input_symbol}" is a binary driver.')
        return

    def _flag_misexpression_elements(self, session):
        """Flag misexpression alleles."""
        # log.debug(f'Flag misexpression alleles for this cgroup: "{self.input_cgroup_str}".')
        for feature_dict in self.features:
            if feature_dict['uniquename'] and feature_dict['uniquename'].startswith('FBal'):
                input_symbol = feature_dict['input_symbol']
                construct_uname_regex = r'^FBtp[0-9]{7}$'
                insertion_uname_regex = r'^FBti[0-9]{7}$'
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
                    allele_feature.feature_id == feature_dict['feature_id'],
                    construct_feature.uniquename.op('~')(construct_uname_regex),
                    construct_feature.is_obsolete.is_(False),
                    insertion_feature.uniquename.op('~')(insertion_uname_regex),
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
                    log.debug(f'Allele "{input_symbol}" is a misexpression element.')
        return

    def _assess_single_group_alleles(self):
        """Assess genotype components that should be restricted to a single cgroup."""
        # log.debug(f'Assess genotype components that should be restricted to a single cgroup for this cgroup: "{self.input_cgroup_str}".')
        for feature_dict in self.features:
            if not feature_dict['uniquename']:
                continue
            input_symbol = feature_dict['input_symbol']
            if feature_dict['type'] in ['transgenic_transposable_element', 'chromosome_structure_variation']:
                feature_dict['single_cgroup'] = False
            elif feature_dict['type'] == 'allele':
                if feature_dict['org_abbr'] != 'Dmel':
                    feature_dict['single_cgroup'] = False
                elif feature_dict['has_constructs'] is True:
                    feature_dict['single_cgroup'] = False
                elif feature_dict['in_vitro'] is True:
                    feature_dict['single_cgroup'] = False
                elif feature_dict['binary_driver'] is True:
                    feature_dict['single_cgroup'] = False
                elif feature_dict['misexpression_element'] is True:
                    feature_dict['single_cgroup'] = False
            if feature_dict['single_cgroup'] is False:
                log.debug(f'"{input_symbol}" is allowed to occupy many complementation groups.')
        return

    def _check_cgroup_feature_count(self):
        """Check that the cgroup has only one or two associated features."""
        if len(self.features) > 2:
            self.errors.append(f'For "{self.input_cgroup_str}", more than the max of two features given for one cgroup')
            log.error(f'For "{self.input_cgroup_str}", more than the max of two features given for one cgroup.')
        verified_feature_ids = [i['feature_id'] for i in self.features if i['feature_id'] is not None]
        if len(verified_feature_ids) < len(self.features):
            self.errors.append(f'For "{self.input_cgroup_str}", could not verify all features given')
            log.error('Could not verify all features given.')
        return

    def _check_cgroup_gene_count(self):
        """Check that for cgroups of classical alleles, only one gene is represented."""
        cgroup_parental_genes = []
        for feature_dict in self.features:
            if feature_dict['single_cgroup'] is True and feature_dict['parental_gene_feature_id']:
                cgroup_parental_genes.append(feature_dict['parental_gene_name'])
        cgroup_parental_genes = set(cgroup_parental_genes)
        if len(cgroup_parental_genes) > 1:
            self.errors.append(f'For "{self.input_cgroup_str}", classical alleles of two different genes share a cgroup')
            log.error('Classical alleles of two different genes share a cgroup.')
        return

    def _check_cgroup_bogus_symbol_count(self):
        """Check that cgroups have max of one bogus symbol feature."""
        bogus_symbols = []
        for feature_dict in self.features:
            if feature_dict['feature_id'] and feature_dict['type'] == 'bogus symbol':
                bogus_symbols.append(feature_dict['feature_id'])
        if len(bogus_symbols) > 1:
            self.errors.append(f'For "{self.input_cgroup_str}", more than one bogus symbol feature given')
            log.error('More than one bogus symbol feature given.')
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
            log.debug(f'cgroup_name="{self.cgroup_name}"')
            log.debug(f'cgroup_desc="{self.cgroup_desc}"')
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
        log.debug(f'cgroup_name="{self.cgroup_name}"')
        log.debug(f'cgroup_desc="{self.cgroup_desc}"')
        return

    def process_cgroup(self, session):
        """Run various ComplementationGroup methods in the correct order."""
        log.debug(f'Processing cgroup {self.input_cgroup_str}')
        self._get_feature_info(session)
        self._get_parental_genes(session)
        self._flag_transgenic_alleles(session)
        self._flag_in_vitro_alleles(session)
        self._flag_binary_drivers(session)
        self._flag_misexpression_elements(session)
        self._assess_single_group_alleles()
        self._check_cgroup_feature_count()
        self._check_cgroup_gene_count()
        self._check_cgroup_bogus_symbol_count()
        self._rank_cgroups()
        log.debug('Done initial parsing of cgroup.\n')
        return
