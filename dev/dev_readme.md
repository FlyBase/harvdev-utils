# Regenerating SQL Alchemy database files

Instructions for refreshing the SQL Alchemy database files.

## Running sqlacodegen

- Install sqlacodegen if it is not already installed.
  - `pip install sqlacodegen`
- Run sqlacodegen against production or reporting, depending on the files you'd like to refresh. Replace `<postgresql_pw>` with your relevant password and update `<reporting_database>` with the name of the appropriate reporting database.
  - Production: `sqlacodegen postgresql://ctabone:<postgresql_pw>@flysql19:5432/production_chado --outfile production.py`
  - Reporting: `sqlacodegen postgresql://ctabone:<postgresql_pw>@flysql20:5432/<reporting_database> --outfile reporting.py`
- Move the output file into `harvdev_utils/production` or `harvdev_utils/reporting` as appropriate. This will overwrite the existing file.
- In the `production` or `reporting` directory, run the script `production_gene_init.py` or `reporting_gen_init.py` as appropriate (_e.g._ `python production_gene_init.py`). This will regenerate the `__init__.py` file with up-to-date classes.
