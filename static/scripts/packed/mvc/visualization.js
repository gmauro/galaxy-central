var TrackBrowserRouter=Backbone.Router.extend({initialize:function(b){this.view=b.view;this.route(/([\w]+)$/,"change_location");this.route(/([\w]+\:[\d,]+-[\d,]+)$/,"change_location");var a=this;a.view.on("navigate",function(c){a.navigate(c)})},change_location:function(a){this.view.go_to(a)}});