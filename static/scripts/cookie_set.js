function CookieSet( cookie_name ) {
    this.cookie_name = cookie_name;
    this.store = store = {};
    q.each( ( q.cookie( cookie_name)  || "" ).split( "|" ), function( k, v ) {
        store[ v ] = true;
    });
};
CookieSet.prototype.add = function( value ) {
    this.store[value] = true;
    return this;
};
CookieSet.prototype.remove = function( value ) {
    delete this.store[value];
    return this;
};
CookieSet.prototype.removeAll = function( value ) {
    this.store = {};
    return this;
};
CookieSet.prototype.contains = function( value ) {
    return ( value in this.store );
};
CookieSet.prototype.save = function() {
    t = [];
    for ( key in this.store ) { 
        if ( key != "" ) { t.push( key ) }
    }
    q.cookie( this.cookie_name, t.join( "|" ) );
    return this;
};