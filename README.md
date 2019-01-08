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
- Tests should be written for each non-trivial function. Please see the `tests` folder for examples.

### Git Branching
- Please branch from develop and merge back via pull request.
- Merges from develop into master should coincide with a new release tag on master and a version increment.
