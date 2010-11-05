import os, os.path

class BaseJobRunner( object ):

    def build_command_line( self, job_wrapper, include_metadata=False ):
        """
        Compose the sequence of commands neccesary to execute a job. This will
        currently include:
            - environment settings corresponding to any requirement tags
            - command line taken from job wrapper
            - commands to set metadata (if include_metadata is True)
        """
        commands = job_wrapper.get_command_line()
        # All job runners currently handle this case which should never
        # occur
        if not commands:
            return None
        # Prepend dependency injection
        if job_wrapper.dependency_shell_commands:
            commands = "; ".join( job_wrapper.dependency_shell_commands + [ commands ] ) 
        # Append metadata setting commands, we don't want to overwrite metadata
        # that was copied over in init_meta(), as per established behavior
        if include_metadata and self.app.config.set_metadata_externally:
            commands += "; cd %s; " % os.path.abspath( os.getcwd() )
            commands += job_wrapper.setup_external_metadata( 
                            exec_dir = os.path.abspath( os.getcwd() ),
                            tmp_dir = self.app.config.new_file_path,
                            dataset_files_path = self.app.model.Dataset.file_path,
                            output_fnames = job_wrapper.get_output_fnames(),
                            set_extension = False,
                            kwds = { 'overwrite' : False } ) 
        return commands
