(function(){var b=Handlebars.template,a=Handlebars.templates=Handlebars.templates||{};a["template-history-historyPanel-anon"]=b(function(g,r,p,k,u){this.compilerInfo=[4,">= 1.0.0"];p=this.merge(p,g.helpers);u=u||{};var q="",i,f,o=this,e="function",c=p.blockHelperMissing,d=this.escapeExpression;function n(z,y){var v="",x,w;v+='\n                <div class="history-name" title="';w={hash:{},inverse:o.noop,fn:o.program(2,m,y),data:y};if(x=p.local){x=x.call(z,w)}else{x=z.local;x=typeof x===e?x.apply(z):x}if(!p.local){x=c.call(z,x,w)}if(x||x===0){v+=x}v+='">\n                    ';if(x=p.name){x=x.call(z,{hash:{},data:y})}else{x=z.name;x=typeof x===e?x.apply(z):x}v+=d(x)+"\n                </div>\n            ";return v}function m(w,v){return"You must be logged in to edit your history name"}function l(y,x){var v="",w;v+='\n            <div class="history-size">';if(w=p.nice_size){w=w.call(y,{hash:{},data:x})}else{w=y.nice_size;w=typeof w===e?w.apply(y):w}v+=d(w)+"</div>\n            ";return v}function j(y,x){var v="",w;v+='\n            \n            <div class="';if(w=p.status){w=w.call(y,{hash:{},data:x})}else{w=y.status;w=typeof w===e?w.apply(y):w}v+=d(w)+'message">';if(w=p.message){w=w.call(y,{hash:{},data:x})}else{w=y.message;w=typeof w===e?w.apply(y):w}v+=d(w)+"</div>\n            ";return v}function h(w,v){return"You are over your disk quota"}function t(w,v){return"Tool execution is on hold until your disk usage drops below your allocated quota"}function s(w,v){return"Your history is empty. Click 'Get Data' on the left pane to start"}q+='<div class="history-controls">\n\n        <div class="history-title">\n            \n            ';i=p["if"].call(r,r.name,{hash:{},inverse:o.noop,fn:o.program(1,n,u),data:u});if(i||i===0){q+=i}q+='\n        </div>\n\n        <div class="history-subtitle clear">\n            ';i=p["if"].call(r,r.nice_size,{hash:{},inverse:o.noop,fn:o.program(4,l,u),data:u});if(i||i===0){q+=i}q+='\n\n            <div class="history-secondary-actions"></div>\n        </div>\n\n        <div class="message-container">\n            ';i=p["if"].call(r,r.message,{hash:{},inverse:o.noop,fn:o.program(6,j,u),data:u});if(i||i===0){q+=i}q+='\n        </div>\n\n        <div class="quota-message errormessage">\n            ';f={hash:{},inverse:o.noop,fn:o.program(8,h,u),data:u};if(i=p.local){i=i.call(r,f)}else{i=r.local;i=typeof i===e?i.apply(r):i}if(!p.local){i=c.call(r,i,f)}if(i||i===0){q+=i}q+=".\n            ";f={hash:{},inverse:o.noop,fn:o.program(10,t,u),data:u};if(i=p.local){i=i.call(r,f)}else{i=r.local;i=typeof i===e?i.apply(r):i}if(!p.local){i=c.call(r,i,f)}if(i||i===0){q+=i}q+='.\n        </div>\n\n    </div>\n\n    \n    <div class="datasets-list"></div>\n\n    <div class="empty-history-message infomessagesmall">\n        ';f={hash:{},inverse:o.noop,fn:o.program(12,s,u),data:u};if(i=p.local){i=i.call(r,f)}else{i=r.local;i=typeof i===e?i.apply(r):i}if(!p.local){i=c.call(r,i,f)}if(i||i===0){q+=i}q+="\n    </div>";return q})})();