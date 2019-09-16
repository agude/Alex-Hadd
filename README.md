# Alex Hadd

Alex Hadd is a python wrapper around 'hadd', a utility for adding [CERN
Root](http://root.cern.ch) histograms. It allows a list of files to be added
in blocks instead of all at once (which can be useful if you are memory
limited), and further allows each block to be added in parallel if your
version of python supports the `multiprocessing` module.

## Installation

Alex Hadd requires Python3, specifically 3.6 or above. You can install this
repository with `pip` as follows:

```bash
git clone https://github.com/agude/Alex-Hadd.git
pip install ./Alex-Hadd
```

## Usage

The program is called as follows:

```bash
ahadd.py output.root *root
```

This will add every histogram in the current directory together, and save the
result as `output.root`.

There is a built in help:

```bash
ahadd.py -h
```

Which provides the following usage guide:

```
usage: ahadd [-h] [-n N_FILES_AT_ONCE] [-t TMP_DIR] [-s] [-f] [-j N_JOBS]
             [--log {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--version]
             output_file input_files [input_files ...]

Script for adding ROOT histograms in parallel

positional arguments:
  output_file           the output file
  input_files           one or more input files

optional arguments:
  -h, --help            show this help message and exit
  -n N_FILES_AT_ONCE, --n-files-at-once N_FILES_AT_ONCE
                        combine this many files at one time [defualt 20]
  -t TMP_DIR, --tmp-dir TMP_DIR
                        location to store temporary intermediate files
  -s, --save-tmp        save temporary files, otherwise they are cleaned up
                        when the program exits [default false]
  -f, --force-overwrite
                        Overwrite the output file if it exists [default false]
  -j N_JOBS, --jobs N_JOBS
                        use this many subprocess [default cpu_count*1.5 = N]
  --log {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        set the logging level, defaults to WARNING
  --version             show program's version number and exit
```

Note that in the case of the `-j` flag, the 'N' in the help output will display
the default calculated for your computer.
