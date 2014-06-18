define(["mvc/base-mvc","utils/localization"],function(a,e){var f=Backbone.View.extend(a.LoggableMixin).extend({initialize:function(g){g=_.defaults(g,{datasets:[],filters:this.DEFAULT_FILTERS,automaticallyPair:true,matchPercentage:1,strategy:"lcs"});this.initialList=g.datasets;this.historyId=g.historyId;this.filters=this.commonFilters[g.filters]||this.commonFilters[this.DEFAULT_FILTERS];if(_.isArray(g.filters)){this.filters=g.filters}this.automaticallyPair=g.automaticallyPair;this.matchPercentage=g.matchPercentage;this.strategy=this.strategies[g.strategy]||this.strategies[this.DEFAULT_STRATEGY];if(_.isFunction(g.strategy)){this.strategy=g.strategy}this.oncancel=g.oncancel;this.oncreate=g.oncreate;this.unpairedPanelHidden=false;this.pairedPanelHidden=false;this._dataSetUp();this._setUpBehaviors()},commonFilters:{none:["",""],illumina:["_1","_2"]},DEFAULT_FILTERS:"illumina",strategies:{lcs:"autoPairLCSs",levenshtein:"autoPairLevenshtein"},DEFAULT_STRATEGY:"lcs",_dataSetUp:function(){this.paired=[];this.unpaired=[];this.selectedIds=[];this._sortInitialList();this._ensureIds();this.unpaired=this.initialList.slice(0);if(this.automaticallyPair){this.autoPair()}},_sortInitialList:function(){this._sortDatasetList(this.initialList)},_sortDatasetList:function(g){g.sort(function(i,h){return naturalSort(i.name,h.name)});return g},_ensureIds:function(){this.initialList.forEach(function(g){if(!g.hasOwnProperty("id")){g.id=_.uniqueId()}});return this.initialList},_splitByFilters:function(i){var h=[],g=[];this.unpaired.forEach(function(j){if(this._filterFwdFn(j)){h.push(j)}if(this._filterRevFn(j)){g.push(j)}}.bind(this));return[h,g]},_filterFwdFn:function(g){return g.name.indexOf(this.filters[0])>=0},_filterRevFn:function(g){return g.name.indexOf(this.filters[1])>=0},_addToUnpaired:function(h){var g=function(i,k){if(i===k){return i}var j=Math.floor((k-i)/2)+i,l=naturalSort(h.name,this.unpaired[j].name);if(l<0){return g(i,j)}else{if(l>0){return g(j+1,k)}}while(this.unpaired[j]&&this.unpaired[j].name===h.name){j++}return j}.bind(this);this.unpaired.splice(g(0,this.unpaired.length),0,h)},autoPair:function(g){g=g||this.strategy;this.simpleAutoPair();return this[g].call(this)},simpleAutoPair:function(){var m=0,k,q=this._splitByFilters(),g=q[0],p=q[1],o,r,h=false;while(m<g.length){var l=g[m];o=l.name.replace(this.filters[0],"");h=false;for(k=0;k<p.length;k++){var n=p[k];r=n.name.replace(this.filters[1],"");if(l!==n&&o===r){h=true;this._pair(g.splice(m,1)[0],p.splice(k,1)[0],{silent:true});break}}if(!h){m+=1}}},autoPairLevenshtein:function(){var n=0,l,s=this._splitByFilters(),g=s[0],q=s[1],p,u,h,r,k;while(n<g.length){var m=g[n];p=m.name.replace(this.filters[0],"");k=Number.MAX_VALUE;for(l=0;l<q.length;l++){var o=q[l];u=o.name.replace(this.filters[1],"");if(m!==o){if(p===u){r=l;k=0;break}h=d(p,u);if(h<k){r=l;k=h}}}var t=1-(k/(Math.max(p.length,u.length)));if(t>=this.matchPercentage){this._pair(g.splice(n,1)[0],q.splice(r,1)[0],{silent:true});if(g.length<=0||q.length<=0){return}}else{n+=1}}},autoPairLCSs:function(){var l=0,h,s=this._splitByFilters(),g=s[0],q=s[1],p,v,u,r,n;if(!g.length||!q.length){return}while(l<g.length){var k=g[l];p=k.name.replace(this.filters[0],"");n=0;for(h=0;h<q.length;h++){var o=q[h];v=o.name.replace(this.filters[1],"");if(k!==o){if(p===v){r=h;n=p.length;break}var m=this._naiveStartingAndEndingLCS(p,v);u=m.length;if(u>n){r=h;n=u}}}var t=n/(Math.min(p.length,v.length));if(t>=this.matchPercentage){this._pair(g.splice(l,1)[0],q.splice(r,1)[0],{silent:true});if(g.length<=0||q.length<=0){return}}else{l+=1}}},_naiveStartingAndEndingLCS:function(l,h){var m="",n="",k=0,g=0;while(k<l.length&&k<h.length){if(l[k]!==h[k]){break}m+=l[k];k+=1}if(k===l.length){return l}if(k===h.length){return h}k=(l.length-1);g=(h.length-1);while(k>=0&&g>=0){if(l[k]!==h[g]){break}n=[l[k],n].join("");k-=1;g-=1}return m+n},_pair:function(i,g,h){h=h||{};var j=this._createPair(i,g,h.name);this.paired.push(j);this.unpaired=_.without(this.unpaired,i,g);if(!h.silent){this.trigger("pair:new",j)}return j},_createPair:function(i,g,h){if(!(i&&g)||(i===g)){throw new Error("Bad pairing: "+[JSON.stringify(i),JSON.stringify(g)])}h=h||this._guessNameForPair(i,g);return{forward:i,name:h,reverse:g}},_guessNameForPair:function(i,g){var h=this._naiveStartingAndEndingLCS(i.name.replace(this.filters[0],""),g.name.replace(this.filters[1],""));return h||(i.name+" & "+g.name)},_unpair:function(h,g){g=g||{};if(!h){throw new Error("Bad pair: "+JSON.stringify(h))}this.paired=_.without(this.paired,h);this._addToUnpaired(h.forward);this._addToUnpaired(h.reverse);if(!g.silent){this.trigger("pair:unpair",[h])}return h},unpairAll:function(){var g=[];while(this.paired.length){g.push(this._unpair(this.paired[0],{silent:true}))}this.trigger("pair:unpair",g)},_pairToJSON:function(g){return{collection_type:"paired",src:"new_collection",name:g.name,element_identifiers:[{name:"forward",id:g.forward.id,src:"hda"},{name:"reverse",id:g.reverse.id,src:"hda"}]}},createList:function(){var i=this,h;if(i.historyId){h="/api/histories/"+this.historyId+"/contents/dataset_collections"}var g={type:"dataset_collection",collection_type:"list:paired",name:_.escape(i.$(".collection-name").val()),element_identifiers:i.paired.map(function(j){return i._pairToJSON(j)})};return jQuery.ajax(h,{type:"POST",contentType:"application/json",data:JSON.stringify(g)}).fail(function(m,j,l){console.error(m,j,l);var k=e("An error occurred while creating this collection");if(m){if(m.readyState===0&&m.status===0){k+=": "+e("Galaxy could not be reached and may be updating.")+e(" Try again in a few minutes.")}else{if(m.responseJSON){k+="<br /><pre>"+JSON.stringify(m.responseJSON)+"</pre>"}else{k+=": "+l}}}i._showAlert(k,"alert-danger")}).done(function(j,k,l){i.trigger("collection:created",j,k,l);if(typeof i.oncreate==="function"){i.oncreate.call(this,j,k,l)}})},render:function(g,h){this.$el.empty().addClass("collection-creator").html(f.templates.main());this._renderHeader(g);this._renderMiddle(g);this._renderFooter(g);this._addPluginComponents();return this},_renderHeader:function(h,i){var g=this.$(".header").empty().html(f.templates.header()).find(".help-content").prepend($(f.templates.helpContent()));this._renderFilters();return g},_renderFilters:function(){return this.$(".forward-column .column-header input").val(this.filters[0]).add(this.$(".reverse-column .column-header input").val(this.filters[1]))},_renderMiddle:function(h,i){var g=this.$(".middle").empty().html(f.templates.middle());if(this.unpairedPanelHidden){this.$(".unpaired-columns").hide()}else{if(this.pairedPanelHidden){this.$(".paired-columns").hide()}}this._renderUnpaired();this._renderPaired();return g},_renderUnpaired:function(l,m){var j=this,k,h,g=[],i=this._splitByFilters();this.$(".forward-column .title").text([i[0].length,e("unpaired forward")].join(" "));this.$(".forward-column .unpaired-info").text(this._renderUnpairedDisplayStr(this.unpaired.length-i[0].length));this.$(".reverse-column .title").text([i[1].length,e("unpaired reverse")].join(" "));this.$(".reverse-column .unpaired-info").text(this._renderUnpairedDisplayStr(this.unpaired.length-i[1].length));this.$(".autopair-link").toggle(this.unpaired.length!==0);if(this.unpaired.length===0){this._renderUnpairedEmpty()}h=i[1].map(function(o,n){if((i[0][n]!==undefined)&&(i[0][n]!==o)){g.push(j._renderPairButton())}return j._renderUnpairedDataset(o)});k=i[0].map(function(n){return j._renderUnpairedDataset(n)});this.$(".unpaired-columns .column-datasets").empty();return this.$(".unpaired-columns .forward-column .column-datasets").append(k).add(this.$(".unpaired-columns .paired-column .column-datasets").append(g)).add(this.$(".unpaired-columns .reverse-column .column-datasets").append(h))},_renderUnpairedDisplayStr:function(g){return["(",g," ",e("filtered out"),")"].join("")},_renderUnpairedDataset:function(g){return $("<li/>").attr("id","dataset-"+g.id).addClass("dataset unpaired").attr("draggable",true).addClass(g.selected?"selected":"").append($("<span/>").addClass("dataset-name").text(g.name)).data("dataset",g)},_renderPairButton:function(){return $("<li/>").addClass("dataset unpaired").append($("<span/>").addClass("dataset-name").text(e("Pair these datasets")))},_renderUnpairedEmpty:function(){var g=$('<div class="empty-message"></div>').text("("+e("no remaining unpaired datasets")+")");this.$(".unpaired-columns .paired-column .column-datasets").prepend(g);return g},_renderPaired:function(j,k){var i=[],g=[],h=[];this.$(".paired-column-title .title").text([this.paired.length,e("paired")].join(" "));this.$(".unpair-all-link").toggle(this.paired.length!==0);if(this.paired.length===0){this._renderPairedEmpty()}this.paired.forEach(function(m,l){i.push($("<li/>").addClass("dataset paired").append($("<span/>").addClass("dataset-name").text(m.forward.name)));g.push($("<li/>").addClass("dataset paired").append($("<span/>").addClass("dataset-name").text(m.name)));h.push($("<li/>").addClass("dataset paired").append($("<span/>").addClass("dataset-name").text(m.reverse.name)));h.push($("<button/>").addClass("unpair-btn").append($("<span/>").addClass("fa fa-unlink").attr("title",e("Unpair"))))});this.$(".paired-columns .column-datasets").empty();return this.$(".paired-columns .forward-column .column-datasets").prepend(i).add(this.$(".paired-columns .paired-column .column-datasets").prepend(g)).add(this.$(".paired-columns .reverse-column .column-datasets").prepend(h))},_renderPairedEmpty:function(){var g=$('<div class="empty-message"></div>').text("("+e("no paired datasets yet")+")");this.$(".paired-columns .paired-column .column-datasets").prepend(g);return g},_renderFooter:function(h,i){var g=this.$(".footer").empty().html(f.templates.footer());if(typeof this.oncancel==="function"){this.$(".cancel-create.btn").show()}return g},_addPluginComponents:function(){this._chooseFiltersPopover(".choose-filters-link");this.$(".help-content i").hoverhighlight(".collection-creator","rgba( 192, 255, 255, 1.0 )")},_chooseFiltersPopover:function(g){function h(k,j){return['<button class="filter-choice btn" ','data-forward="',k,'" data-reverse="',j,'">',e("Forward"),": ",k,", ",e("Reverse"),": ",j,"</button>"].join("")}var i=$(_.template(['<div class="choose-filters">','<div class="help">',e("Choose from the following filters to change which unpaired reads are shown in the display"),":</div>",h("_1","_2"),h("_R1","_R2"),"</div>"].join(""),{}));return this.$(g).popover({container:".collection-creator",placement:"bottom",html:true,content:i})},_validationWarning:function(h,g){var i="validation-warning";if(h==="name"){h=this.$(".collection-name").add(this.$(".collection-name-prompt"));this.$(".collection-name").focus().select()}if(g){h=h||this.$("."+i);h.removeClass(i)}else{h.addClass(i)}},_setUpBehaviors:function(){this.on("pair:new",function(){this._renderUnpaired();this._renderPaired();this.$(".paired-columns").scrollTop(8000000)});this.on("pair:unpair",function(g){this._renderUnpaired();this._renderPaired()});this.on("filter-change",function(){this.filters=[this.$(".forward-unpaired-filter input").val(),this.$(".reverse-unpaired-filter input").val()];this._renderFilters();this._renderUnpaired()});this.on("autopair",function(){this._renderUnpaired();this._renderPaired()});return this},events:{"click .more-help":"_clickMoreHelp","click .less-help":"_clickLessHelp","click .header .alert button":"_hideAlert","click .forward-column .column-title":"_clickShowOnlyUnpaired","click .reverse-column .column-title":"_clickShowOnlyUnpaired","click .unpair-all-link":"_clickUnpairAll","change .forward-unpaired-filter input":function(g){this.trigger("filter-change")},"focus .forward-unpaired-filter input":function(g){$(g.currentTarget).select()},"click .autopair-link":"_clickAutopair","click .choose-filters .filter-choice":"_clickFilterChoice","click .clear-filters-link":"_clearFilters","change .reverse-unpaired-filter input":function(g){this.trigger("filter-change")},"focus .reverse-unpaired-filter input":function(g){$(g.currentTarget).select()},"click .forward-column .dataset.unpaired":"_clickUnpairedDataset","click .reverse-column .dataset.unpaired":"_clickUnpairedDataset","click .paired-column .dataset.unpaired":"_clickPairRow","click .unpaired-columns":"clearSelectedUnpaired","click .paired-column-title":"_clickShowOnlyPaired","mousedown .flexible-partition-drag":"_startPartitionDrag","click .paired-columns .paired-column .dataset-name":"_clickPairName","click .unpair-btn":"_clickUnpair","mouseover .dataset.paired":"_hoverPaired","mouseout .dataset.paired":"_hoverOutPaired","change .collection-name":"_changeName","click .cancel-create":function(g){if(typeof this.oncancel==="function"){this.oncancel.call(this)}},"click .create-collection":"_clickCreate"},_clickMoreHelp:function(g){this.$(".main-help").css("max-height","none");this.$(".main-help .help-content p:first-child").css("white-space","normal");this.$(".more-help").hide()},_clickLessHelp:function(g){this.$(".main-help").css("max-height","");this.$(".main-help .help-content p:first-child").css("white-space","");this.$(".more-help").show()},_showAlert:function(h,g){g=g||"alert-danger";this.$(".main-help").hide();this.$(".header .alert").attr("class","alert alert-dismissable").addClass(g).show().find(".alert-message").html(h)},_hideAlert:function(g){this.$(".main-help").show();this.$(".header .alert").hide()},_clickShowOnlyUnpaired:function(g){if(this.$(".paired-columns").is(":visible")){this.hidePaired()}else{this.splitView()}},_clickShowOnlyPaired:function(g){if(this.$(".unpaired-columns").is(":visible")){this.hideUnpaired()}else{this.splitView()}},hideUnpaired:function(g,h){g=g||0;this.$(".unpaired-columns").hide(g,h);this.$(".paired-columns").show(g).css("flex","1 0 auto");this.unpairedPanelHidden=true},hidePaired:function(g,h){g=g||0;this.$(".unpaired-columns").show(g).css("flex","1 0 auto");this.$(".paired-columns").hide(g,h);this.pairedPanelHidden=true},splitView:function(g,h){g=g||0;this.unpairedPanelHidden=this.pairedPanelHidden=false;this._renderMiddle(g);return this},_clickUnpairAll:function(g){this.unpairAll()},_clickAutopair:function(h){var g=this.autoPair();this.trigger("autopair",g)},_clickFilterChoice:function(h){var g=$(h.currentTarget);this.$(".forward-unpaired-filter input").val(g.data("forward"));this.$(".reverse-unpaired-filter input").val(g.data("reverse"));this._hideChooseFilters();this.trigger("filter-change")},_hideChooseFilters:function(){this.$(".choose-filters-link").popover("hide");this.$(".popover").css("display","none")},_clearFilters:function(g){this.$(".forward-unpaired-filter input").val("");this.$(".reverse-unpaired-filter input").val("");this.trigger("filter-change")},_clickUnpairedDataset:function(g){g.stopPropagation();return this.toggleSelectUnpaired($(g.currentTarget))},toggleSelectUnpaired:function(i,h){h=h||{};var j=i.data("dataset"),g=h.force!==undefined?h.force:!i.hasClass("selected");if(!i.size()||j===undefined){return i}if(g){i.addClass("selected");if(!h.waitToPair){this.pairAllSelected()}}else{i.removeClass("selected")}return i},pairAllSelected:function(h){h=h||{};var i=this,j=[],g=[],k=[];i.$(".unpaired-columns .forward-column .dataset.selected").each(function(){j.push($(this).data("dataset"))});i.$(".unpaired-columns .reverse-column .dataset.selected").each(function(){g.push($(this).data("dataset"))});j.length=g.length=Math.min(j.length,g.length);j.forEach(function(m,l){try{k.push(i._pair(m,g[l],{silent:true}))}catch(n){console.error(n)}});if(k.length&&!h.silent){this.trigger("pair:new",k)}return k},clearSelectedUnpaired:function(){this.$(".unpaired-columns .dataset.selected").removeClass("selected")},_clickPairRow:function(i){var j=$(i.currentTarget).index(),h=$(".unpaired-columns .forward-column .dataset").eq(j).data("dataset"),g=$(".unpaired-columns .reverse-column .dataset").eq(j).data("dataset");this._pair(h,g)},_startPartitionDrag:function(h){var g=this,k=h.pageY;$("body").css("cursor","ns-resize");g.$(".flexible-partition-drag").css("color","black");function j(l){g.$(".flexible-partition-drag").css("color","");$("body").css("cursor","").unbind("mousemove",i)}function i(l){var m=l.pageY-k;if(!g.adjPartition(m)){$("body").trigger("mouseup")}k+=m}$("body").mousemove(i);$("body").one("mouseup",j)},adjPartition:function(h){var g=this.$(".unpaired-columns"),i=this.$(".paired-columns"),j=parseInt(g.css("height"),10),k=parseInt(i.css("height"),10);j=Math.max(10,j+h);k=k-h;if(j<=10){this.hideUnpaired();return false}else{if(!g.is("visible")){g.show()}}if(k<=15){this.hidePaired();if(k<10){return false}}else{if(!i.is("visible")){i.show()}}g.css({height:j+"px",flex:"0 0 auto"});return true},_clickPairName:function(i){var h=$(i.currentTarget),j=this.paired[h.parent().index()],g=prompt("Enter a new name for the pair:",j.name);if(g){j.name=g;h.text(j.name)}},_clickUnpair:function(h){var g=Math.floor($(h.currentTarget).index()/2);this._unpair(this.paired[g])},_hoverPaired:function(i){var g=$(i.currentTarget),h=g.index();if(g.parents(".reverse-column").size()){h=Math.floor(h/2)}this.emphasizePair(h)},_hoverOutPaired:function(i){var g=$(i.currentTarget),h=g.index();if(g.parents(".reverse-column").size()){h=Math.floor(h/2)}this.deemphasizePair(h)},emphasizePair:function(g){this.$(".paired-columns .forward-column .dataset.paired").eq(g).add(this.$(".paired-columns .paired-column .dataset.paired").eq(g)).add(this.$(".paired-columns .reverse-column .dataset.paired").eq(g)).addClass("emphasized")},deemphasizePair:function(g){this.$(".paired-columns .forward-column .dataset.paired").eq(g).add(this.$(".paired-columns .paired-column .dataset.paired").eq(g)).add(this.$(".paired-columns .reverse-column .dataset.paired").eq(g)).removeClass("emphasized")},_changeName:function(g){this._validationWarning("name",!!this._getName())},_getName:function(){return _.escape(this.$(".collection-name").val())},_clickCreate:function(h){var g=this._getName();if(!g){this._validationWarning("name")}else{this.createList()}},_printList:function(h){var g=this;_.each(h,function(i){if(h===g.paired){g._printPair(i)}else{}})},_printPair:function(g){console.debug(g.forward.name,g.reverse.name,": ->",g.name)},toString:function(){return"PairedCollectionCreator"}});f.templates=f.templates||{main:_.template(['<div class="header"></div>','<div class="middle"></div>','<div class="footer">'].join("")),header:_.template(['<div class="main-help well clear">','<a class="more-help" href="javascript:void(0);">',e("More help"),"</a>",'<div class="help-content">','<a class="less-help" href="javascript:void(0);">',e("Less"),"</a>","</div>","</div>",'<div class="alert alert-dismissable">','<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>','<span class="alert-message"></span>',"</div>",'<div class="column-headers vertically-spaced row-flex-container">','<div class="forward-column flex-column column">','<div class="column-header">','<div class="column-title">','<span class="title">',e("Unpaired forward"),"</span>",'<span class="title-info unpaired-info"></span>',"</div>",'<div class="unpaired-filter forward-unpaired-filter pull-left">','<input class="search-query" placeholder="',e("Filter this list"),'" />',"</div>","</div>","</div>",'<div class="paired-column flex-column column">','<div class="column-header">','<a class="choose-filters-link" href="javascript:void(0)">',e("Choose filters"),"</a>",'<a class="clear-filters-link" href="javascript:void(0);">',e("Clear filters"),"</a><br />",'<a class="autopair-link" href="javascript:void(0);">',e("Auto-pair"),"</a>","</div>","</div>",'<div class="reverse-column flex-column column">','<div class="column-header">','<div class="column-title">','<span class="title">',e("Unpaired reverse"),"</span>",'<span class="title-info unpaired-info"></span>',"</div>",'<div class="unpaired-filter reverse-unpaired-filter pull-left">','<input class="search-query" placeholder="',e("Filter this list"),'" />',"</div>","</div>","</div>","</div>"].join("")),middle:_.template(['<div class="unpaired-columns row-flex-container scroll-container">','<div class="forward-column flex-column column">','<ol class="column-datasets"></ol>',"</div>",'<div class="paired-column flex-column column">','<ol class="column-datasets"></ol>',"</div>",'<div class="reverse-column flex-column column">','<ol class="column-datasets"></ol>',"</div>","</div>",'<div class="flexible-partition">','<div class="flexible-partition-drag"></div>','<div class="column-header">','<div class="column-title paired-column-title">','<span class="title"></span>',"</div>",'<a class="unpair-all-link" href="javascript:void(0);">',e("Unpair all"),"</a>","</div>","</div>",'<div class="paired-columns row-flex-container scroll-container">','<div class="forward-column flex-column column">','<ol class="column-datasets"></ol>',"</div>",'<div class="paired-column flex-column column">','<ol class="column-datasets"></ol>',"</div>",'<div class="reverse-column flex-column column">','<ol class="column-datasets"></ol>',"</div>","</div>"].join("")),footer:_.template(['<div class="attributes clear">','<input class="collection-name form-control pull-right" ','placeholder="',e("Enter a name for your new list"),'" />','<div class="collection-name-prompt pull-right">',e("Name"),":</div>","</div>",'<div class="actions clear vertically-spaced">','<div class="other-options pull-left">','<button class="cancel-create btn" tabindex="-1">',e("Cancel"),"</button>",'<div class="create-other btn-group dropup">','<button class="btn btn-default dropdown-toggle" data-toggle="dropdown">',e("Create a different kind of collection"),' <span class="caret"></span>',"</button>",'<ul class="dropdown-menu" role="menu">','<li><a href="#">',e("Create a <i>single</i> pair"),"</a></li>",'<li><a href="#">',e("Create a list of <i>unpaired</i> datasets"),"</a></li>","</ul>","</div>","</div>",'<div class="main-options pull-right">','<button class="create-collection btn btn-primary">',e("Create list"),"</button>","</div>","</div>"].join("")),helpContent:_.template(["<p>",e(["Collections of paired datasets are ordered lists of dataset pairs (often forward and reverse ","reads) that can be passed to tools and workflows in order to have analyses done on the entire ","group. This interface allows you to create a collection, choose which datasets are paired, ","and re-order the final collection."].join("")),"</p>","<p>",e(['Unpaired datasets are shown in the <i data-target=".unpaired-columns">unpaired section</i> ',"(hover over the underlined words to highlight below). ",'Paired datasets are shown in the <i data-target=".paired-columns">paired section</i>.',"<ul>To pair datasets, you can:","<li>Click a dataset in the ",'<i data-target=".unpaired-columns .forward-column .column-datasets,','.unpaired-columns .forward-column">forward column</i> ',"to select it then click a dataset in the ",'<i data-target=".unpaired-columns .reverse-column .column-datasets,','.unpaired-columns .reverse-column">reverse column</i>.',"</li>",'<li>Click one of the "Pair these datasets" buttons in the ','<i data-target=".unpaired-columns .paired-column .column-datasets,','.unpaired-columns .paired-column">middle column</i> ',"to pair the datasets in a particular row.","</li>",'<li>Click <i data-target=".autopair-link">"Auto-pair"</i> ',"to have your datasets automatically paired based on name.","</li>","</ul>"].join("")),"</p>","<p>",e(["<ul>You can filter what is shown in the unpaired sections by:","<li>Entering partial dataset names in either the ",'<i data-target=".forward-unpaired-filter input">forward filter</i> or ','<i data-target=".reverse-unpaired-filter input">reverse filter</i>.',"</li>","<li>Choosing from a list of preset filters by clicking the ",'<i data-target=".choose-filters-link">"Choose filters" link</i>.',"</li>","<li>Clearing the filters by clicking the ",'<i data-target=".clear-filters-link">"Clear filters" link</i>.',"</li>","</ul>"].join("")),"</p>","<p>",e(["To unpair individual dataset pairs, click the ",'<i data-target=".unpair-btn">unpair buttons ( <span class="fa fa-unlink"></span> )</i>. ','Click the <i data-target=".unpair-all-link">"Unpair all" link</i> to unpair all pairs.'].join("")),"</p>","<p>",e(['Once your collection is complete, enter a <i data-target=".collection-name">name</i> and ','click <i data-target=".create-collection">"Create list"</i>.',"(Note: you do not have to pair all unpaired datasets to finish.)"].join("")),"</p>"].join(""))};function d(h,g){if(h.length===0){return g.length}if(g.length===0){return h.length}var k=[];var m;for(m=0;m<=g.length;m++){k[m]=[m]}var l;for(l=0;l<=h.length;l++){k[0][l]=l}for(m=1;m<=g.length;m++){for(l=1;l<=h.length;l++){if(g.charAt(m-1)===h.charAt(l-1)){k[m][l]=k[m-1][l-1]}else{k[m][l]=Math.min(k[m-1][l-1]+1,Math.min(k[m][l-1]+1,k[m-1][l]+1))}}}return k[g.length][h.length]}(function(){jQuery.fn.extend({hoverhighlight:function g(i,h){i=i||"body";if(!this.size()){return this}$(this).each(function(){var k=$(this),j=k.data("target");if(j){k.mouseover(function(l){$(j,i).css({background:h})}).mouseout(function(l){$(j).css({background:""})})}});return this}})}());var b=function c(i,g){g=_.defaults(g||{},{datasets:i,oncancel:function(){Galaxy.modal.hide()},oncreate:function(){Galaxy.modal.hide();Galaxy.currHistoryPanel.refreshContents()}});if(!window.Galaxy||!Galaxy.modal){throw new Error("Galaxy or Galaxy.modal not found")}var h=new f(g).render();Galaxy.modal.show({title:"Create a collection of paired datasets",body:h.$el,width:"80%",height:"700px",closing_events:true});return h};return{PairedCollectionCreator:f,pairedCollectionCreatorModal:b}});