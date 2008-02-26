# -*- coding: utf-8 -*-
#
# Copyright (C) 2008, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.

import os
import gettext
__trans = gettext.translation("pisi", fallback=True)
_ = __trans.ugettext

import pisi.context as ctx
import pisi.util
import pisi.db
import pisi.fetcher

def __listactions(actions):
    beinstalled = []
    beremoved = []

    for pkg in actions:
        action, version = actions[pkg]
        if action == "install":
            beinstalled.append("%s-%s" % (pkg, version))
        else:
            beremoved.append("%s" % pkg)

    return beinstalled, beremoved

def __getpackageurl(package):
    packagedb = pisi.db.packagedb.PackageDB()
    repodb = pisi.db.repodb.RepoDB()

    pkg, ver = pisi.util.parse_package_name(package)
    reponame = packagedb.which_repo(pkg)
    repourl = repodb.get_repo_url(reponame)

    ctx.ui.info(_("Package %s found in repository %s") % (pkg, reponame))

    #return _possible_ url for this package
    return os.path.join(os.path.dirname(repourl), package)

def fetch_remote_file(package, errors):
    uri = pisi.file.File.make_uri(__getpackageurl(package))
    dest = ctx.config.cached_packages_dir()
    filepath = os.path.join(dest, uri.filename())
    if not os.path.exists(filepath):
        try:
            pisi.fetcher.fetch_url(uri, dest, ctx.ui.Progress)
        except pisi.fetcher.FetchError, e:
            errors.append(package)
            ctx.ui.info(pisi.util.colorize(_("%s could not be found") % (package), "red"))
    else:
        ctx.ui.info(_('%s [cached]') % uri.filename())

def takeback(operation):

    historydb = pisi.db.historydb.HistoryDB()
    actions = {}

    for operation in historydb.get_till_operation(operation):
        if operation == "snapshot":
            pass

        for pkg in operation.packages:
            if pkg.operation in ["upgrade", "downgrade", "remove"]:
                actions[pkg.name] = ("install", pkg.before)
            if pkg.operation == "install":
                actions[pkg.name] = ("remove", None)

    beinstalled, beremoved = __listactions(actions)

    if beinstalled:
        ctx.ui.info(_("Following packages will be installed:\n") + pisi.util.strlist(beinstalled))

    if beremoved:
        ctx.ui.info(_("Following packages will be removed:\n") + pisi.util.strlist(beremoved))

    if (beremoved or beinstalled) and not ctx.ui.confirm(_('Do you want to continue?')):
        return

    errors = []
    paths = []
    for pkg in beinstalled:
        ctx.ui.info(pisi.util.colorize(_("Downloading %d / %d") % (beinstalled.index(pkg)+1, len(beinstalled)), "yellow"))
        fetch_remote_file(pkg, errors)
        paths.append(os.path.join(ctx.config.cached_packages_dir(), pkg))

    if errors:
        ctx.ui.info(_("\nFollowing packages could not be found in repositories and are not cached:\n") + 
                    pisi.util.strlist(errors))
        if not ctx.ui.confirm(_('Do you want to continue?')):
            return