

class FilterFactory( object ):
    """
    An instance of this class is responsible for filtering the list
    of tools presented to a given user in a given context.
    """

    def __init__( self, toolbox ):
        self.toolbox = toolbox

        # Prepopulate dict containing filters that are always checked,
        # other filters that get checked depending on context (e.g. coming from
        # trackster or no user found are added in build filters).
        self.default_filters = dict( tool=[ _not_hidden ], section=[], label=[] )
        # Add dynamic filters to these default filters.
        config = toolbox.app.config
        self.__init_filters( "tool", config.tool_filters )
        self.__init_filters( "section", config.tool_section_filters )
        self.__init_filters( "label", config.tool_label_filters )

    def build_filters( self, trans, **kwds ):
        """
        Build list of filters to check tools against given current context.
        """
        filters = self.default_filters.copy()

        filters[ "tool" ].append( _handle_requires_login )

        if kwds.get( "trackster", False ):
            filters[ "tool" ].append( _has_trackster_conf )

        return filters

    def __init_filters( self, key, filters ):
        for filter in filters:
            filter_function = self.__build_filter_function( filter )
            self.default_filters[ key ].append( filter_function )

    def __build_filter_function( self, filter_name ):
        """Obtain python function (importing a submodule if needed)
        corresponding to filter_name.
        """
        if ":" in filter_name:
            # Should be a submodule of filters (e.g. examples:restrict_development_tools)
            (module_name, function_name) = filter_name.rsplit(":", 1)
            module = __import__( module_name.strip(), globals() )
            function = getattr( module, function_name.strip() )
        else:
            # No module found, just load a function from this file or
            # one that has be explicitly imported.
            function = getattr( globals(), filter_name.strip() )
        return function


## Stock Filter Functions
def _not_hidden( context, tool ):
    return not tool.hidden


def _handle_requires_login( context, tool ):
    return not tool.require_login or context.trans.user


def _has_trackster_conf( context, tool ):
    return tool.trackster_conf
