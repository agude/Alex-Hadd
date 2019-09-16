#!/usr/bin/env python3

from distutils.spawn import find_executable
from enum import IntEnum, unique
from os import listdir, devnull
from os.path import isfile
from random import choice
from shutil import copy2, rmtree
from string import ascii_uppercase, digits, ascii_lowercase
from subprocess import call
from sys import exit
from tempfile import mkdtemp
import argparse
import logging


# Library version
__version__ = "3.0.1"


@unique
class EXIT(IntEnum):
    """ Shell exit codes used in this program. """

    GOOD = 0
    GENERIC_BAD = 1
    MISSING_HADD = 2


# Multiprocessing does not exist on some of the older versions of Scientific
# Linux that we still use at CERN
HAS_MP = True
try:
    import multiprocessing as mp
except ImportError:
    HAS_MP = False


## Helper functions
def list_dir_with_path(directory):
    """ Return a list of files with their path """
    return [directory + "/" + f for f in listdir(directory)]


## Worker function
def hadd_multiple(input_tuple):
    """ Takes an input_tuple, hadds the files, and saves them to the given
    directory. The input_tuple has the following form:
    ( out_file, start_num, end_num, total_num, (file0, ..., fileN) ) """

    # Grab our arguments
    (out_file, start_num, end_num, total_num, input_files) = input_tuple

    args = ["hadd", out_file] + input_files
    logging.debug("Calling hadd: Input: %s Output: %s", input_files, out_file)

    # Call hadd
    retcode = None
    logging.debug("Now hadding files %i-%i of %i." % (start_num, end_num, total_num))
    retcode = call(args)
    # Check to makesure that hadd did not throw an error
    if retcode != 0:
        logging.error("Error from hadd!")
        exit(retcode)


## Hadd class
class Hadd:
    """ A class to handle hadding of files, and cleanup of output """

    def __init__(
        self,
        outfile,
        input_files,
        tmpdir,
        force_overwrite=False,
        save=False,
        n_files_at_once=20,
        n_jobs=1,
    ):
        """ Set up the class """
        self.outfile = outfile
        self.input_files = input_files
        self.force_overwrite = force_overwrite
        self.n_files_at_once = n_files_at_once
        self.n_jobs = n_jobs
        self.save = save
        self.counter = 0
        self.__check_output_file()
        self.__print_in_and_out()
        self.__set_tmp_dir(tmpdir)

    def run(self):
        """ Combine files by looping over them """
        logging.info("Combining files")

        i = 0
        input_files = list(self.input_files)  # deep copies the list
        while True:
            logging.info("Starting step %s", i)
            current_write_dir = mkdtemp(prefix=str(i) + "_", dir=self.tmpdir) + "/"
            # Tuplize Files into our special tuple
            current_tuples = self.__tuplize_files(current_write_dir, input_files)
            # Run Hadding
            self.__hadd_multiple(current_write_dir, current_tuples)
            # Check output files
            current_read_dir = current_write_dir
            input_files = list_dir_with_path(current_read_dir)
            # If we have one file left, we're done
            if len(input_files) == 1:
                logging.info(
                    "Copying final file: %s --> %s", input_files[0], self.outfile
                )
                copy2(input_files[0], self.outfile)
                break
            else:
                i += 1
        # Cleanup output files in the tmp directory
        self.__cleanup()

    def __hadd_multiple(self, target_directory, in_tuples):
        """ Given a list of input_files, and a write dir, hadds the files and saves
        them to the directory """
        # Single Job
        if self.n_jobs <= 1:
            for tup in in_tuples:
                hadd_multiple(tup)
        # Multiple Jobs
        else:
            pool = mp.Pool(processes=self.n_jobs)
            # No return values so we don't care about them
            pool.map(hadd_multiple, in_tuples)
            pool.close()  # No more tasks to add
            pool.join()  # Wait for jobs to finish

    def __print_in_and_out(self):
        """ Print the input files, and output file """
        logging.debug("Number of files to hadd at once: %s", self.n_files_at_once)
        logging.info("Output file: %s", self.outfile)
        logging.info("Input files: %s", self.input_files)

    def __check_output_file(self):
        """ Check if the output file exists, if so exit if we don't force
        overwrite """
        if not self.force_overwrite and isfile(self.outfile):
            logging.error("Output file already exists! File: %s", self.outfile)
            exit(EXIT.GENERIC_BAD)
        elif self.force_overwrite and isfile(self.outfile):
            logging.warning(
                "Output file %s already exists; it will be overwritten!", self.outfile
            )

    def __tuplize_files(self, target_directory, input_files):
        """ Takes the input list and writes a specialized tuple of them """
        file_tuple = []

        # Loop to fill tuples
        total_num = len(input_files)
        for i in range(0, total_num, self.n_files_at_once):
            out_file = self.__get_random_root_name(target_directory)
            tmp_list = input_files[i : i + self.n_files_at_once]
            start_num = i + 1
            end_num = i + len(tmp_list)
            new_tuple = (out_file, start_num, end_num, total_num, tmp_list)
            file_tuple.append(new_tuple)

        return tuple(file_tuple)

    def __cleanup(self):
        """ Clean up intermediate files """
        if not self.save:
            logging.debug("Delete tmpdir %s", self.tmpdir)
            rmtree(self.tmpdir)
        else:
            logging.debug("Leaving tmpdir %s", self.tmpdir)

    def __get_random_root_name(self, directory):
        """ Return a random file name """
        chars = ascii_uppercase + digits + ascii_lowercase
        ran = []
        for _ in range(6):
            ran.append(choice(chars))
        num = self.counter
        self.counter += 1
        return directory + f"/input_{num}_" + "".join(ran) + ".root"

    def __set_tmp_dir(self, tmpdir):
        """ Set up a temporary directory to hold intermediate files """

        if tmpdir is None:
            self.tmpdir = mkdtemp(prefix="ahadd_") + "/"
        else:
            self.tmpdir = mkdtemp(prefix="ahadd_", dir=tmpdir) + "/"

        logging.debug("Making temporary directory: %s", self.tmpdir)


def main():
    # Set default jobs number
    if HAS_MP:
        N_JOBS = int(mp.cpu_count() * 1.5)
    else:
        N_JOBS = 1

    argparser = argparse.ArgumentParser(
        description="Script for adding ROOT histograms in parallel"
    )
    argparser.add_argument("output_file", type=str, help="the output file")
    argparser.add_argument(
        "input_files", type=str, nargs="+", help="one or more input files"
    )
    argparser.add_argument(
        "-n",
        "--n-files-at-once",
        action="store",
        type=int,
        default=20,
        help="combine this many files at one time [defualt 20]",
    )
    argparser.add_argument(
        "-t",
        "--tmp-dir",
        action="store",
        type=str,
        default=None,
        help="location to store temporary intermediate files",
    )
    argparser.add_argument(
        "-s",
        "--save-tmp",
        action="store_true",
        default=False,
        help="save temporary files, otherwise they are cleaned up when the program exits [default false]",
    )
    argparser.add_argument(
        "-f",
        "--force-overwrite",
        action="store_true",
        dest="force_overwrite",
        default=False,
        help="Overwrite the output file if it exists [default false]",
    )
    argparser.add_argument(
        "-j",
        "--jobs",
        action="store",
        type=int,
        dest="n_jobs",
        default=N_JOBS,
        help=f"use this many subprocess [default cpu_count*1.5 = {N_JOBS}]",
    )
    argparser.add_argument(
        "--log",
        help="set the logging level, defaults to WARNING",
        dest="log_level",
        default=logging.WARNING,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    argparser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    args = argparser.parse_args()
    logging.basicConfig(level=args.log_level)

    logging.debug("Arguments: %s", args)

    # Check if hadd exists
    if find_executable("hadd") is None:
        logging.error("Can not find hadd.")
        exit(EXIT.MISSING_HADD)

    ## Check n_jobs
    if not HAS_MP:
        args.n_jobs = 1
    # One input file means we can just copy it
    if len(args.input_files) == 1:
        logging.warning("Only one input file; running a simple copy!")
        logging.info(
            "Copying final file: %s --> %s", args.input_files[0], args.output_file
        )
        copy2(args.input_files[0], args.output_file)
        exit(EXIT.GOOD)

    ## Check that the number of files to hadd each step is sane
    if args.n_files_at_once <= 1:
        logging.error(
            "Requested to hadd 1 or fewer files per iteration; this will never converge."
        )
        exit(EXIT.GENERIC_BAD)

    ## Set up and run Hadd
    hadd = Hadd(
        args.output_file,
        args.input_files,
        args.tmp_dir,
        args.force_overwrite,
        args.save_tmp,
        args.n_files_at_once,
        args.n_jobs,
    )
    hadd.run()


if __name__ == "__main__":
    main()
