(function(){var t="0.4.4",j=window.jQuery||window.$||(window.$={}),f={parse:window.JSON&&(window.JSON.parse||window.JSON.decode)||String.prototype.evalJSON&&function(F){return String(F).evalJSON()}||j.parseJSON||j.evalJSON,stringify:Object.toJSON||window.JSON&&(window.JSON.stringify||window.JSON.encode)||j.toJSON};if(!("parse" in f)||!("stringify" in f)){throw new Error("No JSON support found, include //cdnjs.cloudflare.com/ajax/libs/json2/20110223/json2.js to page")}var m={__jstorage_meta:{CRC32:{}}},c={jStorage:"{}"},y=null,o=0,i=false,k={},C=false,z=0,s={},x=+new Date(),A,B={isXML:function(G){var F=(G?G.ownerDocument||G:0).documentElement;return F?F.nodeName!=="HTML":false},encode:function(G){if(!this.isXML(G)){return false}try{return new XMLSerializer().serializeToString(G)}catch(F){try{return G.xml}catch(H){}}return false},decode:function(G){var F=("DOMParser" in window&&(new DOMParser()).parseFromString)||(window.ActiveXObject&&function(I){var J=new ActiveXObject("Microsoft.XMLDOM");J.async="false";J.loadXML(I);return J}),H;if(!F){return false}H=F.call("DOMParser" in window&&(new DOMParser())||window,G,"text/xml");return this.isXML(H)?H:false}};function q(){var F=false;if("localStorage" in window){try{window.localStorage.setItem("_tmptest","tmpval");F=true;window.localStorage.removeItem("_tmptest")}catch(G){}}if(F){try{if(window.localStorage){c=window.localStorage;i="localStorage";z=c.jStorage_update}}catch(M){}}else{if("globalStorage" in window){try{if(window.globalStorage){if(window.location.hostname=="localhost"){c=window.globalStorage["localhost.localdomain"]}else{c=window.globalStorage[window.location.hostname]}i="globalStorage";z=c.jStorage_update}}catch(L){}}else{y=document.createElement("link");if(y.addBehavior){y.style.behavior="url(#default#userData)";document.getElementsByTagName("head")[0].appendChild(y);try{y.load("jStorage")}catch(K){y.setAttribute("jStorage","{}");y.save("jStorage");y.load("jStorage")}var J="{}";try{J=y.getAttribute("jStorage")}catch(I){}try{z=y.getAttribute("jStorage_update")}catch(H){}c.jStorage=J;i="userDataBehavior"}else{y=null;return}}}l();b();w();u();if("addEventListener" in window){window.addEventListener("pageshow",function(N){if(N.persisted){p()}},false)}}function e(){var H="{}";if(i=="userDataBehavior"){y.load("jStorage");try{H=y.getAttribute("jStorage")}catch(G){}try{z=y.getAttribute("jStorage_update")}catch(F){}c.jStorage=H}l();b();u()}function w(){if(i=="localStorage"||i=="globalStorage"){if("addEventListener" in window){window.addEventListener("storage",p,false)}else{document.attachEvent("onstorage",p)}}else{if(i=="userDataBehavior"){setInterval(p,1000)}}}function p(){var F;clearTimeout(C);C=setTimeout(function(){if(i=="localStorage"||i=="globalStorage"){F=c.jStorage_update}else{if(i=="userDataBehavior"){y.load("jStorage");try{F=y.getAttribute("jStorage_update")}catch(G){}}}if(F&&F!=z){z=F;h()}},25)}function h(){var F=f.parse(f.stringify(m.__jstorage_meta.CRC32)),J;e();J=f.parse(f.stringify(m.__jstorage_meta.CRC32));var H,G=[],I=[];for(H in F){if(F.hasOwnProperty(H)){if(!J[H]){I.push(H);continue}if(F[H]!=J[H]&&String(F[H]).substr(0,2)=="2."){G.push(H)}}}for(H in J){if(J.hasOwnProperty(H)){if(!F[H]){G.push(H)}}}E(G,"updated");E(I,"deleted")}function E(K,L){K=[].concat(K||[]);if(L=="flushed"){K=[];for(var J in k){if(k.hasOwnProperty(J)){K.push(J)}}L="deleted"}for(var I=0,F=K.length;I<F;I++){if(k[K[I]]){for(var H=0,G=k[K[I]].length;H<G;H++){k[K[I]][H](K[I],L)}}if(k["*"]){for(var H=0,G=k["*"].length;H<G;H++){k["*"][H](K[I],L)}}}}function n(){var G=(+new Date()).toString();if(i=="localStorage"||i=="globalStorage"){try{c.jStorage_update=G}catch(F){i=false}}else{if(i=="userDataBehavior"){y.setAttribute("jStorage_update",G);y.save("jStorage")}}p()}function l(){if(c.jStorage){try{m=f.parse(String(c.jStorage))}catch(F){c.jStorage="{}"}}else{c.jStorage="{}"}o=c.jStorage?String(c.jStorage).length:0;if(!m.__jstorage_meta){m.__jstorage_meta={}}if(!m.__jstorage_meta.CRC32){m.__jstorage_meta.CRC32={}}}function r(){a();try{c.jStorage=f.stringify(m);if(y){y.setAttribute("jStorage",c.jStorage);y.save("jStorage")}o=c.jStorage?String(c.jStorage).length:0}catch(F){}}function v(F){if(!F||(typeof F!="string"&&typeof F!="number")){throw new TypeError("Key name must be string or numeric")}if(F=="__jstorage_meta"){throw new TypeError("Reserved key name")}return true}function b(){var L,G,J,H,I=Infinity,K=false,F=[];clearTimeout(A);if(!m.__jstorage_meta||typeof m.__jstorage_meta.TTL!="object"){return}L=+new Date();J=m.__jstorage_meta.TTL;H=m.__jstorage_meta.CRC32;for(G in J){if(J.hasOwnProperty(G)){if(J[G]<=L){delete J[G];delete H[G];delete m[G];K=true;F.push(G)}else{if(J[G]<I){I=J[G]}}}}if(I!=Infinity){A=setTimeout(b,I-L)}if(K){r();n();E(F,"deleted")}}function u(){var I,G;if(!m.__jstorage_meta.PubSub){return}var F,H=x;for(I=G=m.__jstorage_meta.PubSub.length-1;I>=0;I--){F=m.__jstorage_meta.PubSub[I];if(F[0]>x){H=F[0];d(F[1],F[2])}}x=H}function d(H,I){if(s[H]){for(var G=0,F=s[H].length;G<F;G++){s[H][G](H,f.parse(f.stringify(I)))}}}function a(){if(!m.__jstorage_meta.PubSub){return}var H=+new Date()-2000;for(var G=0,F=m.__jstorage_meta.PubSub.length;G<F;G++){if(m.__jstorage_meta.PubSub[G][0]<=H){m.__jstorage_meta.PubSub.splice(G,m.__jstorage_meta.PubSub.length-G);break}}if(!m.__jstorage_meta.PubSub.length){delete m.__jstorage_meta.PubSub}}function g(F,G){if(!m.__jstorage_meta){m.__jstorage_meta={}}if(!m.__jstorage_meta.PubSub){m.__jstorage_meta.PubSub=[]}m.__jstorage_meta.PubSub.unshift([+new Date,F,G]);r();n()}function D(K,G){var F=K.length,J=G^F,I=0,H;while(F>=4){H=((K.charCodeAt(I)&255))|((K.charCodeAt(++I)&255)<<8)|((K.charCodeAt(++I)&255)<<16)|((K.charCodeAt(++I)&255)<<24);H=(((H&65535)*1540483477)+((((H>>>16)*1540483477)&65535)<<16));H^=H>>>24;H=(((H&65535)*1540483477)+((((H>>>16)*1540483477)&65535)<<16));J=(((J&65535)*1540483477)+((((J>>>16)*1540483477)&65535)<<16))^H;F-=4;++I}switch(F){case 3:J^=(K.charCodeAt(I+2)&255)<<16;case 2:J^=(K.charCodeAt(I+1)&255)<<8;case 1:J^=(K.charCodeAt(I)&255);J=(((J&65535)*1540483477)+((((J>>>16)*1540483477)&65535)<<16))}J^=J>>>13;J=(((J&65535)*1540483477)+((((J>>>16)*1540483477)&65535)<<16));J^=J>>>15;return J>>>0}j.jStorage={version:t,set:function(G,H,F){v(G);F=F||{};if(typeof H=="undefined"){this.deleteKey(G);return H}if(B.isXML(H)){H={_is_xml:true,xml:B.encode(H)}}else{if(typeof H=="function"){return undefined}else{if(H&&typeof H=="object"){H=f.parse(f.stringify(H))}}}m[G]=H;m.__jstorage_meta.CRC32[G]="2."+D(f.stringify(H),2538058380);this.setTTL(G,F.TTL||0);E(G,"updated");return H},get:function(F,G){v(F);if(F in m){if(m[F]&&typeof m[F]=="object"&&m[F]._is_xml){return B.decode(m[F].xml)}else{return m[F]}}return typeof(G)=="undefined"?null:G},deleteKey:function(F){v(F);if(F in m){delete m[F];if(typeof m.__jstorage_meta.TTL=="object"&&F in m.__jstorage_meta.TTL){delete m.__jstorage_meta.TTL[F]}delete m.__jstorage_meta.CRC32[F];r();n();E(F,"deleted");return true}return false},setTTL:function(G,F){var H=+new Date();v(G);F=Number(F)||0;if(G in m){if(!m.__jstorage_meta.TTL){m.__jstorage_meta.TTL={}}if(F>0){m.__jstorage_meta.TTL[G]=H+F}else{delete m.__jstorage_meta.TTL[G]}r();b();n();return true}return false},getTTL:function(G){var H=+new Date(),F;v(G);if(G in m&&m.__jstorage_meta.TTL&&m.__jstorage_meta.TTL[G]){F=m.__jstorage_meta.TTL[G]-H;return F||0}return 0},flush:function(){m={__jstorage_meta:{CRC32:{}}};r();n();E(null,"flushed");return true},storageObj:function(){function G(){}G.prototype=m;return new G()},index:function(){var F=[],G;for(G in m){if(m.hasOwnProperty(G)&&G!="__jstorage_meta"){F.push(G)}}return F},storageSize:function(){return o},currentBackend:function(){return i},storageAvailable:function(){return !!i},listenKeyChange:function(F,G){v(F);if(!k[F]){k[F]=[]}k[F].push(G)},stopListening:function(G,H){v(G);if(!k[G]){return}if(!H){delete k[G];return}for(var F=k[G].length-1;F>=0;F--){if(k[G][F]==H){k[G].splice(F,1)}}},subscribe:function(F,G){F=(F||"").toString();if(!F){throw new TypeError("Channel not defined")}if(!s[F]){s[F]=[]}s[F].push(G)},publish:function(F,G){F=(F||"").toString();if(!F){throw new TypeError("Channel not defined")}g(F,G)},reInit:function(){e()}};q()})();