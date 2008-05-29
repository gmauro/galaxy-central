#! /usr/bin/python

"""
convert fastq file to separated sequence and quality files.

assume each sequence and quality score are contained in one line
the order should be:
1st line: @title_of_seq
2nd line: nucleotides
3rd line: +title_of_qualityscore (might be skipped)
4th line: quality scores 
(in three forms: a. digits, b. ASCII codes, the first char as the coding base, c. ASCII codes without the first char.)

Usage:
%python convert_fastq2fasta.py <your_fastq_filename> <output_seq_filename> <output_score_filename>
"""

import sys, os
from math import *

assert sys.version_info[:2] >= ( 2, 4 )

def stop_err( msg ):
    sys.stderr.write( "%s" % msg )
    sys.exit()

def __main__():
    # TODO: This tool currently only works for Standard Fastq or Solexa Fastq where the 
    # quality scores are integers.  This tool will not produce the correct result if the 
    # input format is fastqsolexa and the data includes quality scores that are ASCII..  Our
    # fastqsolexa sniffer currently will not sniff data as fastqsolexa when the scores are ASCII,
    # but a user can manually change the data type in whcih case this tool will break.
    infile_name = sys.argv[1]
    outfile_seq = open( sys.argv[2], 'w' )
    outfile_score = open( sys.argv[3], 'w' )
    datatype = sys.argv[4]
    seq_title_startswith = ''
    qual_title_startswith = ''
    default_coding_value = 33
    fastq_block_lines = 0
    
    for i, line in enumerate( file( infile_name ) ):
        line = line.rstrip()
        if not line or line.startswith( '#' ):
            continue
        fastq_block_lines = ( fastq_block_lines + 1 ) % 4
        line_startswith = line[0:1]
        if fastq_block_lines == 1:
            # first line is @title_of_seq
            if not seq_title_startswith:
                seq_title_startswith = line_startswith
            if line_startswith != seq_title_startswith:
                outfile_seq.close()
                outfile_score.close()
                stop_err( 'Invalid fastq format at line %d: %s.' % ( i + 1, line ) )
            read_title = line[1:]
            outfile_seq.write( '>%s\n' % line[1:] )
        elif fastq_block_lines == 2:
            # second line is nucleotides
            read_length = len( line )
            outfile_seq.write( '%s\n' % line )
        elif fastq_block_lines == 3:
            # third line is +title_of_qualityscore ( might be skipped )
            if not qual_title_startswith:
                qual_title_startswith = line_startswith
            if line_startswith != qual_title_startswith:
                outfile_seq.close()
                outfile_score.close()
                stop_err( 'Invalid fastq format at line %d: %s.' % ( i + 1, line ) )    
            quality_title = line[1:]
            if quality_title and read_title != quality_title:
                outfile_seq.close()
                outfile_score.close()
                stop_err( 'Invalid fastq format at line %d: sequence title "%s" differes from score title "%s".' % ( i + 1, read_title, quality_title ) )
            if not quality_title:
                outfile_score.write( '>%s\n' % read_title )
            else:
                outfile_score.write( '>%s\n' % line[1:] )
        else:
            # fourth line is quality scores
            qual = ''
            # peek: ascii or digits?
            val = line.split()[0]
            if val.isdigit():
                # digits
                qual = line
            else:
                if datatype == 'fastqsolexa':
                    outfile_seq.close()
                    outfile_score.close()
                    stop_err( "This tool currently only works with the fastq solexa variant if the socres are integers, not ascii." )
                # ascii
                quality_score_length = len( line )
                if quality_score_length == read_length + 1:
                    # first char is qual_score_startswith
                    qual_score_startswith = ord( line[0:1] )
                    line = line[1:]
                elif quality_score_length == read_length:
                    qual_score_startswith = default_coding_value
                else:
                    stop_err( 'Invalid fastq format at line %d: the number of quality scores ( %d ) is not the same as bases ( %d ).' % ( i + 1, quality_score_length, read_length ) )
                for j, char in enumerate( line ):
                    score = ord( char ) - qual_score_startswith    # 64
                    qual = "%s%s " % ( qual, str( score ) )
            outfile_score.write( '%s\n' % qual )
              
    outfile_seq.close()
    outfile_score.close()

if __name__ == "__main__": __main__() 
    