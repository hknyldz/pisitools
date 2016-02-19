# -*- coding: utf-8 -*-
#
# Copyright (C) 2009, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import pisilinux
import pisilinux.pxml.xmlfile as xmlfile
import pisilinux.pxml.autoxml as autoxml

class Error(pisi.Error):
    pass

__metaclass__ = autoxml.autoxml

class Group(xmlfile.XmlFile, metaclass=autoxml.autoxml):
    "representation for group declarations"

    t_Name = [autoxml.String, autoxml.mandatory]
    t_LocalName = [autoxml.LocalText, autoxml.mandatory]
    t_Icon = [ autoxml.String, autoxml.optional]

class Groups(xmlfile.XmlFile, metaclass=autoxml.autoxml):
    "representation for component declarations"

    tag = "PISI"

    t_Groups = [ [Group], autoxml.optional, "Groups/Group" ]
