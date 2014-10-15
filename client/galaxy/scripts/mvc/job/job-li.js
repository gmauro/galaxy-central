define([
    'mvc/list/list-item',
    'mvc/dataset/dataset-list',
    "mvc/base-mvc",
    "utils/localization"
], function( LIST_ITEM, DATASET_LIST, BASE_MVC, _l ){
//==============================================================================
var _super = LIST_ITEM.FoldoutListItemView;
/** @class
 */
var JobListItemView = _super.extend(/** @lends JobListItemView.prototype */{

    /** logger used to record this.log messages, commonly set to console */
    //logger              : console,


    className   : _super.prototype.className + " job",
    id          : function(){
        return [ 'job', this.model.get( 'id' ) ].join( '-' );
    },

    foldoutPanelClass : DATASET_LIST.DatasetList,

    /** Set up: instance vars, options, and event handlers */
    initialize : function( attributes ){
        if( attributes.logger ){ this.logger = this.model.logger = attributes.logger; }
        this.log( this + '.initialize:', attributes );
        _super.prototype.initialize.call( this, attributes );

        /** where should pages from links be displayed? (default to new tab/window) */
        this.linkTarget = attributes.linkTarget || '_blank';
        this._setUpListeners();
    },

    /** In this override, add the state as a class for use with state-based CSS */
    _swapNewRender : function( $newRender ){
        _super.prototype._swapNewRender.call( this, $newRender );
        if( this.model.has( 'state' ) ){
            this.$el.addClass( 'state-' + this.model.get( 'state' ) );
        }
        return this.$el;
    },

    /** Stub to return proper foldout panel options */
    _getFoldoutPanelOptions : function(){
        var options = _super.prototype._getFoldoutPanelOptions.call( this );
        return _.extend( options, {
            collection  : this.model.outputCollection,
            selecting   : false
        });
    },

    // ........................................................................ misc
    /** String representation */
    toString : function(){
        return 'JobListItemView(' + this.model + ')';
    }
});

// ............................................................................ TEMPLATES
/** underscore templates */
JobListItemView.prototype.templates = (function(){
//TODO: move to require text! plugin

    var elTemplate = BASE_MVC.wrapTemplate([
        '<div class="list-element">',
            '<div class="id"><%= model.id %></div>',
            // errors, messages, etc.
            '<div class="warnings"></div>',

            // multi-select checkbox
            '<div class="selector">',
                '<span class="fa fa-2x fa-square-o"></span>',
            '</div>',
            // space for title bar buttons - gen. floated to the right
            '<div class="primary-actions"></div>',
            '<div class="title-bar"></div>',

            // expandable area for more details
            '<div class="details"></div>',
        '</div>'
    ]);

    var titleBarTemplate = BASE_MVC.wrapTemplate([
        // adding a tabindex here allows focusing the title bar and the use of keydown to expand the dataset display
        '<div class="title-bar clear" tabindex="0">',
            //'<span class="state-icon"></span>',
            '<div class="title">',
                '<span class="name"><%- job.tool_id %></span>',
            '</div>',
            '<div class="subtitle"></div>',
        '</div>'
    ], 'job' );

    //var subtitleTemplate = BASE_MVC.wrapTemplate([
    //    // override this
    //    '<div class="subtitle">',
    //        _l( 'Created' ), ': <%= new Date( job.create_time ).toString() %>, ',
    //        _l( 'Updated' ), ': <%= new Date( job.update_time ).toString() %>',
    //    '</div>'
    //], 'job' );
    //
    //var detailsTemplate = BASE_MVC.wrapTemplate([
    //    '<div class="details">',
    //        '<div class="params">',
    //            '<% _.each( job.params, function( param, paramName ){ %>',
    //                '<div class="param">',
    //                    '<label class="prompt"><%= paramName %></label>',
    //                    '<span class="value"><%= param %></span>',
    //                '</div>',
    //            '<% }) %>',
    //        '</div>',
    //    '</div>'
    //], 'job' );

    return _.extend( {}, _super.prototype.templates, {
        //el    : elTemplate,
        titleBar    : titleBarTemplate,
        //subtitle    : subtitleTemplate,
        //details     : detailsTemplate
    });
}());


//=============================================================================
    return {
        JobListItemView : JobListItemView
    };
});
