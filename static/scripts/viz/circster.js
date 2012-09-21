define( ["libs/d3", "viz/visualization"], function( d3, visualization ) {

// General backbone style inheritence
var Base = function() { this.initialize && this.initialize.apply(this, arguments); }; Base.extend = Backbone.Model.extend;

var SVGUtils = Backbone.Model.extend({

    /**
     * Returns true if element is visible.
     */
    is_visible: function(svg_elt, svg) {
        var eltBRect = svg_elt.getBoundingClientRect(),
            svgBRect = $('svg')[0].getBoundingClientRect();

        if (// To the left of screen?
            eltBRect.right < 0 ||
            // To the right of screen?
            eltBRect.left > svgBRect.right ||
            // Above screen?
            eltBRect.bottom < 0 || 
            // Below screen?
            eltBRect.top > svgBRect.bottom) {
            return false;
        }
        return true;
    }

});

/**
 * Renders a full circster visualization.
 */ 
var CircsterView = Backbone.View.extend({
    className: 'circster',
    
    initialize: function(options) {
        this.total_gap = options.total_gap;
        this.genome = options.genome;
        this.dataset_arc_height = options.dataset_arc_height;
        this.track_gap = 5;
    },
    
    render: function() {
        var self = this,
            dataset_arc_height = this.dataset_arc_height,
            width = self.$el.width(),
            height = self.$el.height(),
            // Compute radius start based on model, will be centered 
            // and fit entirely inside element by default.
            init_radius_start = ( Math.min(width, height)/2 - 
                                  this.model.get('tracks').length * (this.dataset_arc_height + this.track_gap) );

        // Set up SVG element.
        var svg = d3.select(self.$el[0])
              .append("svg")
                .attr("width", width)
                .attr("height", height)
                .attr("pointer-events", "all")
              // Set up zooming, dragging.
              .append('svg:g')
                .call(d3.behavior.zoom().on('zoom', function() {
                    svg.attr("transform",
                      "translate(" + d3.event.translate + ")" + 
                      " scale(" + d3.event.scale + ")");
                    var utils = new SVGUtils();
                    var visible_elts = d3.selectAll('path').filter(function(d, i) {
                        return utils.is_visible(this, svg);
                    });
                    visible_elts.each(function(d, i) {
                        // TODO: redraw visible elements.
                    });
                }))
                .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")")
              .append('svg:g');
                

        // -- Render each dataset in the visualization. --
        this.model.get('tracks').each(function(track, index) {
            var dataset = track.get('genome_wide_data'),
                radius_start = init_radius_start + index * (dataset_arc_height + self.track_gap),
                track_renderer_class = (dataset instanceof visualization.GenomeWideBigWigData ? 
                                        CircsterBigWigTrackRenderer : 
                                        CircsterSummaryTreeTrackRenderer );

            var track_renderer = new track_renderer_class({
                track: track,
                radius_start: radius_start,
                radius_end: radius_start + dataset_arc_height,
                genome: self.genome,
                total_gap: self.total_gap
            });

            track_renderer.render(svg);

        });
    }
});

var CircsterTrackRenderer = Base.extend( {

    initialize: function( options ) {
        this.options = options;
    },

    render: function( svg ) {    
        // Draw background arcs for each chromosome.
        var genome_arcs = this.chroms_layout(),
            radius_start = this.options.radius_start,
            radius_end = this.options.radius_end,
            track_parent_elt = svg.append("g").attr("id", "inner-arc"),
            arc_gen = d3.svg.arc()
                .innerRadius(radius_start)
                .outerRadius(radius_end),
            // Draw arcs.
            chroms_elts = track_parent_elt.selectAll("#inner-arc>path")
                .data(genome_arcs).enter().append("path")
                .attr("d", arc_gen)
                .style("stroke", "#ccc")
                .style("fill",  "#ccc")
                .append("title").text(function(d) { return d.data.chrom; });

        // Render data.
        this.render_data(track_parent_elt);

        // Apply prefs.
        var prefs = this.options.track.get('prefs'),
            block_color = prefs.block_color;
        if (!block_color) { block_color = prefs.color; }
        track_parent_elt.selectAll('path.chrom-data').style('stroke', block_color).style('fill', block_color);
    },

    /**
     * Returns arc layouts for genome's chromosomes/contigs. Arcs are arranged in a circle 
     * separated by gaps.
     */
    chroms_layout: function() {
        // Setup chroms layout using pie.
        var chroms_info = this.options.genome.get_chroms_info(),
            pie_layout = d3.layout.pie().value(function(d) { return d.len; }).sort(null),
            init_arcs = pie_layout(chroms_info),
            gap_per_chrom = this.options.total_gap / chroms_info.length,
            chrom_arcs = _.map(init_arcs, function(arc, index) {
                // For short chroms, endAngle === startAngle.
                var new_endAngle = arc.endAngle - gap_per_chrom;
                arc.endAngle = (new_endAngle > arc.startAngle ? new_endAngle : arc.startAngle);
                return arc;
            });
        return chrom_arcs;
    },

    /**
     * Render chromosome data and attach elements to svg.
     */
    render_chrom_data: function(svg, chrom_arc, data, inner_radius, outer_radius, max) {
    },

    /**
     * Render data as elements attached to svg.
     */
    render_data: function(svg) {
        var self = this,
            chrom_arcs = this.chroms_layout(),
            dataset = this.options.track.get('genome_wide_data'),
            r_start = this.options.radius_start,
            r_end = this.options.radius_end,
                
            // Merge chroms layout with data.
            layout_and_data = _.zip(chrom_arcs, dataset.get('data')),
            
            // Do dataset layout for each chromosome's data using pie layout.
            chroms_data_layout = _.map(layout_and_data, function(chrom_info) {
                var chrom_arc = chrom_info[0],
                    data = chrom_info[1];
                return self.render_chrom_data(svg, chrom_arc, data, 
                                              r_start, r_end, 
                                              dataset.get('min'), dataset.get('max'));
            });

        return chroms_data_layout;
    }
});

/**
 * Rendered for quantitative data.
 */
var CircsterQuantitativeTrackRenderer = CircsterTrackRenderer.extend({

    /**
     * Renders quantitative data with the form [x, value] and assumes data is equally spaced across
     * chromosome.
     */
    render_quantitative_data: function(svg, chrom_arc, data, inner_radius, outer_radius, min, max) {
        // Radius scaler.
        var radius = d3.scale.linear()
                       .domain([min, max])
                       .range([inner_radius, outer_radius]);

        // Scaler for placing data points across arc.
        var angle = d3.scale.linear()
            .domain([0, data.length])
            .range([chrom_arc.startAngle, chrom_arc.endAngle]);

        var line = d3.svg.line.radial()
            .interpolate("linear")
            .radius(function(d) { return radius(d[1]); })
            .angle(function(d, i) { return angle(i); });

        var area = d3.svg.area.radial()
            .interpolate(line.interpolate())
            .innerRadius(radius(0))
            .outerRadius(line.radius())
            .angle(line.angle());

        // Render data.
        var parent = svg.datum(data);
                    
        parent.append("path")
            .attr("class", "chrom-data")
            .attr("d", area);
    }

})

/**
 * Layout for summary tree data in a circster visualization.
 */
var CircsterSummaryTreeTrackRenderer = CircsterQuantitativeTrackRenderer.extend({
    
    /**
     * Renders a chromosome's data.
     */
    render_chrom_data: function(svg, chrom_arc, chrom_data, inner_radius, outer_radius, min, max) {
        // If no chrom data, return null.
        if (!chrom_data || typeof chrom_data === "string") {
            return null;
        }

        return this.render_quantitative_data(svg, chrom_arc, chrom_data[0], inner_radius, outer_radius, min, max);
    }
});

/**
 * Layout for BigWig data in a circster visualization.
 */
var CircsterBigWigTrackRenderer = CircsterQuantitativeTrackRenderer.extend({
    
    /**
     * Renders a chromosome's data.
     */
    render_chrom_data: function(svg, chrom_arc, chrom_data, inner_radius, outer_radius, min, max) {
        var data = chrom_data.data;
        if (data.length === 0) { return; }

        return this.render_quantitative_data(svg, chrom_arc, data, inner_radius, outer_radius, min, max);
    }
});

return {
    CircsterView: CircsterView
};

});
