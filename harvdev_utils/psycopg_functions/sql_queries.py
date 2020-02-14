"""Module:: sql_queries.

Synopsis:
      Commonly used sql queries. Use ".format()" function to add values for "{}" variables.

Author(s):
      Gil dos Santos dossantos@morgan.harvard.edu

"""

# Get all current, non-analysis features given a uniquename regex.
current_features = """
    SELECT DISTINCT f.feature_id,
                    f.organism_id,
                    f.name,
                    f.uniquename,
                    cvt.name,
                    f.is_analysis,
                    f.is_obsolete
    FROM feature f
    JOIN cvterm cvt ON cvt.cvterm_id = f.type_id
    WHERE f.is_obsolete = false and
          f.is_analysis = false and
          f.uniquename ~ '{}';
    """

# Get all current symbol synonym_sgml for all features given a uniquename regex.
current_feat_symbol_sgmls = """
    SELECT DISTINCT f.uniquename,
                    s.synonym_sgml
    FROM feature f
    JOIN feature_synonym fs ON fs.feature_id = f.feature_id
    JOIN synonym s ON s.synonym_id = fs.synonym_id
    JOIN cvterm cvts ON cvts.cvterm_id = s.type_id
    WHERE f.is_obsolete = false and
          f.is_analysis = false and
          f.uniquename ~ '{}' and
          fs.is_current = true and
          fs.is_internal = false and
          cvts.name = 'symbol';
    """

# Get all current fullname synonym_sgml for all features given a uniquename regex.
current_feat_fullname_sgmls = """
    SELECT DISTINCT f.uniquename,
                    s.synonym_sgml
    FROM feature f
    JOIN feature_synonym fs ON fs.feature_id = f.feature_id
    JOIN synonym s ON s.synonym_id = fs.synonym_id
    JOIN cvterm cvts ON cvts.cvterm_id = s.type_id
    WHERE f.is_obsolete = false and
          f.is_analysis = false and
          f.uniquename ~ '{}' and
          fs.is_current = true and
          fs.is_internal = false and
          cvts.name = 'fullname';
    """

# Get subject, object features for subject, object uniquename regex, and rel type.
rel_features = """
    SELECT DISTINCT s.uniquename,
                    o.uniquename
    FROM feature s
    JOIN feature_relationship fr ON fr.subject_id = s.feature_id
    JOIN feature o ON o.feature_id = fr.object_id
    JOIN cvterm cvtfr ON cvtfr.cvterm_id = fr.type_id
    WHERE s.is_obsolete = false and
          s.uniquename ~ '{}' and
          o.is_obsolete = false and
          o.uniquename ~ '{}' and
          cvtfr.name = '{}';
    """

# Reverse perspective of the above query.
# Get object, subject features for object, subject uniquename regex, and rel type.
rel_features_rev = """
    SELECT DISTINCT o.uniquename,
                    s.uniquename
    FROM feature s
    JOIN feature_relationship fr ON fr.subject_id = s.feature_id
    JOIN feature o ON o.feature_id = fr.object_id
    JOIN cvterm cvtfr ON cvtfr.cvterm_id = fr.type_id
    WHERE o.is_obsolete = false and
          o.uniquename ~ '{}' and
          s.is_obsolete = false and
          s.uniquename ~ '{}' and
          cvtfr.name = '{}';
    """

# Get subject, object features for subject, object uniquename regex, and rel type.
# Object constrained to Dmel
rel_dmel_features = """
    SELECT DISTINCT s.uniquename,
                    o.uniquename
    FROM feature s
    JOIN feature_relationship fr ON fr.subject_id = s.feature_id
    JOIN feature o ON o.feature_id = fr.object_id
    JOIN cvterm cvtfr ON cvtfr.cvterm_id = fr.type_id
    WHERE s.is_obsolete = false and
          s.uniquename ~ '{}' and
          o.is_obsolete = false and
          o.uniquename ~ '{}' and
          o.organism_id = 1 and
          cvtfr.name = '{}';
    """

# Reverse perspective of the above query.
# Get object, subject features for object, subject uniquename regex, and rel type.
# Subject constrained to Dmel
rel_dmel_features_rev = """
    SELECT DISTINCT o.uniquename,
                    s.uniquename
    FROM feature s
    JOIN feature_relationship fr ON fr.subject_id = s.feature_id
    JOIN feature o ON o.feature_id = fr.object_id
    JOIN cvterm cvtfr ON cvtfr.cvterm_id = fr.type_id
    WHERE o.is_obsolete = false and
          o.uniquename ~ '{}' and
          s.is_obsolete = false and
          s.uniquename ~ '{}' and
          s.organism_id = 1 and
          cvtfr.name = '{}';
    """

# Get subject of f_r1, object of f_r2 where an intermediate feat is f_r1.object and f_r2.subject.
# Must provide subject regex, intermediate feature regex, object regex, and rel_types for f_r1 and f_r2.
indirect_rel_features = """
    SELECT DISTINCT s.uniquename,
                    o.uniquename
    FROM feature s
    JOIN feature_relationship fr1 ON fr1.subject_id = s.feature_id
    JOIN feature i ON i.feature_id = fr1.object_id
    JOIN feature_relationship fr2 ON fr2.subject_id = i.feature_id
    JOIN feature o ON o.feature_id = fr2.object_id
    JOIN cvterm cvtfr1 ON cvtfr1.cvterm_id = fr1.type_id
    JOIN cvterm cvtfr2 ON cvtfr2.cvterm_id = fr2.type_id
    WHERE s.is_obsolete = false and
          s.is_analysis = false and
          s.uniquename ~ '{}' and
          i.is_obsolete = false and
          i.is_analysis = false and
          i.uniquename ~ '{}' and
          o.is_obsolete = false and
          o.is_analysis = false and
          o.uniquename ~ '{}' and
          cvtfr1.name = '{}' and
          cvtfr2.name = '{}'
    """

# Get all symbol synonyms for features given a feature uniquename regex.
# Include "current" synonym.name (in case it differs from current synonym_sgml).
feat_symbol_synonyms = """
    SELECT DISTINCT f.uniquename,
                    s.name
    FROM feature f
    JOIN feature_synonym fs ON fs.feature_id = f.feature_id
    JOIN synonym s ON s.synonym_id = fs.synonym_id
    JOIN cvterm cvts ON cvts.cvterm_id = s.type_id
    WHERE f.is_obsolete = false and
          f.is_analysis = false and
          f.uniquename ~ '{}' and
          -- fs.is_current = false and
          s.name != s.synonym_sgml and
          fs.is_internal = false and
          cvts.name = 'symbol'
    UNION
    SELECT DISTINCT f.uniquename,
                    s.synonym_sgml
    FROM feature f
    JOIN feature_synonym fs ON fs.feature_id = f.feature_id
    JOIN synonym s ON s.synonym_id = fs.synonym_id
    JOIN cvterm cvts ON cvts.cvterm_id = s.type_id
    WHERE f.is_obsolete = false and
          f.is_analysis = false and
          f.uniquename ~ '{}' and
          fs.is_current = false and
          fs.is_internal = false and
          cvts.name = 'symbol';
    """

# Get all symbol synonyms for features given a feature uniquename regex.
# Include "current" synonym.name (in case it differs from current synonym_sgml).
feat_fullname_synonyms = """
    SELECT DISTINCT f.uniquename,
                    s.name
    FROM feature f
    JOIN feature_synonym fs ON fs.feature_id = f.feature_id
    JOIN synonym s ON s.synonym_id = fs.synonym_id
    JOIN cvterm cvts ON cvts.cvterm_id = s.type_id
    WHERE f.is_obsolete = false and
          f.is_analysis = false and
          f.uniquename ~ '{}' and
          -- fs.is_current = false and
          s.name != s.synonym_sgml and
          fs.is_internal = false and
          cvts.name = 'fullname'
    UNION
    SELECT DISTINCT f.uniquename,
                    s.synonym_sgml
    FROM feature f
    JOIN feature_synonym fs ON fs.feature_id = f.feature_id
    JOIN synonym s ON s.synonym_id = fs.synonym_id
    JOIN cvterm cvts ON cvts.cvterm_id = s.type_id
    WHERE f.is_obsolete = false and
          f.is_analysis = false and
          f.uniquename ~ '{}' and
          fs.is_current = false and
          fs.is_internal = false and
          cvts.name = 'fullname';
    """

# Get all secondary FB IDs for given a feature uniquename regex and accession regex.
feat_secondary_fbids = """
    SELECT DISTINCT f.uniquename,
                    dbx.accession
    FROM feature f
    JOIN feature_dbxref fdbx ON fdbx.feature_id = f.feature_id
    JOIN dbxref dbx ON dbx.dbxref_id = fdbx.dbxref_id
    JOIN db ON db.db_id = dbx.db_id
    WHERE f.is_obsolete = false and
          f.is_analysis = false and
          f.uniquename ~ '{}' and
          fdbx.is_current = false and
          dbx.accession ~ '{}' and
          db.name = 'FlyBase';
    """

# Get all featureprops of a given type for a given feature (specified by regex).
featureprops = """
    SELECT DISTINCT f.uniquename,
                    fp.value
    FROM feature f
    JOIN featureprop fp ON fp.feature_id = f.feature_id
    JOIN cvterm cvtfp ON cvtfp.cvterm_id = fp.type_id
    WHERE f.is_obsolete = false and
          f.is_analysis = false and
          f.uniquename ~ '{}' and
          cvtfp.name = '{}';
    """

# Get CV terms for given feature (uniquename regex) and CV.
feat_cvterm = """
    SELECT DISTINCT f.uniquename,
                    cvt.name
    FROM feature f
    JOIN feature_cvterm fcvt ON fcvt.feature_id = f.feature_id
    JOIN cvterm cvt ON cvt.cvterm_id = fcvt.cvterm_id
    JOIN cv ON cv.cv_id = cvt.cv_id
    WHERE f.is_obsolete = false and
          f.is_analysis = false and
          f.uniquename ~ '{}' and
          cv.name = '{}';
    """

# Get CV terms for given feature (uniquename regex), from a given CV, having a given cvtermprop.
feat_cvterm_cvtprop = """
    SELECT DISTINCT f.uniquename,
                    cvt.name
    FROM feature f
    JOIN feature_cvterm fcvt ON fcvt.feature_id = f.feature_id
    JOIN cvterm cvt ON cvt.cvterm_id = fcvt.cvterm_id
    JOIN cv ON cv.cv_id = cvt.cv_id
    JOIN cvtermprop cvtp ON cvtp.cvterm_id = cvt.cvterm_id
    WHERE f.is_obsolete = false and
          f.is_analysis = false and
          f.uniquename ~ '{}' and
          cv.name = '{}' and
          cvtp.value = '{}';
    """

# Get an organism_id to organism genus correspondence.
orgid_genus = """
    SELECT DISTINCT organism_id,
                    genus
    FROM organism;
    """

# Get an organism to organism abbreviation correspondence.
orgid_abbr = """
    SELECT DISTINCT organism_id,
                    abbreviation
    FROM organism
    WHERE abbreviation IS NOT NULL;
    """

# Get a uniquename-to-symbol_synonym_sgml correspondence.
feat_id_symbol_sgml = """
    SELECT DISTINCT f.uniquename,
                    s.synonym_sgml
    FROM feature f
    JOIN feature_synonym fs ON fs.feature_id = f.feature_id
    JOIN synonym s ON s.synonym_id = fs.synonym_id
    JOIN cvterm cvts ON cvts.cvterm_id = s.type_id
    WHERE f.is_obsolete = false and
          f.is_analysis = false and
          f.uniquename ~ '{}' and
          fs.is_current = true and
          fs.is_internal = false and
          cvts.name = 'symbol';
    """

# Get a uniquename-to-MOD_ID correspondence.
gene_MOD_ids = """
    SELECT DISTINCT f.uniquename,
                    db.name||':'||dbx.accession
    FROM feature f
    JOIN feature_dbxref fdbx ON fdbx.feature_id = f.feature_id
    JOIN dbxref dbx ON dbx.dbxref_id = fdbx.dbxref_id
    JOIN db ON db.db_id = dbx.db_id
    WHERE f.is_obsolete = false and
          f.is_analysis = false and
          f.uniquename ~ '{}' and
          fdbx.is_current = true and
          db.name in ('SGD', 'WormBase', 'ZFIN', 'RGD', 'MGI');
    """

# Get a uniquename-to-MOD_ID correspondence.
gene_HGNC_ids = """
    SELECT DISTINCT f.uniquename,
                    db.name||':'||dbx.accession
    FROM feature f
    JOIN organism o ON o.organism_id = f.organism_id
    JOIN feature_dbxref fdbx ON fdbx.feature_id = f.feature_id
    JOIN dbxref dbx ON dbx.dbxref_id = fdbx.dbxref_id
    JOIN db ON db.db_id = dbx.db_id
    WHERE f.is_obsolete = false and
          f.is_analysis = false and
          f.uniquename ~ '{}' and
          o.abbreviation = 'Hsap' and
          fdbx.is_current = true and
          db.name = 'HGNC';
    """
