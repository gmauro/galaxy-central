import os, logging, threading, time
from Queue import Queue, Empty

from galaxy import model
from paste.deploy.converters import asbool

import pkg_resources

try:
    pkg_resources.require( "drmaa" )
    drmaa = __import__( "drmaa" )
except Exception, e:
    drmaa = str( e )

log = logging.getLogger( __name__ )

if type( drmaa ) != str:
    drmaa_state = {
        drmaa.JobState.UNDETERMINED: 'process status cannot be determined',
        drmaa.JobState.QUEUED_ACTIVE: 'job is queued and active',
        drmaa.JobState.SYSTEM_ON_HOLD: 'job is queued and in system hold',
        drmaa.JobState.USER_ON_HOLD: 'job is queued and in user hold',
        drmaa.JobState.USER_SYSTEM_ON_HOLD: 'job is queued and in user and system hold',
        drmaa.JobState.RUNNING: 'job is running',
        drmaa.JobState.SYSTEM_SUSPENDED: 'job is system suspended',
        drmaa.JobState.USER_SUSPENDED: 'job is user suspended',
        drmaa.JobState.DONE: 'job finished normally',
        drmaa.JobState.FAILED: 'job finished, but failed',
    }

drm_template = """#!/bin/sh
#$ -S /bin/sh
GALAXY_LIB="%s"
if [ "$GALAXY_LIB" != "None" ]; then
    if [ -n "$PYTHONPATH" ]; then
        PYTHONPATH="$GALAXY_LIB:$PYTHONPATH"
    else
        PYTHONPATH="$GALAXY_LIB"
    fi
    export PYTHONPATH
fi
cd %s
%s
"""

class DRMAAJobState( object ):
    def __init__( self ):
        """
        Encapsulates state related to a job that is being run via the DRM and 
        that we need to monitor.
        """
        self.job_wrapper = None
        self.job_id = None
        self.old_state = None
        self.running = False
        self.job_file = None
        self.ofile = None
        self.efile = None
        self.runner_url = None

class DRMAAJobRunner( object ):
    """
    Job runner backed by a finite pool of worker threads. FIFO scheduling
    """
    STOP_SIGNAL = object()
    def __init__( self, app ):
        """Initialize this job runner and start the monitor thread"""
        # Check if drmaa was importable, fail if not
        if type( drmaa ) == str:
            raise Exception( "DRMAAJobRunner requires drmaa module which could not be loaded: %s" % drmaa )
        self.app = app
        self.sa_session = app.model.context
        # 'watched' and 'queue' are both used to keep track of jobs to watch.
        # 'queue' is used to add new watched jobs, and can be called from
        # any thread (usually by the 'queue_job' method). 'watched' must only
        # be modified by the monitor thread, which will move items from 'queue'
        # to 'watched' and then manage the watched jobs.
        self.watched = []
        self.monitor_queue = Queue()
        self.ds = drmaa.Session()
        self.ds.initialize()
        self.monitor_thread = threading.Thread( target=self.monitor )
        self.monitor_thread.start()
        self.work_queue = Queue()
        self.work_threads = []
        nworkers = app.config.cluster_job_queue_workers
        for i in range( nworkers ):
            worker = threading.Thread( target=self.run_next )
            worker.start()
            self.work_threads.append( worker )
        log.debug( "%d workers ready" % nworkers )

    def get_native_spec( self, url ):
        """Get any native DRM arguments specified by the site configuration"""
        try:
            return url.split('/')[2] or None
        except:
            return None

    def run_next( self ):
        """
        Run the next item in the queue (a job waiting to run or finish )
        """
        while 1:
            ( op, obj ) = self.work_queue.get()
            if op is self.STOP_SIGNAL:
                return
            try:
                if op == 'queue':
                    self.queue_job( obj )
                elif op == 'finish':
                    self.finish_job( obj )
                elif op == 'fail':
                    self.fail_job( obj )
            except:
                log.exception( "Uncaught exception %sing job" % op )

    def queue_job( self, job_wrapper ):
        """Create job script and submit it to the DRM"""

        try:
            job_wrapper.prepare()
            command_line = job_wrapper.get_command_line()
        except:
            job_wrapper.fail( "failure preparing job", exception=True )
            log.exception("failure running job %d" % job_wrapper.job_id)
            return

        runner_url = job_wrapper.tool.job_runner
        
        # This is silly, why would we queue a job with no command line?
        if not command_line:
            job_wrapper.finish( '', '' )
            return
        
        # Check for deletion before we change state
        if job_wrapper.get_state() == model.Job.states.DELETED:
            log.debug( "Job %s deleted by user before it entered the queue" % job_wrapper.job_id )
            job_wrapper.cleanup()
            return

        # Change to queued state immediately
        job_wrapper.change_state( model.Job.states.QUEUED )

        # define job attributes
        ofile = "%s/database/pbs/%s.o" % (os.getcwd(), job_wrapper.job_id)
        efile = "%s/database/pbs/%s.e" % (os.getcwd(), job_wrapper.job_id)
        jt = self.ds.createJobTemplate()
        jt.remoteCommand = "%s/database/pbs/galaxy_%s.sh" % (os.getcwd(), job_wrapper.job_id)
        jt.outputPath = ":%s" % ofile
        jt.errorPath = ":%s" % efile
        native_spec = self.get_native_spec( runner_url )
        if native_spec is not None:
            jt.nativeSpecification = native_spec

        script = drm_template % (job_wrapper.galaxy_lib_dir, os.path.abspath( job_wrapper.working_directory ), command_line)
        if self.app.config.set_metadata_externally:
            script += "cd %s\n" % os.path.abspath( os.getcwd() )
            script += "%s\n" % job_wrapper.setup_external_metadata( exec_dir = os.path.abspath( os.getcwd() ),
                                                                    tmp_dir = self.app.config.new_file_path,
                                                                    dataset_files_path = self.app.model.Dataset.file_path,
                                                                    output_fnames = job_wrapper.get_output_fnames(),
                                                                    set_extension = False,
                                                                    kwds = { 'overwrite' : False } ) #we don't want to overwrite metadata that was copied over in init_meta(), as per established behavior
        fh = file( jt.remoteCommand, "w" )
        fh.write( script )
        fh.close()
        os.chmod( jt.remoteCommand, 0750 )

        # job was deleted while we were preparing it
        if job_wrapper.get_state() == model.Job.states.DELETED:
            log.debug( "Job %s deleted by user before it entered the queue" % job_wrapper.job_id )
            self.cleanup( ( ofile, efile, jt.remoteCommand ) )
            job_wrapper.cleanup()
            return

        galaxy_job_id = job_wrapper.job_id
        log.debug("(%s) submitting file %s" % ( galaxy_job_id, jt.remoteCommand ) )
        log.debug("(%s) command is: %s" % ( galaxy_job_id, command_line ) )
        # runJob will raise if there's a submit problem
        job_id = self.ds.runJob(jt)
        log.info("(%s) queued as %s" % ( galaxy_job_id, job_id ) )

        # store runner information for tracking if Galaxy restarts
        job_wrapper.set_runner( runner_url, job_id )

        # Store DRM related state information for job
        drm_job_state = DRMAAJobState()
        drm_job_state.job_wrapper = job_wrapper
        drm_job_state.job_id = job_id
        drm_job_state.ofile = ofile
        drm_job_state.efile = efile
        drm_job_state.job_file = jt.remoteCommand
        drm_job_state.old_state = 'new'
        drm_job_state.running = False
        drm_job_state.runner_url = runner_url
        
        # delete the job template
        self.ds.deleteJobTemplate( jt )

        # Add to our 'queue' of jobs to monitor
        self.monitor_queue.put( drm_job_state )

    def monitor( self ):
        """
        Watches jobs currently in the PBS queue and deals with state changes
        (queued to running) and job completion
        """
        while 1:
            # Take any new watched jobs and put them on the monitor list
            try:
                while 1: 
                    drm_job_state = self.monitor_queue.get_nowait()
                    if drm_job_state is self.STOP_SIGNAL:
                        # TODO: This is where any cleanup would occur
                        self.ds.exit()
                        return
                    self.watched.append( drm_job_state )
            except Empty:
                pass
            # Iterate over the list of watched jobs and check state
            self.check_watched_items()
            # Sleep a bit before the next state check
            time.sleep( 1 )
            
    def check_watched_items( self ):
        """
        Called by the monitor thread to look at each watched job and deal
        with state changes.
        """
        new_watched = []
        for drm_job_state in self.watched:
            job_id = drm_job_state.job_id
            galaxy_job_id = drm_job_state.job_wrapper.job_id
            old_state = drm_job_state.old_state
            try:
                state = self.ds.jobStatus( job_id )
            except drmaa.InvalidJobException:
                # we should only get here if an orphaned job was put into the queue at app startup
                log.debug("(%s/%s) job left DRM queue" % ( galaxy_job_id, job_id ) )
                self.work_queue.put( ( 'finish', drm_job_state ) )
                continue
            except Exception, e:
                # so we don't kill the monitor thread
                log.exception("(%s/%s) Unable to check job status" % ( galaxy_job_id, job_id ) )
                log.warning("(%s/%s) job will now be errored" % ( galaxy_job_id, job_id ) )
                drm_job_state.fail_message = "Cluster could not complete job"
                self.work_queue.put( ( 'fail', drm_job_state ) )
                continue
            if state != old_state:
                log.debug("(%s/%s) state change: %s" % ( galaxy_job_id, job_id, drmaa_state[state] ) )
            if state == drmaa.JobState.RUNNING and not drm_job_state.running:
                drm_job_state.running = True
                drm_job_state.job_wrapper.change_state( model.Job.states.RUNNING )
            if state in ( drmaa.JobState.DONE, drmaa.JobState.FAILED ):
                self.work_queue.put( ( 'finish', drm_job_state ) )
                continue
            drm_job_state.old_state = state
            new_watched.append( drm_job_state )
        # Replace the watch list with the updated version
        self.watched = new_watched
        
    def finish_job( self, drm_job_state ):
        """
        Get the output/error for a finished job, pass to `job_wrapper.finish`
        and cleanup all the DRM temporary files.
        """
        ofile = drm_job_state.ofile
        efile = drm_job_state.efile
        job_file = drm_job_state.job_file
        # collect the output
        try:
            ofh = file(ofile, "r")
            efh = file(efile, "r")
            stdout = ofh.read()
            stderr = efh.read()
        except:
            stdout = ''
            stderr = 'Job output not returned from cluster'
            log.debug(stderr)

        try:
            drm_job_state.job_wrapper.finish( stdout, stderr )
        except:
            log.exception("Job wrapper finish method failed")

        # clean up the drm files
        self.cleanup( ( ofile, efile, job_file ) )

    def fail_job( self, drm_job_state ):
        """
        Seperated out so we can use the worker threads for it.
        """
        self.stop_job( self.sa_session.query( self.app.model.Job ).get( drm_job_state.job_wrapper.job_id ) )
        drm_job_state.job_wrapper.fail( drm_job_state.fail_message )
        self.cleanup( ( drm_job_state.ofile, drm_job_state.efile, drm_job_state.job_file ) )

    def cleanup( self, files ):
        if not asbool( self.app.config.get( 'debug', False ) ):
            for file in files:
                if os.access( file, os.R_OK ):
                    os.unlink( file )

    def put( self, job_wrapper ):
        """Add a job to the queue (by job identifier)"""
        # Change to queued state before handing to worker thread so the runner won't pick it up again
        job_wrapper.change_state( model.Job.states.QUEUED )
        self.work_queue.put( ( 'queue', job_wrapper ) )

    def shutdown( self ):
        """Attempts to gracefully shut down the monitor thread"""
        log.info( "sending stop signal to worker threads" )
        self.monitor_queue.put( self.STOP_SIGNAL )
        for i in range( len( self.work_threads ) ):
            self.work_queue.put( ( self.STOP_SIGNAL, None ) )
        log.info( "drmaa job runner stopped" )

    def stop_job( self, job ):
        """Attempts to delete a job from the DRM queue"""
        try:
            self.ds.control( job.job_runner_external_id, drmaa.JobControlAction.TERMINATE )
            log.debug( "(%s/%s) Removed from DRM queue at user's request" % ( job.id, job.job_runner_external_id ) )
        except drmaa.InvalidJobException:
            log.debug( "(%s/%s) User killed running job, but it was already dead" % ( job.id, job.job_runner_external_id ) )
        except Exception, e:
            log.debug( "(%s/%s) User killed running job, but error encountered removing from DRM queue: %s" % ( job.id, job.job_runner_external_id, e ) )

    def recover( self, job, job_wrapper ):
        """Recovers jobs stuck in the queued/running state when Galaxy started"""
        drm_job_state = DRMAAJobState()
        drm_job_state.ofile = "%s/database/pbs/%s.o" % (os.getcwd(), job.id)
        drm_job_state.efile = "%s/database/pbs/%s.e" % (os.getcwd(), job.id)
        drm_job_state.job_file = "%s/database/pbs/galaxy_%s.sh" % (os.getcwd(), job.id)
        drm_job_state.job_id = str( job.job_runner_external_id )
        drm_job_state.runner_url = job_wrapper.tool.job_runner
        job_wrapper.command_line = job.command_line
        drm_job_state.job_wrapper = job_wrapper
        if job.state == model.Job.states.RUNNING:
            log.debug( "(%s/%s) is still in running state, adding to the DRM queue" % ( job.id, job.job_runner_external_id ) )
            drm_job_state.old_state = drmaa.JobState.RUNNING
            drm_job_state.running = True
            self.monitor_queue.put( drm_job_state )
        elif job.state == model.Job.states.QUEUED:
            log.debug( "(%s/%s) is still in DRM queued state, adding to the DRM queue" % ( job.id, job.job_runner_external_id ) )
            drm_job_state.old_state = drmaa.JobState.QUEUED_ACTIVE
            drm_job_state.running = False
            self.monitor_queue.put( drm_job_state )
