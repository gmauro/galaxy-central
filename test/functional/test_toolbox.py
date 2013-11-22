import sys
import new
import os
from galaxy.tools.parameters import grouping
from galaxy.util import string_as_bool
from base.twilltestcase import TwillTestCase
import galaxy.model
from galaxy.model.orm import and_, desc
from galaxy.model.mapping import context as sa_session
from simplejson import dumps
import requests

toolbox = None


class ToolTestCase( TwillTestCase ):
    """Abstract test case that runs tests based on a `galaxy.tools.test.ToolTest`"""

    def do_it( self, testdef ):
        """
        Run through a tool test case.
        """
        shed_tool_id = self.shed_tool_id

        self.__handle_test_def_errors( testdef )

        galaxy_interactor = self.__galaxy_interactor( testdef )

        test_history = galaxy_interactor.new_history()

        # Upload any needed files
        upload_waits = []
        for test_data in testdef.test_data():
            upload_waits.append( galaxy_interactor.stage_data_async( test_data, test_history, shed_tool_id ) )
        for upload_wait in upload_waits:
            upload_wait()

        data_list = galaxy_interactor.run_tool( testdef, test_history )
        self.assertTrue( data_list )

        self.__verify_outputs( testdef, test_history, shed_tool_id, data_list, galaxy_interactor )

        galaxy_interactor.delete_history( test_history )

    def __galaxy_interactor( self, testdef ):
        interactor_key = testdef.interactor
        interactor_class = GALAXY_INTERACTORS[ interactor_key ]
        return interactor_class( self )

    def __handle_test_def_errors(self, testdef):
        # If the test generation had an error, raise
        if testdef.error:
            if testdef.exception:
                raise testdef.exception
            else:
                raise Exception( "Test parse failure" )

    def __verify_outputs( self, testdef, history, shed_tool_id, data_list, galaxy_interactor ):
        maxseconds = testdef.maxseconds

        output_index = 0 - len( testdef.outputs )
        for output_tuple in testdef.outputs:
            # Get the correct hid
            output_data = data_list[ output_index ]
            self.assertTrue( output_data is not None )
            name, outfile, attributes = output_tuple
            galaxy_interactor.verify_output( history, output_data, outfile, attributes=attributes, shed_tool_id=shed_tool_id, maxseconds=maxseconds )
            output_index += 1


class GalaxyInteractorApi( object ):

    def __init__( self, twill_test_case ):
        self.twill_test_case = twill_test_case
        self.api_url = "%s/api" % twill_test_case.url.rstrip("/")
        self.api_key = self.__get_user_key( twill_test_case.user_api_key, twill_test_case.master_api_key )
        self.uploads = {}

    def verify_output( self, history_id, output_data, outfile, attributes, shed_tool_id, maxseconds ):
        hid = output_data.get( 'id' )
        try:
            fetcher = self.__dataset_fetcher( history_id )
            self.twill_test_case.verify_hid( outfile, hda_id=hid, attributes=attributes, dataset_fetcher=fetcher, shed_tool_id=shed_tool_id )
        except Exception:
            ## TODO: Print this!
            # print >>sys.stderr, self.twill_test_case.get_job_stdout( output_data.get( 'id' ), format=True )
            ## TODO: Print this!
            # print >>sys.stderr, self.twill_test_case.get_job_stderr( output_data.get( 'id' ), format=True )
            raise

    def new_history( self ):
        history_json = self.__post( "histories", {"name": "test_history"} ).json()
        return history_json[ 'id' ]

    def stage_data_async( self, test_data, history_id, shed_tool_id, async=True ):
        fname = test_data[ 'fname' ]
        file_name = self.twill_test_case.get_filename( fname, shed_tool_id=shed_tool_id )
        name = test_data.get( 'name', None )
        if not name:
            name = os.path.basename( file_name )
        tool_input = {
            "file_type": test_data[ 'ftype' ],
            "dbkey": test_data[ 'dbkey' ],  # TODO: Handle it! Doesn't work if undefined, does seem to in Twill.
            "files_0|NAME": name,
            "files_0|type": "upload_dataset",
        }
        files = {
            "files_0|file_data": open( file_name, 'rb')
        }
        submit_response = self.__submit_tool( history_id, "upload1", tool_input, extra_data={"type": "upload_dataset"}, files=files ).json()
        dataset = submit_response["outputs"][0]
        #raise Exception(str(dataset))
        hid = dataset['id']
        self.uploads[ fname ] = {"src": "hda", "id": hid}
        return self.__wait_for_history( history_id )

    def run_tool( self, testdef, history_id ):
        # We need to handle the case where we've uploaded a valid compressed file since the upload
        # tool will have uncompressed it on the fly.
        all_inputs = {}
        for name, value, _ in testdef.inputs:
            all_inputs[ name ] = value

        for key, value in all_inputs.iteritems():
            # TODO: Restrict this to param inputs.
            if value in self.uploads:
                all_inputs[key] = self.uploads[ value ]

        # TODO: Handle repeats.
        # TODO: Handle pages.
        # TODO: Handle force_history_refresh
        datasets = self.__submit_tool( history_id, tool_id=testdef.tool.id, tool_input=all_inputs )
        self.__wait_for_history( history_id )()  # TODO: Remove and respect maxseconds!
        return datasets.json()[ 'outputs' ]

    def output_hid( self, output_data ):
        return output_data[ 'id' ]

    def delete_history( self, history ):
        return None

    def __wait_for_history( self, history_id ):
        def wait():
            while True:
                history_json = self.__get( "histories/%s" % history_id ).json()
                state = history_json[ 'state' ]
                if state == 'ok':
                    #raise Exception(str(self.__get( self.__get( "histories/%s/contents" % history_id ).json()[0]['url'] ).json() ) )
                    #raise Exception(str(self.__get( self.__get( "histories/%s/contents" % history_id ).json()[0]['url'] ).json() ) )
                    break
                elif state == 'error':
                    raise Exception("History in error state.")
        return wait

    def __submit_tool( self, history_id, tool_id, tool_input, extra_data={}, files=None ):
        data = dict(
            history_id=history_id,
            tool_id=tool_id,
            inputs=dumps( tool_input ),
            **extra_data
        )
        return self.__post( "tools", files=files, data=data )

    def __get_user_key( self, user_key, admin_key ):
        if user_key:
            return user_key
        all_users = self.__get( 'users', key=admin_key ).json()
        try:
            test_user = [ user for user in all_users if user["email"] == 'test@bx.psu.edu' ][0]
        except IndexError:
            data = dict(
                email='test@bx.psu.edu',
                password='testuser',
                username='admin-user',
            )
            test_user = self.__post( 'users', data, key=admin_key ).json()
        return self.__post( "users/%s/api_key" % test_user['id'], key=admin_key ).json()

    def __dataset_fetcher( self, history_id ):
        def fetcher( hda_id, base_name=None ):
            url = "histories/%s/contents/%s/display" % (history_id, hda_id)
            if base_name:
                url += "&filename=%s" % base_name
            return self.__get( url ).text

        return fetcher

    def __post( self, path, data={}, files=None, key=None):
        if not key:
            key = self.api_key
        data = data.copy()
        data['key'] = key
        return requests.post( "%s/%s" % (self.api_url, path), data=data, files=files )

    def __get( self, path, data={}, key=None ):
        if not key:
            key = self.api_key
        data = data.copy()
        data['key'] = key
        if path.startswith("/api"):
            path = path[ len("/api"): ]
        url = "%s/%s" % (self.api_url, path)
        return requests.get( url, params=data )


class GalaxyInteractorTwill( object ):

    def __init__( self, twill_test_case ):
        self.twill_test_case = twill_test_case

    def verify_output( self, history, output_data, outfile, attributes, shed_tool_id, maxseconds ):
        hid = output_data.get( 'hid' )
        try:
            self.twill_test_case.verify_dataset_correctness( outfile, hid=hid, attributes=attributes, shed_tool_id=shed_tool_id )
        except Exception:
            print >>sys.stderr, self.twill_test_case.get_job_stdout( output_data.get( 'id' ), format=True )
            print >>sys.stderr, self.twill_test_case.get_job_stderr( output_data.get( 'id' ), format=True )
            raise

    def stage_data_async( self, test_data, history, shed_tool_id, async=True ):
            name = test_data.get( 'name', None )
            if name:
                async = False
            self.twill_test_case.upload_file( test_data['fname'],
                                              ftype=test_data['ftype'],
                                              dbkey=test_data['dbkey'],
                                              metadata=test_data['metadata'],
                                              composite_data=test_data['composite_data'],
                                              shed_tool_id=shed_tool_id,
                                              wait=(not async) )
            if name:
                hda_id = self.twill_test_case.get_history_as_data_list()[-1].get( 'id' )
                try:
                    self.twill_test_case.edit_hda_attribute_info( hda_id=str(hda_id), new_name=name )
                except:
                    print "### call to edit_hda failed for hda_id %s, new_name=%s" % (hda_id, name)
            return lambda: self.twill_test_case.wait()

    def run_tool( self, testdef, test_history ):
        # We need to handle the case where we've uploaded a valid compressed file since the upload
        # tool will have uncompressed it on the fly.
        all_inputs = {}
        for name, value, _ in testdef.inputs:
            all_inputs[ name ] = value

        # See if we have a grouping.Repeat element
        repeat_name = None
        for input_name, input_value in testdef.tool.inputs_by_page[0].items():
            if isinstance( input_value, grouping.Repeat ) and all_inputs.get( input_name, 1 ) not in [ 0, "0" ]:  # default behavior is to test 1 repeat, for backwards compatibility
                if not input_value.min:  # If input_value.min == 1, the element is already on the page don't add new element.
                    repeat_name = input_name
                break

        #check if we need to verify number of outputs created dynamically by tool
        if testdef.tool.force_history_refresh:
            job_finish_by_output_count = len( self.twill_test_case.get_history_as_data_list() )
        else:
            job_finish_by_output_count = False

        # Do the first page
        page_inputs = self.__expand_grouping(testdef.tool.inputs_by_page[0], all_inputs)

        # Run the tool
        self.twill_test_case.run_tool( testdef.tool.id, repeat_name=repeat_name, **page_inputs )
        print "page_inputs (0)", page_inputs
        # Do other pages if they exist
        for i in range( 1, testdef.tool.npages ):
            page_inputs = self.__expand_grouping(testdef.tool.inputs_by_page[i], all_inputs)
            self.twill_test_case.submit_form( **page_inputs )
            print "page_inputs (%i)" % i, page_inputs

        # Check the results ( handles single or multiple tool outputs ).  Make sure to pass the correct hid.
        # The output datasets from the tool should be in the same order as the testdef.outputs.
        data_list = None
        while data_list is None:
            data_list = self.twill_test_case.get_history_as_data_list()
            if job_finish_by_output_count and len( testdef.outputs ) > ( len( data_list ) - job_finish_by_output_count ):
                data_list = None
        return data_list

    def new_history( self ):
        # Start with a new history
        self.twill_test_case.logout()
        self.twill_test_case.login( email='test@bx.psu.edu' )
        admin_user = sa_session.query( galaxy.model.User ).filter( galaxy.model.User.table.c.email == 'test@bx.psu.edu' ).one()
        self.twill_test_case.new_history()
        latest_history = sa_session.query( galaxy.model.History ) \
                                   .filter( and_( galaxy.model.History.table.c.deleted == False,
                                                  galaxy.model.History.table.c.user_id == admin_user.id ) ) \
                                   .order_by( desc( galaxy.model.History.table.c.create_time ) ) \
                                   .first()
        assert latest_history is not None, "Problem retrieving latest_history from database"
        if len( self.twill_test_case.get_history_as_data_list() ) > 0:
            raise AssertionError("ToolTestCase.do_it failed")
        return latest_history

    def delete_history( self, latest_history ):
        self.twill_test_case.delete_history( id=self.twill_test_case.security.encode_id( latest_history.id ) )

    def output_hid( self, output_data ):
        return output_data.get( 'hid' )

    def __expand_grouping( self, tool_inputs, declared_inputs, prefix='' ):
        expanded_inputs = {}
        for key, value in tool_inputs.items():
            if isinstance( value, grouping.Conditional ):
                if prefix:
                    new_prefix = "%s|%s" % ( prefix, value.name )
                else:
                    new_prefix = value.name
                for i, case in enumerate( value.cases ):
                    if declared_inputs[ value.test_param.name ] == case.value:
                        if isinstance(case.value, str):
                            expanded_inputs[ "%s|%s" % ( new_prefix, value.test_param.name ) ] = case.value.split( "," )
                        else:
                            expanded_inputs[ "%s|%s" % ( new_prefix, value.test_param.name ) ] = case.value
                        for input_name, input_value in case.inputs.items():
                            expanded_inputs.update( self.__expand_grouping( { input_name: input_value }, declared_inputs, prefix=new_prefix ) )
            elif isinstance( value, grouping.Repeat ):
                for repeat_index in xrange( 0, 1 ):  # need to allow for and figure out how many repeats we have
                    for r_name, r_value in value.inputs.iteritems():
                        new_prefix = "%s_%d" % ( value.name, repeat_index )
                        if prefix:
                            new_prefix = "%s|%s" % ( prefix, new_prefix )
                        expanded_inputs.update( self.__expand_grouping( { new_prefix : r_value }, declared_inputs, prefix=new_prefix ) )
            elif value.name not in declared_inputs:
                print "%s not declared in tool test, will not change default value." % value.name
            elif isinstance(declared_inputs[value.name], str):
                if prefix:
                    expanded_inputs["%s|%s" % ( prefix, value.name ) ] = declared_inputs[value.name].split(",")
                else:
                    expanded_inputs[value.name] = declared_inputs[value.name].split(",")
            else:
                if prefix:
                    expanded_inputs["%s|%s" % ( prefix, value.name ) ] = declared_inputs[value.name]
                else:
                    expanded_inputs[value.name] = declared_inputs[value.name]
        return expanded_inputs


def build_tests( testing_shed_tools=False, master_api_key=None, user_api_key=None ):
    """
    If the module level variable `toolbox` is set, generate `ToolTestCase`
    classes for all of its tests and put them into this modules globals() so
    they can be discovered by nose.
    """
    if toolbox is None:
        return

    # Push all the toolbox tests to module level
    G = globals()

    # Eliminate all previous tests from G.
    for key, val in G.items():
        if key.startswith( 'TestForTool_' ):
            del G[ key ]

    for i, tool_id in enumerate( toolbox.tools_by_id ):
        tool = toolbox.get_tool( tool_id )
        if tool.tests:
            shed_tool_id = None if not testing_shed_tools else tool.id
            # Create a new subclass of ToolTestCase, dynamically adding methods
            # named test_tool_XXX that run each test defined in the tool config.
            name = "TestForTool_" + tool.id.replace( ' ', '_' )
            baseclasses = ( ToolTestCase, )
            namespace = dict()
            for j, testdef in enumerate( tool.tests ):
                def make_test_method( td ):
                    def test_tool( self ):
                        self.do_it( td )
                    return test_tool
                test_method = make_test_method( testdef )
                test_method.__doc__ = "%s ( %s ) > %s" % ( tool.name, tool.id, testdef.name )
                namespace[ 'test_tool_%06d' % j ] = test_method
                namespace[ 'shed_tool_id' ] = shed_tool_id
                namespace[ 'master_api_key' ] = master_api_key
                namespace[ 'user_api_key' ] = user_api_key
            # The new.classobj function returns a new class object, with name name, derived
            # from baseclasses (which should be a tuple of classes) and with namespace dict.
            new_class_obj = new.classobj( name, baseclasses, namespace )
            G[ name ] = new_class_obj


GALAXY_INTERACTORS = {
    'api': GalaxyInteractorApi,
    'twill': GalaxyInteractorTwill,
}
