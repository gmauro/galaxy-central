"""
XML format classes
"""
import data
import logging
from galaxy.datatypes.sniff import *

log = logging.getLogger(__name__)

class BlastXml( data.Text ):
    """NCBI Blast XML Output data"""
    file_ext = "blastxml"
    def set_peek( self, dataset ):
        """Set the peek and blurb text"""
        dataset.peek  = data.get_file_peek( dataset.file_name )
        dataset.blurb = 'NCBI Blast XML data'
    def sniff( self, filename ):
        """
        Determines whether the file is blastxml
        
        >>> fname = get_test_fname( 'megablast_xml_parser_test1.blastxml' )
        >>> BlastXml().sniff( fname )
        True
        >>> fname = get_test_fname( 'interval.interval' )
        >>> BlastXml().sniff( fname )
        False
        """
        blastxml_header = [ '<?xml version="1.0"?>',
                            '<!DOCTYPE BlastOutput PUBLIC "-//NCBI//NCBI BlastOutput/EN" "http://www.ncbi.nlm.nih.gov/dtd/NCBI_BlastOutput.dtd">',
                            '<BlastOutput>' ]
        for i, line in enumerate( file( filename ) ):
            if i >= len( blastxml_header ):
                return True
            line = line.rstrip( '\n\r' )
            if line != blastxml_header[ i ]:
                return False
