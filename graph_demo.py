import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_cytoscape as cyto
from tweepy_helper import get_tweets
import pandas as pd
from dash.dependencies import Input, Output, State
from plotly.offline import init_notebook_mode
import json
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler

init_notebook_mode(connected=True)

# Explore external_stylesheets themes here https://dash-bootstrap-components.opensource.faculty.ai/docs/themes/explorer/
app = dash.Dash(external_stylesheets=[dbc.themes.SOLAR])




# Define app layout, using Dash Bootstrap Components https://dash-bootstrap-components.opensource.faculty.ai/docs/
app.layout = dbc.Container(
    [
        html.H1("graph_demo.py"),
        dbc.Row([
            dbc.Col(dbc.FormGroup(
                [
                    dbc.Label("Search Phrase", html_for="search_phrase"),
                    dbc.Input(
                        id="search_phrase", placeholder="Enter a search phrase...", type="text", debounce=True),
                    html.Br(),
                    html.P( id='cytoscape-tapNodeData-json'),
                    html.Br(),
                    html.P(id='cytoscape-tapEdgeData-output'),

                ]
            ), md=2),

            dbc.Col(
                cyto.Cytoscape(
                    id='cytoscape',
                    layout={'name': 'cose'},
                    style={'width': '100%', 'height': '800px'},
                    elements=[],




                    stylesheet=[
                        # See https://js.cytoscape.org/#style
                        # Colour nodes by sentiment, size by support
                        {
                            'selector': 'node',
                            'style': {
                                'label': 'data(label)',
                                'font-size': 6,
                                'background-color': 'mapData(weight, -1, 1, red, green)',
                                "width": 'data(size)',
                                "height": 'data(size)',
                                "opacity": 0.75,
                                "color": "white"
                            },
                        }, {
                            'selector': 'edge',
                            'style': {
                                'width': 0.5
                            }
                        },
                    ]
                ),  md=10)]),
    ],
    fluid=True,

)






@app.callback(Output('cytoscape-tapNodeData-json', 'children'),
              Input('cytoscape', 'tapNodeData'))
def displayTapNodeData(data):
    return "#{} was tweeted {} times with an average sentiment of {}".format(data["label"],data["count"],data["weight"]/100)


@app.callback(
    # Callback to update graph elements, based on a search phrase
    Output("cytoscape", "elements"),
    Input("search_phrase", "value"),
    prevent_initial_call=True)
def update_graph(search_phrase):
    # User defines number of tweets and search string
    node_df, edge_df = get_tweets(search_phrase, 50)
    print(node_df["sentiment"].min())

    # Use local data frames for development purposes
    #node_df = pd.read_csv(
        #"C:/Users/hamis/Documents/Uni/158222/assignments/assignment 3/development/hashtag_sentiment.csv", index_col=0)
    #edge_df = pd.read_csv(
        #"C:/Users/hamis/Documents/Uni/158222/assignments/assignment 3/development/hashtag_pairing.csv", index_col=0)
    scaler = MinMaxScaler()
    node_df["sentiment"] = node_df["sentiment"]*100
    print(node_df)
    elements = []
    counts = node_df.groupby(by='tag').count()

    avg_sentiment = node_df.groupby(by='tag').mean()

    # Add nodes
    for tag in node_df['tag'].unique():
        node = {
            'data': {'id': tag,
                     'label': tag,
                     # A scaling factor is applied to each node here.
                     'size': int(counts.loc[tag]) * 3,
                     'count': counts.loc[tag],
                     'weight': float(avg_sentiment.loc[tag])
                     }
        }
        elements.append(node)
    # Add edges
    edge_count = edge_df.groupby(['tag','associated_tag']).size().reset_index(name="pair_count")
    print(edge_count)
    for pair in edge_count.index:
        edge = {'data': {
            'source': edge_count.loc[pair, 'tag'], 'target': edge_count.loc[pair, 'associated_tag'],"count":edge_count.loc[pair, 'pair_count']}}
        if edge not in elements:
            elements.   append(edge)

    return elements

@app.callback(Output('cytoscape-tapEdgeData-output', 'children'),
                  Input('cytoscape', 'tapEdgeData'))
def displayTapEdgeData(data):
        if data:
            return "You recently clicked/tapped the edge between " + data['source'].upper() + " and " + data['target'].upper() + " and occured {} times.".format(data['count'])



if __name__ == "__main__":
    app.run_server()
