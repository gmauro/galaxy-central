// dependencies
define(['utils/utils', 'plugin/library/ui', 'mvc/ui/ui-portlet',
        'plugin/models/group', 'plugin/views/viewport', 'plugin/library/screenshot'],
        function(Utils, Ui, Portlet, Group, ViewportView, Screenshot) {

// widget
return Backbone.View.extend(
{
    // initialize
    initialize: function(app, options)
    {
        // link app
        this.app = app;
        
        // link chart
        this.chart = this.app.chart;
        
        // create viewport
        this.viewport_view = new ViewportView(app);
        
        // link this
        var self = this;
        
        // create portlet
        this.portlet = new Portlet.View({
            icon : 'fa-bar-chart-o',
            title: 'Viewport',
            operations: {
                edit_button: new Ui.ButtonIcon({
                    icon    : 'fa-edit',
                    tooltip : 'Customize this chart',
                    title   : 'Editor',
                    onclick : function() {
                        // attempt to load chart editor
                        self._wait (self.chart, function() {
                            self.app.go('editor');
                        });
                    }
                }),
                picture_button: new Ui.ButtonIcon({
                    icon    : 'fa-camera',
                    tooltip : 'Download PDF-file (' + self.app.config.get('screenshot_url') + ')',
                    title   : 'Screenshot',
                    onclick : function() {
                        // attempt to load chart editor
                        self._wait (self.chart, function() {
                            Screenshot.create(self.viewport_view.$el, self.app.config.get('screenshot_url'), self.chart.get('title'));
                        });
                    }
                })
            }
        });
        
        // append portlet
        this.portlet.append(this.viewport_view.$el);
        
        // set element
        this.setElement(this.portlet.$el);
        
        // events
        var self = this;
        this.chart.on('change:title', function() {
            self._refreshTitle();
        });
    },

    // show
    show: function() {
        // show element
        this.$el.show();
        
        // trigger resize to refresh d3 element
        $(window).trigger('resize');
    },
        
    // hide
    hide: function() {
        this.$el.hide();
    },
    
    // refresh title
    _refreshTitle: function() {
        var title = this.chart.get('title');
        this.portlet.title(title);
    },
    
    // wait for chart to be ready
    _wait: function(chart, callback) {
        // get chart
        if (chart.deferred.ready()) {
            callback();
        } else {
            // show modal
            var self = this;
            this.app.modal.show({
                title   : 'Please wait!',
                body    : 'Your chart is currently being processed. Please wait and try again.',
                buttons : {
                    'Close'     : function() {self.app.modal.hide();},
                    'Retry'     : function() {
                        // hide modal
                        self.app.modal.hide();
                        
                        // retry
                        setTimeout(function() { self._wait(chart, callback); }, self.app.config.get('query_timeout'));
                    }
                }
            });
        }
    }
});

});