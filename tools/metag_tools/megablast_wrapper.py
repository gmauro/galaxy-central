#! /usr/bin/python
"""
run megablast for metagenomics data
"""

import sys, os, tempfile, subprocess
#from megablast_xml_parser import *

DB_LOC = "%s/blastdb.loc" % os.environ.get( 'GALAXY_DATA_INDEX_DIR' )

def __main__():
    # file I/O
    db_build = sys.argv[1]
    query_filename = sys.argv[2]
    output_filename = sys.argv[3]
    
    # megablast parameters
    mega_word_size = sys.argv[4]        # -W
    mega_iden_cutoff = sys.argv[5]      # -p
    mega_disc_word = sys.argv[6]        # -t
    mega_disc_type = sys.argv[7]        # -N
    mega_filter = sys.argv[8]           # -F
    
    output_file = open(output_filename, 'w')
    
    # prepare the database
    db = {}
    db_file = open(DB_LOC, "r")
    for i, line in enumerate(db_file):
        line = line.rstrip('\r\n')
        fields = line.split()
        db[(fields[0])] = []
        for j in xrange(1, len(fields)):
            db[(fields[0])].append(fields[j])
    
    # prepare to run megablast
    retcode = subprocess.call('which megablast 2>&1', shell='True')
    if retcode < 0:
        print >> sys.stderr, "Cannot locate megablast."
        sys.exit()
        
    for chunk in db[(db_build)]:
        megablast_arguments = ["megablast", "-d", chunk, "-i", query_filename]
        megablast_parameters = ["-m", "8", "-a", "8"]
        megablast_user_inputs = ["-W", mega_word_size, "-p", mega_iden_cutoff, "-t", mega_disc_word, "-N", mega_disc_type, "-F", mega_filter]
        megablast_command = " ".join(megablast_arguments) + " " + " ".join(megablast_parameters) + " " + " ".join(megablast_user_inputs) + " 2>&1" 
        
        # use Anton's parser
        megablast_output = os.popen(megablast_command)
        #parse_megablast_xml_output(megablast_output,output_file)
        for i, line in enumerate(megablast_output):
            line = line.strip('\r\n')
            fields = line.split()
            if (not line.startswith("#")): 
                # replace subject id with gi number
                # remove this after re-build blastdb
                subject_id_fields = fields[1].split('|')
                gi = subject_id_fields[1]
                fields[1] = gi
                print >> output_file, "\t".join(fields) 
        
    output_file.close()
    
    # megablast generates a file called error.log, if empty, delete it, if not, show the contents
    if os.path.exists('./error.log'):
        for i, line in enumerate( file('./error.log') ):
            line = line.rstrip('\r\n')
            print >> sys.stdout, line
        os.remove('./error.log')
    
if __name__ == "__main__" : __main__()