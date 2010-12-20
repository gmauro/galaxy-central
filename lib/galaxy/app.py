import sys, os, atexit

from galaxy import config, jobs, util, tools, web
import galaxy.tools.search
import galaxy.tools.data
from galaxy.web import security
import galaxy.model
import galaxy.datatypes.registry
import galaxy.security
from galaxy.tags.tag_handler import GalaxyTagHandler
from galaxy.tools.imp_exp import load_history_imp_exp_tools
from galaxy.sample_tracking import sequencer_types

class UniverseApplication( object ):
    """Encapsulates the state of a Universe application"""
    def __init__( self, **kwargs ):
        print >> sys.stderr, "python path is: " + ", ".join( sys.path )
        # Read config file and check for errors
        self.config = config.Configuration( **kwargs )
        self.config.check()
        config.configure_logging( self.config )
        # Set up datatypes registry
        self.datatypes_registry = galaxy.datatypes.registry.Registry( self.config.root, self.config.datatypes_config )
        galaxy.model.set_datatypes_registry( self.datatypes_registry )
        # Determine the database url
        if self.config.database_connection:
            db_url = self.config.database_connection
        else:
            db_url = "sqlite:///%s?isolation_level=IMMEDIATE" % self.config.database
        # Initialize database / check for appropriate schema version
        from galaxy.model.migrate.check import create_or_verify_database
        create_or_verify_database( db_url, self.config.database_engine_options )
        # Setup the database engine and ORM
        from galaxy.model import mapping
        self.model = mapping.init( self.config.file_path,
                                   db_url,
                                   self.config.database_engine_options,
                                   database_query_profiling_proxy = self.config.database_query_profiling_proxy )
        # Security helper
        self.security = security.SecurityHelper( id_secret=self.config.id_secret )
        # Tag handler
        self.tag_handler = GalaxyTagHandler()
        # Tool data tables
        self.tool_data_tables = galaxy.tools.data.ToolDataTableManager( self.config.tool_data_table_config_path )
        # Initialize the tools
        self.toolbox = tools.ToolBox( self.config.tool_config, self.config.tool_path, self )
        # Search support for tools
        self.toolbox_search = galaxy.tools.search.ToolBoxSearch( self.toolbox )
        # Load datatype converters
        self.datatypes_registry.load_datatype_converters( self.toolbox )
        # Load history import/export tools
        load_history_imp_exp_tools( self.toolbox )
        #load external metadata tool
        self.datatypes_registry.load_external_metadata_tool( self.toolbox )
        # Load datatype indexers
        self.datatypes_registry.load_datatype_indexers( self.toolbox )
        #Load security policy
        self.security_agent = self.model.security_agent
        self.host_security_agent = galaxy.security.HostAgent( model=self.security_agent.model, permitted_actions=self.security_agent.permitted_actions )
        # Heartbeat and memdump for thread / heap profiling
        self.heartbeat = None
        self.memdump = None
        self.memory_usage = None
        # Container for OpenID authentication routines
        if self.config.enable_openid:
            from galaxy.web.framework import openid_manager
            self.openid_manager = openid_manager.OpenIDManager( self.config.openid_consumer_cache_path )
        # Start the heartbeat process if configured and available
        if self.config.use_heartbeat:
            from galaxy.util import heartbeat
            if heartbeat.Heartbeat:
                self.heartbeat = heartbeat.Heartbeat( fname=self.config.heartbeat_log )
                self.heartbeat.start()
        # Enable the memdump signal catcher if configured and available
        if self.config.use_memdump:
            from galaxy.util import memdump
            if memdump.Memdump:
                self.memdump = memdump.Memdump()
        # Start the job queue
        self.job_manager = jobs.JobManager( self )
        # FIXME: These are exposed directly for backward compatibility
        self.job_queue = self.job_manager.job_queue
        self.job_stop_queue = self.job_manager.job_stop_queue
        # Initialize the sequencer types
        self.sequencer_types = sequencer_types.SequencerTypesCollection( self.config.sequencer_type_config_file, self.config.sequencer_type_path, self )
        # Transfer manager client
        if self.config.get_bool( 'enable_deferred_job_queue', False ):
            from jobs import transfer_manager
            self.transfer_manager = transfer_manager.TransferManager( self )
        
    def shutdown( self ):
        self.job_manager.shutdown()
        if self.heartbeat:
            self.heartbeat.shutdown()
