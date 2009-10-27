from galaxy.web.base.controller import *

import pkg_resources
pkg_resources.require( "simplejson" )
import simplejson

from galaxy.tools.parameters import *
from galaxy.tools import DefaultToolState
from galaxy.tools.parameters.grouping import Repeat, Conditional
from galaxy.datatypes.data import Data
from galaxy.util.odict import odict
from galaxy.util.bunch import Bunch
from galaxy.util.topsort import topsort, topsort_levels, CycleError
from galaxy.workflow.modules import *
from galaxy.model.mapping import desc
from galaxy.model.orm import *
from datetime import datetime, timedelta

pkg_resources.require( "WebHelpers" )
from webhelpers import *

# Required for Cloud tab
import galaxy.eggs
galaxy.eggs.require("boto")
from boto.ec2.connection import EC2Connection
from boto.ec2.regioninfo import RegionInfo
from galaxy.cloud import CloudManager

import logging
log = logging.getLogger( __name__ )

uci_states = Bunch(
    NEW_UCI = "newUCI",
    NEW = "new",
    DELETING_UCI = "deletingUCI",
    DELETING = "deleting",
    SUBMITTED_UCI = "submittedUCI",
    SUBMITTED = "submitted",
    SHUTTING_DOWN_UCI = "shutting-downUCI",
    SHUTTING_DOWN = "shutting-down",
    AVAILABLE = "available",
    RUNNING = "running",
    PENDING = "pending",
    ERROR = "error",
    DELETED = "deleted"
)

instance_states = Bunch(
    TERMINATED = "terminated",
    RUNNING = "running",
    PENDING = "pending",
    SHUTTING_DOWN = "shutting-down"
)

class CloudController( BaseController ):
    
#    def __init__( self ):
#        self.cloudManager = CloudManager()
    
    @web.expose
    def index( self, trans ):
        return trans.fill_template( "cloud/index.mako" )
                                   
    @web.expose
    @web.require_login( "use Galaxy cloud" )
    def list( self, trans ):
        """
        Render cloud main page (management of cloud resources)
        """
        user = trans.get_user()
#        pendingInstances = trans.sa_session.query( model.UCI ) \
#            .filter_by( user=user, state="pending" ) \
#            .all()
#            
#        for i inupdate_in range( len ( pendingInstances ) ):
#            stance_state( trans, pendingInstances[i].id )
        
        cloudCredentials = trans.sa_session.query( model.CloudUserCredentials ) \
            .filter_by( user=user ) \
            .order_by( desc( model.CloudUserCredentials.c.name ) ) \
            .all()
        
        liveInstances = trans.sa_session.query( model.UCI ) \
            .filter_by( user=user ) \
            .filter( or_( model.UCI.c.state==uci_states.RUNNING, #"running", 
                          model.UCI.c.state==uci_states.PENDING, #"pending",
                          model.UCI.c.state==uci_states.SUBMITTED, #"submitted", 
                          model.UCI.c.state==uci_states.SUBMITTED_UCI, #"submittedUCI",
                          model.UCI.c.state==uci_states.SHUTTING_DOWN, #"shutting-down",
                          model.UCI.c.state==uci_states.SHUTTING_DOWN_UCI ) ) \
            .order_by( desc( model.UCI.c.update_time ) ) \
            .all()
            
        prevInstances = trans.sa_session.query( model.UCI ) \
            .filter_by( user=user ) \
            .filter( or_( model.UCI.c.state==uci_states.AVAILABLE, #"available", 
                          model.UCI.c.state==uci_states.NEW, #"new", 
                          model.UCI.c.state==uci_states.NEW_UCI, #"newUCI", 
                          model.UCI.c.state==uci_states.ERROR, #"error", 
                          model.UCI.c.state==uci_states.DELETING, #"deleting",
                          model.UCI.c.state==uci_states.DELETING_UCI ) ) \
            .order_by( desc( model.UCI.c.update_time ) ) \
            .all()
        
        # Check after update there are instances in pending state; if so, display message
        # TODO: Auto-refresh once instance is running
        pendingInstances = trans.sa_session.query( model.UCI ) \
            .filter_by( user=user ) \
            .filter( or_( model.UCI.c.state==uci_states.PENDING, #"pending" , \
                          model.UCI.c.state==uci_states.SUBMITTED, #"submitted" , \
                          model.UCI.c.state==uci_states.SUBMITTED_UCI ) ) \
            .all()
        if pendingInstances:
            trans.set_message( "Galaxy instance started. NOTE: Please wait about 3-5 minutes for the instance to " 
                    "start up and then refresh this page. A button to connect to the instance will then appear alongside "
                    "instance description." )         
        
#        log.debug( "provider.is_secure: '%s'" % trans.sa_session.query( model.CloudProvider).filter_by(id=1).first().is_secure )
#        trans.sa_session.query( model.CloudProvider).filter_by(id=1).first().is_secure=False
#        trans.sa_session.flush()
#        log.debug( "provider.is_secure: '%s'" % trans.sa_session.query( model.CloudProvider).filter_by(id=1).first().is_secure )
        
#        log.debug( "image: '%s'" % model.CloudImage.is_secure )
        
        return trans.fill_template( "cloud/configure_cloud.mako",
                                    cloudCredentials = cloudCredentials,
                                    liveInstances = liveInstances,
                                    prevInstances = prevInstances )
    
    @web.expose
    @web.require_login( "use Galaxy cloud" )
    def makeDefault( self, trans, id=None ):
        """ 
        Set current credentials as default.
        """
        currentDefault = get_default_credentials (trans)
        if currentDefault:
            currentDefault.defaultCred = False
        
        newDefault = get_stored_credentials( trans, id )
        newDefault.defaultCred = True
        trans.sa_session.flush()
        trans.set_message( "Credentials '%s' set as default." % newDefault.name )
        
        # TODO: Fix bug that when this function returns, top Galaxy tab bar is missing from the webpage  
        return self.list( trans ) #trans.fill_template( "cloud/configure_cloud.mako",
               #awsCredentials = awsCredentials )
               

    @web.expose
    @web.require_login( "start Galaxy cloud instance" )
    def start( self, trans, id, type='m1.small' ):
        """
        Start a new cloud resource instance
        """
        user = trans.get_user()
        uci = get_uci( trans, id )
        mi = get_mi( trans, uci, type )
        stores = get_stores( trans, uci ) 
        # Ensure instance is not already running (or related state) and store relevant data
        # into DB to initiate instance startup by cloud manager
        if ( len(stores) is not 0 ) and \
           ( uci.state != uci_states.SUBMITTED ) and \
           ( uci.state != uci_states.SUBMITTED_UCI ) and \
           ( uci.state != uci_states.PENDING ) and \
           ( uci.state != uci_states.DELETING ) and \
           ( uci.state != uci_states.DELETING_UCI ) and \
           ( uci.state != uci_states.DELETED ) and \
           ( uci.state != uci_states.RUNNING ) and \
           ( uci.state != uci_states.NEW_UCI ) and \
           ( uci.state != uci_states.NEW ) and \
           ( uci.state != uci_states.ERROR ):
            instance = model.CloudInstance()
            instance.user = user
            instance.image = mi
            instance.uci = uci
            instance.availability_zone = stores[0].availability_zone # Bc. all EBS volumes need to be in the same avail. zone, just check 1st
            instance.type = type
            uci.state = uci_states.SUBMITTED_UCI
            # Persist
            session = trans.sa_session
            session.save_or_update( instance )
            session.save_or_update( uci )
            session.flush()
            # Log  
            trans.log_event ("User initiated starting of cloud instance '%s'." % uci.name )
            trans.set_message( "Galaxy instance started. NOTE: Please wait about 3-5 minutes for the instance to " 
                    "start up and then refresh this page. A button to connect to the instance will then appear alongside "
                    "instance description." )
            return self.list( trans )
        
        trans.show_error_message( "Cannot start instance that is in state '%s'." % uci.state )
        return self.list( trans )
    
    @web.expose
    @web.require_login( "stop Galaxy cloud instance" )
    def stop( self, trans, id ):
        """
        Stop a cloud UCI instance.
        """
        uci = get_uci( trans, id )
        if ( uci.state != uci_states.DELETING ) and \
           ( uci.state != uci_states.DELETING_UCI ) and \
           ( uci.state != uci_states.ERROR ) and \
           ( uci.state != uci_states.SHUTTING_DOWN_UCI ) and \
           ( uci.state != uci_states.SHUTTING_DOWN ) and \
           ( uci.state != uci_states.AVAILABLE ):
            uci.state = uci_states.SHUTTING_DOWN_UCI
            session = trans.sa_session
            session.save_or_update( uci )
            session.flush()
            trans.log_event( "User stopped cloud instance '%s' (id: %s)" % ( uci.name, uci.id ) )
            trans.set_message( "Stopping of Galaxy instance '%s' initiated." % uci.name )
            
            return self.list( trans )
        
        trans.show_error_message( "Cannot stop instance that is in state '%s'." % uci.state )
        return self.list( trans )
    
    @web.expose
    @web.require_login( "delete user configured Galaxy cloud instance" )
    def deleteInstance( self, trans, id ):
        """
        Deletes User Configured Instance (UCI) from the cloud and local database. NOTE that this implies deletion of 
        any and all storage associated with this UCI!
        """
        uci = get_uci( trans, id )
        
        if ( uci.state != uci_states.DELETING_UCI ) and ( uci.state != uci_states.DELETING ) and ( uci.state != uci_states.ERROR ):
            name = uci.name
            uci.state = uci_states.DELETING_UCI
            session = trans.sa_session
            session.save_or_update( uci )
            session.flush()
            trans.log_event( "User marked cloud instance '%s' for deletion." % name )
            trans.set_message( "Galaxy instance '%s' marked for deletion." % name )
            return self.list( trans )
        
        trans.set_message( "Instance '%s' is already marked for deletion." % uci.name )
        return self.list( trans )
    
    @web.expose
    @web.require_login( "add instance storage" )
    def addStorage( self, trans, id ):
        instance = get_uci( trans, id )
        
        
        error( "Adding storage to instance '%s' is not supported yet." % instance.name )
                    
        return self.list( trans )
    
    @web.expose
    @web.require_login( "use Galaxy cloud" )
    def usageReport( self, trans, id ):
        user = trans.get_user()
        id = trans.security.decode_id( id )
        
        prevInstances = trans.sa_session.query( model.CloudInstance ) \
            .filter_by( user=user, state=instance_states.TERMINATED, uci_id=id ) \
            .order_by( desc( model.CloudInstance.c.update_time ) ) \
            .all()
            
        log.debug( "id: %s" % id )
        
        return trans.fill_template( "cloud/view_usage.mako", prevInstances = prevInstances ) 
    
    @web.expose
    @web.require_login( "use Galaxy cloud" )
    def configureNew( self, trans, instanceName='', credName='', volSize='', zone='' ):
        """
        Configure and add new cloud instance to user's instance pool
        """
        inst_error = vol_error = cred_error = None
        error = {}
        user = trans.get_user()
        storedCreds = trans.sa_session.query( model.CloudUserCredentials ).filter_by( user=user ).all()
        if len( storedCreds ) == 0:
            return trans.show_error_message( "You must register credentials before configuring a Galaxy instance." )
        # Create dict mapping of cloud providers to zones available by those providers
        providersToZones = {}
        for storedCred in storedCreds:
            if storedCred.provider.type == 'ec2':
                ec2_zones = ['us-east-1a', 'us-east-1b', 'us-east-1c', 'us-east-1d']
                providersToZones[storedCred.name] = ec2_zones 
            elif storedCred.provider.type == 'eucalyptus':
                providersToZones[storedCred.name] = ['epc']
        
        if instanceName:
            # Create new user configured instance
            try:
                if trans.app.model.UCI \
                    .filter_by (user=user) \
                    .filter(  and_( trans.app.model.UCI.table.c.name==instanceName, trans.app.model.UCI.table.c.state!=uci_states.DELETED ) ) \
                    .first():
                    error['inst_error'] = "An instance with that name already exist."
                elif instanceName=='' or len( instanceName ) > 255:
                    error['inst_error'] = "Instance name must be between 1 and 255 characters long."
                elif credName=='':
                    error['cred_error'] = "You must select credentials."
                elif volSize == '':
                    error['vol_error'] = "You must specify volume size as an integer value between 1 and 1000."
                elif ( int( volSize ) < 1 ) or ( int( volSize ) > 1000 ):
                    error['vol_error'] = "Volume size must be integer value between 1 and 1000."
#                elif type( volSize ) != type( 1 ): # Check if volSize is int
#                    log.debug( "volSize='%s'" % volSize )
#                    error['vol_error'] = "Volume size must be integer value between 1 and 1000."
                elif zone=='':
                    error['zone_error'] = "You must select zone where this UCI will be registered."
                else:
                    # Capture user configured instance information
                    uci = model.UCI()
                    uci.name = instanceName
                    uci.credentials = trans.app.model.CloudUserCredentials.filter(
                        trans.app.model.CloudUserCredentials.table.c.name==credName ).first()
                    uci.user= user
                    uci.total_size = volSize # This is OK now because new instance is being created. 
                    uci.state = uci_states.NEW_UCI
                    
                    storage = model.CloudStore()
                    storage.user = user
                    storage.uci = uci
                    storage.size = volSize
                    storage.availability_zone = zone # TODO: Give user choice here. Also, enable region selection.
                    # Persist
                    session = trans.sa_session
                    session.save_or_update( uci )
                    session.save_or_update( storage )
                    session.flush()
                    # Log and display the management page
                    trans.log_event( "User configured new cloud instance" )
                    trans.set_message( "New Galaxy instance '%s' configured. Once instance status shows 'available' you will be able to start the instance." % instanceName )
                    return self.list( trans )
            except ValueError:
                vol_error = "Volume size must be specified as an integer value only, between 1 and 1000."
            except AttributeError, ae:
                inst_error = "No registered cloud images. You must contact administrator to add some before proceeding."
                log.debug("AttributeError: %s " % str( ae ) )
        
        #TODO: based on user credentials (i.e., provider) selected, zone options will be different (e.g., EC2: us-east-1a vs EPC: epc)
        
        return trans.fill_template( "cloud/configure_uci.mako", 
                                    instanceName = instanceName, 
                                    credName = storedCreds, 
                                    volSize = volSize, 
                                    zone = zone, 
                                    error = error, 
                                    providersToZones = providersToZones )
                
        return trans.show_form( 
            web.FormBuilder( web.url_for(), "Configure new instance", submit_text="Add" )
                .add_text( "instanceName", "Instance name", value="Unnamed instance", error=inst_error ) 
                .add_text( "credName", "Name of registered credentials to use", value="", error=cred_error )
                .add_text( "volSize", "Permanent storage size (1GB - 1000GB)"  
                    "<br />Note: you will be able to add more storage later", value='', error=vol_error ) )
        
    @web.expose
    @web.require_login( "add a cloud image" )
    #@web.require_admin
    def addNewImage( self, trans, image_id='', manifest='', state=None ):
        error = None
        if image_id:
            if len( image_id ) > 255:
                error = "Image ID name exceeds maximum allowable length."
            elif trans.app.model.CloudUserCredentials.filter(  
                    trans.app.model.CloudImage.table.c.image_id==image_id ).first():
                error = "Image with that ID is already registered."
            else:
                # Create new image
                image = model.CloudImage()
                image.image_id = image_id
                image.manifest = manifest
                # Persist
                session = trans.sa_session
                session.save_or_update( image )
                session.flush()
                # Log and display the management page
                trans.log_event( "New cloud image added: '%s'" % image.image_id )
                trans.set_message( "Cloud image '%s' added." % image.image_id )
                if state:
                    image.state= state
                return self.list( trans )
            
        return trans.show_form(
            web.FormBuilder( web.url_for(), "Add new cloud image", submit_text="Add" )
                .add_text( "image_id", "Machine Image ID (AMI or EMI)", value='', error=error )
                .add_text( "manifest", "Manifest", value='', error=error ) )
            
    @web.expose
    @web.require_login( "use Galaxy cloud" )
    def rename( self, trans, id, new_name=None ):
        stored = get_stored_credentials( trans, id )
        if new_name is not None:
            stored.name = new_name
            trans.sa_session.flush()
            trans.set_message( "Credentials renamed to '%s'." % new_name )
            return self.list( trans )
        else:
            return trans.show_form( 
                web.FormBuilder( url_for( id=trans.security.encode_id(stored.id) ), "Rename credentials", submit_text="Rename" ) 
                .add_text( "new_name", "Credentials Name", value=stored.name ) )
   
    @web.expose
    @web.require_login( "use Galaxy cloud" )
    def renameInstance( self, trans, id, new_name=None ):
        instance = get_uci( trans, id )
        if new_name is not None:
            instance.name = new_name
            trans.sa_session.flush()
            trans.set_message( "Instance renamed to '%s'." % new_name )
            return self.list( trans )
        else:
            return trans.show_form( 
                web.FormBuilder( url_for( id=trans.security.encode_id(instance.id) ), "Rename instance", submit_text="Rename" )
                .add_text( "new_name", "Instance name", value=instance.name ) )
            
    @web.expose
    @web.require_login( "use Galaxy cloud" )
    def set_uci_state( self, trans, id, state='available', clear_error=True ):
        """
        Sets state of UCI to given state, optionally resets error field, and resets UCI's launch time field to 'None'.
        """
        uci = get_uci( trans, id )
        uci.state = state
        if clear_error:
            uci.error = None
        uci.launch_time = None
        trans.sa_session.flush()
        trans.set_message( "Instance '%s' state reset." % uci.name )
        return self.list( trans )
   
    @web.expose
    @web.require_login( "add credentials" )
    def add( self, trans, credName='', accessKey='', secretKey='', providerName='' ):
        """
        Add user's cloud credentials stored under name `credName`.
        """
        user = trans.get_user()
        error = {}
        
        if credName or providerName or accessKey or secretKey:
            if credName=='' or len( credName ) > 255:
                error['cred_error'] = "Credentials name must be between 1 and 255 characters in length."
            elif trans.app.model.CloudUserCredentials.filter_by( user=user ).filter(  
                    trans.app.model.CloudUserCredentials.table.c.name==credName ).first():
                error['cred_error'] = "Credentials with that name already exist."
            elif providerName=='':
                error['provider_error'] = "You must select cloud provider associated with these credentials."
            elif accessKey=='' or len( accessKey ) > 255:
                error['access_key_error'] = "Access key must be between 1 and 255 characters long."
            elif secretKey=='' or len( secretKey ) > 255:
                error['secret_key_error'] = "Secret key must be between 1 and 255 characters long."
            else:
                # Create new user stored credentials
                credentials = model.CloudUserCredentials()
                credentials.name = credName
                credentials.user = user
                credentials.access_key = accessKey
                credentials.secret_key = secretKey
                provider = get_provider( trans, providerName )
                credentials.provider = provider
                # Persist
                session = trans.sa_session
                session.save_or_update( credentials )
                session.flush()
                # Log and display the management page
                trans.log_event( "User added new credentials" )
                trans.set_message( "Credential '%s' created" % credentials.name )
#                if defaultCred:
#                    self.makeDefault( trans, credentials.id)
                return self.list( trans )
        
        providers = trans.sa_session.query( model.CloudProvider ).filter_by( user=user ).all()
        return trans.fill_template( "cloud/add_credentials.mako", 
                                    credName = credName, 
                                    providerName = providerName, 
                                    accessKey = accessKey, 
                                    secretKey = secretKey, 
                                    error = error, 
                                    providers = providers
                                    )
        
#        return trans.show_form( 
#            web.FormBuilder( web.url_for(), "Add credentials", submit_text="Add" )
#                .add_text( "credName", "Credentials name", value="Unnamed credentials", error=cred_error )
#                .add_text( "providerName", "Cloud provider name", value="ec2 or eucalyptus", error=provider_error )
#                .add_text( "accessKey", "Access key", value='', error=accessKey_error ) 
#                .add_password( "secretKey", "Secret key", value='', error=secretKey_error ) )
        
    @web.expose
    @web.require_login( "view credentials" )
    def view( self, trans, id=None ):
        """
        View details for user credentials 
        """        
        # Load credentials from database
        stored = get_stored_credentials( trans, id )
        
        return trans.fill_template( "cloud/view.mako", 
                                   credDetails = stored )

    @web.expose
    @web.require_login( "test cloud credentials" )
    def test_cred( self, trans, id=None ):
        """
        Tests credentials provided by user with selected cloud provider 
        """

    @web.expose
    @web.require_login( "view instance details" )
    def viewInstance( self, trans, id=None ):
        """
        View details about running instance
        """
        uci = get_uci( trans, id )
        instances = get_instances( trans, uci ) # TODO: Handle list (will probably need to be done in mako template)
        
        return trans.fill_template( "cloud/viewInstance.mako",
                                    liveInstance = instances )
        

    @web.expose
    @web.require_login( "delete credentials" )
    def delete( self, trans, id=None ):
        """
        Delete user's cloud credentials
        TODO: Because UCI's depend on specific credentials, need to handle case where given credentials are being used by a UCI 
        """
        # Load credentials from database
        stored = get_stored_credentials( trans, id )
        # Delete and save
        sess = trans.sa_session
        sess.delete( stored )
        stored.flush()
        # Display the management page
        trans.set_message( "Credentials '%s' deleted." % stored.name )
        return self.list( trans )
    
    @web.expose
    @web.require_login( "add provider" )
    def add_provider( self, trans, name='', type='', region_name='', region_endpoint='', is_secure='', host='', port='', proxy='', proxy_port='',
                      proxy_user='', proxy_pass='', debug='', https_connection_factory='', path='' ):
        user = trans.get_user()
        error = {}
        try:
            is_secure = int(is_secure)
        except ValueError:
            pass
        
        # Check if Amazon EC2 has already been registered by this user
        ec2_registered = trans.sa_session.query( model.CloudProvider ).filter_by( user=user, type='ec2' ).first()
        
        if region_name or region_endpoint or name or is_secure or port or proxy or debug or path:
            log.debug (" in if ")
            if trans.app.model.CloudProvider \
                .filter_by (user=user, name=name) \
                .first():
                log.debug (" in if 2 ")
                error['name_error'] = "A provider with that name already exist."
            elif name=='' or len( name ) > 255:
                log.debug (" in if 3")
                error['name_error'] = "Provider name must be between 1 and 255 characters long."
            elif type=='':
                log.debug (" in if 4")
                error['type_error'] = "Provider type must be selected."
            elif ec2_registered:
                log.debug (" in if 5")
                error['type_error'] = "Amazon EC2 has already been registered as a provider."
            elif not (is_secure == 0 or is_secure == 1):
                log.debug (" in if 6")
                error['is_secure_error'] = "Field 'is secure' can only take on a value '0' or '1'"
            else:
                log.debug (" in else ")
                provider = model.CloudProvider()
                provider.user = user
                provider.type = type
                provider.name = name
                if region_name:
                    provider.region_name = region_name
                else:
                    provider.region_name = None
                
                if region_endpoint:
                    provider.region_endpoint = region_endpoint
                else:
                    provider.region_endpoint = None
                
                if is_secure=='0':
                    provider.is_secure = False
                else:
                    provider.is_secure = True
                
                if host:
                    provider.host = host
                else:
                    provider.host = None
                
                if port:
                    provider.port = port
                else:
                    provider.port = None
                
                if proxy:
                    provider.proxy = proxy
                else:
                    provider.proxy = None
                
                if proxy_port:
                    provider.proxy_port = proxy_port
                else:
                    provider.proxy_port = None
                
                if proxy_user:
                    provider.proxy_user = proxy_user
                else:
                    provider.proxy_user = None
                
                if proxy_pass:
                    provider.proxy_pass = proxy_pass
                else:
                    provider.proxy_pass = None
                
                if debug:
                    provider.debug = debug
                else:
                    provider.debug = None
                
                if https_connection_factory:
                    provider.https_connection_factory = https_connection_factory
                else:
                    provider.https_connection_factory = None
                
                provider.path = path
                # Persist
                session = trans.sa_session
                session.save_or_update( provider )
                session.flush()
                # Log and display the management page
                trans.log_event( "User configured new cloud provider: '%s'" % name )
                trans.set_message( "New cloud provider '%s' added." % name )
                return self.list( trans )
        
        return trans.fill_template( "cloud/add_provider.mako", 
                                    name = name,
                                    type = type,
                                    region_name = region_name,
                                    region_endpoint = region_endpoint,
                                    is_secure = is_secure,
                                    host = host, 
                                    port = port, 
                                    proxy = proxy,
                                    proxy_port = proxy_port,
                                    proxy_user = proxy_user,
                                    proxy_pass = proxy_pass, 
                                    debug = debug,
                                    https_connection_factory = https_connection_factory,
                                    path = path,
                                    error = error
                                    )
        
    @web.expose
    @web.require_login( "add Amazon EC2 provider" )
    def add_ec2( self, trans ):
        """ Default provider setup for Amazon's EC2. """
        user = trans.get_user()
        # Check if EC2 has already been registered by this user.
        exists = trans.sa_session.query( model.CloudProvider ) \
            .filter_by( user=user, type='ec2' ).first()
        
        if not exists:
            self.add_provider( trans, name='Amazon EC2', type='ec2', region_name='us-east-1', region_endpoint='us-east-1.ec2.amazonaws.com', is_secure=1, path='/' )
            return self.add( trans )
#            providers = trans.sa_session.query( model.CloudProvider ).filter_by( user=user ).all()
#            return trans.fill_template( "cloud/add_credentials.mako", 
#                                        credName = '', 
#                                        providerName = '', 
#                                        accessKey = '', 
#                                        secretKey = '', 
#                                        error = {}, 
#                                        providers = providers
#                                        )
        
        trans.show_error_message( "EC2 is already registered as a cloud provider under name '%s'." % exists.name )   
        return self.list( trans )
    
    @web.json
    def json_update( self, trans ):
        user = trans.get_user()
        UCIs = trans.sa_session.query( model.UCI ).filter_by( user=user ).filter( model.UCI.c.state != uci_states.DELETED ).all()
        insd = {} # instance name-state dict
        for uci in UCIs:
            dict = {}
            dict['id'] = uci.id
            dict['state'] = uci.state
            if uci.launch_time != None:
                dict['launch_time'] = str(uci.launch_time)
                dict['time_ago'] = str(date.distance_of_time_in_words(uci.launch_time, date.datetime.utcnow() ) )
            else:
                dict['launch_time'] = None
                dict['time_ago'] = None
            insd[uci.name] = dict
        return insd
    
## ---- Utility methods -------------------------------------------------------

def get_provider( trans, name ):
    user = trans.get_user()
    return trans.app.model.CloudProvider \
                .filter_by (user=user, name=name) \
                .first()
        
def get_stored_credentials( trans, id, check_ownership=True ):
    """
    Get StoredUserCredentials from the database by id, verifying ownership. 
    """
    # Check if 'id' is in int (i.e., it was called from this program) or
    #    it was passed from the web (in which case decode it)
    if not isinstance( id, int ):
        id = trans.security.decode_id( id )

    stored = trans.sa_session.query( model.CloudUserCredentials ).get( id )
    if not stored:
        error( "Credentials not found" )
    # Verify ownership
    user = trans.get_user()
    if not user:
        error( "Must be logged in to use the cloud." )
    if check_ownership and not( stored.user == user ):
        error( "Credentials are not owned by current user." )
    # Looks good
    return stored

def get_default_credentials( trans, check_ownership=True ):
    """
    Get a StoredUserCredntials from the database by 'default' setting, verifying ownership. 
    """
    user = trans.get_user()
    # Load credentials from database
    stored = trans.sa_session.query( model.CloudUserCredentials ) \
        .filter_by (user=user, defaultCred=True) \
        .first()

    return stored

def get_uci( trans, id, check_ownership=True ):
    """
    Get a UCI object from the database by id, verifying ownership. 
    """
    # Check if 'id' is in int (i.e., it was called from this program) or
    #    it was passed from the web (in which case decode it)
    if not isinstance( id, int ):
        id = trans.security.decode_id( id )

    live = trans.sa_session.query( model.UCI ).get( id )
    if not live:
        error( "Galaxy instance not found." )
    # Verify ownership
    user = trans.get_user()
    if not user:
        error( "Must be logged in to use the cloud." )
    if check_ownership and not( live.user == user ):
        error( "Instance is not owned by current user." )
    # Looks good
    return live

def get_mi( trans, uci, size='m1.small' ):
    """
    Get appropriate machine image (mi) based on instance size.
    TODO: Dummy method - need to implement logic
        For valid sizes, see http://aws.amazon.com/ec2/instance-types/
    """
    if uci.credentials.provider.type == 'ec2':
        return trans.app.model.CloudImage.filter(
            trans.app.model.CloudImage.table.c.id==2).first()
    else:
        return trans.app.model.CloudImage.filter(
            trans.app.model.CloudImage.table.c.id==1).first()

def get_stores( trans, uci ):
    """
    Get stores objects that are connected to uci object
    """
    user = trans.get_user()
    stores = trans.sa_session.query( model.CloudStore ) \
            .filter_by( user=user, uci_id=uci.id ) \
            .all()
            
    return stores

def get_instances( trans, uci ):
    """
    Get objects of instances that are pending or running and are connected to uci object
    """
    user = trans.get_user()
    instances = trans.sa_session.query( model.CloudInstance ) \
            .filter_by( user=user, uci_id=uci.id ) \
            .filter( or_(model.CloudInstance.table.c.state==instance_states.RUNNING, model.CloudInstance.table.c.state==instance_states.PENDING ) ) \
            .first()
            #.all() #TODO: return all but need to edit calling method(s) to handle list
            
    return instances

def get_cloud_instance( conn, instance_id ):
    """
    Returns a cloud instance representation of the instance id, i.e., cloud instance object that cloud API can be invoked on
    """
    # get_all_instances func. takes a list of desired instance id's, so create a list first
    idLst = list() 
    idLst.append( instance_id )
    # Retrieve cloud instance based on passed instance id. get_all_instances( idLst ) method returns reservation ID. Because
    # we are passing only 1 ID, we can retrieve only the first element of the returning list. Furthermore, because (for now!)
    # only 1 instance corresponds each individual reservation, grab only the first element of the returned list of instances.
    cloudInstance = conn.get_all_instances( [instance_id] )[0].instances[0]
    return cloudInstance

def get_connection( trans, credName ):
    """
    Establishes EC2 connection using user's default credentials
    """
    log.debug( '##### Establishing cloud connection.' )
    user = trans.get_user()
    creds = trans.sa_session.query( model.CloudUserCredentials ).filter_by( user=user, name=credName ).first()
    if creds:
        a_key = creds.access_key
        s_key = creds.secret_key
        # Amazon EC2
        #conn = EC2Connection( a_key, s_key )
        # Eucalyptus Public Cloud
        euca_region = RegionInfo( None, "eucalyptus", "mayhem9.cs.ucsb.edu" )
        conn = EC2Connection( aws_access_key_id=a_key, aws_secret_access_key=s_key, is_secure=False, port=8773, region=euca_region, path="/services/Eucalyptus" )
        return conn
    else:
        error( "You must specify default credentials before starting an instance." )
        return 0

def get_keypair_name( trans ):
    """
    Generate keypair using user's default credentials
    """
    conn = get_connection( trans )
    
    log.debug( "Getting user's keypair" )
    key_pair = conn.get_key_pair( 'galaxy-keypair' )
    
    try:
        return key_pair.name
    except AttributeError: # No keypair under this name exists so create it
        log.debug( 'No keypair found, creating keypair' )
        key_pair = conn.create_key_pair( 'galaxy-keypair' )
        # TODO: Store key_pair.material into instance table - this is the only time private key can be retrieved
        #    Actually, probably return key_pair to calling method and store name & key from there...
        
    return key_pair.name

def update_instance_state( trans, id ):
    """
    Update state of instances associated with given UCI id and store state in local database. Also update
    state of the given UCI.  
    """
    uci = get_uci( trans, id )
    # Get list of instances associated with given uci as they are stored in local database
    dbInstances = get_instances( trans, uci ) # TODO: handle list (currently only 1 instance can correspond to 1 UCI)
    oldState = dbInstances.state
    # Establish connection with cloud
    conn = get_connection( trans )
    # Get actual cloud instance object
    cloudInstance = get_cloud_instance( conn, dbInstances.instance_id )
    # Update instance status
    cloudInstance.update()
    dbInstances.state = cloudInstance.state
    log.debug( "Updating instance %s state; current state: %s" % ( str( cloudInstance ).split(":")[1], cloudInstance.state ) )
    # Update state of UCI (TODO: once more than 1 instance is assoc. w/ 1 UCI, this will be need to be updated differently) 
    uci.state = dbInstances.state
    # Persist
    session = trans.sa_session
    session.save_or_update( dbInstances )
    session.save_or_update( uci )
    session.flush()
    
    # If instance is now running, update/process instance (i.e., mount file system, start Galaxy, update DB with DNS)
    if oldState==instance_states.PENDING and dbInstances.state==instance_states.RUNNING:
        update_instance( trans, dbInstances, cloudInstance, conn, uci )
    
    
def update_instance( trans, dbInstance, cloudInstance, conn, uci ):
    """
    Update instance: connect EBS volume, mount file system, start Galaxy, and update local DB w/ DNS info
    
    Keyword arguments:
    trans -- current transaction
    dbInstance -- object of 'instance' as it is stored in local database
    cloudInstance -- object of 'instance' as it resides in the cloud. Functions supported by the cloud API can be
        instantiated directly on this object.
    conn -- cloud connection object
    uci -- UCI object 
    """
    dbInstance.public_dns = cloudInstance.dns_name
    dbInstance.private_dns = cloudInstance.private_dns_name

    # Attach storage volume(s) to instance
    stores = get_stores( trans, uci )
    for i, store in enumerate( stores ):
        log.debug( "Attaching volume '%s' to instance '%s'." % ( store.volume_id, dbInstance.instance_id ) )
        mntDevice = '/dev/sdb'+str(i)
        volStat = conn.attach_volume( store.volume_id, dbInstance.instance_id, mntDevice )
        store.attach_time = datetime.utcnow()
        store.device = mntDevice
        store.i_id = dbInstance.instance_id
        store.status = volStat
        log.debug ( '***** volume status: %s' % volStat )
    
    # Wait until instances have attached and add file system
    
    
    
    # TODO: mount storage through ZFS
    # TODO: start Galaxy 
    
    # Persist
    session = trans.sa_session
    session.save_or_update( dbInstance )
    session.flush()

def attach_ordered_steps( workflow, steps ):
    ordered_steps = order_workflow_steps( steps )
    if ordered_steps:
        workflow.has_cycles = False
        for i, step in enumerate( ordered_steps ):
            step.order_index = i
            workflow.steps.append( step )
    else:
        workflow.has_cycles = True
        workflow.steps = steps

def edgelist_for_workflow_steps( steps ):
    """
    Create a list of tuples representing edges between `WorkflowSteps` based
    on associated `WorkflowStepConnection`s
    """
    edges = []
    steps_to_index = dict( ( step, i ) for i, step in enumerate( steps ) )
    for step in steps:
        edges.append( ( steps_to_index[step], steps_to_index[step] ) )
        for conn in step.input_connections:
            edges.append( ( steps_to_index[conn.output_step], steps_to_index[conn.input_step] ) )
    return edges

def order_workflow_steps( steps ):
    """
    Perform topological sort of the steps, return ordered or None
    """
    try:
        edges = edgelist_for_workflow_steps( steps )
        node_order = topsort( edges )
        return [ steps[i] for i in node_order ]
    except CycleError:
        return None
    
def order_workflow_steps_with_levels( steps ):
    try:
        return topsort_levels( edgelist_for_workflow_steps( steps ) )
    except CycleError:
        return None
    
class FakeJob( object ):
    """
    Fake job object for datasets that have no creating_job_associations,
    they will be treated as "input" datasets.
    """
    def __init__( self, dataset ):
        self.is_fake = True
        self.id = "fake_%s" % dataset.id
    
def get_job_dict( trans ):
    """
    Return a dictionary of Job -> [ Dataset ] mappings, for all finished
    active Datasets in the current history and the jobs that created them.
    """
    history = trans.get_history()
    # Get the jobs that created the datasets
    warnings = set()
    jobs = odict()
    for dataset in history.active_datasets:
        # FIXME: Create "Dataset.is_finished"
        if dataset.state in ( 'new', 'running', 'queued' ):
            warnings.add( "Some datasets still queued or running were ignored" )
            continue
        
        #if this hda was copied from another, we need to find the job that created the origial hda
        job_hda = dataset
        while job_hda.copied_from_history_dataset_association:
            job_hda = job_hda.copied_from_history_dataset_association
        
        if not job_hda.creating_job_associations:
            jobs[ FakeJob( dataset ) ] = [ ( None, dataset ) ]
        
        for assoc in job_hda.creating_job_associations:
            job = assoc.job
            if job in jobs:
                jobs[ job ].append( ( assoc.name, dataset ) )
            else:
                jobs[ job ] = [ ( assoc.name, dataset ) ]
    return jobs, warnings    

def cleanup_param_values( inputs, values ):
    """
    Remove 'Data' values from `param_values`, along with metadata cruft,
    but track the associations.
    """
    associations = []
    names_to_clean = []
    # dbkey is pushed in by the framework
    if 'dbkey' in values:
        del values['dbkey']
    root_values = values
    # Recursively clean data inputs and dynamic selects
    def cleanup( prefix, inputs, values ):
        for key, input in inputs.items():
            if isinstance( input, ( SelectToolParameter, DrillDownSelectToolParameter ) ):
                if input.is_dynamic:
                    values[key] = UnvalidatedValue( values[key] )
            if isinstance( input, DataToolParameter ):
                tmp = values[key]
                values[key] = None
                # HACK: Nested associations are not yet working, but we
                #       still need to clean them up so we can serialize
                # if not( prefix ):
                if tmp: #this is false for a non-set optional dataset
                    associations.append( ( tmp.hid, prefix + key ) )
                # Cleanup the other deprecated crap associated with datasets
                # as well. Worse, for nested datasets all the metadata is
                # being pushed into the root. FIXME: MUST REMOVE SOON
                key = prefix + key + "_"
                for k in root_values.keys():
                    if k.startswith( key ):
                        del root_values[k]            
            elif isinstance( input, Repeat ):
                group_values = values[key]
                for i, rep_values in enumerate( group_values ):
                    rep_index = rep_values['__index__']
                    prefix = "%s_%d|" % ( key, rep_index )
                    cleanup( prefix, input.inputs, group_values[i] )
            elif isinstance( input, Conditional ):
                group_values = values[input.name]
                current_case = group_values['__current_case__']
                prefix = "%s|" % ( key )
                cleanup( prefix, input.cases[current_case].inputs, group_values )
    cleanup( "", inputs, values )
    return associations





