define([],function(){return Backbone.Model.extend({initialize:function(a){this.app=a},refresh:function(){this.dict={};this.xml=$("<div/>");if(!this.app.section){return{}}this._iterate(this.app.section.$el,this.dict,this.xml)},finalize:function(){var a=this;var b={};function c(k,l){for(var f in l){var d=l[f];if(d.input){var m=d.input;var h=k;if(k!=""){h+="|"}h+=m.name;switch(m.type){case"repeat":var g=0;for(var e in d){if(e.indexOf("section")!=-1){c(h+"_"+g++,d[e])}}break;case"conditional":var n=a.app.field_list[m.id].value();for(var e in m.cases){if(m.cases[e].value==n){c(h,l[m.id+"-section-"+e]);break}}break;default:var n=a.app.field_list[m.id].value();b[h]=n}}}}c("",this.dict);return b},findReferences:function(c,e){var g=[];var b=this;function d(h,j){var i=$(j).children();var l=[];var k=false;i.each(function(){var o=this;var n=$(o).attr("id");if(n!==c){var m=b.app.input_list[n];if(m){if(m.name==h){k=true;return false}if(m.data_ref==h&&m.type==e){l.push(n)}}}});if(!k){g=g.concat(l);i.each(function(){d(h,this)})}}var f=this.xml.find("#"+c);if(f.length>0){var a=this.app.input_list[c];if(a){d(a.name,f.parent())}}return g},_iterate:function(d,e,b){var a=this;var c=$(d).children();c.each(function(){var i=this;var h=$(i).attr("id");if($(i).hasClass("section-row")||$(i).hasClass("tab-pane")){e[h]={};var f=a.app.input_list[h];if(f){e[h]={input:f}}var g=$('<div id="'+h+'"/>');b.append(g);a._iterate(i,e[h],g)}else{a._iterate(i,e,b)}})}})});