define(["mvc/ui/ui-modal","mvc/ui/ui-frames","mvc/ui/icon-button"],function(k,j,f){var h=Backbone.Model.extend({});var b=Backbone.Model.extend({defaults:{id:"",type:"",name:"",hda_ldda:"hda",metadata:null},initialize:function(){if(!this.get("metadata")){this._set_metadata()}this.on("change",this._set_metadata,this)},_set_metadata:function(){var n=new h();_.each(_.keys(this.attributes),function(o){if(o.indexOf("metadata_")===0){var p=o.split("metadata_")[1];n.set(p,this.attributes[o]);delete this.attributes[o]}},this);this.set("metadata",n,{silent:true})},get_metadata:function(n){return this.attributes.metadata.get(n)},urlRoot:galaxy_config.root+"api/datasets"});var i=b.extend({defaults:_.extend({},b.prototype.defaults,{chunk_url:null,first_data_chunk:null,chunk_index:-1,at_eof:false}),initialize:function(n){b.prototype.initialize.call(this);this.attributes.chunk_index=(this.attributes.first_data_chunk?1:0);this.attributes.chunk_url=galaxy_config.root+"dataset/display?dataset_id="+this.id;this.attributes.url_viz=galaxy_config.root+"visualization"},get_next_chunk:function(){if(this.attributes.at_eof){return null}var n=this,o=$.Deferred();$.getJSON(this.attributes.chunk_url,{chunk:n.attributes.chunk_index++}).success(function(p){var q;if(p.ck_data!==""){q=p}else{n.attributes.at_eof=true;q=null}o.resolve(q)});return o}});var e=Backbone.Collection.extend({model:b});var a=Backbone.View.extend({initialize:function(n){this.row_count=0;this.loading_chunk=false;new d({model:n.model,$el:this.$el})},expand_to_container:function(){if(this.$el.height()<this.scroll_elt.height()){this.attempt_to_fetch()}},attempt_to_fetch:function(o){var n=this;if(!this.loading_chunk&&this.scrolled_to_bottom()){this.loading_chunk=true;this.loading_indicator.show();$.when(n.model.get_next_chunk()).then(function(p){if(p){n._renderChunk(p);n.loading_chunk=false}n.loading_indicator.hide();n.expand_to_container()})}},render:function(){this.loading_indicator=$("<div/>").attr("id","loading_indicator");this.$el.append(this.loading_indicator);var r=$("<table/>").attr({id:"content_table",cellpadding:0});this.$el.append(r);var n=this.model.get_metadata("column_names"),s=$("<thead/>").appendTo(r),t=$("<tr/>").appendTo(s);if(n){t.append("<th>"+n.join("</th><th>")+"</th>")}else{for(var q=1;q<=this.model.get_metadata("columns");q++){t.append("<th>"+q+"</th>")}}var p=this,o=this.model.get("first_data_chunk");if(o){this._renderChunk(o)}else{$.when(p.model.get_next_chunk()).then(function(u){p._renderChunk(u)})}this.scroll_elt.scroll(function(){p.attempt_to_fetch()})},scrolled_to_bottom:function(){return false},_renderCell:function(q,n,r){var o=$("<td>").text(q);var p=this.model.get_metadata("column_types");if(r!==undefined){o.attr("colspan",r).addClass("stringalign")}else{if(p){if(n<p.length){if(p[n]==="str"||p[n]==="list"){o.addClass("stringalign")}}}}return o},_renderRow:function(n){var o=n.split("\t"),q=$("<tr>"),p=this.model.get_metadata("columns");if(this.row_count%2!==0){q.addClass("dark_row")}if(o.length===p){_.each(o,function(s,r){q.append(this._renderCell(s,r))},this)}else{if(o.length>p){_.each(o.slice(0,p-1),function(s,r){q.append(this._renderCell(s,r))},this);q.append(this._renderCell(o.slice(p-1).join("\t"),p-1))}else{if(p>5&&o.length===p-1){_.each(o,function(s,r){q.append(this._renderCell(s,r))},this);q.append($("<td>"))}else{q.append(this._renderCell(n,0,p))}}}this.row_count++;return q},_renderChunk:function(n){var o=this.$el.find("table");_.each(n.ck_data.split("\n"),function(p,q){if(p!==""){o.append(this._renderRow(p))}},this)}});var g=a.extend({initialize:function(n){a.prototype.initialize.call(this,n);scroll_elt=_.find(this.$el.parents(),function(o){return $(o).css("overflow")==="auto"});if(!scroll_elt){scroll_elt=window}this.scroll_elt=$(scroll_elt)},scrolled_to_bottom:function(){return(this.$el.height()-this.scroll_elt.scrollTop()-this.scroll_elt.height()<=0)}});var m=a.extend({initialize:function(n){a.prototype.initialize.call(this,n);this.scroll_elt=this.$el.css({position:"relative",overflow:"scroll",height:this.options.height||"500px"})},scrolled_to_bottom:function(){return this.$el.scrollTop()+this.$el.innerHeight()>=this.el.scrollHeight}});var d=Backbone.View.extend({col:{chrom:null,start:null,end:null},url_viz:null,dataset_id:null,genome_build:null,file_ext:null,initialize:function(p){var s=parent.Galaxy;if(s&&s.modal){this.modal=s.modal}if(s&&s.frame){this.frame=s.frame}if(!this.modal||!this.frame){return}var o=p.model;var r=o.get("metadata");if(!o.get("file_ext")){return}this.file_ext=o.get("file_ext");if(this.file_ext=="bed"){if(r.get("chromCol")&&r.get("startCol")&&r.get("endCol")){this.col.chrom=r.get("chromCol")-1;this.col.start=r.get("startCol")-1;this.col.end=r.get("endCol")-1}else{console.log("TabularButtonTrackster : Bed-file metadata incomplete.");return}}if(this.file_ext=="vcf"){function q(u,v){for(var t=0;t<v.length;t++){if(v[t].match(u)){return t}}return -1}this.col.chrom=q("Chrom",r.get("column_names"));this.col.start=q("Pos",r.get("column_names"));this.col.end=null;if(this.col.chrom==-1||this.col.start==-1){console.log("TabularButtonTrackster : VCF-file metadata incomplete.");return}}if(this.col.chrom===undefined){return}if(o.id){this.dataset_id=o.id}else{console.log("TabularButtonTrackster : Dataset identification is missing.");return}if(o.get("url_viz")){this.url_viz=o.get("url_viz")}else{console.log("TabularButtonTrackster : Url for visualization controller is missing.");return}if(o.get("genome_build")){this.genome_build=o.get("genome_build")}var n=new f.IconButtonView({model:new f.IconButton({title:"Visualize",icon_class:"chart_curve",id:"btn_viz"})});this.setElement(p.$el);this.$el.append(n.render().$el);this.hide()},events:{"mouseover tr":"show",mouseleave:"hide"},show:function(s){function r(x){return !isNaN(parseFloat(x))&&isFinite(x)}if(this.col.chrom===null){return}var w=$(s.target).parent();var t=w.children().eq(this.col.chrom).html();var n=w.children().eq(this.col.start).html();var p=this.col.end?w.children().eq(this.col.end).html():n;if(!t.match("^#")&&t!==""&&r(n)){var v={dataset_id:this.dataset_id,gene_region:t+":"+n+"-"+p};var q=w.offset();var o=q.left-10;var u=q.top-$(window).scrollTop()+3;$("#btn_viz").css({position:"fixed",top:u+"px",left:o+"px"});$("#btn_viz").off("click");$("#btn_viz").click(this.create_trackster_action(this.url_viz,v,this.genome_build));$("#btn_viz").show()}else{$("#btn_viz").hide()}},hide:function(){this.$el.find("#btn_viz").hide()},create_trackster_action:function(n,q,p){var o=this;return function(){var r={};if(p){r["f-dbkey"]=p}$.ajax({url:n+"/list_tracks?"+$.param(r),dataType:"html",error:function(){o.modal.show({title:"Something went wrong!",body:"Unfortunately we could not add this dataset to the track browser. Please try again or contact us.",buttons:{Cancel:function(){o.modal.hide()}}})},success:function(s){o.modal.show({title:"View Data in a New or Saved Visualization",buttons:{Cancel:function(){o.modal.hide()},"View in saved visualization":function(){o.modal.show({title:"Add Data to Saved Visualization",body:s,buttons:{Cancel:function(){o.modal.hide()},"Add to visualization":function(){o.modal.hide();o.modal.$el.find("input[name=id]:checked").each(function(){var t=$(this).val();q.id=t;o.frame.add({title:"Trackster",type:"url",content:n+"/trackster?"+$.param(q)})})}}})},"View in new visualization":function(){o.modal.hide();o.frame.add({title:"Trackster",type:"url",content:n+"/trackster?"+$.param(q)})}}})}});return false}}});var l=function(q,o,r,n){var p=new o({model:new q(r)});p.render();if(n){n.append(p.$el)}return p};var c=function(p){if(!p.model){p.model=new i(p.dataset_config)}var o=p.parent_elt;var q=p.embedded;delete p.embedded;delete p.parent_elt;delete p.dataset_config;var n=(q?new m(p):new g(p));n.render();if(o){o.append(n.$el);n.expand_to_container()}return n};return{Dataset:b,TabularDataset:i,DatasetCollection:e,TabularDatasetChunkedView:a,createTabularDatasetChunkedView:c}});