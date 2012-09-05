var UserMenuBase=Backbone.View.extend({className:"UserMenuBase",isAcceptableValue:function(e,c,a){var b=this,f=e.val(),g=e.attr("displayLabel")||e.attr("id").replace("phyloViz","");function d(h){return !isNaN(parseFloat(h))&&isFinite(h)}if(!d(f)){alert(g+" is not a number!");return false}if(f>a){alert(g+" is too large.");return false}else{if(f<c){alert(g+" is too small.");return false}}return true},hasIllegalJsonCharacters:function(a){if(a.val().search(/"|'|\\/)!==-1){alert("Named fields cannot contain these illegal characters: double quote(\"), single guote('), or back slash(\\). ");return true}return false}});function PhyloTreeLayout(){var j=this,e=d3.layout.hierarchy().sort(null).value(null),i=360,d="Linear",h=18,f=200,g=0,c=0.5,a=50;j.leafHeight=function(k){if(typeof k==="undefined"){return h}else{h=k;return j}};j.layoutMode=function(k){if(typeof k==="undefined"){return d}else{d=k;return j}};j.layoutAngle=function(k){if(typeof k==="undefined"){return i}if(isNaN(k)||k<0||k>360){return j}else{i=k;return j}};j.separation=function(k){if(typeof k==="undefined"){return f}else{f=k;return j}};j.links=function(k){return d3.layout.tree().links(k)};j.nodes=function(n,l){var m=e.call(j,n,l),k=[],p=0,o=0;m.forEach(function(q){var r=q.data;r.depth=q.depth;p=r.depth>p?r.depth:p;k.push(r)});k.forEach(function(q){if(!q.children){o+=1;q.depth=p}});h=d==="Circular"?i/o:h;g=0;b(k[0],p,h,null);return k};function b(o,q,n,m){var l=o.children,k=0;var p=o.dist||c;p=p>1?1:p;o.dist=p;if(m!==null){o.y0=m.y0+p*f}else{o.y0=a}if(!l){o.x0=g++*n}else{l.forEach(function(r){r.parent=o;k+=b(r,q,n,o)});o.x0=k/l.length}o.x=o.x0;o.y=o.y0;return o.x0}return j}var PhyloTree=Visualization.extend({defaults:{layout:"Linear",separation:250,leafHeight:18,type:"phyloviz",title:"Title",scaleFactor:1,translate:[0,0],fontSize:12,selectedNode:null,nodeAttrChangedTime:0},root:{},toggle:function(a){if(typeof a==="undefined"){return}if(a.children){a._children=a.children;a.children=null}else{a.children=a._children;a._children=null}},toggleAll:function(a){if(a.children&&a.children.length!==0){a.children.forEach(this.toggleAll);toggle(a)}},getData:function(){return this.root},save:function(){var a=this.root;b(a);this.set("root",a);function b(d){delete d.parent;if(d._selected){delete d._selected}d.children?d.children.forEach(b):0;d._children?d._children.forEach(b):0}var c=jQuery.extend(true,{},this.attributes);c.selectedNode=null;show_message("Saving to Galaxy","progress");return $.ajax({url:this.url(),type:"POST",dataType:"json",data:{vis_json:JSON.stringify(c)},success:function(d){var e=d.url.split("id=")[1].split("&")[0],f="/phyloviz/visualization?id="+e;window.history.pushState({},"",f+window.location.hash);hide_modal()}})}});var PhylovizLayoutBase=Backbone.View.extend({defaults:{nodeRadius:4.5},stdInit:function(b){var a=this;a.model.on("change:separation change:leafHeight change:fontSize change:nodeAttrChangedTime",a.updateAndRender,a);a.vis=b.vis;a.i=0;a.maxDepth=-1;a.width=b.width;a.height=b.height},updateAndRender:function(c){var b=d3.select(".vis"),a=this;c=c||a.model.root;a.renderNodes(c);a.renderLinks(c);a.addTooltips()},renderLinks:function(a){var j=this;var b=j.diagonal;var c=j.duration;var e=j.layoutMode;var g=j.vis.selectAll("g.completeLink").data(j.tree.links(j.nodes),function(k){return k.target.id});var i=function(k){k.pos0=k.source.y0+" "+k.source.x0;k.pos1=k.source.y0+" "+k.target.x0;k.pos2=k.target.y0+" "+k.target.x0};var h=g.enter().insert("svg:g","g.node").attr("class","completeLink");h.append("svg:path").attr("class","link").attr("d",function(k){i(k);return"M "+k.pos0+" L "+k.pos1});var f=g.transition().duration(500);f.select("path.link").attr("d",function(k){i(k);return"M "+k.pos0+" L "+k.pos1+" L "+k.pos2});var d=g.exit().remove()},selectNode:function(b){var a=this;d3.selectAll("g.node").classed("selectedHighlight",function(c){if(b.id===c.id){if(b._selected){delete b._selected;return false}else{b._selected=true;return true}}return false});a.model.set("selectedNode",b);$("#phyloVizSelectedNodeName").val(b.name);$("#phyloVizSelectedNodeDist").val(b.dist);$("#phyloVizSelectedNodeAnnotation").val(b.annotation||"")},addTooltips:function(){$(".bs-tooltip").remove();$(".node").attr("data-original-title",function(){var b=this.__data__,a=b.annotation||"None";return b?(b.name?b.name+"<br/>":"")+"Dist: "+b.dist+" <br/>Annotation: "+a:""}).tooltip({placement:"top",trigger:"hover"})}});var PhylovizLinearView=PhylovizLayoutBase.extend({initialize:function(b){var a=this;a.margins=b.margins;a.layoutMode="Linear";a.stdInit(b);a.layout();a.updateAndRender(a.model.root)},layout:function(){var a=this;a.tree=new PhyloTreeLayout().layoutMode("Linear");a.diagonal=d3.svg.diagonal().projection(function(b){return[b.y,b.x]})},renderNodes:function(a){var h=this,i=h.model.get("fontSize")+"px";h.tree.separation(h.model.get("separation")).leafHeight(h.model.get("leafHeight"));var d=500,b=h.tree.separation(h.model.get("separation")).nodes(h.model.root);var c=h.vis.selectAll("g.node").data(b,function(j){return j.name+j.id||(j.id=++h.i)});h.nodes=b;h.duration=d;var e=c.enter().append("svg:g").attr("class","node").on("dblclick",function(){d3.event.stopPropagation()}).on("click",function(j){if(d3.event.altKey){h.selectNode(j)}else{if(j.children&&j.children.length===0){return}h.model.toggle(j);h.updateAndRender(j)}});e.attr("transform",function(j){return"translate("+a.y0+","+a.x0+")"});e.append("svg:circle").attr("r",0.000001).style("fill",function(j){return j._children?"lightsteelblue":"#fff"});e.append("svg:text").attr("class","nodeLabel").attr("x",function(j){return j.children||j._children?-10:10}).attr("dy",".35em").attr("text-anchor",function(j){return j.children||j._children?"end":"start"}).style("fill-opacity",0.000001);var f=c.transition().duration(d);f.attr("transform",function(j){return"translate("+j.y+","+j.x+")"});f.select("circle").attr("r",h.defaults.nodeRadius).style("fill",function(j){return j._children?"lightsteelblue":"#fff"});f.select("text").style("fill-opacity",1).style("font-size",i).text(function(j){return j.name});var g=c.exit().transition().duration(d).remove();g.select("circle").attr("r",0.000001);g.select("text").style("fill-opacity",0.000001);b.forEach(function(j){j.x0=j.x;j.y0=j.y})}});var PhylovizView=Backbone.View.extend({className:"phyloviz",initialize:function(b){var a=this;a.MIN_SCALE=0.05;a.MAX_SCALE=5;a.MAX_DISPLACEMENT=500;a.margins=[10,60,10,80];a.width=$("#PhyloViz").width();a.height=$("#PhyloViz").height();a.radius=a.width;a.data=b.data;$(window).resize(function(){a.width=$("#PhyloViz").width();a.height=$("#PhyloViz").height();a.render()});a.phyloTree=new PhyloTree(b.config);a.phyloTree.root=a.data;a.zoomFunc=d3.behavior.zoom().scaleExtent([a.MIN_SCALE,a.MAX_SCALE]);a.zoomFunc.translate(a.phyloTree.get("translate"));a.zoomFunc.scale(a.phyloTree.get("scaleFactor"));a.navMenu=new HeaderButtons(a);a.settingsMenu=new SettingsMenu({phyloTree:a.phyloTree});a.nodeSelectionView=new NodeSelectionView({phyloTree:a.phyloTree});a.search=new PhyloVizSearch();setTimeout(function(){a.zoomAndPan()},1000)},render:function(){var b=this;$("#PhyloViz").empty();b.mainSVG=d3.select("#PhyloViz").append("svg:svg").attr("width",b.width).attr("height",b.height).attr("pointer-events","all").call(b.zoomFunc.on("zoom",function(){b.zoomAndPan()}));b.boundingRect=b.mainSVG.append("svg:rect").attr("class","boundingRect").attr("width",b.width).attr("height",b.height).attr("stroke","black").attr("fill","white");b.vis=b.mainSVG.append("svg:g").attr("class","vis");b.layoutOptions={model:b.phyloTree,width:b.width,height:b.height,vis:b.vis,margins:b.margins};$("#title").text("Phylogenetic Tree from "+b.phyloTree.get("title")+":");var a=new PhylovizLinearView(b.layoutOptions)},zoomAndPan:function(a){if(typeof a!=="undefined"){var g=a.zoom,c=a.translate}var j=this,e=j.zoomFunc.scale(),i=j.zoomFunc.translate(),f="",h="";switch(g){case"reset":e=1;i=[0,0];break;case"+":e*=1.1;break;case"-":e*=0.9;break;default:if(typeof g==="number"){e=g}else{if(d3.event!==null){e=d3.event.scale}}}if(e<j.MIN_SCALE||e>j.MAX_SCALE){return}j.zoomFunc.scale(e);f="translate("+j.margins[3]+","+j.margins[0]+") scale("+e+")";if(d3.event!==null){h="translate("+d3.event.translate+")"}else{if(typeof c!=="undefined"){var d=c.split(",")[0];var b=c.split(",")[1];if(!isNaN(d)&&!isNaN(b)){i=[i[0]+parseFloat(d),i[1]+parseFloat(b)]}}j.zoomFunc.translate(i);h="translate("+i+")"}j.phyloTree.set("scaleFactor",e);j.phyloTree.set("translate",i);j.vis.attr("transform",h+f)},reloadViz:function(){var b=this,d=$("#phylovizNexSelector :selected").val(),a=b.phyloTree.get("dataset_id"),c="phyloviz/getJsonData?dataset_id="+a+"&treeIndex="+String(d);$.getJSON(c,function(e){window.initPhyloViz(e.data,e.config)})}});var HeaderButtons=Backbone.View.extend({initialize:function(b){var a=this;a.phylovizView=b;$("#panelHeaderRightBtns").empty();$("#phyloVizNavBtns").empty();$("#phylovizNexSelector").off();a.initNavBtns();a.initRightHeaderBtns();$("#phylovizNexSelector").off().on("change",function(){a.phylovizView.reloadViz()})},initRightHeaderBtns:function(){var a=this;rightMenu=create_icon_buttons_menu([{icon_class:"gear",title:"PhyloViz Settings",on_click:function(){$("#SettingsMenu").show();a.settingsMenu.updateUI()}},{icon_class:"disk",title:"Save visualization",on_click:function(){var b=$("#phylovizNexSelector option:selected").text();if(b){a.phylovizView.phyloTree.set("title",b)}a.phylovizView.phyloTree.save()}},{icon_class:"chevron-expand",title:"Search / Edit Nodes",on_click:function(){$("#nodeSelectionView").show()}},{icon_class:"information",title:"Phyloviz Help",on_click:function(){window.open("http://wiki.g2.bx.psu.edu/Learn/Visualization/PhylogeneticTree")}}],{tooltip_config:{placement:"bottom"}});$("#panelHeaderRightBtns").append(rightMenu.$el)},initNavBtns:function(){var a=this,b=create_icon_buttons_menu([{icon_class:"zoom-in",title:"Zoom in",on_click:function(){a.phylovizView.zoomAndPan({zoom:"+"})}},{icon_class:"zoom-out",title:"Zoom out",on_click:function(){a.phylovizView.zoomAndPan({zoom:"-"})}},{icon_class:"arrow-circle",title:"Reset Zoom/Pan",on_click:function(){a.phylovizView.zoomAndPan({zoom:"reset"})}}],{tooltip_config:{placement:"bottom"}});$("#phyloVizNavBtns").append(b.$el)}});var SettingsMenu=UserMenuBase.extend({className:"Settings",initialize:function(b){var a=this;a.phyloTree=b.phyloTree;a.el=$("#SettingsMenu");a.inputs={separation:$("#phyloVizTreeSeparation"),leafHeight:$("#phyloVizTreeLeafHeight"),fontSize:$("#phyloVizTreeFontSize")};$("#settingsCloseBtn").off().on("click",function(){a.el.hide()});$("#phylovizResetSettingsBtn").off().on("click",function(){a.resetToDefaults()});$("#phylovizApplySettingsBtn").off().on("click",function(){a.apply()})},apply:function(){var a=this;if(!a.isAcceptableValue(a.inputs.separation,50,2500)||!a.isAcceptableValue(a.inputs.leafHeight,5,30)||!a.isAcceptableValue(a.inputs.fontSize,5,20)){return}$.each(a.inputs,function(b,c){a.phyloTree.set(b,c.val())})},updateUI:function(){var a=this;$.each(a.inputs,function(b,c){c.val(a.phyloTree.get(b))})},resetToDefaults:function(){$(".bs-tooltip").remove();var a=this;$.each(a.phyloTree.defaults,function(b,c){a.phyloTree.set(b,c)});a.updateUI()},render:function(){}});var NodeSelectionView=UserMenuBase.extend({className:"Settings",initialize:function(b){var a=this;a.el=$("#nodeSelectionView");a.phyloTree=b.phyloTree;a.UI={enableEdit:$("#phylovizEditNodesCheck"),saveChanges:$("#phylovizNodeSaveChanges"),cancelChanges:$("#phylovizNodeCancelChanges"),name:$("#phyloVizSelectedNodeName"),dist:$("#phyloVizSelectedNodeDist"),annotation:$("#phyloVizSelectedNodeAnnotation")};a.valuesOfConcern={name:null,dist:null,annotation:null};$("#nodeSelCloseBtn").off().on("click",function(){a.el.hide()});a.UI.saveChanges.off().on("click",function(){a.updateNodes()});a.UI.cancelChanges.off().on("click",function(){a.cancelChanges()});(function(c){c.fn.enable=function(d){return c(this).each(function(){if(d){c(this).removeAttr("disabled")}else{c(this).attr("disabled","disabled")}})}})(jQuery);a.UI.enableEdit.off().on("click",function(){a.toggleUI()})},toggleUI:function(){var a=this,b=a.UI.enableEdit.is(":checked");!b?a.cancelChanges():"";$.each(a.valuesOfConcern,function(c,d){a.UI[c].enable(b)});if(b){a.UI.saveChanges.show();a.UI.cancelChanges.show()}else{a.UI.saveChanges.hide();a.UI.cancelChanges.hide()}},cancelChanges:function(){var a=this,b=a.phyloTree.get("selectedNode");if(b){$.each(a.valuesOfConcern,function(c,d){a.UI[c].val(b[c])})}},updateNodes:function(){var a=this,b=a.phyloTree.get("selectedNode");if(b){if(!a.isAcceptableValue(a.UI.dist,0,1)||a.hasIllegalJsonCharacters(a.UI.name)||a.hasIllegalJsonCharacters(a.UI.annotation)){return}$.each(a.valuesOfConcern,function(c,d){(b[c])=a.UI[c].val()});a.phyloTree.set("nodeAttrChangedTime",new Date())}else{alert("No node selected")}}});var PhyloVizSearch=UserMenuBase.extend({initialize:function(){var a=this;$("#phyloVizSearchBtn").on("click",function(){var c=$("#phyloVizSearchTerm"),d=$("#phyloVizSearchCondition").val().split("-"),b=d[0],e=d[1];a.hasIllegalJsonCharacters(c);if(b==="dist"){a.isAcceptableValue(c,0,1)}a.searchTree(b,e,c.val())})},searchTree:function(a,c,b){d3.selectAll("g.node").classed("searchHighlight",function(f){var e=f[a];if(typeof e!=="undefined"&&e!==null){if(a==="dist"){switch(c){case"greaterEqual":return e>=+b;case"lesserEqual":return e<=+b;default:return}}else{if(a==="name"||a==="annotation"){return e.toLowerCase().indexOf(b.toLowerCase())!==-1}}}})}});