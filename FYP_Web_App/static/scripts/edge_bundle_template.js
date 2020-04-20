var edge_bundle_schema = {
  "$schema": "https://vega.github.io/schema/vega/v5.json",
  "description": "A network diagram of the relations extracted.",
  "padding": 5,
  "width": 720,
  "height": 720,
  "autosize": "none",

  "signals": [
    {
      "name": "tension", "value": 0.85,
      "bind": {"input": "range", "min": 0, "max": 1, "step": 0.01}
    },
    {
      "name": "radius", "value": 280,
      "bind": {"input": "range", "min": 20, "max": 400}
    },
    {
      "name": "extent", "value": 360,
      "bind": {"input": "range", "min": 0, "max": 360, "step": 1}
    },
    {
      "name": "rotate", "value": 0,
      "bind": {"input": "range", "min": 0, "max": 360, "step": 1}
    },
    {
      "name": "textSize", "value": 8,
      "bind": {"input": "range", "min": 2, "max": 20, "step": 1}
    },
    {
      "name": "textOffset", "value": 2,
      "bind": {"input": "range", "min": 0, "max": 10, "step": 1}
    },
    {
      "name": "layout", "value": "cluster",
      "bind": {"input": "radio", "options": ["tidy", "cluster"]}
    },
    { "name": "colorIn", "value": "forestgreen" },
    { "name": "colorOut", "value": "firebrick" },
    { "name": "neutralColor", "value": "grey"},
    { "name": "originX", "update": "width / 2" },
    { "name": "originY", "update": "height / 2" },
    {
      "name": "active", "value": null,
      "on": [
        { "events": "text:mouseover", "update": "datum.id" },
        { "events": "mouseover[!event.item]", "update": "null" }
      ]
    }
  ],

  "data": [
    {
      "name": "tree",
      "url": "/static/edge_bundle.json",
      "transform": [
        {
          "type": "stratify",
          "key": "id",
          "parentKey": "parent"
        },
        {
          "type": "tree",
          "method": {"signal": "layout"},
          "size": [1, 1],
          "as": ["alpha", "beta", "depth", "children"]
        },
        {
          "type": "formula",
          "expr": "(rotate + extent * datum.alpha + 270) % 360",
          "as":   "angle"
        },
        {
          "type": "formula",
          "expr": "inrange(datum.angle, [90, 270])",
          "as":   "leftside"
        },
        {
          "type": "formula",
          "expr": "originX + radius * datum.beta * cos(PI * datum.angle / 180)",
          "as":   "x"
        },
        {
          "type": "formula",
          "expr": "originY + radius * datum.beta * sin(PI * datum.angle / 180)",
          "as":   "y"
        }
      ]
    },
    {
      "name": "leaves",
      "source": "tree",
      "transform": [
        {
          "type": "filter",
          "expr": "!datum.children"
        }
      ]
    },
    {
        "name": "positive",
        "url": "/static/edge_bundle_dependencies_positive.json",
        "transform": [
        {
          "type": "formula",
          "expr": "treePath('tree', datum.source, datum.target)",
          "as":   "treepathpos",
          "initonly": true
        }
      ]
    },
    {
      "name": "selectedp",
      "source": "positive",
      "transform": [
        {
          "type": "filter",
          "expr": "datum.source === active || datum.target === active"
        }
      ]
    },
    {
        "name": "negative",
        "url": "/static/edge_bundle_dependencies_negative.json",
        "transform": [
        {
          "type": "formula",
          "expr": "treePath('tree', datum.source, datum.target)",
          "as":   "treepathneg",
          "initonly": true
        }
      ]
    },
    {
      "name": "selectedneg",
      "source": "negative",
      "transform": [
        {
          "type": "filter",
          "expr": "datum.source === active || datum.target === active"
        }
      ]
    },
    {
        "name": "neutral",
        "url": "/static/edge_bundle_dependencies_neutral.json",
        "transform": [
        {
          "type": "formula",
          "expr": "treePath('tree', datum.source, datum.target)",
          "as":   "treepathneut",
          "initonly": true
        }
      ]
    },
    {
      "name": "selectedneut",
      "source": "neutral",
      "transform": [
        {
          "type": "filter",
          "expr": "datum.source === active || datum.target === active"
        }
      ]
    }
  ],

  "marks": [
    {
      "type": "text",
      "from": {"data": "leaves"},
      "encode": {
        "enter": {
          "text": {"field": "name"},
          "baseline": {"value": "middle"}
        },
        "update": {
          "x": {"field": "x"},
          "y": {"field": "y"},
          "dx": {"signal": "textOffset * (datum.leftside ? -1 : 1)"},
          "angle": {"signal": "datum.leftside ? datum.angle - 180 : datum.angle"},
          "align": {"signal": "datum.leftside ? 'right' : 'left'"},
          "fontSize": {"signal": "textSize"},
          "fontWeight": [
            {"test": "indata('selectedp', 'source', datum.id)", "value": "bold"},
            {"test": "indata('selectedp', 'target', datum.id)", "value": "bold"},
            {"test": "indata('selectedneg', 'source', datum.id)", "value": "bold"},
            {"test": "indata('selectedneg', 'target', datum.id)", "value": "bold"},
            {"test": "indata('selectedneut', 'source', datum.id)", "value": "bold"},
            {"test": "indata('selectedneut', 'target', datum.id)", "value": "bold"},
            {"value": null}
          ],
          "fill": [
            {"test": "datum.id === active", "value": "black"},
            {"value": "black"}
          ]
        }
      }
    },
    {
      "type": "group",
      "from": {
        "facet": {
          "name":  "pospath",
          "data":  "positive",
          "field": "treepathpos"
        }
      },
      "marks": [
        {
          "type": "line",
          "interactive": false,
          "from": {"data": "pospath"},
          "encode": {
            "enter": {
              "interpolate": {"value": "bundle"},
              "strokeWidth": {"value": 1.5}
            },
            "update": {
              "stroke": [
                {"test": "parent.source === active || parent.target === active", "signal": "colorOut"},
                {"value": "steelblue"}
              ],
              "strokeOpacity": [
                {"test": "parent.source === active || parent.target === active", "value": 1},
                {"value": 0.2}
              ],
              "tension": {"signal": "tension"},
              "x": {"field": "x"},
              "y": {"field": "y"}
            }
          }
        }
      ]
    },
    {
      "type": "group",
      "from": {
        "facet": {
          "name":  "negpath",
          "data":  "negative",
          "field": "treepathneg"
        }
      },
      "marks": [
        {
          "type": "line",
          "interactive": false,
          "from": {"data": "negpath"},
          "encode": {
            "enter": {
              "interpolate": {"value": "bundle"},
              "strokeWidth": {"value": 1.5}
            },
            "update": {
              "stroke": [
                {"test": "parent.source === active || parent.target === active", "signal": "colorIn"},
                {"value": "steelblue"}
              ],
              "strokeOpacity": [
                {"test": "parent.source === active || parent.target === active", "value": 1},
                {"value": 0.2}
              ],
              "tension": {"signal": "tension"},
              "x": {"field": "x"},
              "y": {"field": "y"}
            }
          }
        }
      ]
    },
    {
      "type": "group",
      "from": {
        "facet": {
          "name":  "neutpath",
          "data":  "neutral",
          "field": "treepathneut"
        }
      },
      "marks": [
        {
          "type": "line",
          "interactive": false,
          "from": {"data": "neutpath"},
          "encode": {
            "enter": {
              "interpolate": {"value": "bundle"},
              "strokeWidth": {"value": 1.5}
            },
            "update": {
              "stroke": [
                {"test": "parent.source === active || parent.target === active", "signal": "neutralColor"},
                {"value": "steelblue"}
              ],
              "strokeOpacity": [
                {"test": "parent.source === active || parent.target === active", "value": 1},
                {"value": 0.1}
              ],
              "tension": {"signal": "tension"},
              "x": {"field": "x"},
              "y": {"field": "y"}
            }
          }
        }
      ]
    }
  ],

  "scales": [
    {
      "name": "color",
      "type": "ordinal",
      "domain": ["Positive", "Negative", "Neutral"],
      "range": [{"signal": "colorIn"}, {"signal": "colorOut"}, {"signal": "neutralColor"}]
    }
  ],

  "legends": [
    {
      "stroke": "color",
      "orient": "bottom-right",
      "title": "Relation Sentiments",
      "symbolType": "stroke"
    }
  ]
}
