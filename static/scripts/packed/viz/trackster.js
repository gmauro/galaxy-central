var ui=null;var view=null;var browser_router=null;require(["utils/galaxy.css","libs/jquery/jstorage","libs/jquery/jquery.event.drag","libs/jquery/jquery.event.hover","libs/jquery/jquery.mousewheel","libs/jquery/jquery-ui","libs/jquery/jquery-ui-combobox","libs/farbtastic","libs/jquery/jquery.form","libs/jquery/jquery.rating","mvc/ui"],function(a){a.load_file("/static/style/jquery.rating.css");a.load_file("/static/style/history.css");a.load_file("/static/style/autocomplete_tagging.css");a.load_file("/static/style/jquery-ui/smoothness/jquery-ui.css");a.load_file("/static/style/library.css");a.load_file("/static/style/trackster.css")});define(["libs/backbone/backbone-relational","viz/visualization","viz/trackster_ui"],function(c,a,b){var d=Backbone.View.extend({initialize:function(){ui=new b.TracksterUI(galaxy_config.root);ui.createButtonMenu();ui.buttonMenu.$el.attr("style","float: right");$("#center .unified-panel-header-inner").append(ui.buttonMenu.$el);$("#right .unified-panel-title").append("Bookmarks");$("#right .unified-panel-icons").append("<a id='add-bookmark-button' class='icon-button menu-button plus-button' href='javascript:void(0);' title='Add bookmark'></a>");$("#right-border").click(function(){view.resize_window()});force_right_panel("hide");if(galaxy_config.app.id){this.view_existing()}else{this.view_new()}},set_up_router:function(e){browser_router=new a.TrackBrowserRouter(e);Backbone.history.start()},view_existing:function(){var e=galaxy_config.app.viz_config;view=ui.create_visualization({container:$("#center .unified-panel-body"),name:e.title,vis_id:e.vis_id,dbkey:e.dbkey},e.viewport,e.tracks,e.bookmarks,true);this.init_editor()},view_new:function(){var e=this;$.ajax({url:galaxy_config.root+"api/genomes?chrom_info=True",data:{},error:function(){alert("Couldn't create new browser.")},success:function(f){show_modal("New Visualization",e.template_view_new(f),{Cancel:function(){window.location=galaxy_config.root+"visualization/list"},Create:function(){e.create_browser($("#new-title").val(),$("#new-dbkey").val())}});if(galaxy_config.app.default_dbkey){$("#new-dbkey option[value='"+galaxy_config.app.default_dbkey+"']").attr("selected",true)}$("#new-title").focus();$("select[name='dbkey']").combobox({appendTo:$("#overlay"),size:40});$("#overlay").css("overflow","auto")}})},template_view_new:function(e){var g='<form id="new-browser-form" action="javascript:void(0);" method="post" onsubmit="return false;"><div class="form-row"><label for="new-title">Browser name:</label><div class="form-row-input"><input type="text" name="title" id="new-title" value="Unnamed"></input></div><div style="clear: both;"></div></div><div class="form-row"><label for="new-dbkey">Reference genome build (dbkey): </label><div class="form-row-input"><select name="dbkey" id="new-dbkey">';for(var f in e){g+='<option value="'+e[f][1]+'">'+e[f][0]+"</option>"}g+='</select></div><div style="clear: both;"></div></div><div class="form-row">Is the build not listed here? <a href="'+galaxy_config.root+'user/dbkeys?use_panels=True">Add a Custom Build</a></div></form>';return g},create_browser:function(f,e){$(document).trigger("convert_to_values");view=ui.create_visualization({container:$("#center .unified-panel-body"),name:f,dbkey:e},galaxy_config.app.gene_region);this.init_editor();view.editor=true;hide_modal()},init_editor:function(){$("#center .unified-panel-title").text(view.name+" ("+view.dbkey+")");if(galaxy_config.app.add_dataset){$.ajax({url:galaxy_config.root+"api/datasets/"+galaxy_config.app.add_dataset,data:{hda_ldda:"hda",data_type:"track_config"},dataType:"json",success:function(e){view.add_drawable(b.object_from_template(e,view,view))}})}$("#add-bookmark-button").click(function(){var f=view.chrom+":"+view.low+"-"+view.high,e="Bookmark description";return ui.add_bookmark(f,e,true)});ui.init_keyboard_nav(view);this.set_up_router({view:view})}});return{GalaxyApp:d}});