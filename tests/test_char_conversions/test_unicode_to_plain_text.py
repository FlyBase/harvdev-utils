#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `harvdev_utils` package."""
import pytest

from harvdev_utils.char_conversions import unicode_to_plain_text

dict_to_test = {
    '\u03B1' : 'alpha',
    '\u0391' : 'Alpha',
    '\u03B2' : 'beta',
    '\u0392' : 'Beta',
    '\u03B3' : 'gamma',
    '\u0393' : 'Gamma',
    '\u03B4' : 'delta',
    '\u0394' : 'Delta',
    '\u03B5' : 'epsilon',
    '\u0395' : 'Epsilon',
    '\u03B6' : 'zeta', 
    '\u0396' : 'Zeta',
    '\u03B7' : 'eta',
    '\u0397' : 'Eta',
    '\u03B8' : 'theta',
    '\u0398' : 'Theta',
    '\u03B9' : 'iota',
    '\u0399' : 'Iota',
    '\u03BA' : 'kappa',
    '\u039A' : 'Kappa',
    '\u03BB' : 'lambda',
    '\u039B' : 'Lambda',
    '\u03BC' : 'mu',
    '\u039C' : 'Mu',
    '\u03BD' : 'nu',
    '\u039D' : 'Nu',
    '\u03BE' : 'xi',
    '\u039E' : 'Xi',
    '\u03BF' : 'omicron',
    '\u039F' : 'Omicron',
    '\u03C0' : 'pi',
    '\u03A0' : 'Pi',
    '\u03C1' : 'rho',
    '\u03A1' : 'Rho',
    '\u03C3' : 'sigma',
    '\u03A3' : 'Sigma',
    '\u03C4' : 'tau',
    '\u03A4' : 'Tau',
    '\u03C5' : 'upsilon',
    '\u03A5' : 'Upsilon',
    '\u03C6' : 'phi',
    '\u03A6' : 'Phi',
    '\u03C7' : 'chi',
    '\u03A7' : 'Chi',
    '\u03C8' : 'psi',
    '\u03A8' : 'Psi',
    '\u03C9' : 'omega',
    '\u03A9' : 'Omega'
    }

@pytest.mark.parametrize('key', dict_to_test.keys())
def test_unicode_to_plain_text(key):
    assert unicode_to_plain_text(dict_to_test[key]) == dict_to_test[key]