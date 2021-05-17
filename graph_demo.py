import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_cytoscape as cyto
from tweepy_helper import get_tweets
import pandas as pd
from dash.dependencies import Input, Output, State
from plotly.offline import init_notebook_mode

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
                        id="search_phrase", placeholder="Enter a search phrase...", type="text", debounce=True)
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
                                'color': 'white',
                                'font-size': 6,
                                'background-color': 'mapData(weight, -1, 0, red, yellow)',
                                "width": 'data(size)',
                                "height": 'data(size)',
                                "opacity": 0.75
                            },
                        }, {
                            'selector': 'edge',
                            'style': {
                                'width': 0.5
                            }
                        },
                    ]
                ), md=10)]),
    ],
    fluid=True,
)


@app.callback(
    # Callback to update graph elements, based on a search phrase
    Output("cytoscape", "elements"),
    Input("search_phrase", "value"),
    prevent_initial_call=True)
def update_graph(search_phrase):
    # User defines number of tweets and search string
    node_df, edge_df = get_tweets(search_phrase, 500)

    # Use local data frames for development purposes
    #node_df = pd.read_csv(
        #"C:/Users/hamis/Documents/Uni/158222/assignments/assignment 3/development/hashtag_sentiment.csv", index_col=0)
    #edge_df = pd.read_csv(
        #"C:/Users/hamis/Documents/Uni/158222/assignments/assignment 3/development/hashtag_pairing.csv", index_col=0)

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
                     'weight': float(avg_sentiment.loc[tag])
                     }
        }
        elements.append(node)
    # Add edges
    for pair in edge_df.index:
        edge = {'data': {
            'source': edge_df.loc[pair, 'tag'], 'target': edge_df.loc[pair, 'associated_tag']}}
        if edge not in elements:
            elements.append(edge)

    return elements


if __name__ == "__main__":
    app.run_server()
