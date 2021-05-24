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
import plotly.io as pio

init_notebook_mode(connected=True)
pio.templates.default = 'simple_white'

external_scripts = [
    'https://cdnjs.cloudflare.com/ajax/libs/animejs/2.0.2/anime.min.js'
]

app = dash.Dash(
    external_stylesheets=[dbc.themes.SPACELAB],
    external_scripts=external_scripts,
    title="Twitter #Explorer",
    update_title="Searching Tweets..."
)

# Define app layout
app.layout = dbc.Container([
    dbc.Row([html.H1("Twitter #explorer", className="ml12")]),
    dcc.Tabs(className="tabs", children=[
        dcc.Tab(label="Network Visualisation", className="my-tab", selected_className="selected_tab", children=[
            dbc.Container([
                dbc.Row([
                    dbc.Col(html.Div([
                        html.Br(),
                        dbc.Label("Search Phrase", html_for="search_phrase", style={
                                  'font-size': '1.5rem', 'margin-bottom': '0px'}),
                        dbc.Input(id="search_phrase", placeholder="Enter a search phrase...",
                                  type="text", debounce=True),
                        html.Br(),
                        html.H4("Node Info", style={'margin-bottom': '0px'}),
                        html.P("Click a node for details",
                               style={'font-size': '75%', 'margin-bottom': '4px'}),
                        html.Div(id='cytoscape-tapNodeData-json',
                                 style={'whiteSpace': 'pre-line'}),
                        html.Br(),
                        html.H4("Edge Info", style={'margin-bottom': '0px'}),
                        html.P("Click an edge for details",
                               style={'font-size': '75%', 'margin-bottom': '4px'}),
                        html.Div(id='cytoscape-tapEdgeData-output',
                                 style={'whiteSpace': 'pre-line', 'margin-bottom': '0px'}),
                        html.Div(children=[
                            html.H4("Legend", style={'margin-bottom': '12px'}),
                            html.Img(src="assets/legend.PNG")], style={'margin-top': '40px'})
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
                                        'background-color': 'mapData(weight, -1, 1, red, blue)',
                                        "width": 'data(size)',
                                        "height": 'data(size)',
                                        "opacity": 0.75,
                                        "color": "black"
                                    },
                                },
                                {
                                    'selector': 'edge',
                                    'style': {
                                        'width': 0.2,
                                        "opacity": 0.5,
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
                ], md=4),
                dbc.Col([
                    html.Div(className="stats", children=[
                        html.H2("Word Cloud (VADER)"),
                        html.Img(className="word_cloud",
                                 id="cloud-img")
                    ]),
                    html.Hr(),
                    html.Div(className="stats", children=[
                        html.H2("Sentiment Summary (VADER)"),
                        dcc.Graph(id="bars")
                    ]),
                    html.Hr(),
                    html.Div(className="stats", children=[
                        html.H2("Distribution of Sentiment (Text Blob)"),
                        dcc.Graph(id="dist_plot")
                    ])
                ], md=8)
            ])
        ])
    ]),
], fluid=True)


@app.callback(
    # Callback to update all display components, based on a search phrase
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
    # Append a hashtag to search phrase if required
    if not search_phrase.startswith('#'):
        search_phrase = '#' + search_phrase

    # Retrieve data for various displayed components. Developer defines number of tweets
    node_df, edge_df, cloud_path, hist_data = get_tweets(search_phrase, 100)

    elements = []

    counts = node_df.groupby(by='tag').count()
    avg_sentiment = node_df.groupby(by='tag').mean()

    # Add nodes
    for tag in node_df['tag'].unique():
        node = {
            'data': {
                'id': tag,
                'label': tag,
                'size': int(counts.loc[tag, 'sentiment']),
                'count': counts.loc[tag, 'sentiment'],
                'weight': float(avg_sentiment.loc[tag, 'sentiment'])
            }
        }
        elements.append(node)
    # Add edges
    edge_count = edge_df.groupby(
        ['tag', 'associated_tag']).size().reset_index(name="pair_count")

    for pair in edge_count.index:
        edge = {'data': {
            'source': edge_count.loc[pair, 'tag'],
            'target': edge_count.loc[pair, 'associated_tag'],
            "count": edge_count.loc[pair, 'pair_count']
        }}
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
    # Most positive hashtags
    positive_sentiment = html.Div(className="stats", children=[
        html.H2("Most Positive"),
        dbc.Table.from_dataframe(
            pd.DataFrame(
                {
                    "#": positive.index,
                    "Avg. Sentiment": round(positive['sentiment'], 2)
                }), className="table", bordered=False, dark=False, responsive=True)
    ]
    )

    # Most negative hashtags
    negative_sentiment = html.Div(className="stats", children=[
        html.H2("Most Negative"),
        dbc.Table.from_dataframe(
            pd.DataFrame(
                {
                    "#": negative.index,
                    "Avg. Sentiment": round(negative['sentiment'], 2)
                }), bordered=False, dark=False, responsive=True)
    ]
    )

    # Most popular (count)
    top_count = html.Div(className="stats", children=[
        html.H2("Most Popular"),
        dbc.Table.from_dataframe(
            pd.DataFrame(
                {
                    "#": top5.index,
                    "Count": top5['sentiment']
                }), bordered=False, dark=False, responsive=True)
    ]
    )

    # Most popular locations (count)
    node_df['location'].replace("", np.nan, inplace=True)
    place_count = node_df.dropna().groupby("location").count()
    place_count = place_count.sort_values(by="sentiment", ascending=False)[0:5]
    top_places = html.Div(className="stats", children=[
        html.H2("Places"),
        dbc.Table.from_dataframe(
            pd.DataFrame({
                "Place": place_count.index,
                "Count": place_count['sentiment']}
            ), bordered=False, dark=False, responsive=True)
    ])
    # dist_plot of sentiment
    dist_plot = ff.create_distplot([node_df['sentiment']], ['sentiment'], bin_size=0.2)

    # Bar plot of sentiments summary
    bars = go.Figure([go.Bar(x=["Negative", "Neutral", "Positive"],
                     y=hist_data, marker_color=["red", "grey", "green"])])

    return elements, positive_sentiment, negative_sentiment, top_count, dist_plot, cloud_path, top_places, bars


@app.callback(Output('cytoscape-tapEdgeData-output', 'children'),
              Input('cytoscape', 'tapEdgeData'))
def displayTapEdgeData(data):
    if data:
        return data['source'].upper() + " and " + data['target'].upper() + "\nMentioned together {} time(s).".format(data['count'])


@app.callback(Output('cytoscape-tapNodeData-json', 'children'),
              Input('cytoscape', 'tapNodeData'))
def displayTapNodeData(data):
    return "#{0}\n{1} tweets\nAvg. Sentiment {2:.2f}".format(data["label"], data["count"], data["weight"])


if __name__ == "__main__":
    app.run_server()
