"""
Manage tool data tables, which store (at the application level) data that is
used by tools, for example in the generation of dynamic options. Tables are
loaded and stored by names which tools use to refer to them. This allows
users to configure data tables for a local Galaxy instance without needing
to modify the tool configurations. 
"""

import logging, sys, os.path
from galaxy import util

log = logging.getLogger( __name__ )

class ToolDataTableManager( object ):
    """
    Manages a collection of tool data tables
    """
    
    def __init__( self, config_filename=None ):
        self.data_tables = {}
        if config_filename:
            self.add_from_config_file( config_filename )
        
    def __getitem__( self, key ):
        return self.data_tables.__getitem__( key )
        
    def __contains__( self, key ):
        return self.data_tables.__contains__( key )
        
    def add_from_config_file( self, config_filename ):
        tree = util.parse_xml( config_filename )
        root = tree.getroot()
        for table_elem in root.findall( 'table' ):
            type = table_elem.get( 'type', 'tabular' )
            assert type in tool_data_table_types, "Unknown data table type '%s'" % type
            table = tool_data_table_types[ type ]( table_elem )
            self.data_tables[ table.name ] = table
            log.debug( "Loaded tool data table '%s", table.name )
    
class ToolDataTable( object ):
    def __init__( self, config_element ):
        self.name = config_element.get( 'name' )
    
class TabularToolDataTable( ToolDataTable ):
    """
    Data stored in a tabular / separated value format on disk, allows multiple
    files to be merged but all must have the same column definitions.
    
    <table type="tabular" name="test">
        <column name='...' index = '...' />
        <file path="..." />
        <file path="..." />
    </table>
    """
    
    type_key = 'tabular'
    
    def __init__( self, config_element ):
        super( TabularToolDataTable, self ).__init__( config_element )
        self.configure_and_load( config_element )
    
    def configure_and_load( self, config_element ):
        """
        Configure and load table from an XML element.
        """
        self.separator = config_element.get( 'separator', '\t' )
        self.comment_char = config_element.get( 'comment_char', '#' )
        # Configure columns
        self.parse_column_spec( config_element )
        # Read every file
        all_rows = []
        for file_element in config_element.findall( 'file' ):
            filename = file_element.get( 'path' )
            if not os.path.exists( filename ): 
                log.warn( "Cannot find index file '%s' for tool data table '%s'" % ( filename, self.name ) )
            else:
                all_rows.extend( self.parse_file_fields( open( filename ) ) )
        self.data = all_rows
        
    def get_fields( self ):
        return self.data
            
    def parse_column_spec( self, config_element ):
        """
        Parse column definitions, which can either be a set of 'column' elements
        with a name and index (as in dynamic options config), or a shorthand
        comma separated list of names in order as the text of a 'column_names'
        element.
        
        A column named 'value' is required. 
        """
        self.columns = {}
        if config_element.find( 'columns' ) is not None:
            column_names = util.xml_text( config_element.find( 'columns' ) )
            column_names = [ n.strip() for n in column_names.split( ',' ) ]
            for index, name in enumerate( column_names ):
                self.columns[ name ] = index
                self.largest_index = index
        else:
            for column_elem in config_element.findall( 'column' ):
                name = column_elem.get( 'name', None )
                assert name is not None, "Required 'name' attribute missing from column def"
                index = column_elem.get( 'index', None )
                assert index is not None, "Required 'index' attribute missing from column def"
                index = int( index )
                self.columns[name] = index
                if index > self.largest_index:
                    self.largest_index = index
        assert 'value' in self.columns, "Required 'value' column missing from column def"
        if 'name' not in self.columns:
            self.columns['name'] = self.columns['value']
        
    def parse_file_fields( self, reader ):
        """
        Parse separated lines from file and return a list of tuples.
        
        TODO: Allow named access to fields using the column names.
        """
        rval = []
        for line in reader:
            if line.lstrip().startswith( self.comment_char ):
                continue
            line = line.rstrip( "\n\r" )
            if line:
                fields = line.split( self.separator )
                if self.largest_index < len( fields ):
                    rval.append( fields )
        return rval        

# Registry of tool data types by type_key
tool_data_table_types = dict( [ ( cls.type_key, cls ) for cls in [ TabularToolDataTable ] ] )
