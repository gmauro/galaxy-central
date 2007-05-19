import new, sys
import galaxy.util
import parameters

class ToolTestBuilder( object ):
    """
    Encapsulates information about a tool test, and allows creation of a 
    dynamic TestCase class (the unittest framework is very class oriented, 
    doing dynamic tests in this was allows better integration)
    """
    def __init__( self, tool, name ):
        self.tool = tool
        self.name = name
        self.required_files = []
        self.inputs = []
        self.outputs = []
        self.error = False
        self.exception = None
    def add_param( self, name, value, extra ):
        # FIXME: This needs to be updated for parameter grouping support
        if isinstance( self.tool.inputs[name], parameters.DataToolParameter ):
            self.required_files.append( ( value, extra ) )
        self.inputs.append( ( name, value, extra ) )
    def add_output( self, name, file ):
        self.outputs.append( ( name, file ) )
