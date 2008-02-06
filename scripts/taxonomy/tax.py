#!/usr/bin/env python

"""
Identify full taxonomic standing for sequences identified by gi number

usage: %prog taxonomy_db gi_list_file out_file
    -c, --cols=N: Number of column containing gi within the gi_list file

    gi_list_file - user's input containing gi's in the column specified by option -c

    taxonomy_db - database containing collapsed NCBI taxonomy generated by prepareTaxonomy.sh script 
    distributed with Galaxy. See readme.txt for information on how to generate
    necessary files
    
"""

import pkg_resources
pkg_resources.require( 'bx-python' )
pkg_resources.require( 'pysqlite' )
import traceback
import fileinput
from pysqlite2 import dbapi2 as sqlite
from warnings import warn
from bx.cookbook import doc_optparse
import string, sys

def main():
    
    options, args = doc_optparse.parse( __doc__ )
    
    if len(args) < 3:
        sys.stderr.write("Not enough arguments\n")
        sys.exit(0)    
        
    try:
        db_name, gi_fname, out_fname = args
        giCol = int( options.cols ) - 1
    except:
        doc_optparse.exception
        
    con = sqlite.connect(db_name)
    cur = con.cursor()
    
    fg = open(gi_fname, 'r')
    of = open( out_fname, "w" )
    
    try:
        for line in fg:
                field = string.split(line.rstrip(), '\t')
                sqlTemplate = string.Template('select gi2tax.gi, tax.* from gi2tax left join tax on gi2tax.taxId = tax.taxId where gi2tax.gi = $gi') 
                sql = sqlTemplate.substitute(gi = int(field[giCol]))
                cur.execute(sql)

                for item in cur.fetchall():
                    ranks = string.split(item[2], ",")
                    print >> of, str(item[0]) + "\t" + str(item[1]) + "\t" + "\t".join(ranks) 

    finally:
        fg.close()
        
if __name__ == "__main__":
    main()
