// dependencies
define(['utils/utils'], function(Utils) {

// widget
return Backbone.View.extend(
{
    // number of columns and rows
    colNumber: 0,
    rowNumber: 0,
    
    // indices
    rowIndex: [],
    colIndex: [],
    
    // labels
    rowLabel: [],
    colLabel: [],
    
    // cell size
    cellSize: 0,
    
    // color buckets
    nColors: 0,
        
    // default settings
    optionsDefault: {
        pace    : 1000,
        margin  : {
            top         : 50,
            right       : 10,
            bottom      : 50,
            left        : 100
        },
        colors  : ['#005824','#1A693B','#347B53','#4F8D6B','#699F83','#83B09B','#9EC2B3','#B8D4CB','#D2E6E3','#EDF8FB','#FFFFFF','#F1EEF6','#E6D3E1','#DBB9CD','#D19EB9','#C684A4','#BB6990','#B14F7C','#A63467','#9B1A53','#91003F']
    },

    // initialize
    initialize: function(options) {
        // link this
        var self = this;
        
        // load options
        this.options = Utils.merge(options, this.optionsDefault)
        
        // check requirements
        if (!this.options.data || !this.options.div) {
            console.debug('FAILED - HeatMapPlugin::initialize() - Parameters (container and/or data) missing.');
            return;
        }
        
        // link data
        this.data = this.options.data;
        
        // set element
        this.setElement(this.options.div);
        
        //
        // data indexing
        //
        
        // labels (in alphabetical order)
        this.rowLabel = [];
        this.colLabel = [];
        
        // index (order from original dataset)
        this.rowIndex = [];
        this.colIndex = [];
        
        // unique keys (key indices are unique per label and indicate the labels rank in the alphabetical sorting)
        this.colRank = {};
        this.rowRank = {};
        
        //
        // identify and parse labels
        //
        for (var i in this.data) {
            var cell = this.data[i];
            
            // add label to index list
            var col_label = cell.col_label;
            if (this.colRank[col_label] === undefined) {
                this.colRank[col_label] = true;
                this.colLabel.push(col_label);
                this.colIndex.push(col_label);
            }
            var row_label = cell.row_label;
            if (this.rowRank[row_label] === undefined) {
                this.rowRank[row_label] = true;
                this.rowLabel.push(row_label);
                this.rowIndex.push(row_label);
            }
        }
        
        //
        // sort labels and update rank dictionary
        //
        
        // set sizes
        this.rowNumber = this.rowLabel.length
        this.colNumber = this.colLabel.length
        
        // sort labels alphabetical
        this.rowLabel.sort();
        this.colLabel.sort();
        
        // generate sorted key list for rows
        for (var i in this.rowLabel) {
            var row_label = this.rowLabel[i];
            var row_rank = parseInt(i);
            this.rowRank[row_label] = row_rank;
        }
        
        // generate sorted key list for columns
        for (var i in this.colLabel) {
            var col_label = this.colLabel[i];
            var col_rank = parseInt(i);
            this.colRank[col_label] = col_rank;
        }
        
        //
        // parse indexing from rank dictionary to cells
        // identify data range
        //
        
        // min/max
        this.max = undefined;
        this.min = undefined
        
        // add indices to data
        for (var i in this.data) {
            // get cell data
            var cell = this.data[i];
            
            // add rank
            cell.col_rank = this.colRank[cell.col_label];
            cell.row_rank = this.rowRank[cell.row_label];
            
            // identify max/min values
            if (this.min == undefined || this.min > cell.value) {
                this.min = cell.value;
            }
            if (this.max == undefined || this.max < cell.value) {
                this.max = cell.value;
            }
        }
        
        //
        // translate original create cluster from order in original data
        //
        
        // generate sorted key list for columns
        for (var i in this.colIndex) {
            this.colIndex[i] = this.colRank[this.colIndex[i]];
        }
        // generate sorted key list for columns
        for (var i in this.rowIndex) {
            this.rowIndex[i] = this.rowRank[this.rowIndex[i]];
        }
        
        // middle
        this.mid = (this.max + this.min) / 2;
        
        //
        // set colors
        //
        
        // identify buckets
        this.nColors = this.options.colors.length;
        
        // color scale
        this.colorScale = d3.scale.quantile()
            .domain([this.min, this.mid, this.max])
            .range(this.options.colors);
        
        //
        // add ui elements
        //
        // create ui elements
        this.$tooltip = $(this._templateTooltip());
        this.$select  = $(this._templateSelect());
        
        // append
        this.$el.append(this.$tooltip);
        this.$el.append(this.$select);
        
        // add event to select field
        this.$select.on('change', function(){
            self._sortByOrder(this.value);
        });
        
        //
        // finally draw the heatmap
        //
        this._draw();
    },
    
    _draw: function() {
        // link this
        var self = this;
        
        // container
        var container_width = this.$el.width();
        var container_height = this.$el.height();
        
        // get height
        this.width = this.$el.width() - this.options.margin.left - this.options.margin.right;
        this.height = this.$el.height() - this.options.margin.top - this.options.margin.bottom;
        
        // calculate cell size
        this.cellSize = Math.min(parseInt(this.height / this.rowNumber),
                                 parseInt(this.width / this.colNumber));
        
        // set width/height for plugin
        this.width  = this.cellSize * this.colNumber;
        this.height = this.cellSize * this.rowNumber;
        
        // get dimensions
        var margin              = this.options.margin;
        var width               = this.width;
        var height              = this.height;
        
        // add main group and translate
        this.svg = d3.select(this.$el[0]).append('svg')
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + (container_width - width) / 2 + "," + (container_height - height) / 2 + ")")
      
        // reset sorting
        this.rowSortOrder   = false;
        this.colSortOrder   = false;
        
        // build
        this.rowLabels      = this._buildRowLabels();
        this.colLabels      = this._buildColLabels();
        this.heatMap        = this._buildHeatMap();
        this.legend         = this._buildLegend();
    },
        
    // build legend
    _buildLegend: function() {
        // link this
        var self = this;
        
        // gather data
        var cellSize        = this.cellSize;
        var height          = this.height;
        var legendCellWidth = this.width / this.nColors;
        
        // create range labels
        var dataRange = [];
        for(var i = 0; i < this.nColors; i++) {
            dataRange.push('');
        }
        
        // prepare indices
        var dataRangeMin = 0;
        var dataRangeMid = parseInt((dataRange.length - 1) / 2);
        var dataRangeMax = dataRange.length - 1;
        
        // add labels
        dataRange[dataRangeMin] = this.min;
        dataRange[dataRangeMid] = this.mid;
        dataRange[dataRangeMax] = this.max;
        
        // create legend
        var legend = this.svg.selectAll(".legend")
            .data(dataRange)
            .enter().append("g")
            .attr("class", "legend");

        // add boxes
        legend.append("rect")
            .attr("x", function(d, i) {
                return legendCellWidth * i;
            })
            .attr("y", height + cellSize)
            .attr("width", legendCellWidth)
            .attr("height", cellSize)
            .style("fill", function(d, i) {
                return self.options.colors[i];
            });

        // add text
        legend.append("text")
            .attr("class", "mono")
            .text(function(d) {
                return d;
            })
            .attr("width", legendCellWidth)
            .attr("x", function(d, i) {
                return legendCellWidth * i;
            })
            .attr("y", height + cellSize)
            .style("font-size", cellSize + "px");
    },
    
    // build column labels
    _buildColLabels: function() {
        // link this
        var self = this;
        
        // gather data
        var cellSize = this.cellSize;
        var colIndex = this.colIndex;
        var colLabel = this.colLabel;
        
        // column labels
        var colLabels = this.svg.append("g")
            .selectAll(".colLabelg")
            .data(colLabel)
            .enter()
            .append("text")
            .text(function (d) {
                return d;
            })
            .attr("x", 0)
            .attr("y", function (d, i) {
                return colIndex.indexOf(i) * cellSize;
            })
            .style("font-size", cellSize + "px")
            .style("text-anchor", "left")
            .attr("transform", "translate(" + cellSize / 2 + ", -17) rotate (-90)")
            .attr("class",  function (d, i) {
                return "colLabel mono c" + i;
            })
            .on("mouseover", function(d) {
                d3.select(this).classed("text-hover",true);
                d3.select(this).style("font-size", parseInt(cellSize * 1.3) + "px");
            })
            .on("mouseout" , function(d) {
                d3.select(this).classed("text-hover",false);
                d3.select(this).style("font-size", parseInt(cellSize) + "px");
            })
            .on("click", function(d, i) {
                self.colSortOrder=!self.colSortOrder;
                self._sortByLabel("c", i, self.colSortOrder);
                d3.select("#order").property("selectedIndex", 4).node().focus();
            });
    },
    
    // build row labels
    _buildRowLabels: function() {
        // link this
        var self = this;
        
        // gather data
        var cellSize = this.cellSize;
        var rowIndex = this.rowIndex;
        var rowLabel = this.rowLabel;
        
        // draw labels
        var rowLabels = this.svg.append("g")
            .selectAll(".rowLabelg")
            .data(rowLabel)
            .enter()
            .append("text")
            .text(function (d) {
                return d;
            })
            .attr("x", 0)
            .attr("y", function (d, i) {
                return rowIndex.indexOf(i) * cellSize;
            })
            .style("font-size", cellSize + "px")
            .style("text-anchor", "end")
            .attr("transform", "translate(-10," + cellSize / 1.5 + ")")
            .attr("class", function (d, i) {
                return "rowLabel mono r" + i;
            } )
            .on("mouseover", function(d) {
                d3.select(this).classed("text-hover",true);
                d3.select(this).style("font-size", parseInt(cellSize * 1.3) + "px");
            })
            .on("mouseout" , function(d) {
                d3.select(this).classed("text-hover",false);
                d3.select(this).style("font-size", parseInt(cellSize) + "px");
            })
            .on("click", function(d, i) {
                self.rowSortOrder=!self.rowSortOrder;
                self._sortByLabel("r", i, self.rowSortOrder);
                d3.select("#order").property("selectedIndex", 4).node().focus();
            });
    },
    
    // build heat map
    _buildHeatMap: function() {
        // link this
        var self = this;
        
        // gather data
        var cellSize = this.cellSize;
        var rowIndex = this.rowIndex;
        var rowLabel = this.rowLabel;
        var colIndex = this.colIndex;
        var colLabel = this.colLabel;
        
        // heat map
        var heatMap = this.svg.append("g").attr("class","g3")
            .selectAll(".cellg")
            .data(self.data, function(d) {
                return d.row_rank + ":" + d.col_rank;
            })
            .enter()
            .append("rect")
            .attr("x", function(d) {
                return colIndex.indexOf(d.col_rank) * cellSize;
            })
            .attr("y", function(d) {
                return rowIndex.indexOf(d.row_rank) * cellSize;
            })
            .attr("class", function(d){
                return "cell cell-border cr" + d.row_rank + " cc" + d.col_rank;
            })
            .attr("width", cellSize)
            .attr("height", cellSize)
            .style("fill", function(d) {
                return self.colorScale(d.value);
            })
            .on("mouseover", function(d){
                // highlight text
                d3.select(this).classed("cell-hover",true);
                d3.selectAll(".rowLabel").classed("text-highlight",function(r,ri){ return ri==(d.row_rank);});
                d3.selectAll(".colLabel").classed("text-highlight",function(c,ci){ return ci==(d.col_rank);});
                
                // update the tooltip position and value
                d3.select("#heatmap-tooltip")
                    .style("left", (d3.event.pageX+10) + "px")
                    .style("top", (d3.event.pageY-10) + "px")
                    .select("#value")
                    .text("Label: " + rowLabel[d.row_rank] + " | " + colLabel[d.col_rank] + ", Value: " + d.value);
                // show the tooltip
                d3.select("#heatmap-tooltip").classed("hidden", false);
            })
            .on("mouseout", function(){
                d3.select(this).classed("cell-hover",false);
                d3.selectAll(".rowLabel").classed("text-highlight",false);
                d3.selectAll(".colLabel").classed("text-highlight",false);
                d3.select("#heatmap-tooltip").classed("hidden", true);
            });
    },
    
    // change ordering of cells
    _sortByLabel: function(rORc, i, sortOrder) {
        // get cell size
        var cellSize = this.cellSize;
        
        // define transition / prepare element
        var t = this.svg.transition().duration(this.options.pace);
        
        // collect cells
        var cells=[];
        t.selectAll(".c" + rORc + i)
            .filter(function(ce){
            cells.push(ce);
        });
        
        // sort cells
        cells.sort(function(a, b) {
            if (sortOrder) {
                return b.value - a.value;
            } else {
                return a.value - b.value;
            }
        });
            
        // rows or columns
        if(rORc == "r") {
            // get sorted key list
            var sorted = [];
            for (var i in cells) {
                sorted.push(cells[i].col_rank);
            }
            
            // sort cells
            t.selectAll(".cell")
                .attr("x", function(d) {
                    return sorted.indexOf(d.col_rank) * cellSize;
                });
                
            // sort labels
            t.selectAll(".colLabel")
                .attr("y", function (d, i) {
                    return sorted.indexOf(i) * cellSize;
                });
        } else {
            // get sorted key list
            sorted = [];
            for (var i in cells) {
                sorted.push(cells[i].row_rank);
            }
            
            // sort cells
            t.selectAll(".cell")
                .attr("y", function(d) {
                    return sorted.indexOf(d.row_rank) * cellSize;
            });
            
            // sort labels
            t.selectAll(".rowLabel")
                .attr("y", function (d, i) {
                    return sorted.indexOf(i) * cellSize;
            });
        }
    },

    // sort function
    _sortByOrder: function (value) {
        // link this
        var self = this;
        
        // gather data
        var cellSize = this.cellSize;
        var rowIndex = this.rowIndex;
        var rowLabel = this.rowLabel;
        var colIndex = this.colIndex;
        var colLabel = this.colLabel;
        
        // set duration / select element
        var t = this.svg.transition().duration(this.options.pace);
        if(value=="hclust"){
            t.selectAll(".cell")
                .attr("x", function(d) {
                    return colIndex.indexOf(d.col_rank) * cellSize;
                })
                .attr("y", function(d) {
                    return rowIndex.indexOf(d.row_rank) * cellSize;
                });

            t.selectAll(".rowLabel")
                .attr("y", function(d, i) {
                    return rowIndex.indexOf(i) * cellSize;
                });

            t.selectAll(".colLabel")
                .attr("y", function(d, i) {
                    return colIndex.indexOf(i) * cellSize;
                });

        } else if (value=="byboth") {
            t.selectAll(".cell")
                .attr("x", function(d) {
                    return d.col_rank * cellSize;
                })
                .attr("y", function(d) {
                    return d.row_rank * cellSize;
                });

            t.selectAll(".rowLabel")
                .attr("y", function (d, i) {
                    return i * cellSize;
                });

            t.selectAll(".colLabel")
                .attr("y", function (d, i) {
                    return i * cellSize;
                });
        } else if (value=="byrow") {
            t.selectAll(".cell")
                .attr("y", function(d) {
                    return d.row_rank * cellSize;
                });

            t.selectAll(".rowLabel")
                .attr("y", function (d, i) {
                    return i * cellSize;
                });
        } else if (value=="bycol"){
            t.selectAll(".cell")
                .attr("x", function(d) {
                    return d.col_rank * cellSize;
                });
            t.selectAll(".colLabel")
                .attr("y", function (d, i) {
                    return i * cellSize;
                });
        }
    },
    
    // selection of cells
    _addSelectionTool: function() {
        //
        // selection
        //
        var sa=d3.select(".g3")
        .on("mousedown", function() {
            if( !d3.event.altKey) {
                d3.selectAll(".cell-selected").classed("cell-selected", false);
                d3.selectAll(".rowLabel").classed("text-selected", false);
                d3.selectAll(".colLabel").classed("text-selected", false);
            }
            var p = d3.mouse(this);
            sa.append("rect")
            .attr({
                rx      : 0,
                ry      : 0,
                class   : "selection",
                x       : p[0],
                y       : p[1],
                width   : 1,
                height  : 1
            })
        })
        .on("mousemove", function() {
            var s = sa.select("rect.selection");
      
            if(!s.empty()) {
                var p = d3.mouse(this),
                d = {
                    x       : parseInt(s.attr("x"), 10),
                    y       : parseInt(s.attr("y"), 10),
                    width   : parseInt(s.attr("width"), 10),
                    height  : parseInt(s.attr("height"), 10)
                },
                move = {
                    x : p[0] - d.x,
                    y : p[1] - d.y
                };
      
                if(move.x < 1 || (move.x*2<d.width)) {
                    d.x = p[0];
                    d.width -= move.x;
                } else {
                    d.width = move.x;       
                }

                if(move.y < 1 || (move.y*2<d.height)) {
                    d.y = p[1];
                    d.height -= move.y;
                } else {
                    d.height = move.y;       
                }
                s.attr(d);
      
                // deselect all temporary selected state objects
                d3.selectAll(".cell-selection.cell-selected").classed("cell-selected", false);
                d3.selectAll(".text-selection.text-selected").classed("text-selected",false);
                d3.selectAll(".cell").filter(function(cell_d, i) {
                    if(!d3.select(this).classed("cell-selected") &&
                        // inner circle inside selection frame
                        (this.x.baseVal.value)+cellSize >= d.x && (this.x.baseVal.value)<=d.x+d.width &&
                        (this.y.baseVal.value)+cellSize >= d.y && (this.y.baseVal.value)<=d.y+d.height)
                        {
                            d3.select(this)
                                .classed("cell-selection", true)
                                .classed("cell-selected", true);

                            d3.select(".r"+(cell_d.row_rank))
                                .classed("text-selection",true)
                                .classed("text-selected",true);

                            d3.select(".c"+(cell_d.col_rank))
                                .classed("text-selection",true)
                                .classed("text-selected",true);
                        }
                });
            }
        })
        .on("mouseup", function() {
            // remove selection frame
            sa.selectAll("rect.selection").remove();

            // remove temporary selection marker class
            d3.selectAll(".cell-selection").classed("cell-selection", false);
            d3.selectAll(".text-selection").classed("text-selection",false);
        })
        .on("mouseout", function() {
            if(d3.event.relatedTarget.tagName=='html') {
                // remove selection frame
                sa.selectAll("rect.selection").remove();
            
                // remove temporary selection marker class
                d3.selectAll(".cell-selection").classed("cell-selection", false);
                d3.selectAll(".rowLabel").classed("text-selected",false);
                d3.selectAll(".colLabel").classed("text-selected",false);
            }
        });
    },

    // template
    _templateSelect: function() {
        return  '<select id="order">' +
                    '<option value="hclust">Cluster</option>' +
                    '<option value="byboth">Sort by row and column</option>' +
                    '<option value="byrow">Sort by row label</option>' +
                    '<option value="bycol">Sort by column label</option>' +
                '</select>';
    },
    
    // template
    _templateTooltip: function() {
        return  '<div id="heatmap-tooltip" class="hidden">' +
                    '<p><span id="value"></p>'
                '</div>';
    }
});
});