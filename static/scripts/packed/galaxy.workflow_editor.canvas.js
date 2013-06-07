function Terminal(a){this.element=a;this.connectors=[]}$.extend(Terminal.prototype,{connect:function(a){this.connectors.push(a);if(this.node){this.node.changed()}},disconnect:function(a){this.connectors.splice($.inArray(a,this.connectors),1);if(this.node){this.node.changed()}},redraw:function(){$.each(this.connectors,function(a,b){b.redraw()})},destroy:function(){$.each(this.connectors.slice(),function(a,b){b.destroy()})}});function OutputTerminal(a,b){Terminal.call(this,a);this.datatypes=b}OutputTerminal.prototype=new Terminal();function InputTerminal(b,c,a){Terminal.call(this,b);this.datatypes=c;this.multiple=a}InputTerminal.prototype=new Terminal();$.extend(InputTerminal.prototype,{can_accept:function(a){if(this.connectors.length<1||this.multiple){for(var c in this.datatypes){var f=new Array();f=f.concat(a.datatypes);if(a.node.post_job_actions){for(var d in a.node.post_job_actions){var g=a.node.post_job_actions[d];if(g.action_type=="ChangeDatatypeAction"&&(g.output_name==""||g.output_name==a.name)&&g.action_arguments){f.push(g.action_arguments.newtype)}}}for(var b in f){if(f[b]=="input"||issubtype(f[b],this.datatypes[c])){return true}}}}return false}});function Connector(b,a){this.canvas=null;this.dragging=false;this.inner_color="#FFFFFF";this.outer_color="#D8B365";if(b&&a){this.connect(b,a)}}$.extend(Connector.prototype,{connect:function(b,a){this.handle1=b;if(this.handle1){this.handle1.connect(this)}this.handle2=a;if(this.handle2){this.handle2.connect(this)}},destroy:function(){if(this.handle1){this.handle1.disconnect(this)}if(this.handle2){this.handle2.disconnect(this)}$(this.canvas).remove()},redraw:function(){var d=$("#canvas-container");if(!this.canvas){this.canvas=document.createElement("canvas");if(window.G_vmlCanvasManager){G_vmlCanvasManager.initElement(this.canvas)}d.append($(this.canvas));if(this.dragging){this.canvas.style.zIndex="300"}}var n=function(c){return $(c).offset().left-d.offset().left};var i=function(c){return $(c).offset().top-d.offset().top};if(!this.handle1||!this.handle2){return}var h=n(this.handle1.element)+5;var g=i(this.handle1.element)+5;var p=n(this.handle2.element)+5;var m=i(this.handle2.element)+5;var f=100;var k=Math.min(h,p);var a=Math.max(h,p);var j=Math.min(g,m);var t=Math.max(g,m);var b=Math.min(Math.max(Math.abs(t-j)/2,100),300);var o=k-f;var s=j-f;var q=a-k+2*f;var l=t-j+2*f;this.canvas.style.left=o+"px";this.canvas.style.top=s+"px";this.canvas.setAttribute("width",q);this.canvas.setAttribute("height",l);h-=o;g-=s;p-=o;m-=s;var r=this.canvas.getContext("2d");r.lineCap="round";r.strokeStyle=this.outer_color;r.lineWidth=7;r.beginPath();r.moveTo(h,g);r.bezierCurveTo(h+b,g,p-b,m,p,m);r.stroke();r.strokeStyle=this.inner_color;r.lineWidth=5;r.beginPath();r.moveTo(h,g);r.bezierCurveTo(h+b,g,p-b,m,p,m);r.stroke()}});function Node(a){this.element=a;this.input_terminals={};this.output_terminals={};this.tool_errors={}}$.extend(Node.prototype,{enable_input_terminal:function(f,b,c,a){var d=this;$(f).each(function(){var g=this.terminal=new InputTerminal(this,c,a);g.node=d;g.name=b;$(this).bind("dropinit",function(h,i){return $(i.drag).hasClass("output-terminal")&&g.can_accept(i.drag.terminal)}).bind("dropstart",function(h,i){if(i.proxy.terminal){i.proxy.terminal.connectors[0].inner_color="#BBFFBB"}}).bind("dropend",function(h,i){if(i.proxy.terminal){i.proxy.terminal.connectors[0].inner_color="#FFFFFF"}}).bind("drop",function(h,i){(new Connector(i.drag.terminal,g)).redraw()}).bind("hover",function(){if(g.connectors.length>0){var h=$("<div class='callout'></div>").css({display:"none"}).appendTo("body").append($("<div class='buttons'></div>").append($("<img/>").attr("src",galaxy_paths.attributes.image_path+"/delete_icon.png").click(function(){$.each(g.connectors,function(j,i){if(i){i.destroy()}});h.remove()}))).bind("mouseleave",function(){$(this).remove()});h.css({top:$(this).offset().top-2,left:$(this).offset().left-h.width(),"padding-right":$(this).width()}).show()}});d.input_terminals[b]=g})},enable_output_terminal:function(d,a,b){var c=this;$(d).each(function(){var g=this;var f=this.terminal=new OutputTerminal(this,b);f.node=c;f.name=a;$(this).bind("dragstart",function(j,k){$(k.available).addClass("input-terminal-active");workflow.check_changes_in_active_form();var i=$('<div class="drag-terminal" style="position: absolute;"></div>').appendTo("#canvas-container").get(0);i.terminal=new OutputTerminal(i);var l=new Connector();l.dragging=true;l.connect(this.terminal,i.terminal);return i}).bind("drag",function(i,j){var h=function(){var l=$(j.proxy).offsetParent().offset(),k=j.offsetX-l.left,m=j.offsetY-l.top;$(j.proxy).css({left:k,top:m});j.proxy.terminal.redraw();canvas_manager.update_viewport_overlay()};h();$("#canvas-container").get(0).scroll_panel.test(i,h)}).bind("dragend",function(h,i){i.proxy.terminal.connectors[0].destroy();$(i.proxy).remove();$(i.available).removeClass("input-terminal-active");$("#canvas-container").get(0).scroll_panel.stop()});c.output_terminals[a]=f})},redraw:function(){$.each(this.input_terminals,function(a,b){b.redraw()});$.each(this.output_terminals,function(a,b){b.redraw()})},destroy:function(){$.each(this.input_terminals,function(a,b){b.destroy()});$.each(this.output_terminals,function(a,b){b.destroy()});workflow.remove_node(this);$(this.element).remove()},make_active:function(){$(this.element).addClass("toolForm-active")},make_inactive:function(){var a=this.element.get(0);(function(b){b.removeChild(a);b.appendChild(a)})(a.parentNode);$(a).removeClass("toolForm-active")},init_field_data:function(h){var g=this.element;if(h.type){this.type=h.type}this.name=h.name;this.form_html=h.form_html;this.tool_state=h.tool_state;this.tool_errors=h.tool_errors;this.tooltip=h.tooltip?h.tooltip:"";this.annotation=h.annotation;this.post_job_actions=h.post_job_actions?h.post_job_actions:{};this.workflow_outputs=h.workflow_outputs?h.workflow_outputs:[];if(this.tool_errors){g.addClass("tool-node-error")}else{g.removeClass("tool-node-error")}var d=this;var c=Math.max(150,g.width());var a=g.find(".toolFormBody");a.find("div").remove();var i=$("<div class='inputs'></div>").appendTo(a);$.each(h.data_inputs,function(k,f){var j=$("<div class='terminal input-terminal'></div>");d.enable_input_terminal(j,f.name,f.extensions,f.multiple);var b=$("<div class='form-row dataRow input-data-row' name='"+f.name+"'>"+f.label+"</div>");b.css({position:"absolute",left:-1000,top:-1000,display:"none"});$("body").append(b);c=Math.max(c,b.outerWidth());b.css({position:"",left:"",top:"",display:""});b.remove();i.append(b.prepend(j))});if((h.data_inputs.length>0)&&(h.data_outputs.length>0)){a.append($("<div class='rule'></div>"))}$.each(h.data_outputs,function(k,b){var j=$("<div class='terminal output-terminal'></div>");d.enable_output_terminal(j,b.name,b.extensions);var f=b.name;if(b.extensions.indexOf("input")<0){f=f+" ("+b.extensions.join(", ")+")"}var m=$("<div class='form-row dataRow'>"+f+"</div>");if(d.type=="tool"){var l=$("<div class='callout "+f+"'></div>").css({display:"none"}).append($("<div class='buttons'></div>").append($("<img/>").attr("src",galaxy_paths.attributes.image_path+"/fugue/asterisk-small-outline.png").click(function(){if($.inArray(b.name,d.workflow_outputs)!=-1){d.workflow_outputs.splice($.inArray(b.name,d.workflow_outputs),1);l.find("img").attr("src",galaxy_paths.attributes.image_path+"/fugue/asterisk-small-outline.png")}else{d.workflow_outputs.push(b.name);l.find("img").attr("src",galaxy_paths.attributes.image_path+"/fugue/asterisk-small.png")}workflow.has_changes=true;canvas_manager.draw_overview()}))).tooltip({delay:500,title:"Flag this as a workflow output.  All non-flagged outputs will be hidden."});l.css({top:"50%",margin:"-8px 0px 0px 0px",right:8});l.show();m.append(l);if($.inArray(b.name,d.workflow_outputs)===-1){l.find("img").attr("src",galaxy_paths.attributes.image_path+"/fugue/asterisk-small-outline.png")}else{l.find("img").attr("src",galaxy_paths.attributes.image_path+"/fugue/asterisk-small.png")}m.hover(function(){l.find("img").attr("src",galaxy_paths.attributes.image_path+"/fugue/asterisk-small-yellow.png")},function(){if($.inArray(b.name,d.workflow_outputs)===-1){l.find("img").attr("src",galaxy_paths.attributes.image_path+"/fugue/asterisk-small-outline.png")}else{l.find("img").attr("src",galaxy_paths.attributes.image_path+"/fugue/asterisk-small.png")}})}m.css({position:"absolute",left:-1000,top:-1000,display:"none"});$("body").append(m);c=Math.max(c,m.outerWidth()+17);m.css({position:"",left:"",top:"",display:""});m.detach();a.append(m.append(j))});g.css("width",Math.min(250,Math.max(g.width(),c)));workflow.node_changed(this)},update_field_data:function(f){var c=$(this.element),d=this;this.tool_state=f.tool_state;this.form_html=f.form_html;this.tool_errors=f.tool_errors;this.annotation=f.annotation;var g=$.parseJSON(f.post_job_actions);this.post_job_actions=g?g:{};if(this.tool_errors){c.addClass("tool-node-error")}else{c.removeClass("tool-node-error")}var h=c.find("div.inputs");var b=$("<div class='inputs'></div>");var a=h.find("div.input-data-row");$.each(f.data_inputs,function(l,j){var k=$("<div class='terminal input-terminal'></div>");d.enable_input_terminal(k,j.name,j.extensions,j.multiple);h.find("div[name='"+j.name+"']").each(function(){$(this).find(".input-terminal").each(function(){var i=this.terminal.connectors[0];if(i){k[0].terminal.connectors[0]=i;i.handle2=k[0].terminal}});$(this).remove()});b.append($("<div class='form-row dataRow input-data-row' name='"+j.name+"'>"+j.label+"</div>").prepend(k))});h.replaceWith(b);h.find("div.input-data-row > .terminal").each(function(){this.terminal.destroy()});this.changed();this.redraw()},error:function(d){var a=$(this.element).find(".toolFormBody");a.find("div").remove();var c="<div style='color: red; text-style: italic;'>"+d+"</div>";this.form_html=c;a.html(c);workflow.node_changed(this)},changed:function(){workflow.node_changed(this)}});function Workflow(a){this.canvas_container=a;this.id_counter=0;this.nodes={};this.name=null;this.has_changes=false;this.active_form_has_changes=false}$.extend(Workflow.prototype,{add_node:function(a){a.id=this.id_counter;a.element.attr("id","wf-node-step-"+a.id);this.id_counter++;this.nodes[a.id]=a;this.has_changes=true;a.workflow=this},remove_node:function(a){if(this.active_node==a){this.clear_active_node()}delete this.nodes[a.id];this.has_changes=true},remove_all:function(){wf=this;$.each(this.nodes,function(b,a){a.destroy();wf.remove_node(a)})},rectify_workflow_outputs:function(){var b=false;var a=false;$.each(this.nodes,function(c,d){if(d.workflow_outputs&&d.workflow_outputs.length>0){b=true}$.each(d.post_job_actions,function(g,f){if(f.action_type==="HideDatasetAction"){a=true}})});if(b!==false||a!==false){$.each(this.nodes,function(c,g){if(g.type==="tool"){var f=false;if(g.post_job_actions==null){g.post_job_actions={};f=true}var d=[];$.each(g.post_job_actions,function(i,h){if(h.action_type=="HideDatasetAction"){d.push(i)}});if(d.length>0){$.each(d,function(h,j){f=true;delete g.post_job_actions[j]})}if(b){$.each(g.output_terminals,function(i,j){var h=true;$.each(g.workflow_outputs,function(l,m){if(j.name===m){h=false}});if(h===true){f=true;var k={action_type:"HideDatasetAction",output_name:j.name,action_arguments:{}};g.post_job_actions["HideDatasetAction"+j.name]=null;g.post_job_actions["HideDatasetAction"+j.name]=k}})}if(workflow.active_node==g&&f===true){workflow.reload_active_node()}}})}},to_simple:function(){var a={};$.each(this.nodes,function(c,f){var g={};$.each(f.input_terminals,function(i,j){g[j.name]=null;var h=[];$.each(j.connectors,function(k,l){h[k]={id:l.handle1.node.id,output_name:l.handle1.name};g[j.name]=h})});var b={};if(f.post_job_actions){$.each(f.post_job_actions,function(j,h){var k={action_type:h.action_type,output_name:h.output_name,action_arguments:h.action_arguments};b[h.action_type+h.output_name]=null;b[h.action_type+h.output_name]=k})}if(!f.workflow_outputs){f.workflow_outputs=[]}var d={id:f.id,type:f.type,tool_id:f.tool_id,tool_state:f.tool_state,tool_errors:f.tool_errors,input_connections:g,position:$(f.element).position(),annotation:f.annotation,post_job_actions:f.post_job_actions,workflow_outputs:f.workflow_outputs};a[f.id]=d});return{steps:a}},from_simple:function(b){wf=this;var c=0;wf.name=b.name;var a=false;$.each(b.steps,function(g,f){var d=prebuild_node("tool",f.name,f.tool_id);d.init_field_data(f);if(f.position){d.element.css({top:f.position.top,left:f.position.left})}d.id=f.id;wf.nodes[d.id]=d;c=Math.max(c,parseInt(g));if(!a&&d.type==="tool"){if(d.workflow_outputs.length>0){a=true}else{$.each(d.post_job_actions,function(i,h){if(h.action_type==="HideDatasetAction"){a=true}})}}});wf.id_counter=c+1;$.each(b.steps,function(g,f){var d=wf.nodes[g];$.each(f.input_connections,function(i,h){if(h){if($.isArray(h)){$.each(h,function(m,k){var n=wf.nodes[k.id];var o=new Connector();o.connect(n.output_terminals[k.output_name],d.input_terminals[i]);o.redraw()})}else{var j=wf.nodes[h.id];var l=new Connector();l.connect(j.output_terminals[h.output_name],d.input_terminals[i]);l.redraw()}}});if(a&&d.type==="tool"){$.each(d.output_terminals,function(h,i){if(d.post_job_actions["HideDatasetAction"+i.name]===undefined){d.workflow_outputs.push(i.name);callout=$(d.element).find(".callout."+i.name);callout.find("img").attr("src",galaxy_paths.attributes.image_path+"/fugue/asterisk-small.png");workflow.has_changes=true}})}})},check_changes_in_active_form:function(){if(this.active_form_has_changes){this.has_changes=true;$("#right-content").find("form").submit();this.active_form_has_changes=false}},reload_active_node:function(){if(this.active_node){var a=this.active_node;this.clear_active_node();this.activate_node(a)}},clear_active_node:function(){if(this.active_node){this.active_node.make_inactive();this.active_node=null}parent.show_form_for_tool("<div>No node selected</div>")},activate_node:function(a){if(this.active_node!=a){this.check_changes_in_active_form();this.clear_active_node();parent.show_form_for_tool(a.form_html+a.tooltip,a);a.make_active();this.active_node=a}},node_changed:function(a){this.has_changes=true;if(this.active_node==a){this.check_changes_in_active_form();parent.show_form_for_tool(a.form_html+a.tooltip,a)}},layout:function(){this.check_changes_in_active_form();this.has_changes=true;var i={};var b={};$.each(this.nodes,function(l,k){if(i[l]===undefined){i[l]=0}if(b[l]===undefined){b[l]=[]}});$.each(this.nodes,function(l,k){$.each(k.input_terminals,function(m,n){$.each(n.connectors,function(p,q){var o=q.handle1.node;i[k.id]+=1;b[o.id].push(k.id)})})});node_ids_by_level=[];while(true){level_parents=[];for(var a in i){if(i[a]==0){level_parents.push(a)}}if(level_parents.length==0){break}node_ids_by_level.push(level_parents);for(var f in level_parents){var j=level_parents[f];delete i[j];for(var g in b[j]){i[b[j][g]]-=1}}}if(i.length){return}var d=this.nodes;var h=80;v_pad=30;var c=h;$.each(node_ids_by_level,function(k,l){l.sort(function(p,o){return $(d[p].element).position().top-$(d[o].element).position().top});var m=0;var n=v_pad;$.each(l,function(o,r){var q=d[r];var p=$(q.element);$(p).css({top:n,left:c});m=Math.max(m,$(p).width());n+=$(p).height()+v_pad});c+=m+h});$.each(d,function(k,l){l.redraw()})},bounds_for_all_nodes:function(){var d=Infinity,b=-Infinity,c=Infinity,a=-Infinity,f;$.each(this.nodes,function(h,g){e=$(g.element);f=e.position();d=Math.min(d,f.left);b=Math.max(b,f.left+e.width());c=Math.min(c,f.top);a=Math.max(a,f.top+e.width())});return{xmin:d,xmax:b,ymin:c,ymax:a}},fit_canvas_to_nodes:function(){var a=this.bounds_for_all_nodes();var f=this.canvas_container.position();var i=this.canvas_container.parent();var d=fix_delta(a.xmin,100);var h=fix_delta(a.ymin,100);d=Math.max(d,f.left);h=Math.max(h,f.top);var c=f.left-d;var g=f.top-h;var b=round_up(a.xmax+100,100)+d;var j=round_up(a.ymax+100,100)+h;b=Math.max(b,-c+i.width());j=Math.max(j,-g+i.height());this.canvas_container.css({left:c,top:g,width:b,height:j});this.canvas_container.children().each(function(){var k=$(this).position();$(this).css("left",k.left+d);$(this).css("top",k.top+h)})}});function fix_delta(a,b){if(a<b||a>3*b){new_pos=(Math.ceil(((a%b))/b)+1)*b;return(-(a-new_pos))}return 0}function round_up(a,b){return Math.ceil(a/b)*b}function prebuild_node(l,j,r){var i=$("<div class='toolForm toolFormInCanvas'></div>");var g=new Node(i);g.type=l;if(l=="tool"){g.tool_id=r}var n=$("<div class='toolFormTitle unselectable'>"+j+"</div>");i.append(n);i.css("left",$(window).scrollLeft()+20);i.css("top",$(window).scrollTop()+20);var m=$("<div class='toolFormBody'></div>");var h="<div><img height='16' align='middle' src='"+galaxy_paths.attributes.image_path+"/loading_small_white_bg.gif'/> loading tool info...</div>";m.append(h);g.form_html=h;i.append(m);var k=$("<div class='buttons' style='float: right;'></div>");k.append($("<img/>").attr("src",galaxy_paths.attributes.image_path+"/delete_icon.png").click(function(b){g.destroy()}).hover(function(){$(this).attr("src",galaxy_paths.attributes.image_path+"/delete_icon_dark.png")},function(){$(this).attr("src",galaxy_paths.attributes.image_path+"/delete_icon.png")}));i.appendTo("#canvas-container");var d=$("#canvas-container").position();var c=$("#canvas-container").parent();var a=i.width();var q=i.height();i.css({left:(-d.left)+(c.width()/2)-(a/2),top:(-d.top)+(c.height()/2)-(q/2)});k.prependTo(n);a+=(k.width()+10);i.css("width",a);$(i).bind("dragstart",function(){workflow.activate_node(g)}).bind("dragend",function(){workflow.node_changed(this);workflow.fit_canvas_to_nodes();canvas_manager.draw_overview()}).bind("dragclickonly",function(){workflow.activate_node(g)}).bind("drag",function(o,p){var f=$(this).offsetParent().offset(),b=p.offsetX-f.left,s=p.offsetY-f.top;$(this).css({left:b,top:s});$(this).find(".terminal").each(function(){this.terminal.redraw()})});return g}var ext_to_type=null;var type_to_type=null;function issubtype(b,a){b=ext_to_type[b];a=ext_to_type[a];return(type_to_type[b])&&(a in type_to_type[b])}function populate_datatype_info(a){ext_to_type=a.ext_to_class_name;type_to_type=a.class_to_classes}function ScrollPanel(a){this.panel=a}$.extend(ScrollPanel.prototype,{test:function(v,d){clearTimeout(this.timeout);var k=v.pageX,j=v.pageY,l=$(this.panel),c=l.position(),b=l.width(),i=l.height(),w=l.parent(),s=w.width(),a=w.height(),r=w.offset(),p=r.left,m=r.top,A=p+w.width(),u=m+w.height(),B=-(b-(s/2)),z=-(i-(a/2)),g=(s/2),f=(a/2),h=false,q=5,o=23;if(k-q<p){if(c.left<g){var n=Math.min(o,g-c.left);l.css("left",c.left+n);h=true}}else{if(k+q>A){if(c.left>B){var n=Math.min(o,c.left-B);l.css("left",c.left-n);h=true}}else{if(j-q<m){if(c.top<f){var n=Math.min(o,f-c.top);l.css("top",c.top+n);h=true}}else{if(j+q>u){if(c.top>z){var n=Math.min(o,c.top-B);l.css("top",(c.top-n)+"px");h=true}}}}}if(h){d();var l=this;this.timeout=setTimeout(function(){l.test(v,d)},50)}},stop:function(b,a){clearTimeout(this.timeout)}});function CanvasManager(b,a){this.cv=b;this.cc=this.cv.find("#canvas-container");this.oc=a.find("#overview-canvas");this.ov=a.find("#overview-viewport");this.init_drag()}$.extend(CanvasManager.prototype,{init_drag:function(){var b=this;var a=function(f,g){f=Math.min(f,b.cv.width()/2);f=Math.max(f,-b.cc.width()+b.cv.width()/2);g=Math.min(g,b.cv.height()/2);g=Math.max(g,-b.cc.height()+b.cv.height()/2);b.cc.css({left:f,top:g});b.update_viewport_overlay()};this.cc.each(function(){this.scroll_panel=new ScrollPanel(this)});var d,c;this.cv.bind("dragstart",function(){var g=$(this).offset();var f=b.cc.position();c=f.top-g.top;d=f.left-g.left}).bind("drag",function(f,g){a(g.offsetX+d,g.offsetY+c)}).bind("dragend",function(){workflow.fit_canvas_to_nodes();b.draw_overview()});this.ov.bind("drag",function(k,l){var h=b.cc.width(),n=b.cc.height(),m=b.oc.width(),j=b.oc.height(),f=$(this).offsetParent().offset(),i=l.offsetX-f.left,g=l.offsetY-f.top;a(-(i/m*h),-(g/j*n))}).bind("dragend",function(){workflow.fit_canvas_to_nodes();b.draw_overview()});$("#overview-border").bind("drag",function(g,i){var j=$(this).offsetParent();var h=j.offset();var f=Math.max(j.width()-(i.offsetX-h.left),j.height()-(i.offsetY-h.top));$(this).css({width:f,height:f});b.draw_overview()});$("#overview-border div").bind("drag",function(){})},update_viewport_overlay:function(){var b=this.cc,f=this.cv,a=this.oc,c=this.ov,d=b.width(),j=b.height(),i=a.width(),g=a.height(),h=b.position();c.css({left:-(h.left/d*i),top:-(h.top/j*g),width:(f.width()/d*i)-2,height:(f.height()/j*g)-2})},draw_overview:function(){var j=$("#overview-canvas"),m=j.parent().parent().width(),i=j.get(0).getContext("2d"),d=$("#canvas-container").width(),l=$("#canvas-container").height();var g,a,k,f;var h=this.cv.width();var b=this.cv.height();if(d<h&&l<b){k=d/h*m;f=(m-k)/2;g=l/b*m;a=(m-g)/2}else{if(d<l){a=0;g=m;k=Math.ceil(g*d/l);f=(m-k)/2}else{k=m;f=0;g=Math.ceil(k*l/d);a=(m-g)/2}}j.parent().css({left:f,top:a,width:k,height:g});j.attr("width",k);j.attr("height",g);$.each(workflow.nodes,function(t,q){i.fillStyle="#D2C099";i.strokeStyle="#D8B365";i.lineWidth=1;var s=$(q.element),n=s.position(),c=n.left/d*k,r=n.top/l*g,o=s.width()/d*k,p=s.height()/l*g;if(q.tool_errors){i.fillStyle="#FFCCCC";i.strokeStyle="#AA6666"}else{if(q.workflow_outputs!=undefined&&q.workflow_outputs.length>0){i.fillStyle="#E8A92D";i.strokeStyle="#E8A92D"}}i.fillRect(c,r,o,p);i.strokeRect(c,r,o,p)});this.update_viewport_overlay()}});