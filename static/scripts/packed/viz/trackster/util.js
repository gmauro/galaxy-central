define(function(){var b=function(e){return("promise" in e)};var c=Backbone.Model.extend({defaults:{ajax_settings:{},interval:1000,success_fn:function(d){return true}},go:function(){var g=$.Deferred(),f=this,i=f.get("ajax_settings"),h=f.get("success_fn"),e=f.get("interval"),d=function(){$.ajax(i).success(function(j){if(h(j)){g.resolve(j)}else{setTimeout(d,e)}})};d();return g}});var a=function(d){if(!d){d="#ffffff"}if(typeof(d)==="string"){d=[d]}for(var m=0;m<d.length;m++){d[m]=parseInt(d[m].slice(1),16)}var q=function(w,v,i){return((w*299)+(v*587)+(i*114))/1000};var h=function(y,x,z,v,i,w){return(Math.max(y,v)-Math.min(y,v))+(Math.max(x,i)-Math.min(x,i))+(Math.max(z,w)-Math.min(z,w))};var k,r,j,n,t,l,u,f,g,e,s,p=false,o=0;do{k=Math.round(Math.random()*16777215);r=(k&16711680)>>16;j=(k&65280)>>8;n=k&255;g=q(r,j,n);p=true;for(m=0;m<d.length;m++){t=d[m];l=(t&16711680)>>16;u=(t&65280)>>8;f=t&255;e=q(l,u,f);s=h(r,j,n,l,u,f);if((Math.abs(g-e)<40)||(s<200)){p=false;break}}o++}while(!p&&o<=10);return"#"+(16777216+k).toString(16).substr(1,6)};return{is_deferred:b,ServerStateDeferred:c,get_random_color:a}});