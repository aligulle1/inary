# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#
# Author:  Eray Ozkural <eray@uludag.org.tr>

"""
generic file abstraction that allows us to use URIs for everything
we support only the simple read case ATM
we are just encapsulating a common pattern in our program, nothing big.
like all pisi classes, it has been programmed in a non-restricting way
"""

import os.path
import types

import gettext
__trans = gettext.translation('pisi', fallback=True)
_ = __trans.ugettext

import pisi
from pisi.uri import URI
from pisi.util import join_path as join
from pisi.fetcher import fetch_url
import pisi.context as ctx

class AlreadyHaveException(pisi.Exception):
    def __init__(self, url, localfile):
        pisi.Exception.__init__(self, "URL %s already downloaded as %s" % (url, localfile))
        self.url = url 
        self.localfile = localfile

class Error(pisi.Error):
    pass

class File:

    (read, write) = range(2) # modes
    (xmill, sevenzip) = range(2) # compress enums

    @staticmethod
    def make_uri(uri):
        "handle URI arg"
        if type(uri) == types.StringType or type(uri) == types.UnicodeType:
            uri = URI(uri)
        elif type(uri) != URI:
            raise Error(_("uri must have type either URI or string"))
        return uri

    @staticmethod
    def decompress(localfile, compress):
        if compress == File.xmill:
            pisi.util.run_batch('xdemill -f ' + localfile)
            if not localfile.endswith('.xmi'):
                raise Error(_("xmill compressed filename must end with '.xmi'"))
            localfile = localfile[:-4] + '.xml'
        elif compress == File.sevenzip:
            raise Error(_("sevenzip compression not supported yet"))
        return localfile

    @staticmethod
    def download(uri, transfer_dir = "/tmp", 
                 sha1sum = False, compress = None, sign = None):

        assert type(uri == URI)
        if sha1sum:
            sha1filename = File.download(URI(uri.get_uri() + '.sha1sum'), transfer_dir)
            sha1f = file(sha1filename)
            newsha1 = sha1f.readlines()[0]

        if uri.is_remote_file():
            localfile = join(transfer_dir, uri.filename())
            
            # TODO: code to use old .sha1sum file, is this a necessary optimization?
            #oldsha1fn = localfile + '.sha1sum'
            #if os.exists(oldsha1fn):
                #oldsha1 = file(oldsha1fn).readlines()[0]
            if sha1sum and os.path.exists(localfile):
                oldsha1 = pisi.util.sha1_file(localfile)
                if (newsha1 == oldsha1):
                    # early terminate, we already got it ;)
                    raise AlreadyHaveException(uri, localfile)

            ctx.ui.info(_("Fetching %s") % uri.get_uri())
            fetch_url(uri, transfer_dir)
        else:
            localfile = uri.get_uri() #TODO: use a special function here?
            localfile = File.decompress(localfile, self.compress)

        if sha1sum:        
        
            if (pisi.util.sha1_file(localfile) != newsha1):
                raise Error(_("File integrity of %s compromised.") % uri)

        localfile = File.decompress(localfile, compress)

        return localfile


    def __init__(self, uri, mode, transfer_dir = "/tmp", 
                 sha1sum = False, compress = None, sign = None):
        "it is pointless to open a file without a URI and a mode"
        self.sha1sum = sha1sum
        self.compress = compress
        uri = File.make_uri(uri)
        if mode==File.read or mode==File.write:
            self.mode = mode
        else:
            raise Error(_("File mode must be either File.read or File.write"))
        if uri.is_remote_file():
            if self.mode == File.read:
                localfile = File.download(uri, transfer_dir, sha1sum, compress, sign)
            else:
                raise Error(_("Remote write not implemented"))
        else:
            localfile = uri.get_uri() #TODO: use a special function here?

        if self.mode == File.read:
            access = 'r'
        else:
            access = 'w'
        self.__file__ = file(localfile, access)
        self.localfile = localfile

    def local_file(self):
        "returns the underlying file object"
        return self.__file__

    def close(self, delete_transfer = False):
        "this method must be called at the end of operation"
        self.__file__.close()
        if self.compress == File.xmill:
            pisi.util.run_batch('xcmill -9 -d -f ' + self.localfile)
            self.localfile = self.localfile[:-4] + '.xmi'
        elif self.compress == File.sevenzip:
            raise Error(_("sevenzip compression not supported yet"))
        if self.mode == File.write:
            if self.sha1sum:
                sha1 = pisi.util.sha1_file(self.localfile)
                cs = file(self.localfile + '.sha1sum', 'w')
                cs.write(sha1)
                cs.close()
    
    def flush(self):
        self.__file__.flush()

    def fileno(self):
        return self.__file__.fileno()

    def isatty(self):
        return self.__file__.isatty()

    def next(self):
        return self.__file__.next()
    
    def read(self, size = None):
        if size:
            return self.__file__.read(size)
        else:
            return self.__file__.read()

    def readline(self, size = None):
        if size:
            return self.__file__.readline(size)
        else:
            return self.__file__.readline()
    
    def readlines(self, size = None):
        if size:
            return self.__file__.readlines(size)
        else:
            return self.__file__.readlines()
        
    def xreadlines(self):
        return self.__file__.xreadlines()
    
    def seek(self, offset, whence=0):
        self.__file__.seek(offset, whence)
    
    def tell(self):
        return self.__file__.tell()
        
    def truncate(self):
        self.__file__.truncate()
        
    def write(self, str):
        self.__file__.write(str)

    def writelines(self, sequence):
        self.__file__.writelines(sequence)
