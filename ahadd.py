#!/usr/bin/env python

#  Copyright (C) 2014  Alexander Gude - gude@physics.umn.edu
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
#
#  The most recent version of this program is available at:
#  https://github.com/agude/Alex-Hadd


from tempfile import mkdtemp  # Secure methods of generating random directories
from random import choice
from string import ascii_uppercase, digits, ascii_lowercase
from sys import exit  # Cleanly exit program
from subprocess import call  # Access external programs
from os import listdir, remove, devnull
from os.path import isfile
from shutil import copy2, rmtree

# Multiprocessing does not exist on some of the older versions of Scientific
# Linux that we still use at CERN
HasMP = True
try:
    import multiprocessing as mp
except ImportError:
    HasMP = False


## Helper functions
def listdirwithpath(d):
    """ Return a list of files with their path """
    return [d + '/' + f for f in listdir(d)]


## Worker function
def haddMultiple(inputTuple):
    """ Takes an inputTuple, hadds the files, and saves them to the given
    directory. The inputTuple has the following form:
    ( outFile, startNum, endNum, totalNum, verbosity, (file0, ..., fileN) ) """

    # Grab our arguments
    (outFile, startNum, endNum, totalNum, verbosity, inFiles) = inputTuple
    #print outFile, startNum, endNum, totalNum, verbosity, inFiles

    # Set verbosity
    args = ["hadd", outFile] + inFiles
    if verbosity >= 1:
        print "Calling hadd"
        print "\tOutput:", outfile
        print "\tInput:"
        for f in inFiles:
            print "\t\t", f

    # Call hadd
    retcode = None
    if verbosity >= 0:
        print "Now hadding files %i-%i of %i." % (startNum, endNum, totalNum)
    if verbosity >= 2:
        retcode = call(args)
    else:
        retcode = call(args, stdout=open(devnull, 'wb'))
    # Check to makesure that hadd did not throw an error
    if retcode != 0:
        print "Error from hadd!"
        exit(retcode)


## Hadd class
class hadd:
    """ A class to handle hadding of files, and cleanup of output """
    def __init__(self, outfile, inFiles, tmpdir, verbose=False, vverbose=False, quiet=False, force_overwrite=False, save=False, nAtOnce=20, nJobs=1):
        """ Set up the class """
        self.outfile = outfile
        self.inFiles = inFiles
        self.verbose = verbose
        self.vverbose = vverbose
        self.quiet = quiet
        self.force_overwrite = force_overwrite
        self.nAtOnce = nAtOnce
        self.nJobs = nJobs
        self.save = save
        self.counter = 0
        self.__checkOutFile()
        self.__printInAndOut()
        self.__setTmpDir(tmpdir)

    def run(self):
        """ Combine files by looping over them """
        if not self.quiet:
            print "Combining files"

        i = 0
        inFiles = list(self.inFiles)  # deep copies the list
        while True:
            currentWriteDir = mkdtemp(prefix=str(i) + "_", dir=self.tmpdir) + '/'
            # Tuplize Files into our special tuple
            currentTuples = self.__tuplizeFiles(currentWriteDir, inFiles)
            # Run Hadding
            self.__haddMultiple(currentWriteDir, currentTuples)
            # Check output files
            currentReadDir = currentWriteDir
            inFiles = listdirwithpath(currentReadDir)
            # If we have one file left, we're done
            if len(inFiles) == 1:
                if not self.quiet:
                    print "Copying final file:", inFiles[0], "-->", self.outfile
                copy2(inFiles[0], self.outfile)
                break
            else:
                i += 1
        # Cleanup output files in the tmp directory
        self.__cleanup()

    def __haddMultiple(self, writeDir, inTuples):
        """ Given a list of inFiles, and a write dir, hadds the files and saves
        them to the directory """
        # Single Job
        if self.nJobs <= 1:
            for tup in inTuples:
                haddMultiple(tup)
        # Multiple Jobs
        else:
            pool = mp.Pool(processes=self.nJobs)
            pool.map(haddMultiple, inTuples)  # Note, no return values so we don't care about them
            pool.close()  # No more tasks to add
            pool.join()  # Wait for jobs to finish

    def __printInAndOut(self):
        """ Print the input files, and output file """
        if not self.quiet:
            print "Output file:", out_file
            print "Input files:"
            for f in in_files:
                print "\t", f
            print "Number of files to hadd at once:", self.nAtOnce

    def __checkOutFile(self):
        """ Check if the output file exists, if so exit if we don't force
        overwrite """
        if not self.force_overwrite and isfile(self.outfile):
            print "Output file already exists! File:", self.outfile
            exit(1)  # Other error
        elif self.force_overwrite and isfile(self.outfile):
            if not self.quiet:
                print "Output file already exists; it will be overwritten! File:", self.outfile

    def __tuplizeFiles(self, writeDir, inFiles):
        """ Takes the input list and writes a specialized tuple of them """
        fileTuple = []

        # Set verbosity
        if self.verbose:
            if self.vverbose:
                verbosity = 2
            else:
                verbosity = 1
        elif not self.quiet:
            verbosity = 0
        else:
            verbosity = -1

        # Loop to fill tuples
        totalNum = len(inFiles)
        for i in xrange(0, totalNum, self.nAtOnce):
            outFile = self.__getRandomRootName(writeDir)
            tmpList = inFiles[i:i + self.nAtOnce]
            startNum = i + 1
            endNum = i + len(tmpList)
            newTuple = (outFile, startNum, endNum, totalNum, verbosity, tmpList)
            fileTuple.append(newTuple)

        return tuple(fileTuple)

    def __cleanup(self):
        """ Clean up intermediate files """
        if not self.save:
            rmtree(self.tmpdir)
        # It is not clear we want to force program termination
        #exit(0)  # Normal exit

    def __getRandomRootName(self, dir):
        """ Return a random file name """
        chars = ascii_uppercase + digits + ascii_lowercase
        ran = []
        for x in xrange(6):
            ran.append(choice(chars))
        num = self.counter
        self.counter += 1
        return dir + '/input_%i_' % (num) + ''.join(ran) + ".root"

    def __setTmpDir(self, tmpdir):
        """ Set up a temporary directory to hold intermediate files """
        if self.verbose:
            print "Making temporary directory:",

        if tmpdir == None:
            self.tmpdir = mkdtemp(prefix="ahadd_") + '/'
        else:
            self.tmpdir = mkdtemp(prefix="ahadd_", dir=tmpdir) + '/'

        if self.verbose:
            print self.tmpdir

##### START OF CODE
if __name__ == '__main__':

    # Check if hadd exists
    from distutils.spawn import find_executable
    if find_executable("hadd") is None:
        print "Can not find hadd."
        exit(2)

    # Set default jobs number
    from math import floor
    if HasMP:
        NJOBS = int(floor(mp.cpu_count() * 1.5))
    else:
        NJOBS = 1

    # Allows command line options to be parsed.
    from optparse import OptionParser  # Command line parsing

    usage = "usage: %prog [Options] output_file input_files"
    version = "%prog Version 2.3.4\n\nCopyright (C) 2014 Alexander Gude - gude@physics.umn.edu\nThis is free software.  You may redistribute copies of it under the terms of\nthe GNU General Public License <http://www.gnu.org/licenses/gpl.html>.\nThere is NO WARRANTY, to the extent permitted by law.\n\nWritten by Alexander Gude."
    parser = OptionParser(usage=usage, version=version)
    parser.add_option("-n", "--n-files-at-once", action="store", type="int", dest="nAtOnce", default=20, help="combine this many files at one time [defualt 20]")
    parser.add_option("-t", "--temp-dir", action="store", type="string", dest="tmp_dir", default=None, help="location to store temporary intermediate files")
    parser.add_option("-s", "--save-temp", action="store_true", dest="save_tmp", default=False, help="save temporary files, otherwise they are cleaned up when the program exits [default false]")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="print some extra status messages to stdout [default false]")
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet", default=False, help="do not print any status messages to stdout [default false]")
    parser.add_option("-V", "--very-verbose", action="store_true", dest="vverbose", default=False, help="print everything, even the output from hadd [default false]")
    parser.add_option("-f", "--force-overwrite", action="store_true", dest="force_overwrite", default=False, help="Overwrite the output file if it exists [default false]")
    parser.add_option("-j", "--jobs", action="store", type="int", dest="nJobs", default=NJOBS, help="use this many subprocess [default cpu_count*1.5 = %i]" % NJOBS)

    (options, args) = parser.parse_args()

    ## Check verbosity
    if options.quiet:
        options.verbose = False
        options.vverbose = False
    elif options.vverbose:
        options.verbose = True

    ## Check nJobs
    if not HasMP:
        options.nJobs = 1

    ## Check that we have at least a few files to work on
    in_files = []
    out_file = None
    if len(args) == 2:  # One input file means we can just copy it
        if not options.quiet:
            print "Only one input file; running a simple copy!"
            print "Copying final file:", args[1], "-->", args[0]
        copy2(args[1], args[0])
        exit(0)
    elif len(args) <= 1:
        print "Not enough arguments on the command line. Exiting."
        exit(2)  # Not enough commands
    else:
        out_file = args[0]
        in_files = args[1:]

    ## Check that the number of files to hadd each step is sane
    if options.nAtOnce <= 1:
        print "Requested to hadd 1 or fewer files per iteration; this will never converge."
        exit(1)  # Other error

    ## Set up and run hadd
    h = hadd(out_file, in_files, options.tmp_dir, options.verbose, options.vverbose, options.quiet, options.force_overwrite, options.save_tmp, options.nAtOnce, options.nJobs)
    h.run()
