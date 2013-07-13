Alex Hadd
=========

Alex Hadd is a python wrapper around 'hadd', a utility for adding [CERN
Root](http://root.cern.ch) histograms. It allows a list of files to be added in
blocks instead of all at once (which can be useful if you are memory limited),
and further allows each block to be added in parallel if your version of python
supports the `multiprocessing` module.

Usage
-----

If the program is called as follows:

    ahadd.py -h

It will provide the following usage guide:

    Usage: ahadd.py [Options] output_file input_files

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -n NATONE, --n-files-at-once=NATONE
                            combine this many files at one time [defualt 20]
      -t TMP_DIR, --temp-dir=TMP_DIR
                            location to store temporary intermediate files
      -s, --save-temp       save temporary files, otherwise they are cleaned up
                            when the program exits [default false]
      -v, --verbose         print some extra status messages to stdout [default
                            false]
      -q, --quite           do not print any status messages to stdout [default
                            false]
      -V, --very-verbose    print everything, even the output from hadd [default
                            false]
      -f, --force-overwrite
                            Overwrite the output file if it exists [default false]
      -j NJOBS, --jobs=NJOBS
                            use this many subprocess [default cpu_count*1.5 = N]

Note that in the case of the `-j` flag, the 'N' in the help output will display
the default calculated for your computer.

The simplest usage case is:

    ahadd.py output.root *root

This will add every histogram in the current directory together, and save the
result as output.root.
