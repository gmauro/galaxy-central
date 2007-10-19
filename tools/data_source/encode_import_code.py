import os, sys

from galaxy import datatypes, config, jobs 
from shutil import copyfile

#post processing, set build for data and add additional data to history
def exec_after_process(app, inp_data, out_data, param_dict, tool, stdout, stderr):
    history = out_data.items()[0][1].history
    if history == None:
        print "unknown history!"
        return
    new_stdout = ""
    split_stdout = stdout.split("\n")
    basic_name = ""
    for line in split_stdout:
        fields = line.split("\t")
        if fields[0] == "#File1":
            description = fields[1]
            dbkey = fields[2]
            file_type = fields[3]
            name, data = out_data.items()[0]
            basic_name = data.name
            data.name = data.name + " (" + description + ")"
            data.dbkey = dbkey
            data.info = data.name
            data = app.datatypes_registry.change_datatype( data, file_type )
            data.init_meta()
            data.set_peek()
            app.model.flush()
        elif fields[0] == "#NewFile":
            description = fields[1]
            dbkey = fields[2]
            filepath = fields[3]
            file_type = fields[4]
            newdata = app.model.Dataset()
            newdata.extension = file_type
            newdata.name = basic_name + " (" + description + ")"
            newdata.flush()
            history.add_dataset( newdata )
            newdata.flush()
            app.model.flush()
            try:
                copyfile(filepath,newdata.file_name)
                newdata.info = newdata.name
                newdata.state = jobs.JOB_OK
            except:
                newdata.info = "The requested file is missing from the system."
                newdata.state = jobs.JOB_ERROR
            newdata.dbkey = dbkey
            newdata.init_meta()
            newdata.set_peek()
            #
            app.model.flush()
