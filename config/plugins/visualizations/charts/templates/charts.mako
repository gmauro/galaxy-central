<%
    root        = h.url_for( "/" )
    app_root    = root + "plugins/visualizations/charts/static/"
%>


<!DOCTYPE HTML>
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <title>${hda.name} | ${visualization_name}</title>

        ## install shared libraries
        ${h.js( 'libs/jquery/jquery',
                'libs/bootstrap',
                'libs/require',
                'libs/underscore',
                'libs/backbone/backbone',
                'libs/d3')}

        ## shared css
        ${h.css( 'base' )}

        ## install nv.d3 module
        ${h.javascript_link( app_root + "plugins/nv.d3.js" )}
        ${h.stylesheet_link( app_root + "plugins/nv.d3.css" )}

        ## install boxplot module
        ##${h.javascript_link( app_root + "plugins/box.js" )}

        ## load merged/minified code
        ${h.javascript_link( app_root + "build-app.js" )}
    </head>

    <body>
        <script type="text/javascript">

            // get configuration
            var config = {
                root    : '${root}'
            };
            
            // link galaxy
            var Galaxy = Galaxy || parent.Galaxy;

            // console protection
            window.console = window.console || {
                log     : function(){},
                debug   : function(){},
                info    : function(){},
                warn    : function(){},
                error   : function(){},
                assert  : function(){}
            };

            // configure require
            require.config({
                baseUrl: config.root + "static/scripts/",
                paths: {
                    "plugin": "${app_root}"
                },
                shim: {
                    "libs/underscore": { exports: "_" },
                    "libs/backbone/backbone": { exports: "Backbone" }
                }
            });

            // application
            var app = null;
            $(function() {   
                // request application script
                require(['plugin/app'], function(App) {
                    // load options
                    var options = {
                        id      : ${h.to_json_string( visualization_id )} || undefined,
                        config  : ${h.to_json_string( config )}
                    }
                    
                    // create application
                    app = new App(options);
                    
                    // add to body
                    $('body').append(app.$el);
                });
            });

        </script>
    </body>
</html>
