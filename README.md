[![Build Status](https://travis-ci.com/FlyBase/harvdev-utils.svg?branch=master)](https://travis-ci.com/FlyBase/harvdev-utils)
[![Documentation Status](https://readthedocs.org/projects/harvdev-utils/badge/?version=latest)](https://harvdev-utils.readthedocs.io/en/latest/?badge=latest)

# harvdev_utils Python package
Common Python functions and classes used by FlyBase developers at Harvard.

## Installation

`pip install -e git+https://github.com/FlyBase/harvdev-utils.git@master#egg=harvdev_utils`

## Documentation

- Detailed information for some functions can be found in the [Read the Docs documentation](https://harvdev-utils.readthedocs.io/en/latest/?). This documentation does not include information regarding SQLAlchemy classes and functions (see below).

### SQLAlchemy Classes

- `harvdev_utils` contains two sets of SQLAlchemy classes for use with FlyBase Harvard's `production` and `reporting` databases. The class names correspond to tables within the Chado database and serve as an integral part of writing SQLAlchemy code.
- To use these classes, include the appropriate imports at the top of your Python module:
  - When using production or reporting individually (the classes share overlapping names, so _only_ use this approach if `production` / `reporting` queries are **not** written together in the same module):
    - `from harvdev_utils.production import *`
    - `from harvdev_utils.reporting import *`
  - When using production or reporting both within the _same_ module:
    - `from harvdev_utils import production as prod`
    - `from harvdev_utils import reporting as rep`
    - Code can then be written by prefixing the classes as appropriate when calling them, _e.g._ `prod.Feature`, `rep.Feature`, `rep.Pub`, `prod.Cvterm`, _etc_.

### SQLAlchemy Functions

- `harvdev_utils` contains a set of commonly used Chado-SQLAlchemy functions:

  -  **`harvdev_utils.chado_functions.get_or_create`**
      -  This function allows for values to be inserted into a specific Chado table. If the values already exist in the table, nothing is inserted. If the table uses `rank`, the `rank` value is automatically incremented and the values are _always_ inserted.
      -  Example import: `from harvdev_utils.chado_functions import get_or_create`
      -  The function as defined in the module: `def get_or_create(session, model, ret_col=None, **kwargs)`
      -  Required fields:
          -  `session`: Your SQLAlchemy session.
          -  `model`: The model (aka table) where you'd like to insert data.
          -  `kwargs**`: Values used to look up the appropriate row of a table to insert the data. Please see the example below.
      -  Optional fields: 
          -  `ret_col=` If you'd like a specific value returned from this function, specify the column name of the value you'd like back. Useful when creating new identifiers where you'd like to immediately know just the identifier number.
      -  Example without `ret_col`:
          -  `Fcp = get_or_create(session, FeatureCvtermprop, feature_cvterm_id=feature_cvterm_id_fly, type_id=qualifier_cv_term_id, value='model of')`
          -  `print(Fcp.feature_cvterm_id)`
      -  Another example without `ret_col` where we do not capture the return object:
          -  `get_or_create(session, FeatureCvtermprop, feature_cvterm_id=feature_cvterm_id_fly, type_id=qualifier_cv_term_id, value='model of')`
      -  Example with `ret_col`:
          -  `feature_cvterm_id_fly = get_or_create(session, FeatureCvterm, pub_id=pub_id, feature_id=fly_feature_id, cvterm_id=cv_term_id_disease, ret_col='feature_cvterm_id')`
      -  The debugging level is set to `INFO` by default and can be changed to `DEBUG` by using the following line in your script where appropriate:
          -  `logging.getLogger('harvdev_utils.chado_functions.get_or_create').setLevel(logging.DEBUG)`


## General Development
- The [dev_readme.md](dev/dev_readme.md) file contains instructions for regenerating SQLAlchemy classes.

- Please use [PEP8](https://www.python.org/dev/peps/pep-0008/) whenever possible. 
- Docstrings should follow Google's style guides ([Sphinx guide](http://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html#module-sphinx.ext.napoleon), [additional example 1](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html), [additional example 2](http://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)) and are used to generate [Read the Docs documentation](https://harvdev-utils.readthedocs.io/en/latest/?).
- Tests should be written for each non-trivial function. Please see the `tests` folder for examples. We're using [pytest](https://docs.pytest.org/en/latest/) via [Travis CI](https://travis-ci.com/FlyBase/harvdev_utils.svg?branch=master) for testing. Tests can be run locally with the command `python -m pytest -v` from the root directory of the repository (`-v` flag is optional). 

#### Git Branching

- Please branch from develop and merge back via pull request.
- Merges from develop into master should coincide with a new release tag on master and a version increment.

#### Writing Documentation

- The file `docs/index.rst` should be updated after a new module is added. The `automodule` command will automatically pull in information for specified modules once the code is pushed to GitHub. Please see the [automodule documentation](http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#directive-automodule) for help.

#### Example Development Workflow

- Clone the repository and branch off develop.
- Navigate to the directory `harvdev_utils` and use an existing folder (_e.g._ `char_conversions`) or create a new folder based on the goal of your module.
- Create a single python file containing a function to be used. Feel free to add multiple functions to a single python file if you feel it's appropriate.
- Be sure to add an entry to the `__init__.py` file in the folder where you're working.
    - _e.g._ `from .unicode_to_plain_text import unicode_to_plain_text`
- Update the file `__init__.py` in `harvdev_utils` and add your function to the list of default loaded functions. If the folder you are using does not exist at the top of the file, be sure to import it. 
    - _e.g._ `from .char_conversions import *`
- Navigate to the `tests` folder and create a new sub-folder if you're not using a currently deployed folder (_i.e._ if you're using `char_conversions`, the folder already exists).
- Create your `test` python file with the prefix `test_` .
    - _e.g._ `test_sgml_to_plain_text.py`
- Tests can be run locally with `python -m pytest` from the root directory of the repository.
- Edit the file `docs/index.rst` and be sure the folder that you're using is listed as an automodule.
    - _e.g._ `.. automodule:: harvdev_utils :members:`
- Additional text can be added to `docs/index.rst` as necessary. We can restructure this file if it becomes too long / complex.
- Push your branch to GitHub and open a PR to develop when ready.
- A subsequence merge to master and tagged release can be coordinated with other devs when appropriate.
