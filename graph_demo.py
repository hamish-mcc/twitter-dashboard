import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.figure_factory as ff
import dash_cytoscape as cyto
from tweepy_helper import get_tweets
from dash.dependencies import Input, Output
from plotly.offline import init_notebook_mode
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

init_notebook_mode(connected=True)
pio.templates.default = 'simple_white'

# External script
external_scripts = [
    'https://cdnjs.cloudflare.com/ajax/libs/animejs/2.0.2/anime.min.js']

app = dash.Dash(external_stylesheets=[dbc.themes.SOLAR], external_scripts=external_scripts)

# Layout
app.layout = dbc.Container([
    dbc.Row([html.H1("Twitter #explorer", className="ml12")]),
    dcc.Tabs(className="tabs", children=[
        dcc.Tab(label="Network Visualisation", className="my-tab", selected_className="selected_tab", children=[
            dbc.Container([
                dbc.Row([
                    dbc.Col(html.Div([
                        html.Br(),
                        dbc.Label("Search Phrase", html_for="search_phrase", style={'font-size': '1.5rem', 'margin-bottom': '0px'}),
                        dbc.Input(id="search_phrase", placeholder="Enter a search phrase...",
                                  type="text", debounce=True),
                        html.Br(),
                        html.H4("Node Info", style={'margin-bottom': '0px'}),
                        html.P("Click a node for details",
                               style={'margin-bottom': '4px'}),
                        html.Div(id='cytoscape-tapNodeData-json',
                                 style={'whiteSpace': 'pre-line'}),
                        html.Br(),
                        html.H4("Edge Info", style={'margin-bottom': '0px'}),
                        html.P("Click an edge for details",
                               style={'margin-bottom': '4px'}),
                        html.Div(id='cytoscape-tapEdgeData-output',
                                 style={'whiteSpace': 'pre-line', 'margin-bottom': '0px'})
                    ]), md=3),

                    dbc.Col(
                        cyto.Cytoscape(
                            id='cytoscape',
                            layout={'name': 'cose'},
                            style={'width': '100%', 'height': '800px'},
                            elements=[],
                            stylesheet=[
                                {
                                    'selector': 'node',
                                    'style': {
                                        'label': 'data(label)',
                                        'font-size': 3,
                                        'background-color': 'mapData(weight, -1, 1, red, yellow)',
                                        "width": 'data(size)',
                                        "height": 'data(size)',
                                        "opacity": 0.75,
                                        "color": "white"
                                    },
                                },
                                {
                                    'selector': 'edge',
                                    'style': {
                                        'width': 0.3,
                                        "opacity": 0.9,
                                    }
                                },
                            ]), md=9)
                        ])
                    ], fluid=True)]
                ),

        dcc.Tab(label="Statistics", className="my-tab", selected_className="selected_tab", children=[
            dbc.Row([
                dbc.Col([
                    html.Div(id="positive_sentiment"),
                    html.Div(id="negative_sentiment"),
                    html.Div(id="top_count"),
                    html.Div(id="place_5")
                ]),
                dbc.Col([
                    html.Div(className="stats", children=[
                        html.H2("Word Cloud"),
                        html.Img(className="word_cloud",
                                 id="cloud-img")
                    ]),
                    html.Div(className="stats", children=[
                        html.H2("Distribution of Sentiment"),
                        dcc.Graph(id="dist_plot")]),
                    html.Div(className="stats", children=[
                        html.H2("Tweets Summary"),
                        dcc.Graph(id="bars")]),
                ])
            ])
        ])
    ]),
], fluid=True)


@app.callback(
    # Callback to update graph elements, based on a search phrase
    Output("cytoscape", "elements"),
    Output("positive_sentiment", "children"),
    Output("negative_sentiment", "children"),
    Output("top_count", "children"),
    Output("dist_plot", "figure"),
    Output("cloud-img", "src"),
    Output("place_5", "children"),
    Output("bars", "figure"),
    Input("search_phrase", "value"),
    prevent_initial_call=True)
def update_display(search_phrase):
    # User defines number of tweets and search string
    # Append a hashtag to search phrase if required
    if not search_phrase.startswith('#'):
        search_phrase = '#' + search_phrase

    node_df, edge_df, place_df, cloud_path, y = get_tweets(search_phrase, 50)

    elements = []
    counts = node_df.groupby(by='tag').count()

    avg_sentiment = node_df.groupby(by='tag').mean()

    # Add nodes
    for tag in node_df['tag'].unique():
        node = {
            'data': {'id': tag,
                     'label': tag,
                     # A scaling factor is applied to each node here.
                     'size': int(counts.loc[tag]),
                     'count': counts.loc[tag],
                     'weight': float(avg_sentiment.loc[tag])
                     }
        }
        elements.append(node)
    # Add edges
    edge_count = edge_df.groupby(
        ['tag', 'associated_tag']).size().reset_index(name="pair_count")

    for pair in edge_count.index:
        edge = {'data': {
            'source': edge_count.loc[pair, 'tag'], 'target': edge_count.loc[pair, 'associated_tag'],
            "count": edge_count.loc[pair, 'pair_count']}}
        if edge not in elements:
            elements.append(edge)

    # Most positive and negative
    avg_sentiment = avg_sentiment.sort_values(by="sentiment", ascending=False)
    positive = avg_sentiment[0:5]
    negative = avg_sentiment[-5:].sort_values(by="sentiment", ascending=False)
    # Highest count
    counts = counts.sort_values(by="sentiment", ascending=False)
    top5 = counts[0:5]

    # Tables for statistics tab
    # Top positive hashtags
    positive_sentiment = html.Div(className="stats", children=[
        html.H2("Most Positive"),
        dbc.Table.from_dataframe(
            pd.DataFrame(
                {
                    "#": positive.index,
                    "Avg. Sentiment": round(positive['sentiment'], 2)
                }), className="table", bordered=False, dark=True, responsive=True)
        ]
    )

    # Top negative hashtags
    negative_sentiment = html.Div(className="stats", children=[
        html.H2("Most Negative"),
        dbc.Table.from_dataframe(
            pd.DataFrame(
                {
                    "#": negative.index,
                    "Avg. Sentiment": round(negative['sentiment'], 2)
                }), bordered=False, dark=True, responsive=True)
        ]
    )

    # top most popular
    top_count = html.Div(className="stats", children=[
        html.H2("Most Popular"),
        dbc.Table.from_dataframe(
            pd.DataFrame(
                {
                    "#": top5.index,
                    "Count": top5['sentiment']
                }), bordered=False, dark=True, responsive=True)
        ]
    )

    # top locations twitter posted from
    place_df["place"].replace("", np.nan, inplace=True)
    place_head = place_df.dropna().groupby("place").count().sort_values(by="tweet", ascending=False).head()
    place_head = place_head.reset_index()
    place_5_div = html.Div(className="stats", children=[
        html.H2("Places"),
        dbc.Table.from_dataframe(
            pd.DataFrame({
                "Place": place_head['place'],
                "Count": place_head['tweet']}
            ), bordered=False, dark=True, responsive=True)
    ])

    # dist_plot of sentiments
    dist_plot = ff.create_distplot([node_df['sentiment']], ['sentiment'], bin_size=0.07)

    # Bar plot of sentiments summary
    bars = go.Figure([go.Bar(x=["Negative", "Neutral", "Positive"], y=y, marker_color=["red", "grey", "green"])])

    return elements, positive_sentiment, negative_sentiment, top_count, dist_plot, cloud_path, place_5_div, bars


@app.callback(Output('cytoscape-tapEdgeData-output', 'children'),
              Input('cytoscape', 'tapEdgeData'))
def displayTapEdgeData(data):
    if data:
        return data['source'].upper() + " and " + data['target'].upper() + "\nMentioned together {} time(s).".format(
            data['count'])


@app.callback(Output('cytoscape-tapNodeData-json', 'children'),
              Input('cytoscape', 'tapNodeData'))
def displayTapNodeData(data):
    return "#{0}\n{1} tweets\nAvg. Sentiment {2:.3f}".format(data["label"], data["count"][0], data["weight"] / 10)


if __name__ == "__main__":
    app.run_server()
