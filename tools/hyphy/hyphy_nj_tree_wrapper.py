#Dan Blankenberg
#takes commandline tree def and input multiple fasta alignment file and runs the branch length ananlysis
import os, sys
import hyphy_util

#Retrieve hard coded hyphy path, this will need to be the same across the cluster
HYPHY_PATH = hyphy_util.HYPHY_PATH
HYPHY_EXECUTABLE = hyphy_util.HYPHY_EXECUTABLE

#Read command line arguments
input_filename = os.path.abspath(sys.argv[1].strip())
output_filename1 = os.path.abspath(sys.argv[2].strip())
output_filename2 = os.path.abspath(sys.argv[3].strip())
distance_metric = sys.argv[4].strip()
temp_ps_filename = hyphy_util.get_filled_temp_filename("")

#Guess if this is a single or multiple FASTA input file
found_blank = False
is_multiple = False
for line in open(input_filename):
    line = line.strip()
    if line == "": found_blank = True
    elif line.startswith(">") and found_blank:
        is_multiple = True
        break
    else: found_blank = False

NJ_tree_shared_ibf = hyphy_util.get_filled_temp_filename(hyphy_util.NJ_tree_shared_ibf)

#set up NJ_tree file
NJ_tree_filename = hyphy_util.get_filled_temp_filename(hyphy_util.get_NJ_tree(NJ_tree_shared_ibf))
#setup Config file
config_filename = hyphy_util.get_nj_tree_config_filename(input_filename, distance_metric, output_filename1, temp_ps_filename, NJ_tree_filename)
if is_multiple: 
    os.unlink(NJ_tree_filename)
    os.unlink(config_filename)
    NJ_tree_filename = hyphy_util.get_filled_temp_filename(hyphy_util.get_NJ_treeMF(NJ_tree_shared_ibf))
    config_filename = hyphy_util.get_nj_treeMF_config_filename(input_filename, output_filename1, temp_ps_filename, distance_metric, NJ_tree_filename)
    print "Multiple Alignment Analyses"
else: print "Single Alignment Analyses"


#Run Hyphy
hyphy_cmd = "%s BASEPATH=%s USEPATH=/dev/null %s" % (HYPHY_EXECUTABLE, HYPHY_PATH, config_filename)
hyphy = os.popen(hyphy_cmd, 'r')
#print hyphy.read()
hyphy.close()

#remove temporary files
os.unlink(NJ_tree_filename)
os.unlink(config_filename)


#Convert PS to PDF
if os.path.getsize(temp_ps_filename)>0: temp = os.popen("ps2pdf %s %s" % (temp_ps_filename, output_filename2), 'r').close()
os.unlink(temp_ps_filename)