from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import requests
from dash.dependencies import Output, Input


app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG, "custom.css"])

EW_URL = "http://localhost:8000/evie-ew-status"
TWO_UPS_URL = "http://localhost:8000/evie-2ups-status"


def fetch_data(URL):
    response = requests.get(URL)
    data = response.json()
    return {
        "bot": data["bot"],
        "components": data["components"],
    }


EwBotInfo = fetch_data(EW_URL)
TwoUpsBotInfo = fetch_data(TWO_UPS_URL)


def service_status_tile(name, status, totalRowTiles, info):
    if status == "Green":
        tileImage = "/assets/green.png"
    elif status == "Orange":
        tileImage = "/assets/orange.png"
    elif status == "Red":
        tileImage = "/assets/red.png"
    else:
        tileImage = "/assets/red.png"

    defaultTile = {
        "background-image": f"url('{tileImage}')",
        "background-repeat": "no-repeat",
        "background-size": "cover",
        "height": f"{(50 / (totalRowTiles + 1))}vh",
        "width": f"{( (totalRowTiles + 8.8))}vh",
    }

    tile = html.Div(style=defaultTile)

    # Adding dropdown component with custom CSS class
    dropdown = dbc.DropdownMenu(
        label=name,
        menu_variant="dark",
        size="lg",
        toggle_style={
        "textTransform": "uppercase",
        "background": status,
    }  ,
        children=[dbc.DropdownMenuItem(i) for i in info.split('\n')
        ],
        direction="right",
        in_navbar=False,
    )

    return html.Div([dropdown])


def BotStatusDiv(info_dict):
    masterDivChildren = []

    masterDivChildren.append(
        html.H1(children=info_dict["bot"], style={"textAlign": "left"})
    )

    for component in info_dict["components"]:
        subDivChildren = [html.Br()]
        subDivChildren.append(
            service_status_tile(
                component["name"],
                component["status"],
                len(info_dict["components"]),
                component["info"],
            )
        )
        masterDivChildren.append(
            html.Div(
                children=[
                    dbc.Row(
                        dbc.Col(
                            html.Div(children=subDivChildren),
                        ),
                    ),
                ],
            )
        )

    return masterDivChildren


app.layout = html.Div(
    children=[
        html.Div(
            id="live-update-ew",
            children=BotStatusDiv(EwBotInfo),
            style={"float": "left", "width": "25%"},
        ),
        html.Div(
            id="live-update-2ups",
            children=BotStatusDiv(TwoUpsBotInfo),
            style={
                "float": "left",
            },
        ),
        dcc.Interval(
            id="interval-component",
            interval=60 * 1000, 
            n_intervals=0,
        ),
    ]
)


# Fetches status data for Evie EW every 60 seconds
@app.callback(
    Output("live-update-ew", "children"), Input("interval-component", "n_intervals")
)
def update_ew_data(n):
    EwBotInfo = fetch_data(EW_URL)

    return BotStatusDiv(EwBotInfo)


# Fetches status data for Evie 2UPs every 60 seconds
@app.callback(
    Output("live-update-2ups", "children"), Input("interval-component", "n_intervals")
)
def update_2ups_data(n):
    TwoUpsBotInfo = fetch_data(TWO_UPS_URL)
    return BotStatusDiv(TwoUpsBotInfo)


if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0')
