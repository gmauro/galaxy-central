define(["libs/underscore","viz/trackster/util","mvc/data","libs/backbone/backbone-relational"],function(x,a,y){var g={hidden:false,show:function(){this.set("hidden",false)},hide:function(){this.set("hidden",true)},toggle:function(){this.set("hidden",!this.get("hidden"))},is_visible:function(){return !this.attributes.hidden}};var e=Backbone.RelationalModel.extend({defaults:{name:null,label:null,type:null,value:null,html:null,num_samples:5},subModelTypes:{integer:"IntegerToolParameter","float":"FloatToolParameter",data:"DataToolParameter",select:"SelectToolParameter"},initialize:function(){this.attributes.html=unescape(this.attributes.html)},copy:function(){return new e(this.toJSON())},set_value:function(z){this.set("value",z||"")}});var o={};Backbone.Relational.store.addModelScope(o);var j=o.DataToolParameter=e.extend({});var d=o.IntegerToolParameter=e.extend({set_value:function(z){this.set("value",parseInt(z,10))},get_samples:function(){return d3.scale.linear().domain([this.get("min"),this.get("max")]).ticks(this.get("num_samples"))}});var f=o.FloatToolParameter=d.extend({set_value:function(z){this.set("value",parseFloat(z))}});var t=o.SelectToolParameter=e.extend({get_samples:function(){return x.map(this.get("options"),function(z){return z[0]})}});var i=Backbone.RelationalModel.extend({defaults:{id:null,name:null,description:null,target:null,inputs:[],outputs:[]},relations:[{type:Backbone.HasMany,key:"inputs",relatedModel:e}],urlRoot:galaxy_config.root+"api/tools",remove_inputs:function(A){var z=this,B=z.get("inputs").filter(function(C){return(A.indexOf(C.get("type"))!==-1)});z.get("inputs").remove(B)},copy:function(A){var B=new i(this.toJSON());if(A){var z=new Backbone.Collection();B.get("inputs").each(function(C){if(C.get_samples()){z.push(C)}});B.set("inputs",z)}return B},apply_search_results:function(z){(x.indexOf(z,this.attributes.id)!==-1?this.show():this.hide());return this.is_visible()},set_input_value:function(z,A){this.get("inputs").find(function(B){return B.get("name")===z}).set("value",A)},set_input_values:function(A){var z=this;x.each(x.keys(A),function(B){z.set_input_value(B,A[B])})},run:function(){return this._run()},rerun:function(A,z){return this._run({action:"rerun",target_dataset_id:A.id,regions:z})},get_inputs_dict:function(){var z={};this.get("inputs").each(function(A){z[A.get("name")]=A.get("value")});return z},_run:function(B){var C=x.extend({tool_id:this.id,inputs:this.get_inputs_dict()},B);var A=$.Deferred(),z=new a.ServerStateDeferred({ajax_settings:{url:this.urlRoot,data:JSON.stringify(C),dataType:"json",contentType:"application/json",type:"POST"},interval:2000,success_fn:function(D){return D!=="pending"}});$.when(z.go()).then(function(D){A.resolve(new y.DatasetCollection().reset(D))});return A}});x.extend(i.prototype,g);var q=Backbone.View.extend({});var m=Backbone.Collection.extend({model:i});var v=Backbone.Model.extend(g);var k=Backbone.Model.extend({defaults:{elems:[],open:false},clear_search_results:function(){x.each(this.attributes.elems,function(z){z.show()});this.show();this.set("open",false)},apply_search_results:function(A){var B=true,z;x.each(this.attributes.elems,function(C){if(C instanceof v){z=C;z.hide()}else{if(C instanceof i){if(C.apply_search_results(A)){B=false;if(z){z.show()}}}}});if(B){this.hide()}else{this.show();this.set("open",true)}}});x.extend(k.prototype,g);var c=Backbone.Model.extend({defaults:{search_hint_string:"search tools",min_chars_for_search:3,spinner_url:"",clear_btn_url:"",search_url:"",visible:true,query:"",results:null,clear_key:27},initialize:function(){this.on("change:query",this.do_search)},do_search:function(){var B=this.attributes.query;if(B.length<this.attributes.min_chars_for_search){this.set("results",null);return}var A=B+"*";if(this.timer){clearTimeout(this.timer)}$("#search-clear-btn").hide();$("#search-spinner").show();var z=this;this.timer=setTimeout(function(){$.get(z.attributes.search_url,{query:A},function(C){z.set("results",C);$("#search-spinner").hide();$("#search-clear-btn").show()},"json")},200)},clear_search:function(){this.set("query","");this.set("results",null)}});x.extend(c.prototype,g);var n=Backbone.Model.extend({initialize:function(z){this.attributes.tool_search=z.tool_search;this.attributes.tool_search.on("change:results",this.apply_search_results,this);this.attributes.tools=z.tools;this.attributes.layout=new Backbone.Collection(this.parse(z.layout))},parse:function(A){var z=this,B=function(E){var D=E.model_class;if(D.indexOf("Tool")===D.length-4){return z.attributes.tools.get(E.id)}else{if(D==="ToolSection"){var C=x.map(E.elems,B);E.elems=C;return new k(E)}else{if(D==="ToolSectionLabel"){return new v(E)}}}};return x.map(A,B)},clear_search_results:function(){this.get("layout").each(function(z){if(z instanceof k){z.clear_search_results()}else{z.show()}})},apply_search_results:function(){var A=this.get("tool_search").get("results");if(A===null){this.clear_search_results();return}var z=null;this.get("layout").each(function(B){if(B instanceof v){z=B;z.hide()}else{if(B instanceof i){if(B.apply_search_results(A)){if(z){z.show()}}}else{z=null;B.apply_search_results(A)}}})}});var s=Backbone.View.extend({initialize:function(){this.model.on("change:hidden",this.update_visible,this);this.update_visible()},update_visible:function(){(this.model.attributes.hidden?this.$el.hide():this.$el.show())}});var l=s.extend({tagName:"div",render:function(){this.$el.append(Handlebars.templates.tool_link(this.model.toJSON()));return this}});var b=s.extend({tagName:"div",className:"toolPanelLabel",render:function(){this.$el.append($("<span/>").text(this.model.attributes.text));return this}});var r=s.extend({tagName:"div",className:"toolSectionWrapper",initialize:function(){s.prototype.initialize.call(this);this.model.on("change:open",this.update_open,this)},render:function(){this.$el.append(Handlebars.templates.panel_section(this.model.toJSON()));var z=this.$el.find(".toolSectionBody");x.each(this.model.attributes.elems,function(A){if(A instanceof i){var B=new l({model:A,className:"toolTitle"});B.render();z.append(B.$el)}else{if(A instanceof v){var C=new b({model:A});C.render();z.append(C.$el)}else{}}});return this},events:{"click .toolSectionTitle > a":"toggle"},toggle:function(){this.model.set("open",!this.model.attributes.open)},update_open:function(){(this.model.attributes.open?this.$el.children(".toolSectionBody").slideDown("fast"):this.$el.children(".toolSectionBody").slideUp("fast"))}});var p=Backbone.View.extend({tagName:"div",id:"tool-search",className:"bar",events:{click:"focus_and_select","keyup :input":"query_changed","click #search-clear-btn":"clear"},render:function(){this.$el.append(Handlebars.templates.tool_search(this.model.toJSON()));if(!this.model.is_visible()){this.$el.hide()}this.$el.find("[title]").tooltip();return this},focus_and_select:function(){this.$el.find(":input").focus().select()},clear:function(){this.model.clear_search();this.$el.find(":input").val(this.model.attributes.search_hint_string);this.focus_and_select();return false},query_changed:function(z){if((this.model.attributes.clear_key)&&(this.model.attributes.clear_key===z.which)){this.clear();return false}this.model.set("query",this.$el.find(":input").val())}});var w=Backbone.View.extend({tagName:"div",className:"toolMenu",initialize:function(){this.model.get("tool_search").on("change:results",this.handle_search_results,this)},render:function(){var z=this;var A=new p({model:this.model.get("tool_search")});A.render();z.$el.append(A.$el);this.model.get("layout").each(function(C){if(C instanceof k){var B=new r({model:C});B.render();z.$el.append(B.$el)}else{if(C instanceof i){var D=new l({model:C,className:"toolTitleNoSection"});D.render();z.$el.append(D.$el)}else{if(C instanceof v){var E=new b({model:C});E.render();z.$el.append(E.$el)}}}});z.$el.find("a.tool-link").click(function(D){var C=$(this).attr("class").split(/\s+/)[0],B=z.model.get("tools").get(C);z.trigger("tool_link_click",D,B)});return this},handle_search_results:function(){var z=this.model.get("tool_search").get("results");if(z&&z.length===0){$("#search-no-results").show()}else{$("#search-no-results").hide()}}});var u=Backbone.View.extend({className:"toolForm",render:function(){this.$el.children().remove();this.$el.append(Handlebars.templates.tool_form(this.model.toJSON()))}});var h=Backbone.View.extend({className:"toolMenuAndView",initialize:function(){this.tool_panel_view=new w({collection:this.collection});this.tool_form_view=new u()},render:function(){this.tool_panel_view.render();this.tool_panel_view.$el.css("float","left");this.$el.append(this.tool_panel_view.$el);this.tool_form_view.$el.hide();this.$el.append(this.tool_form_view.$el);var z=this;this.tool_panel_view.on("tool_link_click",function(B,A){B.preventDefault();z.show_tool(A)})},show_tool:function(A){var z=this;A.fetch().done(function(){z.tool_form_view.model=A;z.tool_form_view.render();z.tool_form_view.$el.show();$("#left").width("650px")})}});return{ToolParameter:e,IntegerToolParameter:d,SelectToolParameter:t,Tool:i,ToolCollection:m,ToolSearch:c,ToolPanel:n,ToolPanelView:w,ToolFormView:u}});