define([],function(){return Backbone.Model.extend({initialize:function(a){this.app=a},refresh:function(){this.dict={};this.xml=$("<div/>");if(!this.app.section){return{}}this._iterate(this.app.section.$el,this.dict,this.xml)},finalize:function(d){d=d||{};var a=this;this.job_def={};this.job_ids={};function c(g,f,e){a.job_def[g]=e;a.job_ids[g]=f}function b(k,n){for(var h in n){var f=n[h];if(f.input){var p=f.input;var j=k;if(k!=""){j+="|"}j+=p.name;switch(p.type){case"repeat":var e="section-";var s=[];var m=null;for(var r in f){var l=r.indexOf(e);if(l!=-1){l+=e.length;s.push(parseInt(r.substr(l)));if(!m){m=r.substr(0,l)}}}s.sort(function(t,i){return t-i});var h=0;for(var g in s){b(j+"_"+h++,f[m+s[g]])}break;case"conditional":var q=a.app.field_list[p.id].value();c(j+"|"+p.test_param.name,p.id,q);for(var g in p.cases){if(p.cases[g].value==q){b(j,n[p.id+"-section-"+g]);break}}break;default:var o=a.app.field_list[p.id];var q=o.value();if(d[p.type]){q=d[p.type](q)}if(!o.skip){c(j,p.id,q)}}}}}b("",this.dict);return this.job_def},match:function(a){return this.job_ids&&this.job_ids[a]},matchModel:function(c,e){var a={};var b=this;function d(o,l){for(var k in l){var m=l[k];var h=m.name;if(o!=""){h=o+"|"+h}if(m.type=="repeat"){for(var g in m.cache){d(h+"_"+g,m.cache[g])}}else{if(m.type=="conditional"){var n=m.test_param&&m.test_param.value;for(var g in m.cases){if(m.cases[g].value==n){d(h,m.cases[g].inputs)}}}else{var f=b.app.tree.job_ids[h];if(f){e(f,m)}}}}}d("",c.inputs);return a},matchResponse:function(c){var a={};var b=this;function d(j,h){if(typeof h==="string"){var f=b.app.tree.job_ids[j];if(f){a[f]=h}}else{for(var g in h){var e=g;if(j!==""){e=j+"|"+e}d(e,h[g])}}}d("",c);return a},references:function(c,e){var g=[];var b=this;function d(h,j){var i=$(j).children();var l=[];var k=false;i.each(function(){var o=this;var n=$(o).attr("id");if(n!==c){var m=b.app.input_list[n];if(m){if(m.name==h){k=true;return false}if(m.data_ref==h&&m.type==e){l.push(n)}}}});if(!k){g=g.concat(l);i.each(function(){d(h,this)})}}var f=this.xml.find("#"+c);if(f.length>0){var a=this.app.input_list[c];if(a){d(a.name,f.parent())}}return g},_iterate:function(d,e,b){var a=this;var c=$(d).children();c.each(function(){var i=this;var h=$(i).attr("id");if($(i).hasClass("section-row")){e[h]={};var f=a.app.input_list[h];if(f){e[h]={input:f}}var g=$('<div id="'+h+'"/>');b.append(g);a._iterate(i,e[h],g)}else{a._iterate(i,e,b)}})}})});