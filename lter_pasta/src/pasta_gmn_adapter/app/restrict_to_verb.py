#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""":mod:`restrict_to_verb`
==========================

:Synopsis: Limit views to be called only with specific verb.
:Author: Roger Dahl
"""

import django.http


def _allow_only_verbs(f, verbs):
  def wrap(request, *args, **kwargs):
    if request.method not in verbs:
      return django.http.HttpResponseNotAllowed(verbs)
    return f(request, *args, **kwargs)

  wrap.__doc__ = f.__doc__
  wrap.__name__ = f.__name__
  return wrap


def get(f):
  return _allow_only_verbs(f, ['GET'])


def put(f):
  return _allow_only_verbs(f, ['PUT'])


def post(f):
  return _allow_only_verbs(f, ['POST'])


def delete(f):
  return _allow_only_verbs(f, ['DELETE'])
