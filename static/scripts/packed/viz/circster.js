define(["libs/underscore","libs/d3","viz/visualization"],function(g,l,i){var m=Backbone.Model.extend({is_visible:function(q,n){var o=q.getBoundingClientRect(),p=$("svg")[0].getBoundingClientRect();if(o.right<0||o.left>p.right||o.bottom<0||o.top>p.bottom){return false}return true}});var h={drawTicks:function(r,q,v,p,n){var u=r.append("g").selectAll("g").data(q).enter().append("g").selectAll("g").data(v).enter().append("g").attr("class","tick").attr("transform",function(w){return"rotate("+(w.angle*180/Math.PI-90)+")translate("+w.radius+",0)"});var t=[],s=[],o=function(w){return w.angle>Math.PI?"end":null};if(n){t=[0,0,0,-4];s=[4,0,"",".35em"];o=null}else{t=[1,0,4,0];s=[0,4,".35em",""]}u.append("line").attr("x1",t[0]).attr("y1",t[1]).attr("x2",t[2]).attr("y1",t[3]).style("stroke","#000");u.append("text").attr("x",s[0]).attr("y",s[1]).attr("dx",s[2]).attr("dy",s[3]).attr("text-anchor",o).attr("transform",p).text(function(w){return w.label})},formatNum:function(o,n){if(n===undefined){n=2}if(o===null){return null}var q=null;if(o<1){q=o.toPrecision(n)}else{var p=Math.round(o.toPrecision(n));if(o<1000){q=p}else{if(o<1000000){q=Math.round((p/1000).toPrecision(3)).toFixed(0)+"K"}else{if(o<1000000000){q=Math.round((p/1000000).toPrecision(3)).toFixed(0)+"M"}}}}return q}};var c=Backbone.Model.extend({});var a=Backbone.View.extend({className:"circster",initialize:function(n){this.total_gap=n.total_gap;this.genome=n.genome;this.dataset_arc_height=n.dataset_arc_height;this.track_gap=10;this.label_arc_height=50;this.scale=1;this.circular_views=null;this.chords_views=null;this.model.get("tracks").on("add",this.add_track,this);this.model.get("tracks").on("remove",this.remove_track,this);this.get_circular_tracks()},get_circular_tracks:function(){return this.model.get("tracks").filter(function(n){return n.get("track_type")!=="DiagonalHeatmapTrack"})},get_chord_tracks:function(){return this.model.get("tracks").filter(function(n){return n.get("track_type")==="DiagonalHeatmapTrack"})},get_tracks_bounds:function(){var o=this.get_circular_tracks();dataset_arc_height=this.dataset_arc_height,min_dimension=Math.min(this.$el.width(),this.$el.height()),radius_start=min_dimension/2-o.length*(this.dataset_arc_height+this.track_gap)-(this.label_arc_height+this.track_gap),tracks_start_radii=l.range(radius_start,min_dimension/2,this.dataset_arc_height+this.track_gap);var n=this;return g.map(tracks_start_radii,function(p){return[p,p+n.dataset_arc_height]})},render:function(){var w=this,q=this.dataset_arc_height,n=w.$el.width(),v=w.$el.height(),s=this.get_circular_tracks(),p=this.get_chord_tracks(),r=this.get_tracks_bounds(),o=l.select(w.$el[0]).append("svg").attr("width",n).attr("height",v).attr("pointer-events","all").append("svg:g").call(l.behavior.zoom().on("zoom",function(){var x=l.event.scale;o.attr("transform","translate("+l.event.translate+") scale("+x+")");if(w.scale!==x){if(w.zoom_drag_timeout){clearTimeout(w.zoom_drag_timeout)}w.zoom_drag_timeout=setTimeout(function(){},400)}})).attr("transform","translate("+n/2+","+v/2+")").append("svg:g").attr("class","tracks");this.circular_views=s.map(function(y,z){var x=new d({el:o.append("g")[0],track:y,radius_bounds:r[z],genome:w.genome,total_gap:w.total_gap});x.render();return x});this.chords_views=p.map(function(y){var x=new j({el:o.append("g")[0],track:y,radius_bounds:r[0],genome:w.genome,total_gap:w.total_gap});x.render();return x});var u=this.circular_views[this.circular_views.length-1].radius_bounds[1],t=[u,u+this.label_arc_height];this.label_track_view=new b({el:o.append("g")[0],track:new c(),radius_bounds:t,genome:w.genome,total_gap:w.total_gap});this.label_track_view.render()},add_track:function(t){if(t.get("track_type")==="DiagonalHeatmapTrack"){var p=this.circular_views[0].radius_bounds,s=new j({el:l.select("g.tracks").append("g")[0],track:t,radius_bounds:p,genome:this.genome,total_gap:this.total_gap});s.render();this.chords_views.push(s)}else{var r=this.get_tracks_bounds();g.each(this.circular_views,function(u,v){u.update_radius_bounds(r[v])});g.each(this.chords_views,function(u){u.update_radius_bounds(r[0])});var q=this.circular_views.length,n=new d({el:l.select("g.tracks").append("g")[0],track:t,radius_bounds:r[q],genome:this.genome,total_gap:this.total_gap});n.render();this.circular_views.push(n);var o=r[r.length-1];o[1]=o[0];this.label_track_view.update_radius_bounds(o)}},remove_track:function(o,q,p){var n=this.circular_views[p.index];this.circular_views.splice(p.index,1);n.$el.remove();var r=this.get_tracks_bounds();g.each(this.circular_views,function(s,t){s.update_radius_bounds(r[t])})}});var k=Backbone.View.extend({tagName:"g",initialize:function(n){this.bg_stroke="ccc";this.loading_bg_fill="000";this.bg_fill="ccc";this.total_gap=n.total_gap;this.track=n.track;this.radius_bounds=n.radius_bounds;this.genome=n.genome;this.chroms_layout=this._chroms_layout();this.data_bounds=[];this.scale=1;this.parent_elt=l.select(this.$el[0])},get_fill_color:function(){var n=this.track.get("config").get_value("block_color");if(!n){n=this.track.get("config").get_value("color")}return n},render:function(){var r=this.parent_elt;if(!r){console.log("no parent elt")}var q=this.chroms_layout,t=l.svg.arc().innerRadius(this.radius_bounds[0]).outerRadius(this.radius_bounds[1]),n=r.selectAll("g").data(q).enter().append("svg:g"),p=n.append("path").attr("d",t).attr("class","chrom-background").style("stroke",this.bg_stroke).style("fill",this.loading_bg_fill);p.append("title").text(function(v){return v.data.chrom});var o=this,s=o.track.get("data_manager"),u=(s?s.data_is_ready():true);$.when(u).then(function(){$.when(o._render_data(r)).then(function(){p.style("fill",o.bg_fill);o.render_labels()})})},render_labels:function(){},update_radius_bounds:function(o){this.radius_bounds=o;var n=l.svg.arc().innerRadius(this.radius_bounds[0]).outerRadius(this.radius_bounds[1]);this.parent_elt.selectAll("g>path.chrom-background").transition().duration(1000).attr("d",n);this._transition_chrom_data();this._transition_labels()},update_scale:function(q){var p=this.scale;this.scale=q;if(q<=p){return}var o=this,n=new m();this.parent_elt.selectAll("path.chrom-data").filter(function(s,r){return n.is_visible(this)}).each(function(x,t){var w=l.select(this),s=w.attr("chrom"),v=o.genome.get_chrom_region(s),u=o.track.get("data_manager"),r;if(!u.can_get_more_detailed_data(v)){return}r=o.track.get("data_manager").get_more_detailed_data(v,"Coverage",0,q);$.when(r).then(function(A){w.remove();o._update_data_bounds();var z=g.find(o.chroms_layout,function(B){return B.data.chrom===s});var y=o.get_fill_color();o._render_chrom_data(o.parent_elt,z,A).style("stroke",y).style("fill",y)})});return o},_transition_chrom_data:function(){var o=this.track,q=this.chroms_layout,n=this.parent_elt.selectAll("g>path.chrom-data"),r=n[0].length;if(r>0){var p=this;$.when(o.get("data_manager").get_genome_wide_data(this.genome)).then(function(t){var s=g.reject(g.map(t,function(u,v){var w=null,x=p._get_path_function(q[v],u);if(x){w=x(u.data)}return w}),function(u){return u===null});n.each(function(v,u){l.select(this).transition().duration(1000).attr("d",s[u])})})}},_transition_labels:function(){},_update_data_bounds:function(){var n=this.data_bounds;this.data_bounds=this.get_data_bounds(this.track.get("data_manager").get_genome_wide_data(this.genome));if(this.data_bounds[0]<n[0]||this.data_bounds[1]>n[1]){this._transition_chrom_data()}},_render_data:function(q){var p=this,o=this.chroms_layout,n=this.track,r=$.Deferred();$.when(n.get("data_manager").get_genome_wide_data(this.genome)).then(function(t){p.data_bounds=p.get_data_bounds(t);layout_and_data=g.zip(o,t),chroms_data_layout=g.map(layout_and_data,function(u){var v=u[0],w=u[1];return p._render_chrom_data(q,v,w)});var s=p.get_fill_color();p.parent_elt.selectAll("path.chrom-data").style("stroke",s).style("fill",s);r.resolve(q)});return r},_render_chrom_data:function(n,o,p){},_get_path_function:function(o,n){},_chroms_layout:function(){var o=this.genome.get_chroms_info(),q=l.layout.pie().value(function(s){return s.len}).sort(null),r=q(o),n=this.total_gap/o.length,p=g.map(r,function(u,t){var s=u.endAngle-n;u.endAngle=(s>u.startAngle?s:u.startAngle);return u});return p}});var b=k.extend({initialize:function(n){k.prototype.initialize.call(this,n);this.innerRadius=this.radius_bounds[0];this.radius_bounds[0]=this.radius_bounds[1];this.bg_stroke="fff";this.bg_fill="fff";this.min_arc_len=0.08},_render_data:function(p){var o=this,n=p.selectAll("g");n.selectAll("path").attr("id",function(t){return"label-"+t.data.chrom});n.append("svg:text").filter(function(t){return t.endAngle-t.startAngle>o.min_arc_len}).attr("text-anchor","middle").append("svg:textPath").attr("xlink:href",function(t){return"#label-"+t.data.chrom}).attr("startOffset","25%").attr("font-weight","bold").text(function(t){return t.data.chrom});var q=function(v){var t=(v.endAngle-v.startAngle)/v.value,u=l.range(0,v.value,25000000).map(function(w,x){return{radius:o.innerRadius,angle:w*t+v.startAngle,label:x===0?0:(x%3?null:o.formatNum(w))}});if(u.length<4){u[u.length-1].label=o.formatNum(Math.round((u[u.length-1].angle-v.startAngle)/t))}return u};var s=function(t){return t.angle>Math.PI?"rotate(180)translate(-16)":null};var r=g.filter(this.chroms_layout,function(t){return t.endAngle-t.startAngle>o.min_arc_len});this.drawTicks(this.parent_elt,r,q,s)}});g.extend(b.prototype,h);var f=k.extend({_quantile:function(o,n){o.sort(l.ascending);return l.quantile(o,n)},_render_chrom_data:function(n,q,o){var r=this._get_path_function(q,o);if(!r){return null}var p=n.datum(o.data),s=p.append("path").attr("class","chrom-data").attr("chrom",q.data.chrom).attr("d",r);return s},_get_path_function:function(q,p){if(typeof p==="string"||!p.data||p.data.length===0){return null}var n=l.scale.linear().domain(this.data_bounds).range(this.radius_bounds).clamp(true);var r=l.scale.linear().domain([0,p.data.length]).range([q.startAngle,q.endAngle]);var o=l.svg.line.radial().interpolate("linear").radius(function(s){return n(s[1])}).angle(function(t,s){return r(s)});return l.svg.area.radial().interpolate(o.interpolate()).innerRadius(n(0)).outerRadius(o.radius()).angle(o.angle())},render_labels:function(){var n=this,q=function(){return"rotate(90)"};var p=g.filter(this.chroms_layout,function(r){return r.endAngle-r.startAngle>0.08}),o=g.filter(p,function(s,r){return r%3===0});this.drawTicks(this.parent_elt,o,this._data_bounds_ticks_fn(),q,true)},_transition_labels:function(){if(this.data_bounds.length===0){return}var o=this,q=g.filter(this.chroms_layout,function(r){return r.endAngle-r.startAngle>0.08}),p=g.filter(q,function(s,r){return r%3===0}),n=g.flatten(g.map(p,function(r){return o._data_bounds_ticks_fn()(r)}));this.parent_elt.selectAll("g.tick").data(n).transition().attr("transform",function(r){return"rotate("+(r.angle*180/Math.PI-90)+")translate("+r.radius+",0)"})},_data_bounds_ticks_fn:function(){var n=this;visibleChroms=0;return function(o){return[{radius:n.radius_bounds[0],angle:o.startAngle,label:n.formatNum(n.data_bounds[0])},{radius:n.radius_bounds[1],angle:o.startAngle,label:n.formatNum(n.data_bounds[1])}]}},get_data_bounds:function(n){}});g.extend(f.prototype,h);var d=f.extend({get_data_bounds:function(o){var n=g.flatten(g.map(o,function(p){if(p){return g.map(p.data,function(q){return q[1]})}else{return 0}}));return[g.min(n),this._quantile(n,0.98)]}});var j=k.extend({render:function(){var n=this;$.when(n.track.get("data_manager").data_is_ready()).then(function(){$.when(n.track.get("data_manager").get_genome_wide_data(n.genome)).then(function(q){var p=[],o=n.genome.get_chroms_info();g.each(q,function(u,t){var r=o[t].chrom;var s=g.map(u.data,function(w){var v=n._get_region_angle(r,w[1]),x=n._get_region_angle(w[3],w[4]);return{source:{startAngle:v,endAngle:v+0.01},target:{startAngle:x,endAngle:x+0.01}}});p=p.concat(s)});n.parent_elt.append("g").attr("class","chord").selectAll("path").data(p).enter().append("path").style("fill",n.get_fill_color()).attr("d",l.svg.chord().radius(n.radius_bounds[0])).style("opacity",1)})})},update_radius_bounds:function(n){this.radius_bounds=n;this.parent_elt.selectAll("path").transition().attr("d",l.svg.chord().radius(this.radius_bounds[0]))},_get_region_angle:function(p,n){var o=g.find(this.chroms_layout,function(q){return q.data.chrom===p});return o.endAngle-((o.endAngle-o.startAngle)*(o.data.len-n)/o.data.len)}});var e=Backbone.View.extend({initialize:function(){var n=new i.Genome(galaxy_config.app.genome),o=new i.GenomeVisualization(galaxy_config.app.viz_config),q=new a({el:$("#center .unified-panel-body"),total_gap:2*Math.PI*0.1,genome:n,model:o,dataset_arc_height:25});q.render();$("#center .unified-panel-header-inner").append(galaxy_config.app.viz_config.title+" "+galaxy_config.app.viz_config.dbkey);var p=create_icon_buttons_menu([{icon_class:"plus-button",title:"Add tracks",on_click:function(){i.select_datasets(galaxy_config.root+"visualization/list_current_history_datasets",galaxy_config.root+"api/datasets",o.get("dbkey"),function(r){o.add_tracks(r)})}},{icon_class:"disk--arrow",title:"Save",on_click:function(){show_modal("Saving...","progress");var r=galaxy_config.app.viz_config;$.ajax({url:galaxy_config.root+"visualization/save",type:"POST",dataType:"json",data:{id:r.vis_id,title:r.title,dbkey:r.dbkey,type:"trackster",vis_json:JSON.stringify(r)}}).success(function(s){hide_modal();r.vis_id=s.vis_id;r.has_changes=false;window.history.pushState({},"",s.url+window.location.hash)}).error(function(){show_modal("Could Not Save","Could not save visualization. Please try again later.",{Close:hide_modal})})}},{icon_class:"cross-circle",title:"Close",on_click:function(){window.location=galaxy_config.root+"visualization/list"}}],{tooltip_config:{placement:"bottom"}});p.$el.attr("style","float: right");$("#center .unified-panel-header-inner").append(p.$el);$(".menu-button").tooltip({placement:"bottom"})}});return{GalaxyApp:e}});