#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `harvdev_utils` package."""
import pytest

from harvdev_utils.char_conversions import sub_sup_to_sgml

dict_to_test = {
    '[[' : '<down>',
    ']]' : '</down>',
    '[' : '<up>',
    ']' : '</up>'
}

@pytest.mark.parametrize('key', dict_to_test.keys())
def test_unicode_to_plain_text(key):
    assert sub_sup_to_sgml(dict_to_test[key]) == dict_to_test[key]