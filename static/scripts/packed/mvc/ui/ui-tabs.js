define(["utils/utils"],function(a){var b=Backbone.View.extend({optionsDefault:{title_new:"",operations:null,onnew:null},initialize:function(e){this.visible=false;this.$nav=null;this.$content=null;this.first_tab=null;this.options=a.merge(e,this.optionsDefault);var c=$(this._template(this.options));this.$nav=c.find(".tab-navigation");this.$content=c.find(".tab-content");this.setElement(c);this.list={};var d=this;if(this.options.operations){$.each(this.options.operations,function(g,h){h.$el.prop("id",g);d.$nav.find(".operations").append(h.$el)})}if(this.options.onnew){var f=$(this._template_tab_new(this.options));this.$nav.append(f);f.tooltip({title:"Add a new tab",placement:"bottom",container:d.$el});f.on("click",function(g){f.tooltip("hide");d.options.onnew()})}},size:function(){return _.size(this.list)},add:function(f){var e=this;var h=f.id;var g=$(this._template_tab(f));var d=$(this._template_tab_content(f));this.list[h]=f.ondel?true:false;if(this.options.onnew){this.$nav.find("#new-tab").before(g)}else{this.$nav.append(g)}d.append(f.$el);this.$content.append(d);if(_.size(this.list)==1){g.addClass("active");d.addClass("active");this.first_tab=h}if(f.ondel){var c=g.find("#delete");c.tooltip({title:"Delete this tab",placement:"bottom",container:e.$el});c.on("click",function(){c.tooltip("destroy");e.$el.find(".tooltip").remove();f.ondel();return false})}g.on("click",function(i){i.preventDefault();if(f.onclick){f.onclick()}else{e.show(h)}})},del:function(c){this.$el.find("#tab-"+c).remove();this.$el.find("#"+c).remove();if(this.first_tab==c){this.first_tab=null}if(this.first_tab!=null){this.show(this.first_tab)}if(this.list[c]){delete this.list[c]}},delRemovable:function(){for(var c in this.list){this.del(c)}},show:function(c){this.$el.fadeIn("fast");this.visible=true;if(c){this.$el.find(".tab-element").removeClass("active");this.$el.find(".tab-pane").removeClass("active");this.$el.find("#tab-"+c).addClass("active");this.$el.find("#"+c).addClass("active")}},hide:function(){this.$el.fadeOut("fast");this.visible=false},hideOperation:function(c){this.$nav.find("#"+c).hide()},showOperation:function(c){this.$nav.find("#"+c).show()},setOperation:function(e,d){var c=this.$nav.find("#"+e);c.off("click");c.on("click",d)},title:function(e,d){var c=this.$el.find("#tab-title-text-"+e);if(d){c.html(d)}return c.html()},retitle:function(d){var c=0;for(var e in this.list){this.title(e,++c+": "+d)}},_template:function(c){return'<div class="ui-tabs tabbable tabs-left"><ul id="tab-navigation" class="tab-navigation nav nav-tabs"><div class="operations" style="float: right; margin-bottom: 4px;"></div></ul><div id="tab-content" class="tab-content"/></div>'},_template_tab_new:function(c){return'<li id="new-tab"><a href="javascript:void(0);"><i class="ui-tabs-add fa fa-plus-circle"/>'+c.title_new+"</a></li>"},_template_tab:function(d){var c='<li id="tab-'+d.id+'" class="tab-element"><a id="tab-title-link-'+d.id+'" title="" href="#'+d.id+'" data-original-title=""><span id="tab-title-text-'+d.id+'" class="tab-title-text">'+d.title+"</span>";if(d.ondel){c+='<i id="delete" class="ui-tabs-delete fa fa-minus-circle"/>'}c+="</a></li>";return c},_template_tab_content:function(c){return'<div id="'+c.id+'" class="tab-pane"/>'}});return{View:b}});