# snapshot.py
# Ronald L. Rivest
# July 22, 2017
# python3

"""
snapshot.py provides a way of taking a "snapshot" of a directory
(and its subdirectories).  A snapshot consists of a directory
mapping filenames to file hashes, where the hash values are
computed with SHA256.  In addition to producing a snapshot,
it is also possible to verify that a snapshot is correct
(i.e. that the given files have the correct hashes; other
files may exist that aren't checked).
(Similar to old "tripwire" program.)
"""


import hashlib
import logging
import os
import time


def hash_file(filename):
    """ Return length-64 hexadecimal SHA256 hash of file with given filename. """

    h = hashlib.sha256()
    with open(filename, "rb") as f:
        h.update(f.read(2**20))
    return h.hexdigest()


def compute_dir_hash(topdirname):
    """ Return dict of filename->hashvalue starting from topdir;
        include files in subdirectories.
    """

    dir_hash = {}
    for (dirpath, dirnames, filenames) in os.walk(topdirname):
        for filename in filenames:
            fullfilename = os.path.join(dirpath, filename)
            hashvalue = hash_file(fullfilename)
            dir_hash[fullfilename] = hashvalue
    return dir_hash


def verify_dir_hash(topdirname, dir_hash, exclusions=[]):
    """ Return True if dir_hash is correct now. 
        (Only checks entries in dir_hash; others may exist in
        directory now as well, but they aren't checked.  This
        is OK.)
        Files whose filename starts with a prefix listed in exclusions 
        are not checked (allowing for the snapshot file itself to be 
        excluded).
    """

    new_dir_hash = compute_dir_hash(topdirname)
    for filename in dir_hash:
        if any([filename.startswith(prefix) for prefix in exclusions]):
            continue
        if new_dir_hash.get(filename, "") != dir_hash[filename]:
            return False
    return True
    

def hash_speed():
    """ Report time to hash 2**k bytes, for k=32.
        About 0.4 Gb/sec on a macbook pro.
    """

    logger.info("Measuring SHA256 hash speed on 256MB of data...")
    s = b" "*(2**20)              # 1MB
    for k in [28]:
        t0 = time.time()
        h = hashlib.sha256()
        for _ in range(2**(k-20)):
            h.update(s)
        # hash_value = h.hexdigest()
        t1 = time.time()
        logger.info("    Estimated speed {:0.2f} Gbytes/sec".format((2**(k-30))/(t1-t0)))


def write_hash_dir(topdirname, output_filename):
    """ Write CSV file representing dir_hash to output_file in CSV format. """

    dir_hash = compute_dir_hash(topdirname)
    try:
        output_file = open(output_filename, "w")
        output_file.write("Filename,Hash\n")
        for filename in sorted(dir_hash):
            output_file.write(filename)
            output_file.write(",")
            output_file.write(dir_hash[filename])
            output_file.write("\n")
    finally:
        output_file.close()


if __name__=="__main__":

    dir_hash = compute_dir_hash(".")
    logger.info("Does snapshot work on current directory:",
          verify_dir_hash(".", dir_hash))

    hash_speed()

    hash_filename = "test_data/20-audit-snapshot.csv"
    write_hash_dir(".", hash_filename)
    logger.info("hash file {} written.".format(hash_filename))
