import new
import sys
from base.twilltestcase import TwillTestCase
from base.interactor import build_interactor
import logging
log = logging.getLogger( __name__ )

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
        return build_interactor( self, testdef.interactor )

    def __handle_test_def_errors(self, testdef):
        # If the test generation had an error, raise
        if testdef.error:
            if testdef.exception:
                raise testdef.exception
            else:
                raise Exception( "Test parse failure" )

    def __verify_outputs( self, testdef, history, shed_tool_id, data_list, galaxy_interactor ):
        maxseconds = testdef.maxseconds

        for output_index, output_tuple in enumerate(testdef.outputs):
            # Get the correct hid
            name, outfile, attributes = output_tuple
            try:
                output_data = data_list[ name ]
            except (TypeError, KeyError):
                # Legacy - fall back on ordered data list access if data_list is
                # just a list (case with twill variant)
                output_data = data_list[ len(data_list) - len(testdef.outputs) + output_index ]
            self.assertTrue( output_data is not None )
            try:
                galaxy_interactor.verify_output( history, output_data, outfile, attributes=attributes, shed_tool_id=shed_tool_id, maxseconds=maxseconds )
            except Exception:
                for stream in ['stdout', 'stderr']:
                    stream_output = galaxy_interactor.get_job_stream( history, output_data, stream=stream )
                    print >>sys.stderr, self._format_stream( stream_output, stream=stream, format=True )
                raise


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
