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
import pisilinux.util as util
from pisilinux.scenarioapi.constants import *

def pisilinux_upgraded(*args):
    packages = util.strlist(args).rstrip()
    os.system("pisilinux -D%s upgrade %s" % (consts.pisilinux_db, packages))

def pisilinux_info(package):
    os.system("pisilinux -D%s info %s" % (consts.pisilinux_db, package))

def pisilinux_removed(*args):
    packages = util.strlist(args).rstrip()
    os.system("pisilinux -D%s remove %s" % (consts.pisilinux_db, packages))

def pisilinux_added_repo(name, url):
    os.system("pisilinux -D%s add-repo -y %s %s" % (consts.pisilinux_db, name, url))

def pisilinux_updated_repo():
    os.system("pisilinux -D%s update-repo" % consts.pisilinux_db)

def pisilinux_installed(*args):
    packages = util.strlist(args).rstrip()
    os.system("pisilinux -D%s install %s" % (consts.pisilinux_db, packages))

def pisilinux_reinstalled(package):
    os.system("pisilinux -D%s install --reinstall %s" % (consts.pisilinux_db, package))

