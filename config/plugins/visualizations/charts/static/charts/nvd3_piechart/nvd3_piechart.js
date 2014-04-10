// dependencies
define(['utils/utils'], function(Utils) {

// widget
return Backbone.View.extend(
{
    // initialize
    initialize: function(app, options) {
        this.app        = app;
        this.options    = options;
    },
            
    // render
    draw : function(process_id, chart, request_dictionary)
    {
        // request data
        var self = this;
        this.app.datasets.request(request_dictionary, function() {
            
            // loop through data groups
            for (var key in request_dictionary.groups) {
                // get group
                var group = request_dictionary.groups[key];
                
                // format chart data
                var pie_data = [];
                for (var key in group.values) {
                    var value = group.values[key];
                    pie_data.push ({
                        y : value.y,
                        x : value.label
                    });
                }
            }
            
            // add graph to screen
            nv.addGraph(function() {
                self.chart_3d = nv.models.pieChart()
                    .donut(true)
                    .showLegend(false);
                
                self.options.canvas.datum(pie_data)
                                   .call(self.chart_3d);

                nv.utils.windowResize(self.chart_3d.update);
                
                // set chart state
                chart.state('ok', 'Chart has been drawn.');
            
                // unregister process
                chart.deferred.done(process_id);
            });
        });
    }
});

});