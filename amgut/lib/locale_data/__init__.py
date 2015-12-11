#!/usr/bin/env python
from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The American Gut Project Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


available_locales = set([
    'american_gut', 'british_gut'])


media_locale = {
    'SURVEY_VIOSCREEN_URL': 'https://demo.vioscreen.com/%(survey_id)s',  # THIS IS CURRENTLY MOCKED OUT
    'SURVEY_ASD_URL': 'https://redcapdemo.vanderbilt.edu/surveys/?s=EEAPA8DWDL&survey_id=%(survey_id)s'
}
