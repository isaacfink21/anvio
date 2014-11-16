var VIEWER_WIDTH = window.innerWidth || document.documentElement.clientWidth || document.getElementsByTagName('body')[0].clientWidth;

var layers;
var coverage;
var variability;

function getUrlVars() {
    var map = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
        map[key] = value;
    });
    return map;
}


function loadAll() {
    contig_id = getUrlVars()["contig"];

    $.ajax({
        type: 'GET',
        cache: false,
        url: '/data/charts/' + contig_id,
        success: function(data) {
            contig_data = JSON.parse(data);

            layers = contig_data.layers;
            coverage = contig_data.coverage;
            variability = contig_data.variability;
            competing_nucleotides = contig_data.competing_nucleotides;
            previous_contig_name = contig_data.previous_contig_name;
            next_contig_name = contig_data.next_contig_name;
            index = contig_data.index;
            total = contig_data.total;

            if(layers.length == 0){
                console.log('Warning: no layers returned')
            }

            next_str = " | next &gt;&gt;&gt;";
            prev_str = "&lt;&lt;&lt; prev | ";
            position = index + " of " + total;

            if(next_contig_name)
                next_str = '<small><a href="charts.html?contig=' + next_contig_name + '"> | next &gt;&gt;&gt;</a>';

            if(previous_contig_name)
                prev_str = '<small><a href="charts.html?contig=' + previous_contig_name + '">&lt;&lt;&lt; prev | </a>';

            document.getElementById("header").innerHTML = "<strong>" + contig_id + "</strong> detailed <br /><small>" + prev_str + position + next_str + "</small>";
            createCharts();
        }
    });

}


function createCharts(){
    /* Adapted from Tyler Craft's Multiple area charts with D3.js article:
    http://tympanus.net/codrops/2012/08/29/multiple-area-charts-with-d3-js/  */

    var margin = {top: 20, right: 50, bottom: 150, left: 50};
    var width = VIEWER_WIDTH * .80;
    var chartHeight = 200;
    var height = (chartHeight * (layers.length) + 400);
    var contextHeight = 50;
    var contextWidth = width;

    var svg = d3.select("#chart-container").append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", (height + margin.top + margin.bottom));

    $('#chart-container').css("width", (width + 150) + "px");
    
    var charts = [];
    var maxVariability = 0;
    
    var layersCount = layers.length;
    
    coverage.forEach(function(d) {
        for (var prop in d) {
            if (d.hasOwnProperty(prop)) {
                d[prop] = parseFloat(d[prop]);
            }
        }
    });

    variability.forEach(function(d) {
        for (var prop in d) {
            if (d.hasOwnProperty(prop)) {
                d[prop] = parseFloat(d[prop]);
                
                if (d[prop] > maxVariability) {
                    maxVariability = d[prop];
                }
            }
        }
    });


    for(var i = 0; i < layersCount; i++){
        charts.push(new Chart({
                        name: layers[i],
                        coverage: coverage[i],
                        variability: variability[i],
                        competing_nucleotides: competing_nucleotides[i],
                        id: i,
                        width: width,
                        height: chartHeight,
                        maxVariability: maxVariability,
                        svg: svg,
                        margin: margin,
                        showBottomAxis: (i == layers.length - 1)
                }));
        
    }


    /* Context down below */
    var contextXScale = d3.scale.linear().range([0, contextWidth]).domain(charts[0].xScale.domain());
    
    var contextAxis = d3.svg.axis()
                .scale(contextXScale)
                .tickSize(contextHeight);

    var contextArea = d3.svg.area()
                .interpolate("monotone")
                .x(function(d) { return contextXScale(d); })
                .y0(contextHeight)
                .y1(0);

    var brush = d3.svg.brush()
                .x(contextXScale)
                .on("brush", onBrush);

    var context = svg.append("g")
                .attr("class","context")
                .attr("transform", "translate(" + (margin.left) + "," + (height + margin.top * 3) + ")");
    
    context.append("g")
                .attr("class", "x axis top")
                .attr("transform", "translate(0,0)")
                .call(contextAxis)
                                        
    context.append("g")
                .attr("class", "x brush")
                .call(brush)
                .selectAll("rect")
                .attr("y", 0)
                .attr("height", contextHeight);
    
    function onBrush(){
        /* this will return a date range to pass into the chart object */
        var b = brush.empty() ? contextXScale.domain() : brush.extent();
        b = [Math.floor(b[0]), Math.floor(b[1])];
        for(var i = 0; i < layersCount; i++){
            charts[i].showOnly(b);
        }
    }
}


var base_colors = ['#CCB48F', '#727EA3', '#65567A', '#CCC68F', '#648F7D', '#CC9B8F', '#A37297', '#708059'];

function get_comp_nt_color(nts){
    if(nts == "CT" || nts == "TC")
        return "red";
    if(nts == "GA" || nts == "AG")
        return "green";
    if(nts == "AT" || nts == "TA")
        return "blue";
    if(nts == "CA" || nts == "AC")
        return "purple";
    if(nts == "GT" || nts == "TG")
        return "orange";
    else
        return "black";
}

function Chart(options){
    this.coverage = options.coverage;
    this.variability = options.variability;
    this.competing_nucleotides = options.competing_nucleotides;
    this.width = options.width;
    this.height = options.height;
    this.maxVariability = options.maxVariability;
    this.svg = options.svg;
    this.id = options.id;
    this.name = options.name;
    this.margin = options.margin;
    this.showBottomAxis = options.showBottomAxis;
    
    var localName = this.name;
    var num_data_points = this.variability.length;
    
    this.xScale = d3.scale.linear()
                            .range([0, this.width])
                            .domain([0, this.coverage.length]);
   
    this.maxCoverage = Math.max.apply(null, this.coverage);
    if(this.maxCoverage < 20)
        this.maxCoverage = 20;
    this.yScale = d3.scale.linear()
                            .range([this.height,0])
                            .domain([0,this.maxCoverage]);

    this.yScaleLine = d3.scale.linear()
                            .range([this.height, 0])
                            .domain([0, this.maxVariability]);
    
    var xS = this.xScale;
    var yS = this.yScale;
    var ySL = this.yScaleLine;
    
    this.area = d3.svg.area()
                            .x(function(d, i) { return xS(i); })
                            .y0(this.height)
                            .y1(function(d) { return yS(d); });

    this.line = d3.svg.line()
                            .x(function(d, i) { return xS(i); })
                            .y(function(d, i) { if(i == 0) return ySL(0); if(i == num_data_points - 1) return ySL(0); return ySL(d); })
                            .interpolate('step-before');

    /*
        Assign it a class so we can assign a fill color
        And position it on the page
    */
    this.chartContainer = this.svg.append("g")
                        .attr('class',this.name.toLowerCase())
                        .attr("transform", "translate(" + this.margin.left + "," + (this.margin.top + (this.height * this.id) + (10 * this.id)) + ")");

    this.lineContainer = this.svg.append("g")
                        .attr('class',this.name.toLowerCase())
                        .attr("transform", "translate(" + this.margin.left + "," + (this.margin.top + (this.height * this.id) + (10 * this.id)) + ")");

    this.textContainer = this.svg.append("g")
                        .attr('class',this.name.toLowerCase())
                        .attr("transform", "translate(" + this.margin.left + "," + (this.margin.top + (this.height * this.id) + (10 * this.id)) + ")");

    /* get the color */
    if(this.id + 1 > base_colors.length){
        color = base_colors[this.id % base_colors.length];
    } else {
        color = base_colors[this.id];
    }

    /* Add both into the page */
    this.chartContainer.append("path")
                              .data([this.coverage])
                              .attr("class", "chart")
                              .style("fill", color)
                              .attr("d", this.area);
                                    
    this.lineContainer.append("path")
                              .data([this.variability])
                              .attr("class", "line")
                              .style("stroke", '#000000')
                              .style("stroke-width", "1")
                              .attr("d", this.line);

    this.textContainer.selectAll("text")
                            .data(d3.entries(this.competing_nucleotides))
                            .enter()
                            .append("text")
                            .attr("x", function (d) { return xS(d.key); })
                            .attr("y", function (d) { return 0; })
                            .attr("writing-mode", "tb")
                            .attr("font-size", "7px")
                            .attr("glyph-orientation-vertical", "0")
                            .attr("fill", function (d){return get_comp_nt_color(d.value);})
                            .text(function (d) {
                                return d.value;
                            });


    
    this.xAxisTop = d3.svg.axis().scale(this.xScale).orient("top");

    if(this.id == 0){
        this.chartContainer.append("g")
                    .attr("class", "x axis top")
                    .attr("transform", "translate(0,0)")
                    .call(this.xAxisTop);
    }
    
        
    this.yAxis = d3.svg.axis().scale(this.yScale).orient("left").ticks(5);
    this.yAxisLine = d3.svg.axis().scale(this.yScaleLine).orient("right").ticks(5);
        
    this.chartContainer.append("g")
                   .attr("class", "y axis")
                   .attr("transform", "translate(-15,0)")
                   .call(this.yAxis);

    this.lineContainer.append("g")
                   .attr("class", "y axis")
                   .attr("transform", "translate(" + (this.width + 15) + ",0)")
                   .call(this.yAxisLine);

    this.chartContainer.append("text")
                   .attr("class","country-title")
                   .attr("transform", "translate(0,20)")
                   .text(this.name);
    
}
    
Chart.prototype.showOnly = function(b){
        this.xScale.domain(b); var xS = this.xScale;
        this.chartContainer.selectAll("path").data([this.coverage]).attr("d", this.area);
        this.lineContainer.select("path").data([this.variability]).attr("d", this.line);
        this.textContainer.selectAll("text").data(d3.entries(this.competing_nucleotides)).attr("x", function (d) { return xS(d.key); });
        this.chartContainer.select(".x.axis.top").call(this.xAxisTop);
}

