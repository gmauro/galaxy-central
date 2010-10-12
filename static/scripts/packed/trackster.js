var DENSITY=200,FEATURE_LEVELS=10,MAX_FEATURE_DEPTH=100,DATA_ERROR="There was an error in indexing this dataset. ",DATA_NOCONVERTER="A converter for this dataset is not installed. Please check your datatypes_conf.xml file.",DATA_NONE="No data for this chrom/contig.",DATA_PENDING="Currently indexing... please wait",DATA_LOADING="Loading data...",CACHED_TILES_FEATURE=10,CACHED_TILES_LINE=30,CACHED_DATA=5,CONTEXT=$("<canvas></canvas>").get(0).getContext("2d"),PX_PER_CHAR=CONTEXT.measureText("A").width,RIGHT_STRAND,LEFT_STRAND;var right_img=new Image();right_img.src=image_path+"/visualization/strand_right.png";right_img.onload=function(){RIGHT_STRAND=CONTEXT.createPattern(right_img,"repeat")};var left_img=new Image();left_img.src=image_path+"/visualization/strand_left.png";left_img.onload=function(){LEFT_STRAND=CONTEXT.createPattern(left_img,"repeat")};var right_img_inv=new Image();right_img_inv.src=image_path+"/visualization/strand_right_inv.png";right_img_inv.onload=function(){RIGHT_STRAND_INV=CONTEXT.createPattern(right_img_inv,"repeat")};var left_img_inv=new Image();left_img_inv.src=image_path+"/visualization/strand_left_inv.png";left_img_inv.onload=function(){LEFT_STRAND_INV=CONTEXT.createPattern(left_img_inv,"repeat")};function round_1000(a){return Math.round(a*1000)/1000}var Cache=function(a){this.num_elements=a;this.clear()};$.extend(Cache.prototype,{get:function(b){var a=this.key_ary.indexOf(b);if(a!=-1){this.key_ary.splice(a,1);this.key_ary.push(b)}return this.obj_cache[b]},set:function(b,c){if(!this.obj_cache[b]){if(this.key_ary.length>=this.num_elements){var a=this.key_ary.shift();delete this.obj_cache[a]}this.key_ary.push(b)}this.obj_cache[b]=c;return c},clear:function(){this.obj_cache={};this.key_ary=[]}});var View=function(a,c,e,d,b){this.container=a;this.vis_id=d;this.dbkey=b;this.title=e;this.chrom=c;this.tracks=[];this.label_tracks=[];this.max_low=0;this.max_high=0;this.num_tracks=0;this.track_id_counter=0;this.zoom_factor=3;this.min_separation=30;this.has_changes=false;this.init();this.reset()};$.extend(View.prototype,{init:function(){var c=this.container,a=this;this.top_labeltrack=$("<div/>").addClass("top-labeltrack").appendTo(c);this.content_div=$("<div/>").addClass("content").css("position","relative").appendTo(c);this.viewport_container=$("<div/>").addClass("viewport-container").addClass("viewport-container").appendTo(this.content_div);this.intro_div=$("<div/>").addClass("intro").text("Select a chrom from the dropdown below").hide();this.nav_container=$("<div/>").addClass("nav-container").appendTo(c);this.nav_labeltrack=$("<div/>").addClass("nav-labeltrack").appendTo(this.nav_container);this.nav=$("<div/>").addClass("nav").appendTo(this.nav_container);this.overview=$("<div/>").addClass("overview").appendTo(this.nav);this.overview_viewport=$("<div/>").addClass("overview-viewport").appendTo(this.overview);this.overview_close=$("<a href='javascript:void(0);'>Close Overview</a>").addClass("overview-close").hide().appendTo(this.overview_viewport);this.overview_highlight=$("<div />").addClass("overview-highlight").hide().appendTo(this.overview_viewport);this.overview_box_background=$("<div/>").addClass("overview-boxback").appendTo(this.overview_viewport);this.overview_box=$("<div/>").addClass("overview-box").appendTo(this.overview_viewport);this.default_overview_height=this.overview_box.height();this.nav_controls=$("<div/>").addClass("nav-controls").appendTo(this.nav);this.chrom_form=$("<form/>").attr("action",function(){void (0)}).appendTo(this.nav_controls);this.chrom_select=$("<select/>").attr({name:"chrom"}).css("width","15em").addClass("no-autocomplete").append("<option value=''>Loading</option>").appendTo(this.chrom_form);var b=function(d){if(d.type==="focusout"||(d.keyCode||d.which)===13||(d.keyCode||d.which)===27){if((d.keyCode||d.which)!==27){a.go_to($(this).val())}$(this).hide();a.location_span.show();a.chrom_select.show();return false}};this.nav_input=$("<input/>").addClass("nav-input").hide().bind("keypress focusout",b).appendTo(this.chrom_form);this.location_span=$("<span/>").addClass("location").appendTo(this.chrom_form);this.location_span.bind("click",function(){a.location_span.hide();a.chrom_select.hide();a.nav_input.css("display","inline-block");a.nav_input.select();a.nav_input.focus()});if(this.vis_id!==undefined){this.hidden_input=$("<input/>").attr("type","hidden").val(this.vis_id).appendTo(this.chrom_form)}this.zo_link=$("<a/>").click(function(){a.zoom_out();a.redraw()}).html('<img src="'+image_path+'/fugue/magnifier-zoom-out.png" />').appendTo(this.chrom_form);this.zi_link=$("<a/>").click(function(){a.zoom_in();a.redraw()}).html('<img src="'+image_path+'/fugue/magnifier-zoom.png" />').appendTo(this.chrom_form);$.ajax({url:chrom_url,data:(this.vis_id!==undefined?{vis_id:this.vis_id}:{dbkey:this.dbkey}),dataType:"json",success:function(d){if(d.reference){a.add_label_track(new ReferenceTrack(a))}a.chrom_data=d.chrom_info;var f='<option value="">Select Chrom/Contig</option>';for(i in a.chrom_data){var e=a.chrom_data[i]["chrom"];f+='<option value="'+e+'">'+e+"</option>"}a.chrom_select.html(f);a.intro_div.show();a.chrom_select.bind("change",function(){a.change_chrom(a.chrom_select.val())})},error:function(){alert("Could not load chroms for this dbkey:",a.dbkey)}});this.content_div.bind("dblclick",function(d){a.zoom_in(d.pageX,this.viewport_container)});this.overview_box.bind("dragstart",function(d){this.current_x=d.offsetX}).bind("drag",function(d){var g=d.offsetX-this.current_x;this.current_x=d.offsetX;var f=Math.round(g/a.viewport_container.width()*(a.max_high-a.max_low));a.move_delta(-f)});this.overview_close.bind("click",function(){for(var d in a.tracks){a.tracks[d].is_overview=false}$(this).siblings().filter("canvas").remove();$(this).parent().css("height",a.overview_box.height());a.overview_highlight.hide();$(this).hide()});this.viewport_container.bind("dragstart",function(d){this.original_low=a.low;this.current_height=d.clientY;this.current_x=d.offsetX;this.enable_pan=(d.clientX<a.viewport_container.width()-16)?true:false}).bind("drag",function(g){if(!this.enable_pan||this.in_reordering){return}var d=$(this);var j=g.offsetX-this.current_x;var f=d.scrollTop()-(g.clientY-this.current_height);d.scrollTop(f);this.current_height=g.clientY;this.current_x=g.offsetX;var h=Math.round(j/a.viewport_container.width()*(a.high-a.low));a.move_delta(h)});this.top_labeltrack.bind("dragstart",function(d){this.drag_origin_x=d.clientX;this.drag_origin_pos=d.clientX/a.viewport_container.width()*(a.high-a.low)+a.low;this.drag_div=$("<div />").css({height:a.content_div.height()+30,top:"0px",position:"absolute","background-color":"#cfc",border:"1px solid #6a6",opacity:0.5,"z-index":1000}).appendTo($(this))}).bind("drag",function(j){var f=Math.min(j.clientX,this.drag_origin_x)-a.container.offset().left,d=Math.max(j.clientX,this.drag_origin_x)-a.container.offset().left,h=(a.high-a.low),g=a.viewport_container.width();a.update_location(Math.round(f/g*h)+a.low,Math.round(d/g*h)+a.low);this.drag_div.css({left:f+"px",width:(d-f)+"px"})}).bind("dragend",function(k){var f=Math.min(k.clientX,this.drag_origin_x),d=Math.max(k.clientX,this.drag_origin_x),h=(a.high-a.low),g=a.viewport_container.width(),j=a.low;a.low=Math.round(f/g*h)+j;a.high=Math.round(d/g*h)+j;this.drag_div.remove();a.redraw()});this.add_label_track(new LabelTrack(this,this.top_labeltrack));this.add_label_track(new LabelTrack(this,this.nav_labeltrack))},update_location:function(a,b){this.location_span.text(commatize(a)+" - "+commatize(b));this.nav_input.val(this.chrom+":"+commatize(a)+"-"+commatize(b))},change_chrom:function(d,a,f){var c=this;var e=$.grep(c.chrom_data,function(h,j){return h.chrom===d})[0];if(e===undefined){return}if(d!==c.chrom){c.chrom=d;if(c.chrom===""){c.intro_div.show()}else{c.intro_div.hide()}c.chrom_select.val(c.chrom);c.max_high=e.len;c.reset();c.redraw(true);for(var g in c.tracks){var b=c.tracks[g];if(b.init){b.init()}}}if(a!==undefined&&f!==undefined){c.low=Math.max(a,0);c.high=Math.min(f,c.max_high)}c.overview_viewport.find("canvas").remove();c.redraw()},go_to:function(f){var k=this,b=f.split(":"),h=b[0],j=b[1];if(j!==undefined){try{var g=j.split("-"),a=parseInt(g[0].replace(/,/g,"")),d=parseInt(g[1].replace(/,/g,""))}catch(c){return false}}k.change_chrom(h,a,d)},move_delta:function(c){var a=this;var b=a.high-a.low;if(a.low-c<a.max_low){a.low=a.max_low;a.high=a.max_low+b}else{if(a.high-c>a.max_high){a.high=a.max_high;a.low=a.max_high-b}else{a.high-=c;a.low-=c}}a.redraw()},add_track:function(a){a.view=this;a.track_id=this.track_id_counter;this.tracks.push(a);if(a.init){a.init()}a.container_div.attr("id","track_"+a.track_id);this.track_id_counter+=1;this.num_tracks+=1},add_label_track:function(a){a.view=this;this.label_tracks.push(a)},remove_track:function(a){this.has_changes=true;a.container_div.fadeOut("slow",function(){$(this).remove()});delete this.tracks[this.tracks.indexOf(a)];this.num_tracks-=1},reset:function(){this.low=this.max_low;this.high=this.max_high;this.viewport_container.find(".yaxislabel").remove()},redraw:function(h){var g=this.high-this.low,f=this.low,b=this.high;if(f<this.max_low){f=this.max_low}if(b>this.max_high){b=this.max_high}if(this.high!==0&&g<this.min_separation){b=f+this.min_separation}this.low=Math.floor(f);this.high=Math.ceil(b);this.resolution=Math.pow(10,Math.ceil(Math.log((this.high-this.low)/200)/Math.LN10));this.zoom_res=Math.pow(FEATURE_LEVELS,Math.max(0,Math.ceil(Math.log(this.resolution,FEATURE_LEVELS)/Math.log(FEATURE_LEVELS))));var a=this.low/(this.max_high-this.max_low)*this.overview_viewport.width();var e=(this.high-this.low)/(this.max_high-this.max_low)*this.overview_viewport.width();var j=13;this.overview_box.css({left:a,width:Math.max(j,e)}).show();if(e<j){this.overview_box.css("left",a-(j-e)/2)}if(this.overview_highlight){this.overview_highlight.css({left:a,width:e})}this.update_location(this.low,this.high);if(!h){for(var c=0,d=this.tracks.length;c<d;c++){if(this.tracks[c]&&this.tracks[c].enabled){this.tracks[c].draw()}}for(var c=0,d=this.label_tracks.length;c<d;c++){this.label_tracks[c].draw()}}},zoom_in:function(b,c){if(this.max_high===0||this.high-this.low<this.min_separation){return}var d=this.high-this.low,e=d/2+this.low,a=(d/this.zoom_factor)/2;if(b){e=b/this.viewport_container.width()*(this.high-this.low)+this.low}this.low=Math.round(e-a);this.high=Math.round(e+a);this.redraw()},zoom_out:function(){if(this.max_high===0){return}var b=this.high-this.low,c=b/2+this.low,a=(b*this.zoom_factor)/2;this.low=Math.round(c-a);this.high=Math.round(c+a);this.redraw()}});var Track=function(b,a,c){this.name=b;this.parent_element=c;this.view=a;this.init_global()};$.extend(Track.prototype,{init_global:function(){this.container_div=$("<div />").addClass("track");if(!this.hidden){this.header_div=$("<div class='track-header' />").appendTo(this.container_div);if(this.view.editor){this.drag_div=$("<div class='draghandle' />").appendTo(this.header_div)}this.name_div=$("<div class='menubutton popup' />").appendTo(this.header_div);this.name_div.text(this.name)}this.content_div=$("<div class='track-content'>").appendTo(this.container_div);this.parent_element.append(this.container_div)},init_each:function(c,b){var a=this;a.enabled=false;a.data_queue={};a.tile_cache.clear();a.data_cache.clear();a.initial_canvas=undefined;a.content_div.css("height","auto");if(!a.content_div.text()){a.content_div.text(DATA_LOADING)}a.container_div.removeClass("nodata error pending");if(a.view.chrom){$.getJSON(data_url,c,function(d){if(!d||d==="error"||d.kind==="error"){a.container_div.addClass("error");a.content_div.text(DATA_ERROR);if(d.message){var f=a.view.tracks.indexOf(a);var e=$("<a href='javascript:void(0);'></a>").attr("id",f+"_error");e.text("Click to view error");$("#"+f+"_error").live("click",function(){show_modal("Trackster Error","<pre>"+d.message+"</pre>",{Close:hide_modal})});a.content_div.append(e)}}else{if(d==="no converter"){a.container_div.addClass("error");a.content_div.text(DATA_NOCONVERTER)}else{if(d.data!==undefined&&(d.data===null||d.data.length===0)){a.container_div.addClass("nodata");a.content_div.text(DATA_NONE)}else{if(d==="pending"){a.container_div.addClass("pending");a.content_div.text(DATA_PENDING);setTimeout(function(){a.init()},5000)}else{a.content_div.text("");a.content_div.css("height",a.height_px+"px");a.enabled=true;b(d);a.draw()}}}}})}else{a.container_div.addClass("nodata");a.content_div.text(DATA_NONE)}}});var TiledTrack=function(){var d=this,c=d.view;if(d.hidden){return}if(d.display_modes!==undefined){if(d.mode_div===undefined){d.mode_div=$("<div class='right-float menubutton popup' />").appendTo(d.header_div);var h=d.display_modes[0];d.mode=h;d.mode_div.text(h);var a=function(j){d.mode_div.text(j);d.mode=j;d.tile_cache.clear();d.draw()};var f={};for(var e in d.display_modes){var g=d.display_modes[e];f[g]=function(j){return function(){a(j)}}(g)}make_popupmenu(d.mode_div,f)}else{d.mode_div.hide()}}var b={};b["Set as overview"]=function(){c.overview_viewport.find("canvas").remove();d.is_overview=true;d.set_overview();for(var j in c.tracks){if(c.tracks[j]!==d){c.tracks[j].is_overview=false}}};b["Edit configuration"]=function(){var k=function(){hide_modal()};var j=function(){d.update_options(d.track_id);hide_modal()};show_modal("Configure Track",d.gen_options(d.track_id),{Cancel:k,OK:j})};b.Remove=function(){c.remove_track(d);if(c.num_tracks===0){$("#no-tracks").show()}};make_popupmenu(d.name_div,b)};$.extend(TiledTrack.prototype,Track.prototype,{draw:function(){var j=this.view.low,e=this.view.high,f=e-j,d=this.view.resolution;var l=$("<div style='position: relative;'></div>"),m=this.content_div.width()/f,h;this.content_div.children(":first").remove();this.content_div.append(l),this.max_height=0;var a=Math.floor(j/d/DENSITY);while((a*DENSITY*d)<e){var k=this.content_div.width()+"_"+m+"_"+a;var c=this.tile_cache.get(k);if(c){var g=a*DENSITY*d;var b=(g-j)*m;if(this.left_offset){b-=this.left_offset}c.css({left:b});l.append(c);this.max_height=Math.max(this.max_height,c.height());this.content_div.css("height",this.max_height+"px")}else{this.delayed_draw(this,k,j,e,a,d,l,m)}a+=1}},delayed_draw:function(c,e,a,f,b,d,g,h){setTimeout(function(){if(!(a>c.view.high||f<c.view.low)){tile_element=c.draw_tile(d,b,g,h);if(tile_element){if(!c.initial_canvas){c.initial_canvas=$(tile_element).clone();var l=tile_element.get(0).getContext("2d");var j=c.initial_canvas.get(0).getContext("2d");var k=l.getImageData(0,0,l.canvas.width,l.canvas.height);j.putImageData(k,0,0);c.set_overview()}c.tile_cache.set(e,tile_element);c.max_height=Math.max(c.max_height,tile_element.height());c.content_div.css("height",c.max_height+"px")}}},50)},set_overview:function(){var a=this.view;a.overview_viewport.height(a.default_overview_height);a.overview_box.height(a.default_overview_height);if(this.initial_canvas&&this.is_overview){a.overview_close.show();a.overview_viewport.append(this.initial_canvas);a.overview_highlight.show().height(this.initial_canvas.height());a.overview_viewport.height(this.initial_canvas.height()+a.overview_box.height())}$(window).trigger("resize")}});var LabelTrack=function(a,b){this.track_type="LabelTrack";this.hidden=true;Track.call(this,null,a,b);this.container_div.addClass("label-track")};$.extend(LabelTrack.prototype,Track.prototype,{draw:function(){var c=this.view,d=c.high-c.low,g=Math.floor(Math.pow(10,Math.floor(Math.log(d)/Math.log(10)))),a=Math.floor(c.low/g)*g,e=this.content_div.width(),b=$("<div style='position: relative; height: 1.3em;'></div>");while(a<c.high){var f=(a-c.low)/d*e;b.append($("<div class='label'>"+commatize(a)+"</div>").css({position:"absolute",left:f-1}));a+=g}this.content_div.children(":first").remove();this.content_div.append(b)}});var ReferenceTrack=function(a){this.track_type="ReferenceTrack";this.hidden=true;Track.call(this,null,a,a.top_labeltrack);TiledTrack.call(this);this.height_px=12;this.container_div.addClass("reference-track");this.dummy_canvas=$("<canvas></canvas>").get(0).getContext("2d");this.data_queue={};this.data_cache=new Cache(CACHED_DATA);this.tile_cache=new Cache(CACHED_TILES_LINE)};$.extend(ReferenceTrack.prototype,TiledTrack.prototype,{get_data:function(d,b){var c=this,a=b*DENSITY*d,f=(b+1)*DENSITY*d,e=d+"_"+b;if(!c.data_queue[e]){c.data_queue[e]=true;$.ajax({url:reference_url,dataType:"json",data:{chrom:this.view.chrom,low:a,high:f,dbkey:this.view.dbkey},success:function(g){c.data_cache.set(e,g);delete c.data_queue[e];c.draw()},error:function(h,g,j){console.log(h,g,j)}})}},draw_tile:function(f,b,k,o){var g=b*DENSITY*f,d=DENSITY*f,e=$("<canvas class='tile'></canvas>"),n=e.get(0).getContext("2d"),j=f+"_"+b;if(o>PX_PER_CHAR){if(this.data_cache.get(j)===undefined){this.get_data(f,b);return}var m=this.data_cache.get(j);if(m===null){this.content_div.css("height","0px");return}e.get(0).width=Math.ceil(d*o+this.left_offset);e.get(0).height=this.height_px;e.css({position:"absolute",top:0,left:(g-this.view.low)*o-this.left_offset});for(var h=0,l=m.length;h<l;h++){var a=Math.round(h*o);n.fillText(m[h],a+this.left_offset,10)}k.append(e);return e}this.content_div.css("height","0px")}});var LineTrack=function(d,b,a,c){this.track_type="LineTrack";this.display_modes=["Line","Filled","Intensity"];this.mode="Line";Track.call(this,d,b,b.viewport_container);TiledTrack.call(this);this.height_px=80;this.dataset_id=a;this.data_cache=new Cache(CACHED_DATA);this.tile_cache=new Cache(CACHED_TILES_LINE);this.prefs={min_value:undefined,max_value:undefined,mode:"Line"};if(c.min_value!==undefined){this.prefs.min_value=c.min_value}if(c.max_value!==undefined){this.prefs.max_value=c.max_value}};$.extend(LineTrack.prototype,TiledTrack.prototype,{init:function(){var a=this,b=a.view.tracks.indexOf(a);a.vertical_range=undefined;this.init_each({stats:true,chrom:a.view.chrom,low:null,high:null,dataset_id:a.dataset_id},function(c){a.container_div.addClass("line-track");data=c.data;if(isNaN(parseFloat(a.prefs.min_value))||isNaN(parseFloat(a.prefs.max_value))){a.prefs.min_value=data.min;a.prefs.max_value=data.max;$("#track_"+b+"_minval").val(a.prefs.min_value);$("#track_"+b+"_maxval").val(a.prefs.max_value)}a.vertical_range=a.prefs.max_value-a.prefs.min_value;a.total_frequency=data.total_frequency;$("#linetrack_"+b+"_minval").remove();$("#linetrack_"+b+"_maxval").remove();a.container_div.css("position","relative");var e=$("<div />").addClass("yaxislabel").attr("id","linetrack_"+b+"_minval").text(round_1000(a.prefs.min_value));var d=$("<div />").addClass("yaxislabel").attr("id","linetrack_"+b+"_maxval").text(round_1000(a.prefs.max_value));d.css({position:"absolute",top:"22px",left:"10px"});d.prependTo(a.container_div);e.css({position:"absolute",top:a.height_px+11+"px",left:"10px"});e.prependTo(a.container_div)})},get_data:function(d,b){var c=this,a=b*DENSITY*d,f=(b+1)*DENSITY*d,e=d+"_"+b;if(!c.data_queue[e]){c.data_queue[e]=true;$.ajax({url:data_url,dataType:"json",data:{chrom:this.view.chrom,low:a,high:f,dataset_id:this.dataset_id,resolution:this.view.resolution},success:function(g){data=g.data;c.data_cache.set(e,data);delete c.data_queue[e];c.draw()},error:function(h,g,j){console.log(h,g,j)}})}},draw_tile:function(p,r,c,e){if(this.vertical_range===undefined){return}var s=r*DENSITY*p,a=DENSITY*p,b=$("<canvas class='tile'></canvas>"),v=p+"_"+r;if(this.data_cache.get(v)===undefined){this.get_data(p,r);return}var j=this.data_cache.get(v);if(j===null){return}b.css({position:"absolute",top:0,left:(s-this.view.low)*e});b.get(0).width=Math.ceil(a*e);b.get(0).height=this.height_px;var o=b.get(0).getContext("2d"),k=false,l=this.prefs.min_value,g=this.prefs.max_value,n=this.vertical_range,t=this.total_frequency,d=this.height_px,m=this.mode;o.beginPath();if(data.length>1){var f=Math.ceil((data[1][0]-data[0][0])*e)}else{var f=10}var u,h;for(var q=0;q<data.length;q++){u=(data[q][0]-s)*e;h=data[q][1];if(m=="Intensity"){if(h===null){continue}if(h<=l){h=l}else{if(h>=g){h=g}}h=255-Math.floor((h-l)/n*255);o.fillStyle="rgb("+h+","+h+","+h+")";o.fillRect(u,0,f,this.height_px)}else{if(h===null){if(k&&m==="Filled"){o.lineTo(u,d)}k=false;continue}else{if(h<=l){h=l}else{if(h>=g){h=g}}h=Math.round(d-(h-l)/n*d);if(k){o.lineTo(u,h)}else{k=true;if(m==="Filled"){o.moveTo(u,d);o.lineTo(u,h)}else{o.moveTo(u,h)}}}}}if(m==="Filled"){if(k){o.lineTo(u,d)}o.fill()}else{o.stroke()}c.append(b);return b},gen_options:function(k){var a=$("<div />").addClass("form-row");var e="track_"+k+"_minval",h=$("<label></label>").attr("for",e).text("Min value:"),b=(this.prefs.min_value===undefined?"":this.prefs.min_value),j=$("<input></input>").attr("id",e).val(b),g="track_"+k+"_maxval",d=$("<label></label>").attr("for",g).text("Max value:"),f=(this.prefs.max_value===undefined?"":this.prefs.max_value),c=$("<input></input>").attr("id",g).val(f);return a.append(h).append(j).append(d).append(c)},update_options:function(c){var a=$("#track_"+c+"_minval").val(),b=$("#track_"+c+"_maxval").val();if(a!==this.prefs.min_value||b!==this.prefs.max_value){this.prefs.min_value=parseFloat(a);this.prefs.max_value=parseFloat(b);this.vertical_range=this.prefs.max_value-this.prefs.min_value;$("#linetrack_"+c+"_minval").text(this.prefs.min_value);$("#linetrack_"+c+"_maxval").text(this.prefs.max_value);this.tile_cache.clear();this.draw()}}});var FeatureTrack=function(d,b,a,c){this.track_type="FeatureTrack";this.display_modes=["Auto","Dense","Squish","Pack"];Track.call(this,d,b,b.viewport_container);TiledTrack.call(this);this.height_px=0;this.container_div.addClass("feature-track");this.dataset_id=a;this.zo_slots={};this.show_labels_scale=0.001;this.showing_details=false;this.vertical_detail_px=10;this.vertical_nodetail_px=2;this.summary_draw_height=20;this.default_font="9px Monaco, Lucida Console, monospace";this.inc_slots={};this.data_queue={};this.s_e_by_tile={};this.tile_cache=new Cache(CACHED_TILES_FEATURE);this.data_cache=new Cache(20);this.left_offset=200;this.prefs={block_color:"black",label_color:"black",show_counts:true};if(c.block_color!==undefined){this.prefs.block_color=c.block_color}if(c.label_color!==undefined){this.prefs.label_color=c.label_color}if(c.show_counts!==undefined){this.prefs.show_counts=c.show_counts}};$.extend(FeatureTrack.prototype,TiledTrack.prototype,{init:function(){var a=this,b="initial";this.init_each({low:a.view.max_low,high:a.view.max_high,dataset_id:a.dataset_id,chrom:a.view.chrom,resolution:this.view.resolution,mode:a.mode},function(c){a.mode_div.show();a.data_cache.set(b,c);a.draw()})},get_data:function(a,d){var b=this,c=a+"_"+d;if(!b.data_queue[c]){b.data_queue[c]=true;$.getJSON(data_url,{chrom:b.view.chrom,low:a,high:d,dataset_id:b.dataset_id,resolution:this.view.resolution,mode:this.mode},function(e){b.data_cache.set(c,e);delete b.data_queue[c];b.draw()})}},incremental_slots:function(a,h,c,r){if(!this.inc_slots[a]){this.inc_slots[a]={};this.inc_slots[a].w_scale=a;this.inc_slots[a].mode=r;this.s_e_by_tile[a]={}}var n=this.inc_slots[a].w_scale,z=[],l=0,b=$("<canvas></canvas>").get(0).getContext("2d"),o=this.view.max_low;var B=[];if(this.inc_slots[a].mode!==r){delete this.inc_slots[a];this.inc_slots[a]={mode:r,w_scale:n};delete this.s_e_by_tile[a];this.s_e_by_tile[a]={}}for(var w=0,x=h.length;w<x;w++){var g=h[w],m=g[0];if(this.inc_slots[a][m]!==undefined){l=Math.max(l,this.inc_slots[a][m]);B.push(this.inc_slots[a][m])}else{z.push(w)}}for(var w=0,x=z.length;w<x;w++){var g=h[z[w]],m=g[0],s=g[1],d=g[2],q=g[3],e=Math.floor((s-o)*n),f=Math.ceil((d-o)*n);if(q!==undefined&&!c){var t=b.measureText(q).width;if(e-t<0){f+=t}else{e-=t}}var v=0;while(true){var p=true;if(this.s_e_by_tile[a][v]!==undefined){for(var u=0,A=this.s_e_by_tile[a][v].length;u<A;u++){var y=this.s_e_by_tile[a][v][u];if(f>y[0]&&e<y[1]){p=false;break}}}if(p){if(this.s_e_by_tile[a][v]===undefined){this.s_e_by_tile[a][v]=[]}this.s_e_by_tile[a][v].push([e,f]);this.inc_slots[a][m]=v;l=Math.max(l,v);break}v++}}return l},rect_or_text:function(n,o,f,m,b,d,k,e,h){n.textAlign="center";var j=Math.round(o/2);if((this.mode==="Pack"||this.mode==="Auto")&&d!==undefined&&o>PX_PER_CHAR){n.fillStyle=this.prefs.block_color;n.fillRect(k,h+1,e,9);n.fillStyle="#eee";for(var g=0,l=d.length;g<l;g++){if(b+g>=f&&b+g<=m){var a=Math.floor(Math.max(0,(b+g-f)*o));n.fillText(d[g],a+this.left_offset+j,h+9)}}}else{n.fillStyle=this.prefs.block_color;n.fillRect(k,h+4,e,3)}},draw_tile:function(ae,o,r,ar){var L=o*DENSITY*ae,ak=(o+1)*DENSITY*ae,K=ak-L;var al=(!this.initial_canvas?"initial":L+"_"+ak);var G=this.data_cache.get(al);var e;if(G===undefined||(this.mode!=="Auto"&&G.dataset_type==="summary_tree")){this.data_queue[[L,ak]]=true;this.get_data(L,ak);return}var a=Math.ceil(K*ar),S=$("<canvas class='tile'></canvas>"),ag=this.prefs.label_color,h=this.prefs.block_color,q=this.mode,v=25,ac=(q==="Squish")||(q==="Dense")&&(q!=="Pack")||(q==="Auto"&&(G.extra_info==="no_detail")),W=this.left_offset,aq,B,at;if(G.dataset_type==="summary_tree"){B=this.summary_draw_height}else{if(q==="Dense"){B=v;at=10}else{at=(ac?this.vertical_nodetail_px:this.vertical_detail_px);var w=(ar<0.0001?1/view.zoom_res:ar);B=this.incremental_slots(w,G.data,ac,q)*at+v;aq=this.inc_slots[w]}}S.css({position:"absolute",top:0,left:(L-this.view.low)*ar-W});S.get(0).width=a+W;S.get(0).height=B;r.parent().css("height",Math.max(this.height_px,B)+"px");var H=S.get(0).getContext("2d");H.fillStyle=h;H.font=this.default_font;H.textAlign="right";if(G.dataset_type=="summary_tree"){var R,O=55,aj=255-O,n=aj*2/3,Y=G.data,J=G.max,p=G.avg,b=Math.ceil(G.delta*ar);for(var an=0,F=Y.length;an<F;an++){var aa=Math.floor((Y[an][0]-L)*ar);var Z=Y[an][1];if(!Z){continue}R=Math.floor(aj-(Z/J)*aj);H.fillStyle="rgb("+R+","+R+","+R+")";H.fillRect(aa+W,0,b,this.summary_draw_height);if(this.prefs.show_counts&&H.measureText(Z).width<b){if(R>n){H.fillStyle="black"}else{H.fillStyle="#ddd"}H.textAlign="center";H.fillText(Z,aa+W+(b/2),12)}}e="Summary";r.append(S);return S}if(G.message){S.css({border:"solid red","border-width":"2px 2px 2px 0px"});H.fillStyle="red";H.textAlign="left";H.fillText(G.message,100+W,at)}var ap=G.data;var am=0;for(var an=0,F=ap.length;an<F;an++){var T=ap[an],Q=T[0],ao=T[1],ab=T[2],M=T[3];if(ao<=ak&&ab>=L){var ad=Math.floor(Math.max(0,(ao-L)*ar)),I=Math.ceil(Math.min(a,Math.max(0,(ab-L)*ar))),X=(q==="Dense"?1:(1+aq[Q]))*at;if(G.dataset_type==="bai"){H.fillStyle=h;if(T[4] instanceof Array){var C=Math.floor(Math.max(0,(T[4][0]-L)*ar)),P=Math.ceil(Math.min(a,Math.max(0,(T[4][1]-L)*ar))),A=Math.floor(Math.max(0,(T[5][0]-L)*ar)),u=Math.ceil(Math.min(a,Math.max(0,(T[5][1]-L)*ar)));if(T[4][1]>=L&&T[4][0]<=ak){this.rect_or_text(H,ar,L,ak,T[4][0],T[4][2],C+W,P-C,X)}if(T[5][1]>=L&&T[5][0]<=ak){this.rect_or_text(H,ar,L,ak,T[5][0],T[5][2],A+W,u-A,X)}if(A>P){H.fillStyle="#999";H.fillRect(P+W,X+5,A-P,1)}}else{H.fillStyle=h;this.rect_or_text(H,ar,L,ak,ao,M,ad+W,I-ad,X)}if(q!=="Dense"&&!ac&&ao>L){H.fillStyle=this.prefs.label_color;if(o===0&&ad-H.measureText(M).width<0){H.textAlign="left";H.fillText(Q,I+2+W,X+8)}else{H.textAlign="right";H.fillText(Q,ad-2+W,X+8)}H.fillStyle=h}}else{if(G.dataset_type==="interval_index"){if(ac){H.fillStyle=h;H.fillRect(ad+W,X+5,I-ad,1)}else{var E=T[4],V=T[5],af=T[6],g=T[7];var D,ah,N=null,au=null;if(V&&af){N=Math.floor(Math.max(0,(V-L)*ar));au=Math.ceil(Math.min(a,Math.max(0,(af-L)*ar)))}if(q!=="Dense"&&M!==undefined&&ao>L){H.fillStyle=ag;if(o===0&&ad-H.measureText(M).width<0){H.textAlign="left";H.fillText(M,I+2+W,X+8)}else{H.textAlign="right";H.fillText(M,ad-2+W,X+8)}H.fillStyle=h}if(g){if(E){if(E=="+"){H.fillStyle=RIGHT_STRAND}else{if(E=="-"){H.fillStyle=LEFT_STRAND}}H.fillRect(ad+W,X,I-ad,10);H.fillStyle=h}for(var al=0,f=g.length;al<f;al++){var t=g[al],d=Math.floor(Math.max(0,(t[0]-L)*ar)),U=Math.ceil(Math.min(a,Math.max((t[1]-L)*ar)));if(d>U){continue}D=5;ah=3;H.fillRect(d+W,X+ah,U-d,D);if(N!==undefined&&!(d>au||U<N)){D=9;ah=1;var ai=Math.max(d,N),z=Math.min(U,au);H.fillRect(ai+W,X+ah,z-ai,D)}}}else{D=9;ah=1;H.fillRect(ad+W,X+ah,I-ad,D);if(T.strand){if(T.strand=="+"){H.fillStyle=RIGHT_STRAND_INV}else{if(T.strand=="-"){H.fillStyle=LEFT_STRAND_INV}}H.fillRect(ad+W,X,I-ad,10);H.fillStyle=h}}}}else{if(G.dataset_type==="vcf"){if(ac){H.fillStyle=h;H.fillRect(ad+W,X+5,I-ad,1)}else{var s=T[4],m=T[5],c=T[6];D=9;ah=1;H.fillRect(ad+W,X,I-ad,D);if(q!=="Dense"&&M!==undefined&&ao>L){H.fillStyle=ag;if(o===0&&ad-H.measureText(M).width<0){H.textAlign="left";H.fillText(M,I+2+W,X+8)}else{H.textAlign="right";H.fillText(M,ad-2+W,X+8)}H.fillStyle=h}var l=s+" / "+m;if(ao>L&&H.measureText(l).width<(I-ad)){H.fillStyle="white";H.textAlign="center";H.fillText(l,W+ad+(I-ad)/2,X+8);H.fillStyle=h}}}}}am++}}r.append(S);return S},gen_options:function(j){var a=$("<div />").addClass("form-row");var e="track_"+j+"_block_color",l=$("<label />").attr("for",e).text("Block color:"),m=$("<input />").attr("id",e).attr("name",e).val(this.prefs.block_color),k="track_"+j+"_label_color",g=$("<label />").attr("for",k).text("Text color:"),h=$("<input />").attr("id",k).attr("name",k).val(this.prefs.label_color),f="track_"+j+"_show_count",c=$("<label />").attr("for",f).text("Show summary counts"),b=$('<input type="checkbox" style="float:left;"></input>').attr("id",f).attr("name",f).attr("checked",this.prefs.show_counts),d=$("<div />").append(b).append(c);return a.append(l).append(m).append(g).append(h).append(d)},update_options:function(e){var b=$("#track_"+e+"_block_color").val(),d=$("#track_"+e+"_label_color").val(),c=$("#track_"+e+"_mode option:selected").val(),a=$("#track_"+e+"_show_count").attr("checked");if(b!==this.prefs.block_color||d!==this.prefs.label_color||a!==this.prefs.show_counts){this.prefs.block_color=b;this.prefs.label_color=d;this.prefs.show_counts=a;this.tile_cache.clear();this.draw()}}});var ReadTrack=function(d,b,a,c){FeatureTrack.call(this,d,b,a,c);this.track_type="ReadTrack";this.vertical_detail_px=10;this.vertical_nodetail_px=5};$.extend(ReadTrack.prototype,TiledTrack.prototype,FeatureTrack.prototype,{});