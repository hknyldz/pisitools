# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2011, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.

import os
import fcntl
import re
from . import fetcher

import gettext
__trans = gettext.translation('pisilinux', fallback=True)
_ = __trans.gettext

import pisilinux
import pisilinux.context as ctx
import pisilinux.uri
import pisilinux.util
import pisilinux.pgraph as pgraph
import pisilinux.db.packagedb
import pisilinux.db.repodb
import pisilinux.db.filesldb
import pisilinux.db.installdb
import pisilinux.db.historydb
import pisilinux.db.sourcedb
import pisilinux.db.componentdb
import pisilinux.db.groupdb
import pisilinux.index
import pisilinux.config
import pisilinux.metadata
import pisilinux.file
import pisilinux.blacklist
import pisilinux.atomicoperations
import pisilinux.operations.remove
import pisilinux.operations.upgrade
import pisilinux.operations.install
import pisilinux.operations.history
import pisilinux.operations.helper
import pisilinux.operations.check
import pisilinux.operations.emerge
import pisilinux.operations.build
import pisilinux.errors

def locked(func):
    """
    Decorator for synchronizing privileged functions
    """
    def wrapper(*__args,**__kw):
        try:
            lock = file(pisilinux.util.join_path(pisilinux.context.config.lock_dir(), 'pisilinux'), 'w')
        except IOError:
            raise pisilinux.errors.PrivilegeError(_("You have to be root for this operation."))

        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            ctx.locked = True
        except IOError:
            if not ctx.locked:
                raise pisilinux.errors.AnotherInstanceError(_("Another instance of pisilinux is running. Only one instance is allowed."))

        try:
            pisilinux.db.invalidate_caches()
            ret = func(*__args,**__kw)
            pisilinux.db.update_caches()
            return ret
        finally:
            ctx.locked = False
            lock.close()
    return wrapper

def set_userinterface(ui):
    """
    Set the user interface where the status information will be send
    @param ui: User interface
    """
    ctx.ui = ui

def set_io_streams(stdout=None, stderr=None):
    """
    Set standart i/o streams
    Used by Buildfarm
    @param stdout: Standart output
    @param stderr: Standart input
    """
    if stdout:
        ctx.stdout = stdout
    if stderr:
        ctx.stderr = stderr

def set_comar(enable):
    """
    Set comar usage
    False means no preremove and postinstall scripts will be run
    @param enable: Flag indicating comar usage
    """
    ctx.comar = enable

def set_comar_updated(updated):
    """
    Set comar package update status
    @param updated: True if COMAR package is updated, else False
    """
    ctx.comar_updated = updated

def set_dbus_sockname(sockname):
    """
    Set dbus socket file
    Used by YALI
    @param sockname: Path to dbus socket file
    """
    ctx.dbus_sockname = sockname

def set_dbus_timeout(timeout):
    """
    Set dbus timeout
    Used by YALI
    @param timeout: Timeout in seconds
    """
    ctx.dbus_timeout = timeout

def set_signal_handling(enable):
    """
    Enable signal handling. Signal handling in pisilinux mostly used for disabling keyboard interrupts
    in critical paths.
    Used by YALI
    @param enable: Flag indicating signal handling usage
    """
    if enable:
        ctx.sig = pisilinux.signalhandler.SignalHandler()
    else:
        ctx.sig = None

def set_options(options):
    """
    Set various options of pisilinux
    @param options: option set

           >>> options = pisilinux.config.Options()

           options.destdir     # pisilinux destination directory where operations will take effect
           options.username    # username that for reaching remote repository
           options.password    # password that for reaching remote repository
           options.debug       # flag controlling debug output
           options.verbose     # flag controlling verbosity of the output messages
           options.output_dir  # build and delta operations package output directory
    """
    ctx.config.set_options(options)

def list_needs_restart():
    """
    Return a list of packages that need a service restart.
    """
    return pisilinux.db.installdb.InstallDB().list_needs_restart()

def list_needs_reboot():
    """
    Return a list of packages that need a system reboot.
    """
    return pisilinux.db.installdb.InstallDB().list_needs_reboot()

def add_needs_restart(package):
    """
    Add a new package to service restart list.
    """
    pisilinux.db.installdb.InstallDB().mark_needs_restart(package)

def add_needs_reboot(package):
    """
    Add a new package to system reboot list.
    """
    pisilinux.db.installdb.InstallDB().mark_needs_reboot(package)

def remove_needs_restart(package):
    """
    Remove a package from service restart list. Passing "*" will clear whole list.
    """
    pisilinux.db.installdb.InstallDB().clear_needs_restart(package)

def remove_needs_reboot(package):
    """
    Remove a package from system reboot list. Passing "*" will clear whole list.
    """
    pisilinux.db.installdb.InstallDB().clear_needs_reboot(package)

def list_pending():
    """
    Return a list of configuration pending packages -> list_of_strings
    """
    return pisilinux.db.installdb.InstallDB().list_pending()

def list_installed():
    """
    Return a list of installed packages -> list_of_strings
    """
    return pisilinux.db.installdb.InstallDB().list_installed()

def list_obsoleted(repo=None):
    """
    Return a list of obsoleted packages -> list_of_strings
    @param repo: Repository of the obsoleted packages. If repo is None than returns
    a list of all the obsoleted packages in all the repositories
    """
    return pisilinux.db.packagedb.PackageDB().get_obsoletes(repo)

def list_replaces(repo=None):
    """
    Return a dictionary of the replaced packages in the given repository
    @param repo: Repository of the replaced packages. If repo is None than returns
    a dictionary of all the replaced packages in all the repositories

    {'gaim':['pidgin'], 'gimp-i18n':['gimp-i18n-tr', 'gimp-18n-de', ...]}

    gaim replaced by pidgin and gimp-i18n is divided into smaller packages which also
    replaces gimp-i18n
    """
    return pisilinux.db.packagedb.PackageDB().get_replaces(repo)

def list_available(repo=None):
    """
    Return a list of available packages in the given repository -> list_of_strings
    @param repo: Repository of the packages. If repo is None than returns
    a list of all the available packages in all the repositories
    """
    return pisilinux.db.packagedb.PackageDB().list_packages(repo)

def list_sources(repo=None):
    """
    Return a list of available source packages in the given repository -> list_of_strings
    @param repo: Repository of the source packages. If repo is None than returns
    a list of all the available source packages in all the repositories
    """
    return pisilinux.db.sourcedb.SourceDB().list_sources(repo)

def list_newest(repo=None, since=None):
    """
    Return a list of newest packages in the given repository -> list_of_strings since
    last update or before.
    @param repo: Repository of the packages. If repo is None than returns a list of
    all the newest packages from all the repositories.
    @param since: yyyy-mm-dd formatted
    """
    return pisilinux.db.packagedb.PackageDB().list_newest(repo, since)

def list_upgradable():
    """
    Return a list of packages that are upgraded in the repository -> list_of_strings
    """
    installdb = pisilinux.db.installdb.InstallDB()
    is_upgradable = pisilinux.operations.upgrade.is_upgradable

    upgradable = list(filter(is_upgradable, installdb.list_installed()))
    # replaced packages can not pass is_upgradable test, so we add them manually
    upgradable.extend(list_replaces())

    # consider also blacklist filtering
    upgradable = pisilinux.blacklist.exclude_from(upgradable, ctx.const.blacklist)

    return upgradable

def list_repos(only_active=True):
    """
    Return a list of the repositories -> list_of_strings
    @param only_active: return only the active repos list -> list_of_strings
    """
    return pisilinux.db.repodb.RepoDB().list_repos(only_active)

def get_install_order(packages):
    """
    Return a list of packages in the installation order with extra needed
    dependencies -> list_of_strings
    @param packages: list of package names -> list_of_strings
    """
    install_order = pisilinux.operations.install.plan_install_pkg_names
    i_graph, order = install_order(packages)
    return order

def get_remove_order(packages):
    """
    Return a list of packages in the remove order -> list_of_strings
    @param packages: list of package names -> list_of_strings
    """
    remove_order = pisilinux.operations.remove.plan_remove
    i_graph, order = remove_order(packages)
    return order

def get_upgrade_order(packages):
    """
    Return a list of packages in the upgrade order with extra needed
    dependencies -> list_of_strings
    @param packages: list of package names -> list_of_strings
    """
    upgrade_order = pisilinux.operations.upgrade.plan_upgrade
    i_graph, order = upgrade_order(packages)
    return order

def get_base_upgrade_order(packages):
    """
    Return a list of packages of the system.base component that needs to be upgraded
    or installed in install order -> list_of_strings
    All the packages of the system.base component must be installed on the system
    @param packages: list of package names -> list_of_strings
    """
    upgrade_order = pisilinux.operations.upgrade.upgrade_base
    order = upgrade_order(packages)
    return list(order)

def get_conflicts(packages):
    """
    Return a tuple of the conflicting packages information -> tuple
    @param packages: list of package names -> list_of_strings

    >>> (pkgs, within, pairs) = pisilinux.api.get_conflicts(packages)
    >>>
    >>> pkgs # list of packages that are installed and conflicts with the
             # given packages list -> list_of_strings
    >>> [...]
    >>> within # list of packages that already conflict with each other
               # in the given packages list -> list_of_strings
    >>> [...]
    >>> pairs # dictionary of conflict information that contains which package in the
              # given packages list conflicts with which of the installed packages

    >>> {'imlib2': <class pisilinux.conflict.Conflict>, 'valgrind': <class pisilinux.conflict.Conflict>,
    'libmp4v2':'<class pisilinux.conflict.Conflict>}

    >>> print map(lambda c:str(pairs[c]), pairs)
    >>> ['imblib', 'callgrind', 'faad2 release >= 3']
    """
    return pisilinux.conflict.calculate_conflicts(packages, pisilinux.db.packagedb.PackageDB())

def check(package, config=False):
    """
    Returns a dictionary that contains a list of both corrupted and missing files
    @param package: name of the package to be checked
    @param config: _only_ check the config files of the package, default behaviour is to check all the files
    of the package but the config files
    """
    return pisilinux.operations.check.check_package(package, config)

def search_package(terms, lang=None, repo=None):
    """
    Return a list of packages that contains all the given terms either in its name, summary or
    description -> list_of_strings
    @param terms: a list of terms used to search package -> list_of_strings
    @param lang: language of the summary and description
    @param repo: Repository of the packages. If repo is None than returns a list of all the packages
    in all the repositories that meets the search
    """
    packagedb = pisilinux.db.packagedb.PackageDB()
    return packagedb.search_package(terms, lang, repo)

def search_installed(terms, lang=None):
    """
    Return a list of components that contains all the given terms either in its name, summary or
    description -> list_of_strings
    @param terms: a list of terms used to search components -> list_of_strings
    @param lang: language of the summary and description
    """
    installdb = pisilinux.db.installdb.InstallDB()
    return installdb.search_package(terms, lang)

def search_source(terms, lang=None, repo=None):
    """
    Return a list of source packages that contains all the given terms either in its name, summary or
    description -> list_of_strings
    @param terms: a list of terms used to search source package -> list_of_strings
    @param lang: language of the summary and description
    @param repo: Repository of the source packages. If repo is None than returns a list of all the source
    packages in all the repositories that meets the search
    """
    sourcedb = pisilinux.db.sourcedb.SourceDB()
    return sourcedb.search_spec(terms, lang, repo)

def search_component(terms, lang=None, repo=None):
    """
    Return a list of components that contains all the given terms either in its name, summary or
    description -> list_of_strings
    @param terms: a list of terms used to search components -> list_of_strings
    @param lang: language of the summary and description
    @param repo: Repository of the components. If repo is None than returns a list of all the components
    in all the repositories that meets the search
    """
    componentdb = pisilinux.db.componentdb.ComponentDB()
    return componentdb.search_component(terms, lang, repo)

def search_file(term):
    """
    Returns a tuple of package and matched files list that matches the files of the installed
    packages -> list_of_tuples
    @param term: used to search file -> list_of_strings

    >>> files = pisilinux.api.search_file("kvm-")

    >>> print files

    >>> [("kvm", (["lib/modules/2.6.18.8-86/extra/kvm-amd.ko","lib/modules/2.6.18.8-86/extra/kvm-intel.ko"])),]
    """
    if term.startswith("/"): # FIXME: why? why?
        term = term[1:]
    return ctx.filesdb.search_file(term)

def fetch(packages=[], path=os.path.curdir):
    """
    Fetches the given packages from the repository without installing, just downloads the packages.
    @param packages: list of package names -> list_of_strings
    @param path: path to where the packages will be downloaded. If not given, packages will be downloaded
    to the current working directory.
    """
    packagedb = pisilinux.db.packagedb.PackageDB()
    repodb = pisilinux.db.repodb.RepoDB()
    for name in packages:
        package, repo = packagedb.get_package_repo(name)
        ctx.ui.info(_("%s package found in %s repository") % (package.name, repo))
        uri = pisilinux.uri.URI(package.packageURI)
        output = os.path.join(path, uri.path())
        if os.path.exists(output) and package.packageHash == pisilinux.util.sha1_file(output):
            ctx.ui.warning(_("%s package already fetched") % uri.path())
            continue
        if uri.is_absolute_path():
            url = str(pkg_uri)
        else:
            url = os.path.join(os.path.dirname(repodb.get_repo_url(repo)), str(uri.path()))

        fetcher.fetch_url(url, path, ctx.ui.Progress)

@locked
def upgrade(packages=[], repo=None):
    """
    Upgrades the given packages, if no package given upgrades all the packages
    @param packages: list of package names -> list_of_strings
    @param repo: name of the repository that only the packages from that repo going to be upgraded
    """
    pisilinux.db.historydb.HistoryDB().create_history("upgrade")
    return pisilinux.operations.upgrade.upgrade(packages, repo)

@locked
def remove(packages, ignore_dependency=False, ignore_safety=False):
    """
    Removes the given packages from the system
    @param packages: list of package names -> list_of_strings
    @param ignore_dependency: removes packages without looking into theirs reverse deps if True
    @param ignore_safety: system.base packages can also be removed if True
    """
    pisilinux.db.historydb.HistoryDB().create_history("remove")
    return pisilinux.operations.remove.remove(packages, ignore_dependency, ignore_safety)

@locked
def install(packages, reinstall=False, ignore_file_conflicts=False, ignore_package_conflicts=False):
    """
    Returns True if no errors occured during the operation
    @param packages: list of package names -> list_of_strings
    @param reinstall: reinstalls already installed packages else ignores
    @param ignore_file_conflicts: Ignores file conflicts during the installation and continues to install
    packages.
    @param ignore_package_conflicts: Ignores package conflicts during the installation and continues to
    install packages.
    """

    pisilinux.db.historydb.HistoryDB().create_history("install")

    if not ctx.get_option('ignore_file_conflicts'):
        ctx.set_option('ignore_file_conflicts', ignore_file_conflicts)

    if not ctx.get_option('ignore_package_conflicts'):
        ctx.set_option('ignore_package_conflicts', ignore_package_conflicts)

    # Install pisilinux package files or pisilinux packages from a repository
    if packages and packages[0].endswith(ctx.const.package_suffix):
        return pisilinux.operations.install.install_pkg_files(packages, reinstall)
    else:
        return pisilinux.operations.install.install_pkg_names(packages, reinstall)

@locked
def takeback(operation):
    """
    Takes back the system to a previous state. Uses pisilinux history to find out which packages were
    installed at the time _after_ the given operation that the system is requested to be taken back.
    @param operation: number of the operation that the system will be taken back -> integer
    """

    historydb = pisilinux.db.historydb.HistoryDB()
    historydb.create_history("takeback")

    pisilinux.operations.history.takeback(operation)

def get_takeback_plan(operation):
    """
    Calculates and returns the plan of the takeback operation that contains information of which
    packages are going to be removed and which packages are going to be installed
    @param operation: number of the operation that the system will be taken back -> integer
    """

    beinstalled, beremoved, configs = pisilinux.operations.history.plan_takeback(operation)
    return beinstalled, beremoved

@locked
def set_repo_activity(name, active):
    """
    Changes the activity status of a  repository. Inactive repositories will have no effect on
    upgrades and installs.
    @param name: name of the repository
    @param active: the new repository status
    """
    repodb = pisilinux.db.repodb.RepoDB()
    if active:
        repodb.activate_repo(name)
    else:
        repodb.deactivate_repo(name)
    pisilinux.db.regenerate_caches()

@locked
def emerge(packages):
    """
    Builds and installs the given packages from source
    @param packages: list of package names -> list_of_strings
    """
    pisilinux.db.historydb.HistoryDB().create_history("emerge")
    return pisilinux.operations.emerge.emerge(packages)

@locked
def delete_cache():
    """
    Deletes cached packages, cached archives, build dirs, db caches
    """
    ctx.ui.info(_("Cleaning package cache %s...") % ctx.config.cached_packages_dir())
    pisilinux.util.clean_dir(ctx.config.cached_packages_dir())
    ctx.ui.info(_("Cleaning source archive cache %s...") % ctx.config.archives_dir())
    pisilinux.util.clean_dir(ctx.config.archives_dir())
    ctx.ui.info(_("Cleaning temporary directory %s...") % ctx.config.tmp_dir())
    pisilinux.util.clean_dir(ctx.config.tmp_dir())
    for cache in [x for x in os.listdir(ctx.config.cache_root_dir()) if x.endswith(".cache")]:
        cache_file = pisilinux.util.join_path(ctx.config.cache_root_dir(), cache)
        ctx.ui.info(_("Removing cache file %s...") % cache_file)
        os.unlink(cache_file)

@locked
def snapshot():
    """
    Takes snapshot of the system packages. The snapshot is only a record of which packages are currently
    installed. The record is kept by pisilinux history mechanism as it works automatically on install, remove
    and upgrade operations.
    """

    installdb = pisilinux.db.installdb.InstallDB()
    historydb = pisilinux.db.historydb.HistoryDB()
    historydb.create_history("snapshot")

    li = installdb.list_installed()
    progress = ctx.ui.Progress(len(li))

    processed = 0
    for name in installdb.list_installed():
        package = installdb.get_package(name)
        historydb.add_package(pkgBefore=package, operation="snapshot")
        # Save changed config files of the package in snapshot
        for f in installdb.get_files(name).list:
            if f.type == "config" and pisilinux.util.config_changed(f):
                fpath = pisilinux.util.join_path(ctx.config.dest_dir(), f.path)
                historydb.save_config(name, fpath)

        processed += 1
        ctx.ui.display_progress(operation = "snapshot",
                                percent = progress.update(processed),
                                info = _("Taking snapshot of the system"))

    historydb.update_history()

def calculate_download_size(packages):
    """
    Returns the total download size and the cached size of the packages.
    @param packages: list of package names -> list_of_strings
    """
    total_size, cached_size = pisilinux.operations.helper.calculate_download_sizes(packages)
    return total_size, cached_size

def get_package_requirements(packages):
    """
    Returns a dict with two keys - systemRestart, serviceRestart - with package lists as their values
    @param packages: list of package names -> list_of_strings

    >>> lu = pisilinux.api.list_upgrades()

    >>> requirements = pisilinux.api.get_package_requirements(lu)

    >>> print requirements
    >>> { "systemRestart":["kernel", "module-alsa-driver"], "serviceRestart":["mysql-server", "memcached", "postfix"] }

    """

    actions = ("systemRestart", "serviceRestart")
    requirements = dict((action, []) for action in actions)

    installdb = pisilinux.db.installdb.InstallDB()
    packagedb = pisilinux.db.packagedb.PackageDB()

    for i_pkg in packages:
        try:
            pkg = packagedb.get_package(i_pkg)
        except Exception: #FIXME: Should catch RepoItemNotFound exception
            pass

        version, release, build = installdb.get_version(i_pkg)
        pkg_actions = pkg.get_update_actions(release)

        for action_name in pkg_actions:
            if action_name in actions:
                requirements[action_name].append(pkg.name)

    return requirements

# ****** Danger Zone Below! Tressspassers' eyes will explode! ********** #

def package_graph(A, packagedb, ignore_installed = False, reverse=False):
    """Construct a package relations graph.

    Graph will contain all dependencies of packages A, if ignore_installed
    option is True, then only uninstalled deps will be added.

    """

    ctx.ui.debug('A = %s' % str(A))

    # try to construct a pisilinux graph of packages to
    # install / reinstall

    G_f = pgraph.PGraph(packagedb)             # construct G_f

    # find the "install closure" graph of G_f by package
    # set A using packagedb
    for x in A:
        G_f.add_package(x)
    B = A
    #state = {}
    while len(B) > 0:
        Bp = set()
        for x in B:
            pkg = packagedb.get_package(x)
            #print pkg
            if reverse:
                for name,dep in packagedb.get_rev_deps(x):
                    if ignore_installed:
                        if dep.satisfied_by_installed():
                            continue
                    if not name in G_f.vertices():
                        Bp.add(name)
                    G_f.add_dep(name, dep)
            else:
                for dep in pkg.runtimeDependencies():
                    if ignore_installed:
                        if dep.satisfied_by_installed():
                            continue
                    if not dep.package in G_f.vertices():
                        Bp.add(str(dep.package))
                    G_f.add_dep(x, dep)
        B = Bp
    return G_f

def generate_pending_order(A):
    # returns pending package list in reverse topological order of dependency
    installdb = pisilinux.db.installdb.InstallDB()
    G_f = pgraph.PGraph(installdb) # construct G_f
    for x in A:
        G_f.add_package(x)
    B = A
    while len(B) > 0:
        Bp = set()
        for x in B:
            pkg = installdb.get_package(x)
            for dep in pkg.runtimeDependencies():
                if dep.package in G_f.vertices():
                    G_f.add_dep(x, dep)
        B = Bp
    if ctx.get_option('debug'):
        import sys
        G_f.write_graphviz(sys.stdout)
    order = G_f.topological_sort()
    order.reverse()

    componentdb = pisilinux.db.componentdb.ComponentDB()
    # Bug 4211
    if componentdb.has_component('system.base'):
        order = reorder_base_packages(order)

    return order

@locked
def configure_pending(packages=None):
    # Import COMAR
    import pisilinux.comariface

    # start with pending packages
    # configure them in reverse topological order of dependency
    installdb = pisilinux.db.installdb.InstallDB()
    if not packages:
        packages = installdb.list_pending()
    else:
        packages = set(packages).intersection(installdb.list_pending())

    order = generate_pending_order(packages)
    try:
        for x in order:
            if installdb.has_package(x):
                pkginfo = installdb.get_package(x)
                pkg_path = installdb.package_path(x)
                m = pisilinux.metadata.MetaData()
                metadata_path = pisilinux.util.join_path(pkg_path, ctx.const.metadata_xml)
                m.read(metadata_path)
                # FIXME: we need a full package info here!
                pkginfo.name = x
                ctx.ui.notify(pisilinux.ui.configuring, package = pkginfo, files = None)
                pisilinux.comariface.post_install(
                    pkginfo.name,
                    m.package.providesComar,
                    pisilinux.util.join_path(pkg_path, ctx.const.comar_dir),
                    pisilinux.util.join_path(pkg_path, ctx.const.metadata_xml),
                    pisilinux.util.join_path(pkg_path, ctx.const.files_xml),
                    None,
                    None,
                    m.package.version,
                    m.package.release
                )
                ctx.ui.notify(pisilinux.ui.configured, package = pkginfo, files = None)
            installdb.clear_pending(x)
    except ImportError:
        raise pisilinux.Error(_("comar package is not fully installed"))

def info(package, installed = False):
    if package.endswith(ctx.const.package_suffix):
        return info_file(package)
    else:
        metadata, files, repo = info_name(package, installed)
        return metadata, files

def info_file(package_fn):

    if not os.path.exists(package_fn):
        raise pisilinux.Error (_('File %s not found') % package_fn)

    package = pisilinux.package.Package(package_fn)
    package.read()
    return package.metadata, package.files

def info_name(package_name, useinstalldb=False):
    """Fetch package information for the given package."""

    installdb = pisilinux.db.installdb.InstallDB()
    packagedb = pisilinux.db.packagedb.PackageDB()
    if useinstalldb:
        package = installdb.get_package(package_name)
        repo = None
    else:
        package, repo = packagedb.get_package_repo(package_name)

    metadata = pisilinux.metadata.MetaData()
    metadata.package = package
    #FIXME: get it from sourcedb if available
    metadata.source = None
    #TODO: fetch the files from server if possible (wow, you maniac -- future exa)
    if useinstalldb and installdb.has_package(package.name):
        try:
            files = installdb.get_files(package.name)
        except pisilinux.Error as e:
            ctx.ui.warning(e)
            files = None
    else:
        files = None
    return metadata, files, repo

def index(dirs=None, output='pisilinux-index.xml',
          skip_sources=False, skip_signing=False,
          compression=0):
    """Accumulate pisilinux XML files in a directory, and write an index."""
    index = pisilinux.index.Index()
    index.distribution = None
    if not dirs:
        dirs = ['.']
    for repo_dir in dirs:
        repo_dir = str(repo_dir)
        ctx.ui.info(_('Building index of pisilinux files under %s') % repo_dir)
        index.index(repo_dir, skip_sources)

    sign = None if skip_signing else pisilinux.file.File.detached
    index.write(output, sha1sum=True, compress=compression, sign=sign)
    ctx.ui.info(_('Index file written'))

@locked
def add_repo(name, indexuri, at = None):
    if not re.match("^[0-9%s\-\\_\\.\s]*$" % str(pisilinux.util.letters()), name):
        raise pisilinux.Error(_('Not a valid repo name.'))
    repodb = pisilinux.db.repodb.RepoDB()
    if repodb.has_repo(name):
        raise pisilinux.Error(_('Repo %s already present.') % name)
    elif repodb.has_repo_url(indexuri, only_active = False):
        repo = repodb.get_repo_by_url(indexuri)
        raise pisilinux.Error(_('Repo already present with name %s.') % repo)
    else:
        repo = pisilinux.db.repodb.Repo(pisilinux.uri.URI(indexuri))
        repodb.add_repo(name, repo, at = at)
        pisilinux.db.flush_caches()
        ctx.ui.info(_('Repo %s added to system.') % name)

@locked
def remove_repo(name):
    repodb = pisilinux.db.repodb.RepoDB()
    if repodb.has_repo(name):
        repodb.remove_repo(name)
        pisilinux.db.flush_caches()
        ctx.ui.info(_('Repo %s removed from system.') % name)
    else:
        raise pisilinux.Error(_('Repository %s does not exist. Cannot remove.')
                 % name)

@locked
def update_repos(repos, force=False):
    pisilinux.db.historydb.HistoryDB().create_history("repoupdate")
    updated = False
    try:
        for repo in repos:
            updated |= __update_repo(repo, force)
    finally:
        if updated:
            pisilinux.db.regenerate_caches()

@locked
def update_repo(repo, force=False):
    pisilinux.db.historydb.HistoryDB().create_history("repoupdate")
    updated = __update_repo(repo, force)
    if updated:
        pisilinux.db.regenerate_caches()

def __update_repo(repo, force=False):
    ctx.ui.action(_('Updating repository: %s') % repo)
    ctx.ui.notify(pisilinux.ui.updatingrepo, name = repo)
    repodb = pisilinux.db.repodb.RepoDB()
    index = pisilinux.index.Index()
    if repodb.has_repo(repo):
        repouri = repodb.get_repo(repo).indexuri.get_uri()
        try:
            index.read_uri_of_repo(repouri, repo)
        except pisilinux.file.AlreadyHaveException as e:
            ctx.ui.info(_('%s repository information is up-to-date.') % repo)
            if force:
                ctx.ui.info(_('Updating database at any rate as requested'))
                index.read_uri_of_repo(repouri, repo, force = force)
            else:
                return False

        pisilinux.db.historydb.HistoryDB().update_repo(repo, repouri, "update")
        repodb.check_distribution(repo)

        try:
            index.check_signature(repouri, repo)
        except pisilinux.file.NoSignatureFound as e:
            ctx.ui.warning(e)

        ctx.ui.info(_('Package database updated.'))
    else:
        raise pisilinux.Error(_('No repository named %s found.') % repo)

    return True

# FIXME: rebuild_db is only here for filesdb and it really is ugly. we should not need any rebuild.
@locked
def rebuild_db():

    # save parameters and shutdown pisilinux
    options = ctx.config.options
    ui = ctx.ui
    comar = ctx.comar
    pisilinux._cleanup()

    ctx.filesdb.close()
    ctx.filesdb.destroy()
    ctx.filesdb = pisilinux.db.filesldb.FilesLDB()

    # reinitialize everything
    set_userinterface(ui)
    set_options(options)
    set_comar(comar)

############# FIXME: this was a quick fix. ##############################

# api was importing other module's functions and providing them as api functions. This is wrong.
# these are quick fixes for this problem. The api functions should be in this module.

# from pisilinux.operations import install, remove, upgrade, emerge
# from pisilinux.operations import plan_install_pkg_names as plan_install
# from pisilinux.operations import plan_remove, plan_upgrade, upgrade_base, calculate_conflicts, reorder_base_packages
# from pisilinux.build import build_until
# from pisilinux.atomicoperations import resurrect_package, build

def calculate_conflicts(*args, **kw):
    return pisilinux.conflict.calculate_conflicts(*args, **kw)

def reorder_base_packages(*args, **kw):
    return pisilinux.operations.helper.reorder_base_packages(*args, **kw)

def build_until(*args, **kw):
    return pisilinux.operations.build.build_until(*args, **kw)

def build(*args, **kw):
    return pisilinux.atomicoperations.build(*args, **kw)

########################################################################

## Deletes the cached pisilinux packages to keep the package cache dir within cache limits
#  @param all When set all the cached packages will be deleted
@locked
def clearCache(all=False):

    import glob

    def getPackageLists(pkgList):
        latest = {}
        for f in pkgList:
            try:
                name, full_version = util.parse_package_name(f)
                version, release, build = pisilinux.util.split_version(full_version)

                release = int(release)
                if name in latest:
                    lversion, lrelease = latest[name]
                    if lrelease > release:
                        continue

                latest[name] = full_version, release

            except:
                pass

        latestVersions = []
        for pkg in latest:
            latestVersions.append("%s-%s" % (pkg, latest[pkg][0]))

        oldVersions = list(set(pkgList) - set(latestVersions))
        return oldVersions, latestVersions

    def getRemoveOrder(cacheDir, pkgList):
        sizes = {}
        for pkg in pkgList:
            sizes[pkg] = os.stat(os.path.join(cacheDir, pkg) + ctx.const.package_suffix).st_size

        # sort dictionary by value from PEP-265
        from operator import itemgetter
        return sorted(iter(sizes.items()), key=itemgetter(1), reverse=False)

    def removeOrderByLimit(cacheDir, order, limit):
        totalSize = 0
        for pkg, size in order:
            totalSize += size
            if totalSize >= limit:
                try:
                    os.remove(os.path.join(cacheDir, pkg) + ctx.const.package_suffix)
                except exceptions.OSError:
                    pass

    def removeAll(cacheDir):
        cached = glob.glob("%s/*.pisilinux" % cacheDir) + glob.glob("%s/*.part" % cacheDir)
        for pkg in cached:
            try:
                os.remove(pkg)
            except exceptions.OSError:
                pass

    cacheDir = ctx.config.cached_packages_dir()

    pkgList = [os.path.basename(x).split(ctx.const.package_suffix)[0] for x in glob.glob("%s/*.pisilinux" % cacheDir)]
    if not all:
        # Cache limits from pisilinux.conf
        config = pisilinux.configfile.ConfigurationFile("/etc/pisilinux/pisilinux.conf")
        cacheLimit = int(config.get("general", "package_cache_limit")) * 1024 * 1024 # is this safe?
        if not cacheLimit:
            return

        old, latest = getPackageLists(pkgList)
        order = getRemoveOrder(cacheDir, latest) + getRemoveOrder(cacheDir, old)
        removeOrderByLimit(cacheDir, order, cacheLimit)
    else:
        removeAll(cacheDir)
