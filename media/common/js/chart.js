var globalChartOptions = {
      seriesColors: chartColors,
      grid: {
          backgroundColor: "white"
      },
      axesDefaults: {
          labelRenderer: $.jqplot.CanvasAxisLabelRenderer
      },
      seriesDefaults: { // applies to all rows
          lineWidth: 2,
          style: 'square',
          rendererOptions: { smooth: false }
      },
      highlighter: {
          show: true,
          sizeAdjust: 7.5
      },
      legend: {
          renderer: $.jqplot.EnhancedLegendRenderer,
          show: true,
          showLabels: true,
          location: 'n',
          placement: 'inside',
          //marginTop: "60px",
          //marginBottom: "-25px",
          fontSize: '11px',
          fontFamily: ["Lucida Grande","Lucida Sans Unicode","Arial","Verdana","sans-serif"],
          rendererOptions: {
              seriesToggle: 'normal',
              numberRows: 1
          }
      }
};

var chartColors = [ "#4bb2c5", "#c5b47f", "#EAA228",
                    "#579575", "#839557", "#958c12",
                    "#953579", "#4b5de4", "#d8b83f",
                    "#ff5800", "#0085cc"];  // assumes max of 11 series will be shown

var scenarioPlot;

var chartMetrics = {
  'standing_timber': {
    'variableName': 'standing_timber',
    'title': "Boardfoot Volume",
    'axisLabel': "Standing Boardfeet (MBF)",
    'mapLabel': "Standing Boardfeet (MBF)",
    'mapText': "Standing merchantable boardfoot volume in each stand (MBF/acre)",
    'chartText': "Standing merchantable boardfoot volume across property (MBF Total)",
    'displayChart': true,
    'displayMap': true,
    'axisFormat': "%'d"
  },
  'standing_vol': {
    'variableName': 'standing_vol',
    'title': "Cubic Volume",
    'axisLabel': "Standing volume (ft3)",
    'mapLabel': "Standing volume (ft3)",
    'mapText': "Standing merchantable cubic volume in each stand (ft3/acre)",
    'chartText': "Standing merchantable cubic volume across property (ft3 total)",
    'displayChart': true,
    'displayMap': true,
    'axisFormat': "%'d"
  },
  'age': {
    'variableName': 'age',
    'title': "Age",
    'axisLabel': "Age (years)",
    'mapLabel': "Age (years)",
    'mapText': "Stand Age (years)",
    'chartText': "Age (years)",
    'displayChart': false,
    'displayMap': true,
    'axisFormat': "%'d"
  },
  'ba': {
    'variableName': 'ba',
    'title': "Basal Area",
    'axisLabel': "Basal Area (ft2/acre)",
    'mapLabel': "Basal Area (ft2)",
    'mapText': "Total basal area in each stand (ft2/acre)",
    'chartText': "Basal Area (ft2/acre)",
    'displayChart': false,
    'displayMap': true,
    'axisFormat': "%'d"
  },
  // 'tpa': {
  //   'variableName': 'tpa',
  //   'title': "Trees per acre",
  //   'axisLabel': "Trees per acre",
  //   'mapLabel': "Trees per acre",
  //   'axisFormat': "%'d"
  // },
  'agl_carbon': {
    'variableName': 'agl_carbon',
    'title': "Carbon (Live Tree)",
    'axisLabel': "Carbon (metric tons C)",
    'mapLabel': "Carbon (metric tons C)",
    'mapText': "Carbon storage in above-ground live tree biomass in each stand (metric tons C/acre)",
    'chartText': "Total carbon storage in above-ground live tree biomass across property (metric tons C)",
    'displayChart': true,
    'displayMap': true,
    'axisFormat': "%'d"
  },
  'total_carbon': {
    'variableName': 'total_carbon',
    'title': "Carbon (Stand Total)",
    'axisLabel': "Carbon (metric tons C)",
    'mapLabel': "Carbon (metric tons C)",
    'mapText': "Carbon storage in trees, snags, and downed wood in each stand (metric tons C/acre)",
    'chartText': "Carbon storage in trees, snags, and downed wood across property (metric tons C)",
    'displayChart': true,
    'displayMap': true,
    'axisFormat': "%'d"
  },
  'harvested_timber': {
    'variableName': 'harvested_timber',
    'title': "Boardfoot Yield (each period)",
    'axisLabel': "Timber yield (MBF)",
    'mapLabel': "Timber yield (MBF)",
    'mapText': "Timber yield from each stand over past five years (MBF/ac)",
    'chartText': "Timber yield across property over past five years (MBF)",
    'displayChart': true,
    'displayMap': true,
    'axisFormat': "%'d"
  },
  'cum_harvest': {
    'variableName': 'cum_harvest',
    'title': "Boardfoot Yield (cumulative)",
    'axisLabel': "Cumulative Timber yield (MBF)",
    'mapLabel': "Cumulative Timber yield (MBF)",
    'mapText': "Cumulative boardfoot yield for each stand (MBF/ac)",
    'chartText': "Cumulative boardfoot yield across property (MBF)",
    'displayChart': true,
    'displayMap': true,
    'axisFormat': "%'d"
  },
  'fire': {
    'variableName': 'fire',
    'title': "Fire Hazard",
    'axisLabel': "High Fire Hazard (acres)",
    'mapLabel': "Fire Hazard rating",
    'mapText': "Fire hazard rating (1=low, 2=medium, 3=medium-high, 4=high)",
    'chartText': "Acres of high fire hazard rating across property",
    'displayChart': true,
    'displayMap': true,
    'axisFormat': "%'d"
  },
  'es_btl': {
    'variableName': 'es_btl',
    'title': "Spruce Beetle Hazard",
    'axisLabel': "High Spruce Beetle Hazard (acres)",
    'mapLabel': "Spruce Beetle Hazard rating",
    'mapText': "Spruce beetle hazard rating (4-5=low...7-9=moderate...11-12=high)",
    'chartText': "Acres of high spruce beetle hazard rating",
    'displayChart': true,
    'displayMap': true,
    'axisFormat': "%'d"
  },
  'pine_btl': {
    'variableName': 'pine_btl',
    'title': "Pine Beetle Hazard",
    'axisLabel': "High Pine Beetle Hazard (acres)",
    'mapLabel': "Pine Beetle Hazard rating",
    'mapText': "Pine Beetle Hazard rating (Ponderosa 3-4=low, 5-8=moderate, 9-11=high; Lodgepole 2-7=low, 8-13=moderate, 14=high)",
    'chartText': "Acres at high risk to pine beetle for Ponderosa or Lodgepole pine",
    'displayChart': true,
    'displayMap': true,
    'axisFormat': "%'d"
  }
};

var refreshCharts = function(){

  var selectedMetric = $("#chart-metrics-select").find(":selected").val();
  if (!selectedMetric || !(selectedMetric in chartMetrics)) {
      alert("WARNING: no metric selected. Defaulting to 'agl_carbon'");
      selectedMetric = 'agl_carbon';
  }

  // destroy then replot to prevent memory leaks
  if (scenarioPlot) {
    $('#chart-scenario *').unbind(); // iexplorer
    scenarioPlot.destroy();
  }

  var containerWidth = $("#scenario-charts-tab-content").width();
  var containerHeight = $(window).height();
  $("#chart-scenario").width(containerWidth - 30);
  $("#chart-scenario").height(containerHeight - 300);

  var scenarioData = [];
  var scenarioLabels = [];
  var metric = chartMetrics[selectedMetric];

  $.each(app.scenarios.viewModel.selectedFeatures(), function() {
    var newData = [];
    var resall;
    var res = this.fields.output_property_metrics;

    if (res) {
        resall = res['__all__'];
    }

    if (resall) {
        newData = resall[metric.variableName];
    }

    if (newData.length === 0) {
        newData = [[null]];
    }

    scenarioData.push(newData);
    scenarioLabels.push({'label': this.fields.name});

  });

  $('#chart-scenario-text').html(metric.chartText);

  /*
   *  AGL Regional baseline, hardcoded madness here
   */
  if (metric.variableName == "agl_carbon") {
    var acres = app.scenarios.viewModel.property.acres();
    var baseline_peracre;
    switch (app.scenarios.viewModel.property.variant()) {
      case "Pacific Northwest Coast":
          baseline_peracre = 38.6; // units = metric tons of carbon per acre (not CO2)
          break;
      case "South Central Oregon":
          baseline_peracre = 13.2;
          break;
      case "Eastside Cascades":
          baseline_peracre = 13.2;
          break;
      case "Inland California and Southern Cascades":
          baseline_peracre = 23.6;
          break;
      case "Westside Cascades":
          baseline_peracre = 32.1;
          break;
      case "Blue Mountains":
          baseline_peracre = 10.4;
          break;
    }
    if (baseline_peracre) {
        // baseline = AGL (tC/acre) * acres = AGL(metric tons C)
        var baseline = baseline_peracre * acres;
        scenarioData.push([['2001-12-31 11:59PM', baseline], ['2120-12-31 11:59PM', baseline]]);
        scenarioLabels.push({'label': "Regional Average (" + baseline_peracre + " tC/ac)"});
    }
  }

  if (scenarioData.length > 0) {
    var date = new Date();
    var year_min = date.getFullYear();
    var year_max = date.getFullYear() + 101;
    for (var i = 0; i < scenarioData[0].length; i++) {
        var step_date = year_min + (i * 5);
        scenarioData[0][i][0] = '' + step_date + scenarioData[0][i][0].substring(4);
    }
    var date_min = 'Jan 01, ' + year_min + ' 8:00AM';
    var date_max = 'Jan 01, ' + year_max + ' 8:00AM';
    scenarioPlot = $.jqplot('chart-scenario', scenarioData, $.extend(globalChartOptions, {
        //title: metric.title,
        series: scenarioLabels,
        axes: {
            xaxis: {
              label: "Year",
              renderer: $.jqplot.DateAxisRenderer,
              tickOptions: {formatString:'%Y'},
              min:date_min,
              max:date_max,
              tickInterval:'10 years',
              pad: 0
            },
            yaxis: {
              label: metric.axisLabel,
              tickInterval: 10000,
              tickOptions: {formatString: metric.axisFormat}
            }
        }
    }));
  }
};
