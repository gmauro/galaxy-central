define([],function(){function l(r,q){for(var p in r){if(r.hasOwnProperty(p)){q(r[p],p,r)}}}function i(r,q){for(var p in q){if(q.hasOwnProperty(p)){r[p]=q[p]}}return r}function f(r,q){for(var p in q){if(q.hasOwnProperty(p)){if(!r.hasOwnProperty(p)||r[p]!==q[p]){return false}}}return true}function c(w,p){var t=typeof p==="function"?p:undefined,s=typeof p==="object"?p:undefined,u=[],q=0;for(var r in w){if(w.hasOwnProperty(r)){var v=w[r];if(t){u.push(t.call(v,v,r,q))}else{if(s){if(typeof v==="object"&&f(v,s)){u.push(v)}}else{u.push(v)}}q+=1}}return u}function g(r,s,q){var p=this;p.source=r!==undefined?r:null;p.target=s!==undefined?s:null;p.data=q||null;return p}g.prototype.toString=function(){return this.source+"->"+this.target};g.prototype.toJSON=function(){var p={source:this.source,target:this.target};if(this.data){p.data=this.data}return p};function m(q,r){var p=this;p.name=q!==undefined?q:"(unnamed)";p.data=r||null;p.edges={};p.degree=0;return p}window.Vertex=m;m.prototype.toString=function(){return"Vertex("+this.name+")"};m.prototype.eachEdge=function(p){return c(this.edges,p)};m.prototype.toJSON=function(){return{name:this.name,data:this.data}};var k=function(r,q){var p=this;p.graph=r;p.processFns=q||{vertexEarly:function(t,s){},edge:function(u,t,s){},vertexLate:function(t,s){}};p._cache={};return p};k.prototype.search=function e(q){var p=this;if(q in p._cache){return p._cache[q]}if(!(q instanceof m)){q=p.graph.vertices[q]}return(p._cache[q.name]=p._search(q))};k.prototype._searchTree=function a(q){var p=this;return new j(true,{edges:q.edges,vertices:Object.keys(q.discovered).map(function(r){return p.graph.vertices[r].toJSON()})})};k.prototype.searchTree=function b(p){return this._searchTree(this.search(p))};var n=function(r,q){var p=this;k.call(this,r,q);return p};n.prototype=new k();n.prototype.constructor=n;n.prototype._search=function d(u,s){s=s||{discovered:{},edges:[]};var r=this,p=[];function q(v,w){var x=this;if(r.processFns.edge){r.processFns.edge.call(r,x,w,s)}if(!s.discovered[v.name]){s.discovered[v.name]=true;s.edges.push({source:x.name,target:v.name});p.push(v)}}s.discovered[u.name]=true;p.push(u);while(p.length){var t=p.shift();if(r.processFns.vertexEarly){r.processFns.vertexEarly.call(r,t,s)}r.graph.eachAdjacent(t,q);if(r.processFns.vertexLate){r.processFns.vertexLate.call(r,t,s)}}return s};var h=function(r,q){var p=this;k.call(this,r,q);return p};h.prototype=new k();h.prototype.constructor=h;h.prototype._search=function(u,q){q=q||{discovered:{},edges:[],entryTimes:{},exitTimes:{}};var p=this,t=0;function s(w,x){var v=this;if(p.processFns.edge){p.processFns.edge.call(p,v,x,q)}if(!q.discovered[w.name]){q.edges.push({source:v.name,target:w.name});r(w)}}function r(v){q.discovered[v.name]=true;if(p.processFns.vertexEarly){p.processFns.vertexEarly.call(p,v,q)}q.entryTimes[v.name]=t++;p.graph.eachAdjacent(v,s);if(p.processFns.vertexLate){p.processFns.vertexLate.call(p,v,q)}q.exitTimes[v.name]=t++}r(u);return q};function j(q,r,p){this.directed=q||false;return this.init(p).read(r)}window.Graph=j;j.prototype.init=function(q){q=q||{};var p=this;p.allowReflexiveEdges=q.allowReflexiveEdges||false;p.vertices={};p.numEdges=0;return p};j.prototype.read=function(q){if(!q){return this}var p=this;if(q.hasOwnProperty("nodes")){return p.readNodesAndLinks(q)}if(q.hasOwnProperty("vertices")){return p.readVerticesAndEdges(q)}return p};j.prototype.readNodesAndLinks=function(q){if(!(q&&q.hasOwnProperty("nodes"))){return this}var p=this;q.nodes.forEach(function(r){p.createVertex(r.name,r.data)});(q.links||[]).forEach(function(u,s){var r=q.nodes[u.source].name,t=q.nodes[u.target].name;p.createEdge(r,t,p.directed)});return p};j.prototype.readVerticesAndEdges=function(q){if(!(q&&q.hasOwnProperty("vertices"))){return this}var p=this;q.vertices.forEach(function(r){p.createVertex(r.name,r.data)});(q.edges||[]).forEach(function(s,r){p.createEdge(s.source,s.target,p.directed)});return p};j.prototype.createVertex=function(p,q){if(this.vertices[p]){return this.vertices[p]}return(this.vertices[p]=new m(p,q))};j.prototype.createEdge=function(q,r,t,u){var v=q===r;if(!this.allowReflexiveEdges&&v){return null}sourceVertex=this.vertices[q];targetVertex=this.vertices[r];if(!(sourceVertex&&targetVertex)){return null}var p=this,s=new g(q,r,u);sourceVertex.edges[r]=s;sourceVertex.degree+=1;p.numEdges+=1;if(!v&&!t){p.createEdge(r,q,true)}return s};j.prototype.edges=function(p){return Array.prototype.concat.apply([],this.eachVertex(function(q){return q.eachEdge(p)}))};j.prototype.eachVertex=function(p){return c(this.vertices,p)};j.prototype.adjacent=function(q){var p=this;return c(q.edges,function(r){return p.vertices[r.target]})};j.prototype.eachAdjacent=function(r,q){var p=this;return c(r.edges,function(t){var s=p.vertices[t.target];return q.call(r,s,t)})};j.prototype.print=function(){var p=this;console.log("Graph has "+Object.keys(p.vertices).length+" vertices");p.eachVertex(function(q){console.log(q.toString());q.eachEdge(function(r){console.log("\t "+r)})});return p};j.prototype.toDOT=function(){var q=this,p=[];p.push("graph bler {");q.edges(function(r){p.push("\t"+r.from+" -- "+r.to+";")});p.push("}");return p.join("\n")};j.prototype.toNodesAndLinks=function(){var p=this,q={};return{nodes:p.eachVertex(function(t,s,r){q[t.name]=r;return t.toJSON()}),links:p.edges(function(s){var r=s.toJSON();r.source=q[s.source];r.target=q[s.target];return r})}};j.prototype.toVerticesAndEdges=function(){var p=this;return{vertices:p.eachVertex(function(r,q){return r.toJSON()}),edges:p.edges(function(q){return q.toJSON()})}};j.prototype.breadthFirstSearch=function(q,p){return new n(this).search(q)};j.prototype.breadthFirstSearchTree=function(q,p){return new n(this).searchTree(q)};j.prototype.depthFirstSearch=function(q,p){return new h(this).search(q)};j.prototype.depthFirstSearchTree=function(q,p){return new h(this).searchTree(q)};j.prototype.weakComponents=function(){var r=this,u=this,q,t=[];function p(v){var w=new h(u)._search(v);q=q.filter(function(x){return !(x in w.discovered)});return{vertices:Object.keys(w.discovered).map(function(x){return r.vertices[x].toJSON()}),edges:w.edges.map(function(y){var x=r.vertices[y.target].edges[y.source]!==undefined;if(r.directed&&x){var z=y.source;y.source=y.target;y.target=z}return y})}}if(r.directed){u=new j(false,r.toNodesAndLinks())}q=Object.keys(u.vertices);while(q.length){var s=u.vertices[q.shift()];t.push(p(s))}return t};j.prototype.weakComponentGraph=function(){var p=this.weakComponents();return new j(this.directed,{vertices:p.reduce(function(r,q){return r.concat(q.vertices)},[]),edges:p.reduce(function(r,q){return r.concat(q.edges)},[])})};j.prototype.weakComponentGraphArray=function(){return this.weakComponents().map(function(p){return new j(this.directed,p)})};function o(s,p,r){var u={nodes:[],links:[]};function t(v){return Math.floor(Math.random()*v)}for(var q=0;q<p;q++){u.nodes.push({name:q})}for(q=0;q<r;q++){u.links.push({source:t(p),target:t(p)})}return new j(s,u)}return{Vertex:m,Edge:g,BreadthFirstSearch:n,DepthFirstSearch:h,Graph:j,randGraph:o}});