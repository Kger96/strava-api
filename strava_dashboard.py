import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px

# initialising dash app
app = dash.Dash()

# Create Stocks data dataframe
df = px.data.stocks()


def stock_prices():
    # Function for creating line chart showing Google stock prices over time
    fig = go.Figure([go.Scatter(x=df['date'], y=df['GOOG'], line=dict(color='firebrick', width=4), name='Google')])
    fig.update_layout(title='Prices over time',
                      xaxis_title='Dates',
                      yaxis_title='Prices')
    return fig


# Layout of the dashboard
app.layout = html.Div(id='parent', children=[html.H1(id='H1', children='Styling using html components',
                                                     style={'textAlign': 'center',
                                                            'marginTop': 40,
                                                            'marginBottom': 40}),
                                             dcc.Dropdown(id='dropdown',
                                                          options=[{'label': 'Google', 'value': 'GOOG'},
                                                                   {'label': 'Apple', 'value': 'AAPL'},
                                                                   {'label': 'Amazon', 'value': 'AMZN'}],
                                                          value='GOOGL'),
                                             dcc.Graph(id='line_plot', figure=stock_prices())])


# Callback to update the graph when the dropdown is altered.
@app.callback(Output(component_id='line_plot', component_property='figure'),
              [Input(component_id='dropdown', component_property='value')])
def graph_update(dropdown_value):
    print(dropdown_value)
    fig = go.Figure(
        [go.Scatter(x=df['date'], y=df['{}'.format(dropdown_value)], line=dict(color='firebrick', width=4))])
    fig.update_layout(title='Stock prices over time',
                      xaxis_title='Dates',
                      yaxis_title='Prices')
    return fig


if __name__ == '__main__':
    app.run_server()
