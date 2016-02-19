#!/usr/bin/python
#-*- coding: utf-8 -*-
#
# Copyright (C) 2006, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import os

from pisilinux.scenarioapi.repoops import *
from pisilinux.scenarioapi.pisilinuxops import *
from pisilinux.scenarioapi.constants import *

def let_repo_had(package, *args):
    repo_added_package(package, *args)
    repo_updated_index()

def let_pisilinux_had(*args):
    url = os.path.join(os.getcwd(), consts.repo_url)
    pisilinux_added_repo(consts.repo_name, url)
    packages = util.strlist(args).rstrip()
    os.system("pisilinux -D%s install --ignore-dependency %s" % (consts.pisilinux_db, packages))
