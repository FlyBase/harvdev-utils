[![Build Status](https://travis-ci.com/FlyBase/harvdev_utils.svg?branch=master)](https://travis-ci.com/FlyBase/harvdev_utils)
[![Documentation Status](https://readthedocs.org/projects/harvdev-utils/badge/?version=latest)](https://harvdev-utils.readthedocs.io/en/latest/?badge=latest)

# harvdev_utils
Common Python functions used by FlyBase developers at Harvard.

## Installation
`pip install -e git+https://github.com/FlyBase/harvdev_utils.git#egg=harvdev_utils`

## Documentation
- Detailed information for all available functions can be found in the [Read the Docs documentation](https://harvdev-utils.readthedocs.io/en/latest/?).

## Development
- Please use [PEP8](https://www.python.org/dev/peps/pep-0008/) whenever possible. 
- Docstrings should follow Google's style guides ([Sphinx guide](http://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html#module-sphinx.ext.napoleon), [additional example 1](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html), [additional example 2](http://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)) and are used to generate [Read the Docs documentation](https://harvdev-utils.readthedocs.io/en/latest/?).
- Tests should be written for each non-trivial function. Please see the `tests` folder for examples. We're using [pytest](https://docs.pytest.org/en/latest/) via [Travis CI](https://travis-ci.com/FlyBase/harvdev_utils.svg?branch=master) for testing. Tests can be run locally with the command `python -m pytest` from the root directory of the repository. 

#### Git Branching
- Please branch from develop and merge back via pull request.
- Merges from develop into master should coincide with a new release tag on master and a version increment.

#### Writing Documentation
- The file `docs/index.rst` should be updated after a new module is added. The `automodule` command will automatically pull in information for specified modules once the code is pushed to GitHub. Please see the [automodule documentation](http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#directive-automodule) for help.

#### Example Development Workflow
- Clone the repository and branch off develop.
- Navigate to the directory `harvdev_utils` and use an existing folder (_e.g._ `char_conversions`) or create a new folder based on the goal of your module.
- Create a single python file containing a function to be used.
- Be sure to add an entry to the `__init__.py` file in the folder where you're working.
    - _e.g._ `from .unicode_to_plain_text import unicode_to_plain_text`
- Update the file `__init__.py` in `harvdev_utils` and add your function to the list of default loaded functions. If the folder you are using does not exist at the top of the file, be sure to import it. 
    - _e.g._ `from .char_conversions import *`
- Navigate to the `tests` folder and create a new sub-folder if you're not using a currently deployed folder (_i.e._ if you're using `char_conversions`, the folder already exists).
- Create your `test` python file with the prefix `test` .
    - _e.g._ `test_sgml_to_plain_text.py`
- Tests can be run locally with `python -m pytest` from the root directory of the repository.
- Edit the file `docs/index.rst` and be sure the folder that you're using is listed as an automodule.
    - _e.g._ `.. automodule:: harvdev_utils :members:`
- Additional text can be added to `docs/index.rst` as necessary. We can restructure this file if it becomes too long / complex.
- Push your branch to GitHub and open a PR to develop when ready.
- A subsequence merge to master and tagged release can be coordinated with other devs when appropriate.