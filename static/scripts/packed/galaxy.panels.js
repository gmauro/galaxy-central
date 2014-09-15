!function(c,d){var e=function(){if(d("#DD-helper").length==0){d("<div id='DD-helper'/>").appendTo("body").hide()}};var b=160,h=800;var k=function(n){this.$panel=n.panel;this.$center=n.center;this.$drag=n.drag;this.$toggle=n.toggle;this.left=!n.right;this.hidden=false;this.hidden_by_tool=false;this.saved_size=null;this.init()};d.extend(k.prototype,{resize:function(n){this.$panel.css("width",n);if(this.left){this.$center.css("left",n)}else{this.$center.css("right",n)}if(document.recalc){document.recalc()}},do_toggle:function(){var n=this;if(this.hidden){this.$toggle.removeClass("hidden");if(this.left){this.$panel.css("left",-this.saved_size).show().animate({left:0},"fast",function(){n.resize(n.saved_size)})}else{this.$panel.css("right",-this.saved_size).show().animate({right:0},"fast",function(){n.resize(n.saved_size)})}n.hidden=false}else{n.saved_size=this.$panel.width();if(document.recalc){document.recalc()}if(this.left){this.$panel.animate({left:-this.saved_size},"fast")}else{this.$panel.animate({right:-this.saved_size},"fast")}if(this.left){this.$center.css("left",0)}else{this.$center.css("right",0)}n.hidden=true;n.$toggle.addClass("hidden")}this.hidden_by_tool=false},handle_minwidth_hint:function(n){var o=this.$center.width()-(this.hidden?this.saved_size:0);if(o<n){if(!this.hidden){this.do_toggle();this.hidden_by_tool=true}}else{if(this.hidden_by_tool){this.do_toggle();this.hidden_by_tool=false}}},force_panel:function(n){if((this.hidden&&n=="show")||(!this.hidden&&n=="hide")){this.do_toggle()}},init:function(){var o=this,p;o.$toggle.remove().appendTo("body");o.$toggle.on("click",function(){o.do_toggle()});function n(s){var t=s.pageX-p;p=s.pageX;var q=o.$panel.width(),r=(o.left)?(q+t):(q-t);r=Math.min(h,Math.max(b,r));o.resize(r)}this.$drag.on("mousedown",function(q){p=q.pageX;d("#DD-helper").show().on("mousemove",n).one("mouseup",function(r){d(this).hide().off("mousemove",n)})})}});var f=function(n){this.$overlay=n.overlay;this.$dialog=n.dialog;this.$header=this.$dialog.find(".modal-header");this.$body=this.$dialog.find(".modal-body");this.$footer=this.$dialog.find(".modal-footer");this.$backdrop=n.backdrop;this.$header.find(".close").on("click",d.proxy(this.hide,this))};d.extend(f.prototype,{setContent:function(p){this.$header.hide();if(p.title){this.$header.find(".title").html(p.title);this.$header.show()}if(p.closeButton){this.$header.find(".close").show();this.$header.show()}else{this.$header.find(".close").hide()}this.$footer.hide();var o=this.$footer.find(".buttons").html("");if(p.buttons){d.each(p.buttons,function(r,s){o.append(d("<button></button> ").text(r).click(s)).append(" ")});this.$footer.show()}var q=this.$footer.find(".extra_buttons").html("");if(p.extra_buttons){d.each(p.extra_buttons,function(r,s){q.append(d("<button></button>").text(r).click(s)).append(" ")});this.$footer.show()}var n=p.body;if(n=="progress"){n=d("<div class='progress progress-striped active'><div class='progress-bar' style='width: 100%'></div></div>")}this.$body.html(n)},show:function(n,o){if(!this.$dialog.is(":visible")){if(n.backdrop){this.$backdrop.addClass("in")}else{this.$backdrop.removeClass("in")}this.$overlay.show();this.$dialog.show();this.$overlay.addClass("in");this.$body.css("min-width",this.$body.width());this.$body.css("max-height",d(window).height()-this.$footer.outerHeight()-this.$header.outerHeight()-parseInt(this.$dialog.css("padding-top"),10)-parseInt(this.$dialog.css("padding-bottom"),10))}if(o){o()}},hide:function(){var n=this;n.$dialog.fadeOut(function(){n.$overlay.hide();n.$backdrop.removeClass("in");n.$body.children().remove();n.$body.css("min-width",undefined)})}});var m;d(function(){m=new f({overlay:d("#top-modal"),dialog:d("#top-modal-dialog"),backdrop:d("#top-modal-backdrop")})});function a(){m.hide()}function l(r,n,p,o,q){m.setContent({title:r,body:n,buttons:p,extra_buttons:o});m.show({backdrop:true},q)}function g(r,n,p,o,q){m.setContent({title:r,body:n,buttons:p,extra_buttons:o});m.show({backdrop:false},q)}function j(p){var q=p.width||"600";var o=p.height||"400";var n=p.scroll||"auto";d("#overlay-background").bind("click.overlay",function(){a();d("#overlay-background").unbind("click.overlay")});m.setContent({closeButton:true,title:"&nbsp;",body:d("<div style='margin: -5px;'><iframe style='margin: 0; padding: 0;' src='"+p.url+"' width='"+q+"' height='"+o+"' scrolling='"+n+"' frameborder='0'></iframe></div>")});m.show({backdrop:true})}function i(n,o){if(n){d(".loggedin-only").show();d(".loggedout-only").hide();d("#user-email").text(n);if(o){d(".admin-only").show()}}else{d(".loggedin-only").hide();d(".loggedout-only").show();d(".admin-only").hide()}}d(function(){var n=d("#masthead ul.nav > li.dropdown > .dropdown-menu");d("body").on("click.nav_popups",function(p){n.hide();d("#DD-helper").hide();if(d(p.target).closest("#masthead ul.nav > li.dropdown > .dropdown-menu").length){return}var o=d(p.target).closest("#masthead ul.nav > li.dropdown");if(o.length){d("#DD-helper").show();o.children(".dropdown-menu").show();p.preventDefault()}})});c.ensure_dd_helper=e;c.Panel=k;c.Modal=f;c.hide_modal=a;c.show_modal=l;c.show_message=g;c.show_in_overlay=j;c.user_changed=i}(window,window.jQuery);