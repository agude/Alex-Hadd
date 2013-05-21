#!/usr/bin/python
#  Copyright (C) 2012  Alexander Gude - gude@physics.umn.edu
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.


from optparse import OptionParser # Command line parsing
from tempfile import mkdtemp # Secure methods of generating random directories
from random import choice
from string import ascii_uppercase,digits,ascii_lowercase
from sys import exit # Cleanly exit program
from subprocess import call # Access external programs
from os import listdir,remove,devnull
from os.path import isfile
from shutil import copy2,rmtree

## Help functions
def listdirwithpath(dir):
    """ Return a list of files with their path """
    return [ dir+'/'+f for f in listdir(dir) ]

## Hadd class
class hadd:
    """ A class to handle hadding of files, and cleanup of output """
    def __init__(self, outfile, infiles, tmpdir, verbose=False, vverbose=False, quite=False, force_overwrite=False, save=False, natonce=20):
        """ Set up the class """
        self.outfile = outfile
        self.infiles = infiles
        self.verbose = verbose
        self.vverbose = vverbose
        self.quite = quite
        self.force_overwrite = force_overwrite
        self.natonce = natonce
        self.save = save
        self.counter = 0
        self.__checkOutFile()
        self.__printInAndOut()
        self.__setTmpDir(tmpdir)

    def run(self):
        """ Combine files by looping over them """
        if not self.quite: print "Combining files"

        i = 0
        infiles = list(self.infiles) # deep copies the list
        while True:
            currentWriteDir = mkdtemp(prefix=str(i)+"_", dir=self.tmpdir) + '/'
            self.__haddMultiple(currentWriteDir, infiles)
            currentReadDir = currentWriteDir
            infiles = listdirwithpath(currentReadDir)
            if len(infiles) == 1:
                if not self.quite: print "Copying final file:",infiles[0],"-->",self.outfile
                copy2(infiles[0], self.outfile)
                break
            else:
                i += 1
        self.__cleanup()

    def __printInAndOut(self):
        """ Print the input files, and output file """
        if not self.quite:
            print "Output file:",out_file
            print "Input files:"
            for f in in_files:
                print "\t",f
            print "Number of files to hadd at once:",self.natonce

    def __checkOutFile(self):
        """ Check if the output file exists, if so exit if we don't force
        overwrite """
        if not self.force_overwrite and isfile(self.outfile):
            print "Output file already exists! File:",self.outfile
            exit(1) # Other error
        elif self.force_overwrite and isfile(self.outfile):
            if not self.quite: print "Output file already exists; it will be overwriten! File:",self.outfile

    def __cleanup(self):
        """ Clean up intermediate files """
        if not self.save:
            rmtree(self.tmpdir)
        exit(0) # Normal exit

    def __haddMultiple(self, writeDir, inFiles):
        """ Given a list of inFiles, and a write dir, hadds the files and saves
        them to the directory """
        while inFiles:
            currentFiles = []
            if len(inFiles) >= self.natonce:
                for i in xrange(self.natonce):
                    currentFiles.append(inFiles.pop())
            else:
                currentFiles = inFiles
                inFiles = []

            outfile = self.__getRandomRootName(writeDir)
            self.__hadd(outfile, currentFiles)

    def __getRandomRootName(self, dir):
        """ Return a random file name """
        chars = ascii_uppercase+digits+ascii_lowercase
        ran = []
        for x in xrange(6):
            ran.append(choice(chars))
        num = self.counter
        self.counter += 1
        return dir + '/input_%i_'%(num) + ''.join(ran) + ".root"

    def __setTmpDir(self,tmpdir):
        """ Set up a temporary directory to hold intermediate files """
        if self.verbose: print "Making temporary directory:",

        if tmpdir == None:
            self.tmpdir = mkdtemp(prefix="ahadd_") + '/'
        else:
            self.tmpdir = mkdtemp(prefix="ahadd_",dir=options.tmp_dir) + '/'

        if self.verbose: print self.tmpdir

    def __hadd(self, outfile, infiles):
        """ Call hadd """
        args = ["hadd", outfile] + infiles
        if self.verbose: 
            print "Calling hadd"
            print "\tOutput:",outfile
            print "\tInput:"
            for f in infiles:
                print "\t\t",f

        if self.vverbose:
            return (call(args), outfile)
        else:
            return (call(args, stdout=open(devnull, 'wb')), outfile)

##### START OF CODE
""" Allows command line options to be parsed. Called first to in order to let functions use them.  """

usage = "usage: %prog [Options] outputfile inputfiles"
version = "%prog Version 1.1.1\n\nCopyright (C) 2012 Alexander Gude - gude@physics.umn.edu\nThis is free software.  You may redistribute copies of it under the terms of\nthe GNU General Public License <http://www.gnu.org/licenses/gpl.html>.\nThere is NO WARRANTY, to the extent permitted by law.\n\nWritten by Alexander Gude."
parser = OptionParser(usage=usage,version=version)
parser.add_option("-n", "--n-files-at-once", action="store", type="int", dest="natonce", default=20, help="combine this many files at one time [defualt 4]")
parser.add_option("-t", "--temp-dir", action="store", type="string", dest="tmp_dir", default=None, help="location to store temporary intermediate files")
parser.add_option("-s", "--save-temp", action="store_true", dest="save_tmp", default=False, help="save temporary files, otherwise they are cleaned up when the program exits [default false]")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="print some extra status messages to stdout [default false]")
parser.add_option("-q", "--quite", action="store_true", dest="quite", default=False, help="do not print any status messages to stdout [default false]")
parser.add_option("-V", "--very-verbose", action="store_true", dest="vverbose", default=False, help="print everything, even the output from hadd [default false]")
parser.add_option("-f", "--force-overwrite", action="store_true", dest="force_overwrite", default=False, help="Overwrite the output file if it exists [default false]")

(options, args) = parser.parse_args()

## Check verbosity
if options.quite:
    options.verbose = False
    options.vverbose = False
elif options.vverbose:
    options.verbose = True

## Check that we have at least a few files to work on
in_files = []
out_file = None
if len(args) <= 2:
    print "Not enough arguments on the command line. Exiting."
    exit(2) # Not enough commands
else:
    out_file = args[0]
    in_files = args[1:]

## Check that the number of files to hadd each step is sane
if options.natonce <= 1:
    print "Requested to hadd 1 or fewer files per iteration; this will never converge."
    exit(1) # Other error

## Set up and run hadd
h = hadd(out_file, in_files, options.tmp_dir, options.verbose, options.vverbose, options.quite, options.force_overwrite, options.save_tmp, options.natonce)
h.run()
