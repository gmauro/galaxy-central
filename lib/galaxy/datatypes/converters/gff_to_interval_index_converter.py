#!/usr/bin/env python

"""
Convert from GFF file to interval index file.

usage:
    python gff_to_interval_index_converter.py [input] [output]
"""

from __future__ import division

import sys, fileinput
from galaxy import eggs
import pkg_resources; pkg_resources.require( "bx-python" )
from galaxy.datatypes.util.gff_util import *
from bx.interval_index_file import Indexes

def main():
    # Arguments
    input_fname, out_fname = sys.argv[1:]
        
    # Do conversion.
    index = Indexes()
    offset = 0
    reader_wrapper = GFFReaderWrapper( fileinput.FileInput( input_fname ), fix_strand=True )
    for feature in list( reader_wrapper ):
        # TODO: need to address comments:
        # if comment:
        #   increment_offset.
        
        # Add feature; index expects BED coordinates.
        convert_gff_coords_to_bed( feature )
        index.add( feature.chrom, feature.start, feature.end, offset )
        
        # Increment offset by feature length; feature length is all 
        # intervals/lines that comprise feature.
        feature_len = 0
        for interval in feature.intervals:
            # HACK: +1 for EOL char. Need bx-python to provide raw_line itself 
            # b/c TableReader strips EOL characters, thus changing the line
            # length.
            feature_len += len( interval.raw_line ) + 1
        offset += feature_len
            
    index.write( open(out_fname, "w") )
    
if __name__ == "__main__": 
    main()
    