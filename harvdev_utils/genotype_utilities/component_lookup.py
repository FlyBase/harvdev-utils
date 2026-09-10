# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chado lookups needed to build an Alliance-compliant genotype.

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu

Notes:
    Deriving an Alliance-compliant genotype needs the same handful of facts
    about each of its component features: what the feature is, whether it maps
    onto some other feature for Alliance reporting, and a few flags about the
    allele it came from. This module holds those lookups behind one interface
    so that the cost of getting them can be traded off against the number of
    genotypes being processed:

    - ComponentLookup issues one query per fact per feature. This is right for
      a handful of genotypes (e.g., a curator checking a genotype string, or
      the disease annotation loader), and it is the historical behaviour.
    - PrefetchedComponentLookup answers from dicts built up front by a fixed
      number of set-based queries. This is right for a whole-database pass:
      re-assessing every chado genotype one component at a time needs millions
      of round trips, which is what made such a run take over half a day.

    The prefetched subclass only overrides the per-feature methods; everything
    it does not override falls through to the query-per-fact base class, so
    rarely-needed lookups stay lazy.

    Prefetching is scoped to features that are components of current chado
    genotypes, plus the features those components map onto. Anything outside
    that scope is not in the dicts, so a PrefetchedComponentLookup must only
    be asked about genotypes assembled from feature_genotype.

"""

from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Set, Tuple
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from harvdev_utils.production import (
    Cv, Cvterm, Db, Dbxref, Feature, FeatureCvterm, FeatureCvtermprop,
    FeatureGenotype, FeatureRelationship, FeatureRelationshipPub, FeaturePub,
    FeatureSynonym, Featureprop, Genotype, GenotypeCvterm, GenotypeDbxref,
    Organism, Organismprop, Pub, Synonym
)
from harvdev_utils.chado_functions import get_or_create
from harvdev_utils.char_conversions import greek_to_sgml, sub_sup_to_sgml

# Regex patterns as constants (easier to maintain/change if needed)
FEATURE_UNIQUENAME_REGEX = r'^FB(al|ab|ba|ti|tp)[0-9]{7}$'    # FTA-258: include FBba balancers.
FBAL_REGEX = r'^FBal[0-9]{7}$'
FBAB_REGEX = r'^FBab[0-9]{7}$'
FBBA_REGEX = r'^FBba[0-9]{7}$'
FBGO_REGEX = r'^FBgo[0-9]{7}$'
FBTP_REGEX = r'^FBtp[0-9]{7}$'
FBTI_REGEX = r'^FBti[0-9]{7}$'
FBGN_REGEX = r'^FBgn[0-9]{7}$'

# The pub under which "unspecified" insertions were made for constructs.
UNSPECIFIED_INSERTION_PUB = 'FBrf0262355'

# Chunk size for queries that filter on a Python-side list of feature_ids.
ID_CHUNK_SIZE = 10000


class FeatureRef(NamedTuple):
    """The little that callers need to know about a feature they were handed."""

    feature_id: int
    uniquename: str
    name: str


class KnownGenotype(NamedTuple):
    """An existing chado genotype that already carries an FBgo ID."""

    genotype_id: int
    uniquename: str
    curie: str


def _chunked(ids: Iterable[int]) -> Iterable[List[int]]:
    """Break an iterable of feature_ids into ID_CHUNK_SIZE-sized lists."""
    chunk: List[int] = []
    for an_id in ids:
        chunk.append(an_id)
        if len(chunk) == ID_CHUNK_SIZE:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


class ComponentLookup(object):
    """Per-feature chado lookups for genotype components, one query per fact."""

    def __init__(self, log):
        """Create a ComponentLookup.

        Args:
            log (Logger): The logging object to use.

        Returns:
            An object of the ComponentLookup class.

        """
        self.log = log

    #########################################
    # Resolving an input symbol to a feature.
    #########################################

    def feature_by_name(self, session, feature_name: str) -> FeatureRef:
        """Find the one current FBal/FBab/FBba/FBti/FBtp feature having the given name.

        Args:
            session (Session): SQLAlchemy session for the chado database.
            feature_name (str): A feature.name, in plain text.

        Returns:
            A FeatureRef for the matching feature.

        Raises:
            NoResultFound: If no feature has the name.
            MultipleResultsFound: If many features have the name.

        """
        filters = (
            Feature.is_obsolete.is_(False),
            Feature.is_analysis.is_(False),
            Feature.uniquename.op('~')(FEATURE_UNIQUENAME_REGEX),
            Feature.name == feature_name,
        )
        result = session.query(Feature).filter(*filters).one()
        return FeatureRef(result.feature_id, result.uniquename, result.name)

    def bogus_feature(self, session, symbol: str) -> Tuple[FeatureRef, bool]:
        """Find, or create, the internal "bogus symbol" feature for a symbol.

        Args:
            session (Session): SQLAlchemy session for the chado database.
            symbol (str): A bogus symbol: e.g., "+", "wg[+]", "wg[-]".

        Returns:
            A (FeatureRef, is_new) tuple; is_new is True if the feature was created here.

        """
        filters = (
            Feature.is_obsolete.is_(False),
            Feature.is_analysis.is_(False),
            Feature.name == symbol,
            Feature.uniquename == Feature.name,
            Cvterm.name == 'bogus symbol',
        )
        try:
            result = session.query(Feature).\
                select_from(Feature).\
                join(Cvterm, (Cvterm.cvterm_id == Feature.type_id)).\
                filter(*filters).\
                one()
            return FeatureRef(result.feature_id, result.uniquename, result.name), False
        except NoResultFound:
            org_id = 1
            if symbol == '+':
                org_id = '1367'    # Corresponds to Unknown, which is what the old perl parser did.
            new_feature, _ = get_or_create(session, Feature, type_id=60494, organism_id=org_id, name=symbol, uniquename=symbol)
            return FeatureRef(new_feature.feature_id, new_feature.uniquename, new_feature.name), True

    ###################################
    # Basic information about features.
    ###################################

    def feature_basics(self, session, feature_id: int) -> Dict[str, Any]:
        """Get reportable details for one FBal/FBab/FBba/FBti/FBtp feature.

        Args:
            session (Session): SQLAlchemy session for the chado database.
            feature_id (int): The feature.feature_id of interest.

        Returns:
            A dict of "uniquename", "name", "type", "org_abbr" and "current_symbol".

        Raises:
            NoResultFound: If the feature has no current symbol synonym.
            MultipleResultsFound: If the feature has many current symbol synonyms.

        """
        feature_type = aliased(Cvterm, name='feature_type')
        synonym_type = aliased(Cvterm, name='synonym_type')
        filters = (
            Feature.is_obsolete.is_(False),
            Feature.is_analysis.is_(False),
            Feature.uniquename.op('~')(FEATURE_UNIQUENAME_REGEX),
            Feature.feature_id == feature_id,
            FeatureSynonym.is_current.is_(True),
            synonym_type.name == 'symbol',
        )
        result = session.query(Feature, feature_type, Organism, Synonym).\
            select_from(Feature).\
            join(Organism, (Organism.organism_id == Feature.organism_id)).\
            join(feature_type, (feature_type.cvterm_id == Feature.type_id)).\
            join(FeatureSynonym, (FeatureSynonym.feature_id == Feature.feature_id)).\
            join(Synonym, (Synonym.synonym_id == FeatureSynonym.synonym_id)).\
            join(synonym_type, (synonym_type.cvterm_id == Synonym.type_id)).\
            filter(*filters).\
            one()
        return {
            'uniquename': result.Feature.uniquename,
            'name': result.Feature.name,
            'type': result.feature_type.name,
            'org_abbr': result.Organism.abbreviation,
            'current_symbol': greek_to_sgml(result.Synonym.synonym_sgml),
        }

    def component_basics(self, session, feature_id: int) -> Dict[str, Any]:
        """Get reportable details for any genotype component, bogus symbols included.

        Args:
            session (Session): SQLAlchemy session for the chado database.
            feature_id (int): The feature.feature_id of interest.

        Returns:
            A dict of "uniquename", "name", "type", "org_abbr" and "current_symbol".

        Raises:
            NoResultFound: If the feature is neither a reportable feature nor a bogus symbol.
            MultipleResultsFound: If the feature has many current symbol synonyms.

        """
        try:
            return self.feature_basics(session, feature_id)
        except NoResultFound:
            pass
        filters = (
            Feature.feature_id == feature_id,
            Feature.uniquename == Feature.name,
            Cvterm.name == 'bogus symbol',
        )
        result = session.query(Feature).\
            select_from(Feature).\
            join(Cvterm, (Cvterm.cvterm_id == Feature.type_id)).\
            filter(*filters).\
            one()
        return self._bogus_symbol_basics(result.uniquename, result.name)

    @staticmethod
    def _bogus_symbol_basics(uniquename: str, name: str) -> Dict[str, Any]:
        """Build the basics dict for a "bogus symbol" feature."""
        return {
            'uniquename': uniquename,
            'name': name,
            'type': 'bogus symbol',
            'org_abbr': None,
            'current_symbol': sub_sup_to_sgml(name),
        }

    ############################################
    # Mapping a component to the feature to use.
    ############################################

    def construct_unspecified_insertion(self, session, construct_feature_id: int) -> FeatureRef:
        """Find the one "unspecified" insertion produced by a construct.

        Args:
            session (Session): SQLAlchemy session for the chado database.
            construct_feature_id (int): The feature.feature_id of an FBtp construct.

        Returns:
            A FeatureRef for the FBti insertion.

        Raises:
            NoResultFound: If the construct produced no such insertion.
            MultipleResultsFound: If the construct produced many such insertions.

        """
        construct = aliased(Feature, name='construct')
        insertion = aliased(Feature, name='insertion')
        filters = (
            construct.feature_id == construct_feature_id,
            insertion.is_obsolete.is_(False),
            insertion.uniquename.op('~')(FBTI_REGEX),
            insertion.is_analysis.is_(False),
            insertion.name.op('~')('unspecified$'),
            Cvterm.name == 'producedby',
            Pub.uniquename == UNSPECIFIED_INSERTION_PUB,
        )
        result = session.query(insertion).\
            select_from(construct).\
            join(FeatureRelationship, (FeatureRelationship.object_id == construct.feature_id)).\
            join(insertion, (insertion.feature_id == FeatureRelationship.subject_id)).\
            join(Cvterm, (Cvterm.cvterm_id == FeatureRelationship.type_id)).\
            join(FeatureRelationshipPub, (FeatureRelationshipPub.feature_relationship_id == FeatureRelationship.feature_relationship_id)).\
            join(Pub, (Pub.pub_id == FeatureRelationshipPub.pub_id)).\
            filter(*filters).\
            one()
        return FeatureRef(result.feature_id, result.uniquename, result.name)

    def balancer_aberration(self, session, balancer: FeatureRef, input_symbol: str) -> FeatureRef:
        """Find the parent aberration of a usable balancer.

        Args:
            session (Session): SQLAlchemy session for the chado database.
            balancer (FeatureRef): An FBba balancer feature.
            input_symbol (str): The symbol the balancer came from, for logging.

        Returns:
            A FeatureRef for the parent FBab aberration.

        Raises:
            NoResultFound: If the balancer is not flagged usable, or has no parent aberration.
            MultipleResultsFound: If the balancer has many parent aberrations.

        """
        if not self._balancer_is_usable(session, balancer.feature_id):
            self.log.error(f'For "{input_symbol}" ({balancer.uniquename}), '
                           f'found no "balancer_status=true" featureprop, so it is not mappable.')
            raise NoResultFound
        balancer_feature = aliased(Feature, name='balancer')
        aberration = aliased(Feature, name='aberration')
        filters = (
            balancer_feature.feature_id == balancer.feature_id,
            balancer_feature.is_obsolete.is_(False),
            balancer_feature.is_analysis.is_(False),
            balancer_feature.uniquename.op('~')(FBBA_REGEX),
            aberration.is_obsolete.is_(False),
            aberration.is_analysis.is_(False),
            aberration.uniquename.op('~')(FBAB_REGEX),
            Cvterm.name == 'variant_of',
        )
        result = session.query(aberration).\
            select_from(balancer_feature).\
            join(FeatureRelationship, (FeatureRelationship.subject_id == balancer_feature.feature_id)).\
            join(aberration, (aberration.feature_id == FeatureRelationship.object_id)).\
            join(Cvterm, (Cvterm.cvterm_id == FeatureRelationship.type_id)).\
            filter(*filters).\
            one()
        return FeatureRef(result.feature_id, result.uniquename, result.name)

    def _balancer_is_usable(self, session, balancer_feature_id: int) -> bool:
        """Report whether a balancer carries a "balancer_status=true" featureprop."""
        prop_type = aliased(Cvterm, name='prop_type')
        filters = (
            Featureprop.feature_id == balancer_feature_id,
            prop_type.name == 'balancer_status',
            Featureprop.value == 'true',
        )
        balancer_status = session.query(Featureprop).\
            select_from(Featureprop).\
            join(prop_type, (prop_type.cvterm_id == Featureprop.type_id)).\
            filter(*filters).\
            first()
        return balancer_status is not None

    def alliance_insertion(self, session, allele_feature_id: int) -> Optional[FeatureRef]:
        """Find the insertion that represents an allele at the Alliance, if any.

        Args:
            session (Session): SQLAlchemy session for the chado database.
            allele_feature_id (int): The feature.feature_id of an FBal allele.

        Returns:
            A FeatureRef for the FBti insertion, or None if the allele has no such insertion.

        Raises:
            MultipleResultsFound: If the allele has many such insertions.

        """
        allele = aliased(Feature, name='allele')
        insertion = aliased(Feature, name='insertion')
        filters = (
            allele.feature_id == allele_feature_id,
            insertion.is_obsolete.is_(False),
            insertion.uniquename.op('~')(FBTI_REGEX),
            insertion.is_analysis.is_(False),
            Cvterm.name == 'is_represented_at_alliance_as',
        )
        result = session.query(insertion).\
            select_from(allele).\
            join(FeatureRelationship, (FeatureRelationship.subject_id == allele.feature_id)).\
            join(insertion, (insertion.feature_id == FeatureRelationship.object_id)).\
            join(Cvterm, (Cvterm.cvterm_id == FeatureRelationship.type_id)).\
            filter(*filters).\
            one_or_none()
        if result is None:
            return None
        return FeatureRef(result.feature_id, result.uniquename, result.name)

    def allele_construct_insertions(self, session, allele_feature_id: int) -> Dict[int, FeatureRef]:
        """Find "unspecified" insertions for the constructs associated with an allele.

        Args:
            session (Session): SQLAlchemy session for the chado database.
            allele_feature_id (int): The feature.feature_id of an FBal allele.

        Returns:
            A dict of FBti FeatureRefs keyed by the feature_id of the FBtp construct that produced them.

        """
        allele = aliased(Feature, name='allele')
        construct = aliased(Feature, name='construct')
        insertion = aliased(Feature, name='insertion')
        ac_rel_type = aliased(Cvterm, name='ac_rel_type')
        ic_rel_type = aliased(Cvterm, name='ic_rel_type')
        ac_rel = aliased(FeatureRelationship, name='ac_rel')
        ic_rel = aliased(FeatureRelationship, name='ic_rel')
        filters = (
            allele.feature_id == allele_feature_id,
            construct.is_obsolete.is_(False),
            construct.uniquename.op('~')(FBTP_REGEX),
            construct.is_analysis.is_(False),
            insertion.is_obsolete.is_(False),
            insertion.uniquename.op('~')(FBTI_REGEX),
            insertion.is_analysis.is_(False),
            insertion.name.op('~')('unspecified$'),
            ac_rel_type.name == 'associated_with',
            ic_rel_type.name == 'producedby',
            Pub.uniquename == UNSPECIFIED_INSERTION_PUB,
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
            cons_ins_dict[result.construct.feature_id] = FeatureRef(result.insertion.feature_id, result.insertion.uniquename, result.insertion.name)
        return cons_ins_dict

    def constructs_for_pub(self, session, construct_feature_ids: Iterable[int], pub_id: int) -> List[int]:
        """Find which of the given constructs are associated with a given pub.

        Args:
            session (Session): SQLAlchemy session for the chado database.
            construct_feature_ids (Iterable[int]): feature.feature_ids of FBtp constructs.
            pub_id (int): The pub.pub_id of interest.

        Returns:
            A list of feature.feature_ids for the constructs associated with the pub.

        """
        filters = (
            Feature.feature_id.in_(tuple(construct_feature_ids)),
            Pub.pub_id == pub_id,
        )
        results = session.query(Feature).\
            select_from(Feature).\
            join(FeaturePub, (FeaturePub.feature_id == Feature.feature_id)).\
            join(Pub, (Pub.pub_id == FeaturePub.pub_id)).\
            filter(*filters).\
            distinct()
        return [i.feature_id for i in results]

    ###################################
    # Flags and relationships of alleles.
    ###################################

    def is_in_vitro(self, session, allele_feature_id: int) -> bool:
        """Report whether an allele has an "in vitro construct" annotation.

        Args:
            session (Session): SQLAlchemy session for the chado database.
            allele_feature_id (int): The feature.feature_id of an FBal allele.

        Returns:
            True if the allele has the annotation.

        """
        filters = (
            FeatureCvterm.feature_id == allele_feature_id,
            Cvterm.name == 'in vitro construct',
        )
        results = session.query(Cvterm).\
            select_from(FeatureCvterm).\
            join(Cvterm, (Cvterm.cvterm_id == FeatureCvterm.cvterm_id)).\
            filter(*filters).\
            distinct()
        for _ in results:
            return True
        return False

    def is_misexpression_element(self, session, allele_feature_id: int) -> bool:
        """Report whether an allele is a misexpression element.

        Args:
            session (Session): SQLAlchemy session for the chado database.
            allele_feature_id (int): The feature.feature_id of an FBal allele.

        Returns:
            True if the allele's insertion comes from a "misexpression element" construct.

        """
        return self._misexpression_query(session, [allele_feature_id]).first() is not None

    @staticmethod
    def _misexpression_query(session, allele_feature_ids: Iterable[int]):
        """Build a query for FBal feature_ids that are misexpression elements."""
        allele = aliased(Feature, name='mis_allele')
        construct = aliased(Feature, name='mis_construct')
        insertion = aliased(Feature, name='mis_insertion')
        ai_rel = aliased(FeatureRelationship, name='mis_ai_rel')
        ic_rel = aliased(FeatureRelationship, name='mis_ic_rel')
        ai_rel_type = aliased(Cvterm, name='mis_ai_rel_type')
        ic_rel_type = aliased(Cvterm, name='mis_ic_rel_type')
        tool_type = aliased(Cvterm, name='mis_tool_type')
        tool_rel = aliased(Cvterm, name='mis_tool_rel')
        filters = (
            allele.feature_id.in_(tuple(allele_feature_ids)),
            construct.uniquename.op('~')(FBTP_REGEX),
            construct.is_obsolete.is_(False),
            insertion.uniquename.op('~')(FBTI_REGEX),
            insertion.is_obsolete.is_(False),
            ai_rel_type.name == 'associated_with',
            ic_rel_type.name == 'producedby',
            tool_type.name == 'misexpression element',
            tool_rel.name == 'tool_uses',
        )
        return session.query(allele.feature_id).\
            select_from(allele).\
            join(ai_rel, (ai_rel.subject_id == allele.feature_id)).\
            join(insertion, (insertion.feature_id == ai_rel.object_id)).\
            join(ai_rel_type, (ai_rel_type.cvterm_id == ai_rel.type_id)).\
            join(ic_rel, (ic_rel.subject_id == insertion.feature_id)).\
            join(construct, (construct.feature_id == ic_rel.object_id)).\
            join(ic_rel_type, (ic_rel_type.cvterm_id == ic_rel.type_id)).\
            join(FeatureCvterm, (FeatureCvterm.feature_id == construct.feature_id)).\
            join(tool_type, (tool_type.cvterm_id == FeatureCvterm.cvterm_id)).\
            join(FeatureCvtermprop, (FeatureCvtermprop.feature_cvterm_id == FeatureCvterm.feature_cvterm_id)).\
            join(tool_rel, (tool_rel.cvterm_id == FeatureCvtermprop.type_id)).\
            filter(*filters).\
            distinct()

    def parental_gene(self, session, allele_feature_id: int) -> FeatureRef:
        """Find the parental Drosophilid gene of an allele.

        Args:
            session (Session): SQLAlchemy session for the chado database.
            allele_feature_id (int): The feature.feature_id of an FBal allele.

        Returns:
            A FeatureRef for the parental FBgn gene.

        Raises:
            NoResultFound: If the allele has no Drosophilid parental gene.
            MultipleResultsFound: If the allele has many parental genes.

        """
        rel_type = aliased(Cvterm, name='rel_type')
        org_prop_type = aliased(Cvterm, name='org_prop_type')
        filters = (
            org_prop_type.name == 'taxgroup',
            Organismprop.value == 'drosophilid',
            FeatureRelationship.subject_id == allele_feature_id,
            rel_type.name == 'alleleof',
            Feature.is_obsolete.is_(False),
            Feature.is_analysis.is_(False),
            Feature.uniquename.op('~')(FBGN_REGEX),
        )
        result = session.query(Feature).\
            select_from(Feature).\
            join(Organismprop, (Organismprop.organism_id == Feature.organism_id)).\
            join(org_prop_type, (org_prop_type.cvterm_id == Organismprop.type_id)).\
            join(FeatureRelationship, (FeatureRelationship.object_id == Feature.feature_id)).\
            join(rel_type, (rel_type.cvterm_id == FeatureRelationship.type_id)).\
            filter(*filters).\
            one()
        return FeatureRef(result.feature_id, result.uniquename, result.name)

    def possible_genes_for_insertion(self, session, insertion_feature_id: int) -> List[str]:
        """Find Drosophilid genes that an at-locus insertion could belong to.

        Args:
            session (Session): SQLAlchemy session for the chado database.
            insertion_feature_id (int): The feature.feature_id of an FBti insertion.

        Returns:
            A list of FBgn IDs.

        """
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
        return [i.uniquename for i in results]

    #################################
    # Finding an existing genotype.
    #################################

    def genotype_by_description(self, session, description: str) -> Optional[KnownGenotype]:
        """Find the current chado genotype having the given description.

        The description is built from the FlyBase IDs of the genotype's components, so it is
        the identity of a genotype: see check_genotypes.py, which derives both it and
        genotype.uniquename from feature_genotype and merges genotypes that share it.

        Args:
            session (Session): SQLAlchemy session for the chado database.
            description (str): A genotype.description.

        Returns:
            A KnownGenotype, or None if no current genotype with an FBgo ID has the description.

        Raises:
            MultipleResultsFound: If many current genotypes with FBgo IDs have the description.

        """
        filters = (
            Genotype.description == description,
            Genotype.is_obsolete.is_(False),
            GenotypeDbxref.is_current.is_(True),
            Dbxref.accession.op('~')(FBGO_REGEX),
            Db.name == 'FlyBase',
        )
        result = session.query(Genotype, Dbxref).\
            select_from(Genotype).\
            join(GenotypeDbxref, (GenotypeDbxref.genotype_id == Genotype.genotype_id)).\
            join(Dbxref, (Dbxref.dbxref_id == GenotypeDbxref.dbxref_id)).\
            join(Db, (Db.db_id == Dbxref.db_id)).\
            filter(*filters).\
            one_or_none()
        if result is None:
            return None
        return KnownGenotype(result.Genotype.genotype_id, result.Genotype.uniquename, result.Dbxref.accession)

    def is_alliance_compliant(self, session, genotype_id: int) -> bool:
        """Report whether a genotype already carries the "alliance_compliant" annotation.

        Args:
            session (Session): SQLAlchemy session for the chado database.
            genotype_id (int): The genotype.genotype_id of interest.

        Returns:
            True if the genotype is already flagged.

        """
        filters = (
            GenotypeCvterm.genotype_id == genotype_id,
            Cvterm.name == 'alliance_compliant',
            Cv.name == 'genotype characteristics',
        )
        results = session.query(GenotypeCvterm.genotype_cvterm_id).\
            select_from(GenotypeCvterm).\
            join(Cvterm, (Cvterm.cvterm_id == GenotypeCvterm.cvterm_id)).\
            join(Cv, (Cv.cv_id == Cvterm.cv_id)).\
            filter(*filters).\
            distinct()
        for _ in results:
            return True
        return False

    def register_alliance_compliant(self, genotype_id: int) -> None:
        """Note a genotype flagged "alliance_compliant" during this run.

        The base class needs no bookkeeping: an annotation added to the session is visible
        to the next query against it.

        Args:
            genotype_id (int): The genotype.genotype_id that was flagged.

        Returns:
            None

        """
        return

    def genotype_by_uniquename(self, session, uniquename: str) -> Optional[Tuple[int, Optional[str]]]:
        """Find whichever genotype holds a uniquename, current or obsolete, FBgo ID or not.

        genotype.uniquename is unique, so a new genotype cannot be given one that is taken.

        Args:
            session (Session): SQLAlchemy session for the chado database.
            uniquename (str): A genotype.uniquename.

        Returns:
            A (genotype_id, description) tuple, or None if the uniquename is free.

        """
        result = session.query(Genotype.genotype_id, Genotype.description).\
            filter(Genotype.uniquename == uniquename).\
            one_or_none()
        if result is None:
            return None
        return (result.genotype_id, result.description)

    def register_genotype(self, description: str, uniquename: str, genotype_id: int, curie: str) -> None:
        """Note a genotype created during this run, so later lookups can find it.

        The base class needs no bookkeeping: a genotype added to the session is visible to
        the next query against it.

        Args:
            description (str): The new genotype's description.
            uniquename (str): The new genotype's uniquename.
            genotype_id (int): The new genotype.genotype_id.
            curie (str): The new genotype's FBgo ID.

        Returns:
            None

        """
        return


class PrefetchedComponentLookup(ComponentLookup):
    """Genotype component lookups answered from dicts built by set-based queries.

    Only components of current chado genotypes, and the features they map onto, are in
    scope. Ask about anything else and the answer will be wrong, not slow.
    """

    def __init__(self, session, log):
        """Create a PrefetchedComponentLookup and populate it from chado.

        Args:
            session (Session): SQLAlchemy session for the chado database.
            log (Logger): The logging object to use.

        Returns:
            An object of the PrefetchedComponentLookup class.

        """
        super().__init__(log)
        self.component_ids: Set[int] = set()                            # feature_ids of components of current genotypes.
        self._alliance_insertions: Dict[int, List[FeatureRef]] = {}     # FBal feature_id to FBti FeatureRefs.
        self._construct_insertions: Dict[int, List[FeatureRef]] = {}    # FBtp feature_id to unspecified FBti FeatureRefs.
        self._allele_construct_insertions: Dict[int, Dict[int, FeatureRef]] = {}    # FBal feature_id to FBtp-keyed FBti FeatureRefs.
        self._usable_balancers: Set[int] = set()                        # FBba feature_ids flagged "balancer_status=true".
        self._balancer_aberrations: Dict[int, List[FeatureRef]] = {}    # FBba feature_id to parent FBab FeatureRefs.
        self._in_vitro_alleles: Set[int] = set()                        # FBal feature_ids with "in vitro construct" annotations.
        self._misexpression_alleles: Set[int] = set()                   # FBal feature_ids that are misexpression elements.
        self._parental_genes: Dict[int, List[FeatureRef]] = {}          # FBal feature_id to parental FBgn FeatureRefs.
        self._insertion_genes: Dict[int, List[str]] = {}                # FBti feature_id to possible FBgn IDs.
        self._feature_basics: Dict[int, Dict[str, Any]] = {}            # feature_id to basic reportable details.
        self._multi_symbol_ids: Set[int] = set()                        # feature_ids of features having many current symbols.
        self._genotypes_by_desc: Dict[str, List[KnownGenotype]] = {}    # genotype.description to KnownGenotypes.
        self._compliant_genotype_ids: Set[int] = set()                   # genotype_ids flagged "alliance_compliant".
        self._genotypes_by_uniquename: Dict[str, Tuple[int, Optional[str]]] = {}    # genotype.uniquename to (genotype_id, description).
        self._prefetch(session)

    ####################
    # Prefetch machinery.
    ####################

    def _prefetch(self, session) -> None:
        """Populate every lookup dict."""
        self.log.info('Prefetch chado data needed to assess genotype components.')
        self._prefetch_component_ids(session)
        self._prefetch_alliance_insertions(session)
        self._prefetch_construct_insertions(session)
        self._prefetch_allele_construct_insertions(session)
        self._prefetch_balancer_mappings(session)
        self._prefetch_allele_flags(session)
        self._prefetch_parental_genes(session)
        self._prefetch_insertion_genes(session)
        self._prefetch_feature_basics(session)
        self._prefetch_known_genotypes(session)
        self._prefetch_compliant_genotypes(session)
        self.log.info('Done prefetching chado data needed to assess genotype components.')
        return

    def _prefetch_component_ids(self, session) -> None:
        """Collect the feature_ids of all components of current genotypes."""
        results = session.query(FeatureGenotype.feature_id).\
            select_from(FeatureGenotype).\
            join(Genotype, (Genotype.genotype_id == FeatureGenotype.genotype_id)).\
            filter(Genotype.is_obsolete.is_(False)).\
            distinct()
        self.component_ids = {i.feature_id for i in results}
        self.log.info(f'Found {len(self.component_ids)} distinct features used as components of current genotypes.')
        return

    def _mapped_feature_ids(self) -> Set[int]:
        """Collect the feature_ids of every feature that a component can map onto."""
        mapped_ids: Set[int] = set()
        for feature_refs in self._alliance_insertions.values():
            mapped_ids.update(i.feature_id for i in feature_refs)
        for feature_refs in self._construct_insertions.values():
            mapped_ids.update(i.feature_id for i in feature_refs)
        for construct_dict in self._allele_construct_insertions.values():
            mapped_ids.update(i.feature_id for i in construct_dict.values())
        for feature_refs in self._balancer_aberrations.values():
            mapped_ids.update(i.feature_id for i in feature_refs)
        return mapped_ids

    ###################
    # Prefetch queries.
    ###################

    def _prefetch_alliance_insertions(self, session) -> None:
        """Map each component allele to the insertion that represents it at the Alliance."""
        allele = aliased(Feature, name='allele')
        insertion = aliased(Feature, name='insertion')
        counter = 0
        for id_chunk in _chunked(self.component_ids):
            filters = (
                allele.feature_id.in_(id_chunk),
                allele.uniquename.op('~')(FBAL_REGEX),
                insertion.is_obsolete.is_(False),
                insertion.uniquename.op('~')(FBTI_REGEX),
                insertion.is_analysis.is_(False),
                Cvterm.name == 'is_represented_at_alliance_as',
            )
            results = session.query(allele.feature_id.label('allele_id'), insertion).\
                select_from(allele).\
                join(FeatureRelationship, (FeatureRelationship.subject_id == allele.feature_id)).\
                join(insertion, (insertion.feature_id == FeatureRelationship.object_id)).\
                join(Cvterm, (Cvterm.cvterm_id == FeatureRelationship.type_id)).\
                filter(*filters).\
                distinct()
            for result in results:
                feature_ref = FeatureRef(result.insertion.feature_id, result.insertion.uniquename, result.insertion.name)
                self._alliance_insertions.setdefault(result.allele_id, []).append(feature_ref)
                counter += 1
        self.log.info(f'Found {counter} "is_represented_at_alliance_as" insertions for component alleles.')
        return

    def _prefetch_construct_insertions(self, session) -> None:
        """Map each component construct to its "unspecified" insertion."""
        construct = aliased(Feature, name='construct')
        insertion = aliased(Feature, name='insertion')
        counter = 0
        for id_chunk in _chunked(self.component_ids):
            filters = (
                construct.feature_id.in_(id_chunk),
                construct.uniquename.op('~')(FBTP_REGEX),
                insertion.is_obsolete.is_(False),
                insertion.uniquename.op('~')(FBTI_REGEX),
                insertion.is_analysis.is_(False),
                insertion.name.op('~')('unspecified$'),
                Cvterm.name == 'producedby',
                Pub.uniquename == UNSPECIFIED_INSERTION_PUB,
            )
            results = session.query(construct.feature_id.label('construct_id'), insertion).\
                select_from(construct).\
                join(FeatureRelationship, (FeatureRelationship.object_id == construct.feature_id)).\
                join(insertion, (insertion.feature_id == FeatureRelationship.subject_id)).\
                join(Cvterm, (Cvterm.cvterm_id == FeatureRelationship.type_id)).\
                join(FeatureRelationshipPub, (FeatureRelationshipPub.feature_relationship_id == FeatureRelationship.feature_relationship_id)).\
                join(Pub, (Pub.pub_id == FeatureRelationshipPub.pub_id)).\
                filter(*filters).\
                distinct()
            for result in results:
                feature_ref = FeatureRef(result.insertion.feature_id, result.insertion.uniquename, result.insertion.name)
                self._construct_insertions.setdefault(result.construct_id, []).append(feature_ref)
                counter += 1
        self.log.info(f'Found {counter} "unspecified" insertions for component constructs.')
        return

    def _prefetch_allele_construct_insertions(self, session) -> None:
        """Map each component allele to the "unspecified" insertions of its constructs."""
        allele = aliased(Feature, name='allele')
        construct = aliased(Feature, name='construct')
        insertion = aliased(Feature, name='insertion')
        ac_rel_type = aliased(Cvterm, name='ac_rel_type')
        ic_rel_type = aliased(Cvterm, name='ic_rel_type')
        ac_rel = aliased(FeatureRelationship, name='ac_rel')
        ic_rel = aliased(FeatureRelationship, name='ic_rel')
        counter = 0
        for id_chunk in _chunked(self.component_ids):
            filters = (
                allele.feature_id.in_(id_chunk),
                allele.uniquename.op('~')(FBAL_REGEX),
                construct.is_obsolete.is_(False),
                construct.uniquename.op('~')(FBTP_REGEX),
                construct.is_analysis.is_(False),
                insertion.is_obsolete.is_(False),
                insertion.uniquename.op('~')(FBTI_REGEX),
                insertion.is_analysis.is_(False),
                insertion.name.op('~')('unspecified$'),
                ac_rel_type.name == 'associated_with',
                ic_rel_type.name == 'producedby',
                Pub.uniquename == UNSPECIFIED_INSERTION_PUB,
            )
            results = session.query(allele.feature_id.label('allele_id'), construct.feature_id.label('construct_id'), insertion).\
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
            for result in results:
                feature_ref = FeatureRef(result.insertion.feature_id, result.insertion.uniquename, result.insertion.name)
                self._allele_construct_insertions.setdefault(result.allele_id, {})[result.construct_id] = feature_ref
                counter += 1
        self.log.info(f'Found {counter} construct-associated "unspecified" insertions for component alleles.')
        return

    def _prefetch_balancer_mappings(self, session) -> None:
        """Flag usable component balancers and map them to their parent aberrations."""
        prop_type = aliased(Cvterm, name='prop_type')
        balancer = aliased(Feature, name='balancer')
        aberration = aliased(Feature, name='aberration')
        for id_chunk in _chunked(self.component_ids):
            filters = (
                Featureprop.feature_id.in_(id_chunk),
                prop_type.name == 'balancer_status',
                Featureprop.value == 'true',
            )
            results = session.query(Featureprop.feature_id).\
                select_from(Featureprop).\
                join(prop_type, (prop_type.cvterm_id == Featureprop.type_id)).\
                filter(*filters).\
                distinct()
            self._usable_balancers.update(i.feature_id for i in results)
        counter = 0
        for id_chunk in _chunked(self._usable_balancers):
            filters = (
                balancer.feature_id.in_(id_chunk),
                balancer.is_obsolete.is_(False),
                balancer.is_analysis.is_(False),
                balancer.uniquename.op('~')(FBBA_REGEX),
                aberration.is_obsolete.is_(False),
                aberration.is_analysis.is_(False),
                aberration.uniquename.op('~')(FBAB_REGEX),
                Cvterm.name == 'variant_of',
            )
            results = session.query(balancer.feature_id.label('balancer_id'), aberration).\
                select_from(balancer).\
                join(FeatureRelationship, (FeatureRelationship.subject_id == balancer.feature_id)).\
                join(aberration, (aberration.feature_id == FeatureRelationship.object_id)).\
                join(Cvterm, (Cvterm.cvterm_id == FeatureRelationship.type_id)).\
                filter(*filters).\
                distinct()
            for result in results:
                feature_ref = FeatureRef(result.aberration.feature_id, result.aberration.uniquename, result.aberration.name)
                self._balancer_aberrations.setdefault(result.balancer_id, []).append(feature_ref)
                counter += 1
        self.log.info(f'Found {len(self._usable_balancers)} usable component balancers, having {counter} parent aberrations.')
        return

    def _prefetch_allele_flags(self, session) -> None:
        """Flag component alleles that are in vitro, or misexpression elements."""
        for id_chunk in _chunked(self.component_ids):
            filters = (
                FeatureCvterm.feature_id.in_(id_chunk),
                Cvterm.name == 'in vitro construct',
            )
            results = session.query(FeatureCvterm.feature_id).\
                select_from(FeatureCvterm).\
                join(Cvterm, (Cvterm.cvterm_id == FeatureCvterm.cvterm_id)).\
                filter(*filters).\
                distinct()
            self._in_vitro_alleles.update(i.feature_id for i in results)
            results = self._misexpression_query(session, id_chunk)
            self._misexpression_alleles.update(i[0] for i in results)
        self.log.info(f'Found {len(self._in_vitro_alleles)} component alleles with "in vitro construct" annotations.')
        self.log.info(f'Found {len(self._misexpression_alleles)} component alleles that are misexpression elements.')
        return

    def _prefetch_parental_genes(self, session) -> None:
        """Map each component allele to its parental Drosophilid gene."""
        rel_type = aliased(Cvterm, name='rel_type')
        org_prop_type = aliased(Cvterm, name='org_prop_type')
        counter = 0
        for id_chunk in _chunked(self.component_ids):
            filters = (
                org_prop_type.name == 'taxgroup',
                Organismprop.value == 'drosophilid',
                FeatureRelationship.subject_id.in_(id_chunk),
                rel_type.name == 'alleleof',
                Feature.is_obsolete.is_(False),
                Feature.is_analysis.is_(False),
                Feature.uniquename.op('~')(FBGN_REGEX),
            )
            results = session.query(FeatureRelationship.subject_id.label('allele_id'), Feature).\
                select_from(Feature).\
                join(Organismprop, (Organismprop.organism_id == Feature.organism_id)).\
                join(org_prop_type, (org_prop_type.cvterm_id == Organismprop.type_id)).\
                join(FeatureRelationship, (FeatureRelationship.object_id == Feature.feature_id)).\
                join(rel_type, (rel_type.cvterm_id == FeatureRelationship.type_id)).\
                filter(*filters).\
                distinct()
            for result in results:
                feature_ref = FeatureRef(result.Feature.feature_id, result.Feature.uniquename, result.Feature.name)
                self._parental_genes.setdefault(result.allele_id, []).append(feature_ref)
                counter += 1
        self.log.info(f'Found {counter} parental Drosophilid genes for component alleles.')
        return

    def _prefetch_insertion_genes(self, session) -> None:
        """Map each insertion in play to the Drosophilid genes it could belong to."""
        insertion_ids = {i.feature_id for refs in self._alliance_insertions.values() for i in refs}
        insertion_ids.update(i.feature_id for refs in self._construct_insertions.values() for i in refs)
        insertion_ids.update(i.feature_id for cons in self._allele_construct_insertions.values() for i in cons.values())
        insertion_ids.update(self.component_ids)
        gene = aliased(Feature, name='gene')
        allele = aliased(Feature, name='allele')
        insertion = aliased(Feature, name='insertion')
        ag_rel = aliased(FeatureRelationship, name='ag_rel')
        ai_rel = aliased(FeatureRelationship, name='ai_rel')
        ag_rel_type = aliased(Cvterm, name='ag_rel_type')
        ai_rel_type = aliased(Cvterm, name='ai_rel_type')
        counter = 0
        for id_chunk in _chunked(insertion_ids):
            filters = (
                ai_rel.object_id.in_(id_chunk),
                insertion.uniquename.op('~')(FBTI_REGEX),
                allele.is_obsolete.is_(False),
                allele.uniquename.op('~')(FBAL_REGEX),
                gene.is_obsolete.is_(False),
                gene.uniquename.op('~')(FBGN_REGEX),
                ai_rel_type.name == 'associated_with',
                ag_rel_type.name == 'alleleof',
                Organismprop.value == 'drosophilid',
            )
            results = session.query(ai_rel.object_id.label('insertion_id'), gene.uniquename.label('gene_uniquename')).\
                select_from(gene).\
                join(Organismprop, (Organismprop.organism_id == gene.organism_id)).\
                join(ag_rel, (ag_rel.object_id == gene.feature_id)).\
                join(ag_rel_type, (ag_rel_type.cvterm_id == ag_rel.type_id)).\
                join(allele, (allele.feature_id == ag_rel.subject_id)).\
                join(ai_rel, (ai_rel.subject_id == allele.feature_id)).\
                join(ai_rel_type, (ai_rel_type.cvterm_id == ai_rel.type_id)).\
                join(insertion, (insertion.feature_id == ai_rel.object_id)).\
                filter(*filters).\
                distinct()
            for result in results:
                self._insertion_genes.setdefault(result.insertion_id, []).append(result.gene_uniquename)
                counter += 1
        self.log.info(f'Found {counter} possible Drosophilid genes for {len(self._insertion_genes)} insertions.')
        return

    def _prefetch_feature_basics(self, session) -> None:
        """Get reportable details for every component and every feature a component maps onto."""
        wanted_ids = set(self.component_ids)
        wanted_ids.update(self._mapped_feature_ids())
        feature_type = aliased(Cvterm, name='feature_type')
        synonym_type = aliased(Cvterm, name='synonym_type')
        multi_symbol_ids: Set[int] = set()
        for id_chunk in _chunked(wanted_ids):
            filters = (
                Feature.is_obsolete.is_(False),
                Feature.is_analysis.is_(False),
                Feature.uniquename.op('~')(FEATURE_UNIQUENAME_REGEX),
                Feature.feature_id.in_(id_chunk),
                FeatureSynonym.is_current.is_(True),
                synonym_type.name == 'symbol',
            )
            results = session.query(Feature, feature_type, Organism, Synonym).\
                select_from(Feature).\
                join(Organism, (Organism.organism_id == Feature.organism_id)).\
                join(feature_type, (feature_type.cvterm_id == Feature.type_id)).\
                join(FeatureSynonym, (FeatureSynonym.feature_id == Feature.feature_id)).\
                join(Synonym, (Synonym.synonym_id == FeatureSynonym.synonym_id)).\
                join(synonym_type, (synonym_type.cvterm_id == Synonym.type_id)).\
                filter(*filters).\
                distinct()
            for result in results:
                feature_id = result.Feature.feature_id
                if feature_id in self._feature_basics:
                    multi_symbol_ids.add(feature_id)
                    continue
                self._feature_basics[feature_id] = {
                    'uniquename': result.Feature.uniquename,
                    'name': result.Feature.name,
                    'type': result.feature_type.name,
                    'org_abbr': result.Organism.abbreviation,
                    'current_symbol': greek_to_sgml(result.Synonym.synonym_sgml),
                }
        # Bogus symbol features have no symbol synonym, and are never mapping targets.
        bogus_counter = 0
        for id_chunk in _chunked(self.component_ids):
            filters = (
                Feature.feature_id.in_(id_chunk),
                Feature.uniquename == Feature.name,
                Cvterm.name == 'bogus symbol',
            )
            results = session.query(Feature).\
                select_from(Feature).\
                join(Cvterm, (Cvterm.cvterm_id == Feature.type_id)).\
                filter(*filters).\
                distinct()
            for result in results:
                self._feature_basics[result.feature_id] = self._bogus_symbol_basics(result.uniquename, result.name)
                bogus_counter += 1
        for feature_id in multi_symbol_ids:
            del self._feature_basics[feature_id]
        self._multi_symbol_ids = multi_symbol_ids
        self.log.info(f'Got details for {len(self._feature_basics)} features, {bogus_counter} of them bogus symbols.')
        if multi_symbol_ids:
            self.log.warning(f'Found {len(multi_symbol_ids)} features having many current symbols; they will be reported as errors.')
        return

    def _prefetch_known_genotypes(self, session) -> None:
        """Map the description of every current, FBgo-bearing genotype to that genotype."""
        filters = (
            Genotype.is_obsolete.is_(False),
            GenotypeDbxref.is_current.is_(True),
            Dbxref.accession.op('~')(FBGO_REGEX),
            Db.name == 'FlyBase',
        )
        results = session.query(Genotype.genotype_id, Genotype.uniquename, Genotype.description, Dbxref.accession).\
            select_from(Genotype).\
            join(GenotypeDbxref, (GenotypeDbxref.genotype_id == Genotype.genotype_id)).\
            join(Dbxref, (Dbxref.dbxref_id == GenotypeDbxref.dbxref_id)).\
            join(Db, (Db.db_id == Dbxref.db_id)).\
            filter(*filters).\
            distinct()
        counter = 0
        for result in results:
            self._genotypes_by_desc.setdefault(result.description, []).append(KnownGenotype(result.genotype_id, result.uniquename, result.accession))
            counter += 1
        # Every genotype, not just the current ones with FBgo IDs: genotype.uniquename is unique
        # across the table, so any row holding one blocks a new genotype from taking it.
        all_genotypes = session.query(Genotype.genotype_id, Genotype.uniquename, Genotype.description).distinct()
        for result in all_genotypes:
            self._genotypes_by_uniquename[result.uniquename] = (result.genotype_id, result.description)
        redundant = [i for i in self._genotypes_by_desc.values() if len(i) > 1]
        self.log.info(f'Found {counter} current genotypes with FBgo IDs, having {len(self._genotypes_by_desc)} distinct descriptions.')
        self.log.info(f'Found {len(self._genotypes_by_uniquename)} genotype uniquenames already in use.')
        if redundant:
            self.log.warning(f'Found {len(redundant)} genotype descriptions shared by many genotypes; they will be reported as errors.')
        return

    def _prefetch_compliant_genotypes(self, session) -> None:
        """Collect the genotype_ids of genotypes already flagged "alliance_compliant"."""
        filters = (
            Cvterm.name == 'alliance_compliant',
            Cv.name == 'genotype characteristics',
        )
        results = session.query(GenotypeCvterm.genotype_id).\
            select_from(GenotypeCvterm).\
            join(Cvterm, (Cvterm.cvterm_id == GenotypeCvterm.cvterm_id)).\
            join(Cv, (Cv.cv_id == Cvterm.cv_id)).\
            filter(*filters).\
            distinct()
        self._compliant_genotype_ids = {i.genotype_id for i in results}
        self.log.info(f'Found {len(self._compliant_genotype_ids)} genotypes already flagged "alliance_compliant".')
        return

    #####################################
    # Lookups answered from the prefetch.
    #####################################

    def feature_basics(self, session, feature_id: int) -> Dict[str, Any]:
        """Get reportable details for one reportable feature; see the base class."""
        if feature_id in self._multi_symbol_ids:
            raise MultipleResultsFound
        basics = self._feature_basics.get(feature_id)
        if basics is None or basics['type'] == 'bogus symbol':
            raise NoResultFound
        return basics

    def component_basics(self, session, feature_id: int) -> Dict[str, Any]:
        """Get reportable details for any component, bogus symbols included; see the base class."""
        if feature_id in self._multi_symbol_ids:
            raise MultipleResultsFound
        basics = self._feature_basics.get(feature_id)
        if basics is None:
            raise NoResultFound
        return basics

    def construct_unspecified_insertion(self, session, construct_feature_id: int) -> FeatureRef:
        """Find a construct's "unspecified" insertion; see ComponentLookup."""
        return self._only_one(self._construct_insertions.get(construct_feature_id, []))

    def balancer_aberration(self, session, balancer: FeatureRef, input_symbol: str) -> FeatureRef:
        """Find a usable balancer's parent aberration; see ComponentLookup."""
        if balancer.feature_id not in self._usable_balancers:
            self.log.error(f'For "{input_symbol}" ({balancer.uniquename}), '
                           f'found no "balancer_status=true" featureprop, so it is not mappable.')
            raise NoResultFound
        return self._only_one(self._balancer_aberrations.get(balancer.feature_id, []))

    def alliance_insertion(self, session, allele_feature_id: int) -> Optional[FeatureRef]:
        """Find an allele's Alliance insertion; see ComponentLookup."""
        feature_refs = self._alliance_insertions.get(allele_feature_id, [])
        if not feature_refs:
            return None
        return self._only_one(feature_refs)

    def allele_construct_insertions(self, session, allele_feature_id: int) -> Dict[int, FeatureRef]:
        """Find an allele's construct-associated insertions; see ComponentLookup."""
        return dict(self._allele_construct_insertions.get(allele_feature_id, {}))

    def is_in_vitro(self, session, allele_feature_id: int) -> bool:
        """Report whether an allele is in vitro; see ComponentLookup."""
        return allele_feature_id in self._in_vitro_alleles

    def is_misexpression_element(self, session, allele_feature_id: int) -> bool:
        """Report whether an allele is a misexpression element; see ComponentLookup."""
        return allele_feature_id in self._misexpression_alleles

    def parental_gene(self, session, allele_feature_id: int) -> FeatureRef:
        """Find an allele's parental Drosophilid gene; see ComponentLookup."""
        return self._only_one(self._parental_genes.get(allele_feature_id, []))

    def possible_genes_for_insertion(self, session, insertion_feature_id: int) -> List[str]:
        """Find the genes an insertion could belong to; see ComponentLookup."""
        return list(self._insertion_genes.get(insertion_feature_id, []))

    def genotype_by_description(self, session, description: str) -> Optional[KnownGenotype]:
        """Find the genotype having a description; see ComponentLookup."""
        known_genotypes = self._genotypes_by_desc.get(description, [])
        if not known_genotypes:
            return None
        return self._only_one(known_genotypes)

    def is_alliance_compliant(self, session, genotype_id: int) -> bool:
        """Report whether a genotype is already flagged compliant; see the base class."""
        return genotype_id in self._compliant_genotype_ids

    def register_alliance_compliant(self, genotype_id: int) -> None:
        """Note a genotype flagged during this run; see the base class."""
        self._compliant_genotype_ids.add(genotype_id)
        return

    def genotype_by_uniquename(self, session, uniquename: str) -> Optional[Tuple[int, Optional[str]]]:
        """Find whichever genotype holds a uniquename; see the base class."""
        return self._genotypes_by_uniquename.get(uniquename)

    def register_genotype(self, description: str, uniquename: str, genotype_id: int, curie: str) -> None:
        """Note a genotype created during this run; see the base class."""
        self._genotypes_by_desc.setdefault(description, []).append(KnownGenotype(genotype_id, uniquename, curie))
        self._genotypes_by_uniquename[uniquename] = (genotype_id, description)
        return

    @staticmethod
    def _only_one(results: List[Any]) -> Any:
        """Return the one result, mirroring the exceptions that SQLAlchemy's one() raises."""
        if not results:
            raise NoResultFound
        if len(results) > 1:
            raise MultipleResultsFound
        return results[0]
