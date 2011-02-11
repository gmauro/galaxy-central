import logging
import subprocess
from Queue import Queue
import threading

from galaxy import model

import os, errno
from time import sleep

from galaxy.jobs import TaskWrapper

log = logging.getLogger( __name__ )

__all__ = [ 'TaskedJobRunner' ]

class TaskedJobRunner( object ):
    """
    Job runner backed by a finite pool of worker threads. FIFO scheduling
    """
    STOP_SIGNAL = object()
    def __init__( self, app ):
        """Start the job runner with 'nworkers' worker threads"""
        self.app = app
        self.sa_session = app.model.context
        # start workers
        self.queue = Queue()
        self.threads = []
        nworkers = app.config.local_task_queue_workers
        log.info( "Starting tasked-job runners" )
        for i in range( nworkers  ):
            worker = threading.Thread( target=self.run_next )
            worker.start()
            self.threads.append( worker )
        log.debug( "%d workers ready", nworkers )

    def run_next( self ):
        """Run the next job, waiting until one is available if neccesary"""
        while 1:
            job_wrapper = self.queue.get()
            if job_wrapper is self.STOP_SIGNAL:
                return
            try:
                self.run_job( job_wrapper )
            except:
                log.exception( "Uncaught exception running tasked job" )

    def run_job( self, job_wrapper ):
        job_wrapper.set_runner( 'tasks:///', None )
        stderr = stdout = command_line = ''
        # Prepare the job to run
        try:
            job_wrapper.prepare()
            command_line = job_wrapper.get_command_line()
        except:
            job_wrapper.fail( "failure preparing job", exception=True )
            log.exception("failure running job %d" % job_wrapper.job_id)
            return
        # If we were able to get a command line, run the job.  ( must be passed to tasks )
        if command_line:
            try:
                # DBTODO read tool info and use the right kind of parallelism.  
                # For now, the only splitter is the 'basic' one, n-ways split on one input, one output.
                # This is incredibly simplified.  Parallelism ultimately needs to describe which inputs, how, etc.
                job_wrapper.change_state( model.Job.states.RUNNING )
                self.sa_session.flush()
                parent_job = job_wrapper.get_job()
                # Split with the tool-defined method.
                if job_wrapper.tool.parallelism == "basic":
                    from galaxy.jobs.splitters import basic
                    if len(job_wrapper.get_input_fnames()) > 1 or len(job_wrapper.get_output_fnames()) > 1:
                        log.error("The basic splitter is not capable of handling jobs with multiple inputs or outputs.")
                        job_wrapper.change_state( model.Job.states.ERROR )
                        job_wrapper.fail("Job Splitting Failed, the basic splitter only handles tools with one input and one output")
                        # Requeue as a standard job?
                        return
                    input_file = job_wrapper.get_input_fnames()[0]
                    working_directory = job_wrapper.working_directory
                    # DBTODO execute an external task to do the splitting, this should happen at refactor.
                    # Regarding number of ways split, use "hints" in tool config?
                    # If the number of tasks is sufficiently high, we can use it to calculate job completion % and give a running status.
                    basic.split(input_file, working_directory, 
                                        20, #Needs serious experimentation to find out what makes the most sense.
                                        parent_job.input_datasets[0].dataset.ext)
                    # Tasks in this parts list are in alphabetical listdir order (15 before 5), but that should not matter.
                    parts = [os.path.join(os.path.abspath(job_wrapper.working_directory), p, os.path.basename(input_file)) 
                                for p in os.listdir(job_wrapper.working_directory) 
                                if p.startswith('task_')]
                else:
                    job_wrapper.change_state( model.Job.states.ERROR )
                    job_wrapper.fail("Job Splitting Failed, no match for '%s'" % job_wrapper.tool.parallelism)
                # Assemble parts into task_wrappers

                # Not an option for now.  Task objects don't *do* anything useful yet, but we'll want them tracked outside this thread to do anything.
                # if track_tasks_in_database:
                tasks = []
                task_wrappers = []
                for part in parts:
                    task = model.Task(parent_job, part)
                    self.sa_session.add(task)
                    tasks.append(task)
                self.sa_session.flush()
                # Must flush prior to the creation and queueing of task wrappers.
                for task in tasks:
                    tw = TaskWrapper(task, job_wrapper.queue)
                    task_wrappers.append(tw)
                    self.app.job_manager.dispatcher.put(tw)
                tasks_incomplete = False
                sleep_time = 1
                while tasks_incomplete is False:
                    tasks_incomplete = True
                    for tw in task_wrappers:
                        if not tw.get_state() == model.Task.states.OK:
                            tasks_incomplete = False
                    sleep( sleep_time )
                    if sleep_time < 8:
                        sleep_time *= 2
                output_filename = job_wrapper.get_output_fnames()[0].real_path
                basic.merge(working_directory, output_filename)
                log.debug('execution finished: %s' % command_line)
                for tw in task_wrappers:
                    # Prevent repetitive output, e.g. "Sequence File Aligned"x20
                    # Eventually do a reduce for jobs that output "N reads mapped", combining all N for tasks.
                    if stdout.strip() != tw.get_task().stdout.strip():
                        stdout += tw.get_task().stdout
                    if stderr.strip() != tw.get_task().stderr.strip():                        
                        stderr += tw.get_task().stderr
            except Exception:
                job_wrapper.fail( "failure running job", exception=True )
                log.exception("failure running job %d" % job_wrapper.job_id)
                return

        #run the metadata setting script here
        #this is terminate-able when output dataset/job is deleted
        #so that long running set_meta()s can be canceled without having to reboot the server
        if job_wrapper.get_state() not in [ model.Job.states.ERROR, model.Job.states.DELETED ] and self.app.config.set_metadata_externally and job_wrapper.output_paths:
            external_metadata_script = job_wrapper.setup_external_metadata( output_fnames = job_wrapper.get_output_fnames(),
                                                                            set_extension = True,
                                                                            kwds = { 'overwrite' : False } ) #we don't want to overwrite metadata that was copied over in init_meta(), as per established behavior
            log.debug( 'executing external set_meta script for job %d: %s' % ( job_wrapper.job_id, external_metadata_script ) )
            external_metadata_proc = subprocess.Popen( args = external_metadata_script, 
                                         shell = True, 
                                         env = os.environ,
                                         preexec_fn = os.setpgrp )
            job_wrapper.external_output_metadata.set_job_runner_external_pid( external_metadata_proc.pid, self.sa_session )
            external_metadata_proc.wait()
            log.debug( 'execution of external set_meta finished for job %d' % job_wrapper.job_id )
        
        # Finish the job                
        try:
            job_wrapper.finish( stdout, stderr )
        except:
            log.exception("Job wrapper finish method failed")
            job_wrapper.fail("Unable to finish job", exception=True)

    def put( self, job_wrapper ):
        """Add a job to the queue (by job identifier)"""
        # Change to queued state before handing to worker thread so the runner won't pick it up again
        job_wrapper.change_state( model.Job.states.QUEUED )
        self.queue.put( job_wrapper )
    
    def shutdown( self ):
        """Attempts to gracefully shut down the worker threads"""
        log.info( "sending stop signal to worker threads" )
        for i in range( len( self.threads ) ):
            self.queue.put( self.STOP_SIGNAL )
        log.info( "local job runner stopped" )

    def check_pid( self, pid ):
        # DBTODO Need to check all subtask pids and return some sort of cumulative result.
        return True
        try:
            os.kill( pid, 0 )
            return True
        except OSError, e:
            if e.errno == errno.ESRCH:
                log.debug( "check_pid(): PID %d is dead" % pid )
            else:
                log.warning( "check_pid(): Got errno %s when attempting to check PID %d: %s" %( errno.errorcode[e.errno], pid, e.strerror ) )
            return False

    def stop_job( self, job ):
        # DBTODO Call stop on all of the tasks.
        #if our local job has JobExternalOutputMetadata associated, then our primary job has to have already finished
        if job.external_output_metadata:
            pid = job.external_output_metadata[0].job_runner_external_pid #every JobExternalOutputMetadata has a pid set, we just need to take from one of them
        else:
            pid = job.job_runner_external_id
        if pid in [ None, '' ]:
            log.warning( "stop_job(): %s: no PID in database for job, unable to stop" % job.id )
            return
        pid = int( pid )
        if not self.check_pid( pid ):
            log.warning( "stop_job(): %s: PID %d was already dead or can't be signaled" % ( job.id, pid ) )
            return
        for sig in [ 15, 9 ]:
            try:
                os.killpg( pid, sig )
            except OSError, e:
                log.warning( "stop_job(): %s: Got errno %s when attempting to signal %d to PID %d: %s" % ( job.id, errno.errorcode[e.errno], sig, pid, e.strerror ) )
                return  # give up
            sleep( 2 )
            if not self.check_pid( pid ):
                log.debug( "stop_job(): %s: PID %d successfully killed with signal %d" %( job.id, pid, sig ) )
                return
        else:
            log.warning( "stop_job(): %s: PID %d refuses to die after signaling TERM/KILL" %( job.id, pid ) )

    def recover( self, job, job_wrapper ):
        # DBTODO Task Recovery, this should be possible.
        job_wrapper.change_state( model.Job.states.ERROR, info = "This job was killed when Galaxy was restarted.  Please retry the job." )

