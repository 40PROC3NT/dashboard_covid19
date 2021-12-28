from global_utils import update_geojson, transform_df_wide_long, fix_countries_names, get_variables_dict

import dash_leaflet as dl
import dash_leaflet.express as dlx
import dash
from dash.dependencies import Output, Input, State
from dash_extensions.javascript import arrow_function
from dash import dcc, html
import plotly.express as px
import os
import pandas as pd
import time
import dash_leaflet as dl
import dash_leaflet.express as dlx
from dash import html, Output, Input
from dash_extensions.javascript import arrow_function, assign


geojson_date = '2021-12-20'


data_folder_path = os.path.join(os.getcwd(), 'data_world')
data_path = os.path.join(data_folder_path, 'owid-covid-data.csv')
df = fix_countries_names(pd.read_csv(data_path))
quantiles_list = update_geojson(df, geojson_date)
df_long = transform_df_wide_long(df)

available_indicators = list(set(df_long['metrics']))
variables_dict = get_variables_dict()


def get_info(feature=None):
    header = [html.H4("Informacje o kraju")]
    if not feature:
        return header + [html.P("Najedź kursorem na wybrane państwo")]
    return header + [html.Br(), html.B(feature["properties"]["name"]), html.Br(), html.Br(),
                     html.B("Kontynent:"), " {}".format(feature["properties"]["continent"]), html.Br(),
                     html.B("Subregion:"), " {}".format(feature["properties"]["subregion"]), html.Br(), html.Br(),
                     html.B("Populacja:"), " {:,} osób".format(feature["properties"]["pop_est"]).replace(',', ' '), html.Br(),
                     html.B("Gęstość zaludnienia:"), " {} osób / km".format(feature["properties"]["population_density"]), html.Sup("2"), html.Br(),
                     html.B("Mediana wieku:"), " {} lat".format(feature["properties"]["median_age"]), html.Br(), html.Br(),
                     html.B("PKB:"), " {:,} mln $".format(feature["properties"]["gdp_md_est"]).replace(',', ' '), html.Br(),
                     html.B("Ekonomia:"), " {}".format(feature["properties"]["economy"]), html.Br(), html.Br(),
                     html.B("Siedmiodniowa średnia liczby zakażeń:"), " {} / mln osób".format(feature["properties"]["new_cases_smoothed_per_million"])]


app = dash.Dash(__name__, prevent_initial_callbacks=True, suppress_callback_exceptions=True)

colors = {'background': 'rgba(45, 45, 45, 1)',
            'text': '#7FDBFF'}

indices = sorted(list(set(df.date)), reverse=True)
countries_list = sorted(list(set(df.location)))

classes = quantiles_list
colorscale = ['#FFEDA0', '#FED976', '#FEB24C', '#FD8D3C', '#FC4E2A', '#E31A1C', '#BD0026', '#800026']
style = dict(weight=2, opacity=1, color='white', dashArray='3', fillOpacity=0.7)


# Create colorbar.
ctg = ["{:.0f}+".format(cls, classes[i + 1]) for i, cls in enumerate(classes[:-1])] + ["{:.0f}+".format(classes[-1])]
colorbar = dlx.categorical_colorbar(categories=ctg, colorscale=colorscale, width=300, height=30, position="bottomleft")
# Geojson rendering logic, must be JavaScript as it is executed in clientside.
style_handle = assign("""function(feature, context){
    const {classes, colorscale, style, colorProp} = context.props.hideout;  // get props from hideout
    const value = feature.properties[colorProp];  // get value the determines the color
    for (let i = 0; i < classes.length; ++i) {
        if (value > classes[i]) {
            style.fillColor = colorscale[i];  // set the fill color according to the class
        }
    }
    return style;
}""")


geojson = dl.GeoJSON(url="/assets/updated_geo_world.json",  # url to geojson file
                     options=dict(style=style_handle),  # how to style each polygon
                     zoomToBounds=True,  # when true, zooms to bounds when data changes (e.g. on load)
                     zoomToBoundsOnClick=True,  # when true, zooms to bounds of feature (e.g. polygon) on click
                     hoverStyle=arrow_function(dict(weight=5, color='#666', dashArray='')),  # style applied on hover
                     hideout=dict(colorscale=colorscale, classes=classes, style=style, colorProp="new_cases_smoothed_per_million"),
                     id="geojson")


# Create info control.
info = html.Div(children=get_info(), id="info", className="info",
                style={"position": "absolute", "top": "10px", "right": "10px", "z-index": "1000"})



app.layout = html.Div(id='layout', className="body",
    children=[
            dcc.Link(href='https://github.com/owid/covid-19-data/tree/master/public/data', style={'horizontalAlign':'right'}, refresh=True, children=[html.Button('DATASET', id='href_div', className='myButton', style={"width": '100%', 'font-size': '10px', 'text-align': 'right'})]),
            html.Div(id='title', style={'textAlign': 'center', 'verticalAlign': 'middle', 'justify-content': 'center', 'align-items': 'center'}, children=[html.H2('Dashboard COVID-19', style={"font-family": "Lucida Console", "color": "white"}),
            html.Div([
            dcc.Tabs(id="tabs", style={"font-family": "Lucida Console", "background-color":'#1E1E1E', 'font-size':'12px'}, children=[
                    dcc.Tab(label='MAPA', value='tab-1'),
                    dcc.Tab(label='WYKRES', value='tab-2')]),
                    html.Div(id='tabs-content')
                ]),
            ]),
        ])



@app.callback(Output('tabs-content', 'children'),
              Input('tabs', 'value'))
def render_content(tab):
    if tab == 'tab-1':
        return html.Div(id='tab1_content', children=[
                        html.Div([dl.Map(children=[dl.TileLayer(minZoom=2, maxZoom=6), geojson, colorbar, info])],
                                style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block"}, id="map"),
                        html.Div(id='country_time_div', style={'width': '100%', 'margin-left': '5%', 'margin-top':'1%', 'margin-bottom':'1%', 'height':'10%', 'align-items': 'center', 'justify-content': 'center'},
                            children=[
                            html.Div(id="country", style={'width': '20%', 'textAlign': 'center', "font-family": "Lucida Console", 'color': 'white', 'display':'inline-block', 'verticalAlign': 'middle', 'font-size': '24px'}),
                            html.Div(id='date_selection', style={'width': '70%', 'display':'inline-block', 'verticalAlign': 'middle', "font-family": "Lucida Console"}, children=[
                                html.Div(style={'verticalAlign': 'middle', "font-family": "Lucida Console", 'display':'inline'}, children=
                                        [html.B('Data początkowa', style={'font-size':'12px', 'margin-left':'5%', 'color':'white'}),
                                        dcc.Dropdown(id="dropdown1", options=[{'label': str(val), 'value': str(val)} for val in indices], placeholder="yyyy-mm-dd", style={'font-size':'12px', 'margin-left':'2%', 'width': '120px', 'display':'inline-block', 'verticalAlign': 'middle'}),
                                        html.B('Data końcowa', style={'font-size':'12px', 'margin-left':'5%', 'color':'white'}),
                                        dcc.Dropdown(id="dropdown2", options=[{'label': str(val), 'value': str(val)} for val in indices], placeholder="yyyy-mm-dd", style={'font-size':'12px', 'margin-left':'2%', 'width': '120px', 'display':'inline-block', 'verticalAlign': 'middle'}),
                                        html.B('Porównaj z', style={'font-size':'12px', 'margin-left':'5%', 'color':'white'}),
                                        dcc.Dropdown(id="dropdown_compare", placeholder="Wybierz kraj", style={'font-size':'12px', 'margin-left':'2%', 'width': '325px', 'display':'inline-block', 'verticalAlign': 'middle'}, options=[{'label': str(val), 'value': str(val)} for val in countries_list], multi=True),])])]),
                    
                            dcc.Loading(id="loading-1", type="default", children=[
                                html.Div(id='plot_area', style={'align-items': 'center', 'justify-content':'center', 'margin':'auto', 'display':'none'}, children=[
                                    html.Div(id='title1_plotarea', style={'textAlign': 'center', "border":"2px black solid", "background-color":'#1E1E1E'}, children=html.H4('Przypadki zachorowań', style={"font-family": "Lucida Console", "color": "white", "align": "center", "width":"100%"})),
                                    dcc.Graph(id='fig1', style={'width':'50%', 'height':'350px', 'display':'inline-block', 'margin':'auto'}),
                                    dcc.Graph(id='fig2', style={'width':'50%', 'height':'350px', 'display':'inline-block', 'margin':'auto'}),
                                    html.Div(id='title2_plotarea', style={'textAlign': 'center', "border":"2px black solid", "background-color":'#1E1E1E'}, children=html.H4('Zgony', style={"font-family": "Lucida Console", "color": "white", "align": "center", "width":"100%"})),
                                    dcc.Graph(id='fig3', style={'width':'50%', 'height':'350px', 'display':'inline-block', 'margin':'auto'}),
                                    dcc.Graph(id='fig4', style={'width':'50%', 'height':'350px', 'display':'inline-block', 'margin':'auto'}),
                                    html.Div(id='title3_plotarea', style={'textAlign': 'center', "border":"2px black solid", "background-color":'#1E1E1E'}, children=html.H4('Hospitalizacja', style={"font-family": "Lucida Console", "color": "white", "align": "center", "width":"100%"})),
                                    dcc.Graph(id='fig5', style={'width':'50%', 'height':'350px', 'display':'inline-block', 'margin':'auto'}),
                                    dcc.Graph(id='fig6', style={'width':'50%', 'height':'350px', 'display':'inline-block', 'margin':'auto'}),
                                    html.Div(id='title4_plotarea', style={'textAlign': 'center', "border":"2px black solid", "background-color":'#1E1E1E'}, children=html.H4('Testy', style={"font-family": "Lucida Console", "color": "white", "align": "center", "width":"100%"})),
                                    dcc.Graph(id='fig7', style={'width':'50%', 'height':'350px', 'display':'inline-block', 'margin':'auto'}),
                                    dcc.Graph(id='fig8', style={'width':'50%', 'height':'350px', 'display':'inline-block', 'margin':'auto'}),
                                    html.Div(id='title5_plotarea', style={'textAlign': 'center', "border":"2px black solid", "background-color":'#1E1E1E'}, children=html.H4('Szczepienia', style={"font-family": "Lucida Console", "color": "white", "align": "center", "width":"100%"})),
                                    dcc.Graph(id='fig9', style={'width':'50%', 'height':'350px', 'display':'inline-block', 'margin':'auto'}),
                                    dcc.Graph(id='fig10', style={'width':'50%', 'height':'350px', 'display':'inline-block', 'margin':'auto'}),
                                    html.Div(id='title6_plotarea', style={'textAlign': 'center', "border":"2px black solid", "background-color":'#1E1E1E'}, children=html.H4('Poziom restrykcji', style={"font-family": "Lucida Console", "color": "white", "align": "center", "width":"100%"})),
                                    dcc.Graph(id='fig11', style={'width':'100%', 'height':'350px', 'display':'inline-block', 'margin':'auto'}),
                        ])
                    ])
                ])
    elif tab == 'tab-2':
        return html.Div([
                        html.Div([
                            html.Div([
                                html.H4('Zmienna na osi X: ', style={"font-family": "Lucida Console", "color": "white"}),
                                dcc.Dropdown(
                                    id='xaxis-column',
                                    options=[{'label': i, 'value': i} for i in available_indicators]),
                                ], style={'width': '60%', 'display':'inline-block', 'verticalAlign': 'top', "font-family": "Lucida Console", 'font-size':'12px'},
                            ),
                            html.Div([
                                html.H5('Skala osi X: ', style={"font-family": "Lucida Console", "color": "white"}),
                                dcc.RadioItems(
                                    id='xaxis-type',
                                    options=[{'label': i, 'value': i} for i in ['Liniowa', 'Logarytmiczna']],
                                    value='Liniowa',
                                    labelStyle={'display': 'inline-block', "font-family": "Lucida Console", "color": "white", 'margin-right': '20px', 'font-size':'10px'}
                            )
                            ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 'font-size':'12px'}),
                        ], style={'width': '90%', 'margin-top': '10px', 'verticalAlign': 'top', 'align-items': 'center', 'justify-content':'center', 'margin':'auto'}),

                        html.Div([
                            html.Div([
                                html.H4('Zmienna na osi Y: ', style={"font-family": "Lucida Console", "color": "white"}),
                                dcc.Dropdown(
                                    id='yaxis-column',
                                    options=[{'label': i, 'value': i} for i in available_indicators]),
                                ], style={'width': '60%', 'display':'inline-block', 'verticalAlign': 'top', "font-family": "Lucida Console", 'font-size':'12px'},
                            ),
                            html.Div([
                                html.H5('Skala osi Y: ', style={"font-family": "Lucida Console", "color": "white"}),
                                dcc.RadioItems(
                                    id='yaxis-type',
                                    options=[{'label': i, 'value': i} for i in ['Liniowa', 'Logarytmiczna']],
                                    value='Liniowa',
                                    labelStyle={'display': 'inline-block', "font-family": "Lucida Console", "color": "white", 'margin-right': '20px', 'font-size':'10px'}
                            )
                            ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 'font-size':'12px'}),
                        ], style={'width': '90%', 'margin-top': '10px', 'verticalAlign': 'top', 'align-items': 'center', 'justify-content':'center', 'margin':'auto'}),

                        html.Div([
                            html.Div([
                                html.H4('Zmienna odpowiadająca za wielkość punktów: ', style={"font-family": "Lucida Console", "color": "white"}),
                                dcc.Dropdown(
                                    id='size-column',
                                    options=[{'label': i, 'value': i} for i in available_indicators]),
                                ], style={'width': '60%', 'display':'inline-block', 'verticalAlign': 'top', "font-family": "Lucida Console", 'font-size':'12px'},
                            ),
                            html.Div([
                                html.H5('Opcje: ', style={"font-family": "Lucida Console", "color": "white"}),
                                dcc.Checklist(
                                    id='size-type',
                                    options=[{'label': i, 'value': i} for i in ['Uwzględnij wielkość punktów', 'Uwzględnij fasety dla kontynentów', 'Uwzględnij linię trendu']],
                                    labelStyle={'display': 'block', "font-family": "Lucida Console", "color": "white", 'margin-bottom': '5px', 'font-size':'10px'}),
                            ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 'font-size':'12px'}),
                        ], style={'width': '90%', 'margin-top': '10px', 'verticalAlign': 'top', 'align-items': 'center', 'justify-content':'center', 'margin':'auto', 'font-size':'12px'}),

                        html.Div([
                            html.Div([
                                html.H4('Data: ', style={"font-family": "Lucida Console", "color": "white"}),
                                dcc.Dropdown(id="dropdown_wykres", options=[{'label': str(val), 'value': str(val)} for val in indices],
                                placeholder="yyyy-mm-dd", value=max(indices), style={"font-family": "Lucida Console", 'font-size':'12px'})
                                ], style={'width': '60%', 'display':'inline-block', 'verticalAlign': 'top'},
                            ),
                            html.Div([
                                html.Button('POKAŻ WYKRES', id='plot_button', className='myButton', style={"width": '200px', 'height':'40px', 'font-size': '10px', 'text-align': 'center', "font-family": "Lucida Console"})
                            ], style={'width': '30%', 'display': 'inline-block', 'margin-top':'40px'}),
                        ], style={'width': '90%', 'margin-top': '10px', 'verticalAlign': 'top', 'align-items': 'center', 'justify-content':'center', 'margin':'auto', 'font-size':'12px'}),

                    html.Div(id='tab-2-graph-div', children=[
                        dcc.Graph(id='indicator-graphic', style={'height':'100%'}),
                    ], style={'margin-top': '50px', 'height': '850px', 'display':'none'}),

                ], style={'width': '100%'})



@app.callback(Output("plot_area", "style"), [Input("geojson", "n_clicks")])
def show_hide_element1(n_clicks):
    style = {'align-items': 'center', 'justify-content':'center', 'margin':'auto', 'display': 'block'}
    if n_clicks == 1:
        time.sleep(4)
        return style
    elif n_clicks > 1:
        return style


@app.callback(Output("info", "children"), [Input("geojson", "hover_feature")])
def info_hover(feature):
    return get_info(feature)


@app.callback(Output("country", "children"), [Input("geojson", "click_feature")])
def capital_click(feature):
    if feature is not None:
        return f"{feature['properties']['name']}"


@app.callback(
    Output('tab-2-graph-div', 'style'),
    Input('plot_button', 'n_clicks'),
    State('xaxis-column', 'value'),
    State('yaxis-column', 'value'),
    State('dropdown_wykres', 'value'))
def show_tab2_plot(click, xaxis_column, yaxis_column, dropdown_wykres):
    if (xaxis_column is not None and yaxis_column is not None and dropdown_wykres is not None):
        return {'margin-top': '50px', 'height': '850px', 'display':'block'}


@app.callback(
    Output('indicator-graphic', 'figure'),
    Input('xaxis-column', 'value'),
    Input('yaxis-column', 'value'),
    Input('size-column', 'value'),
    Input('xaxis-type', 'value'),
    Input('yaxis-type', 'value'),
    Input('size-type', 'value'),
    Input('dropdown_wykres', 'value'))
def update_graph(xaxis_column_name, yaxis_column_name, size_column_name,
                 xaxis_type, yaxis_type, size_facet_line_type,
                 date_value):
        
    if size_facet_line_type == ['Uwzględnij wielkość punktów']:
        dff_date = df_long[df_long['date'] == date_value]
        dff_x = dff_date[dff_date['metrics'] == xaxis_column_name]
        dff_y = dff_date[dff_date['metrics'] == yaxis_column_name]
        dff_size = dff_date[dff_date['metrics'] == size_column_name]

        dff = pd.merge(left=dff_x, right=dff_y, how="inner", on=['continent', 'location', 'date'])
        dff = pd.merge(left=dff, right=dff_size, how="inner", on=['continent', 'location', 'date'])
        dff = dff.dropna()
        dff = dff.rename(columns = {"values_x":xaxis_column_name, 'values_y':yaxis_column_name, 'values':size_column_name})

        fig = px.scatter(dff,
                        x=xaxis_column_name,
                        y=yaxis_column_name,
                        color='continent',
                        size=size_column_name,
                        hover_name='location',
                        category_orders={"continent": ["Europe", "North America", "South America", "Asia", "Oceania", "Africa"]})

    elif size_facet_line_type == ['Uwzględnij linię trendu']:
        dff_date = df_long[df_long['date'] == date_value]
        dff_x = dff_date[dff_date['metrics'] == xaxis_column_name]
        dff_y = dff_date[dff_date['metrics'] == yaxis_column_name]

        dff = pd.merge(left=dff_x, right=dff_y, how="inner", on=['continent', 'location', 'date'])
        dff = dff.dropna()
        dff = dff.rename(columns = {"values_x":xaxis_column_name, 'values_y':yaxis_column_name, 'values':size_column_name})

        fig = px.scatter(dff,
                        x=xaxis_column_name,
                        y=yaxis_column_name,
                        color='continent',
                        hover_name='location',
                        trendline="ols", 
                        trendline_scope="overall", 
                        trendline_color_override="black",
                        category_orders={"continent": ["Europe", "North America", "South America", "Asia", "Oceania", "Africa"]})

    elif size_facet_line_type == ['Uwzględnij wielkość punktów', 'Uwzględnij linię trendu'] or size_facet_line_type == ['Uwzględnij linię trendu', 'Uwzględnij wielkość punktów']:
        dff_date = df_long[df_long['date'] == date_value]
        dff_x = dff_date[dff_date['metrics'] == xaxis_column_name]
        dff_y = dff_date[dff_date['metrics'] == yaxis_column_name]
        dff_size = dff_date[dff_date['metrics'] == size_column_name]

        dff = pd.merge(left=dff_x, right=dff_y, how="inner", on=['continent', 'location', 'date'])
        dff = pd.merge(left=dff, right=dff_size, how="inner", on=['continent', 'location', 'date'])
        dff = dff.dropna()
        dff = dff.rename(columns = {"values_x":xaxis_column_name, 'values_y':yaxis_column_name, 'values':size_column_name})
        
        fig = px.scatter(dff,
                x=xaxis_column_name,
                y=yaxis_column_name,
                hover_name='location',
                color='continent',
                size=size_column_name,
                trendline="ols", 
                trendline_scope="overall", 
                trendline_color_override="black",
                category_orders={"continent": ["Europe", "North America", "South America", "Asia", "Oceania", "Africa"]})

    elif size_facet_line_type == ['Uwzględnij fasety dla kontynentów']:
        dff_date = df_long[df_long['date'] == date_value]
        dff_x = dff_date[dff_date['metrics'] == xaxis_column_name]
        dff_y = dff_date[dff_date['metrics'] == yaxis_column_name]
        dff_size = dff_date[dff_date['metrics'] == size_column_name]

        dff = pd.merge(left=dff_x, right=dff_y, how="inner", on=['continent', 'location', 'date'])
        dff = dff.dropna()
        dff = dff.rename(columns = {"values_x":xaxis_column_name, 'values_y':yaxis_column_name})
        
        fig = px.scatter(dff,
                x=xaxis_column_name,
                y=yaxis_column_name,
                color='continent',
                hover_name='location',
                facet_col="continent",
                category_orders={"continent": ["Europe", "North America", "South America", "Asia", "Oceania", "Africa"]})

    elif size_facet_line_type == ['Uwzględnij fasety dla kontynentów', 'Uwzględnij linię trendu'] or size_facet_line_type == ['Uwzględnij linię trendu', 'Uwzględnij fasety dla kontynentów']:
        dff_date = df_long[df_long['date'] == date_value]
        dff_x = dff_date[dff_date['metrics'] == xaxis_column_name]
        dff_y = dff_date[dff_date['metrics'] == yaxis_column_name]

        dff = pd.merge(left=dff_x, right=dff_y, how="inner", on=['continent', 'location', 'date'])
        dff = dff.dropna()
        dff = dff.rename(columns = {"values_x":xaxis_column_name, 'values_y':yaxis_column_name})
        
        fig = px.scatter(dff,
                x=xaxis_column_name,
                y=yaxis_column_name,
                color='continent',
                hover_name='location',
                facet_col="continent",
                trendline="ols", 
                category_orders={"continent": ["Europe", "North America", "South America", "Asia", "Oceania", "Africa"]})

    elif size_facet_line_type == ['Uwzględnij fasety dla kontynentów', 'Uwzględnij wielkość punktów'] or size_facet_line_type == ['Uwzględnij wielkość punktów', 'Uwzględnij fasety dla kontynentów']:
        dff_date = df_long[df_long['date'] == date_value]
        dff_x = dff_date[dff_date['metrics'] == xaxis_column_name]
        dff_y = dff_date[dff_date['metrics'] == yaxis_column_name]
        dff_size = dff_date[dff_date['metrics'] == size_column_name]

        dff = pd.merge(left=dff_x, right=dff_y, how="inner", on=['continent', 'location', 'date'])
        dff = pd.merge(left=dff, right=dff_size, how="inner", on=['continent', 'location', 'date'])
        dff = dff.dropna()
        dff = dff.rename(columns = {"values_x":xaxis_column_name, 'values_y':yaxis_column_name, 'values':size_column_name})
        
        fig = px.scatter(dff,
                x=xaxis_column_name,
                y=yaxis_column_name,
                color='continent',
                hover_name='location',
                size=size_column_name,
                facet_col="continent",
                category_orders={"continent": ["Europe", "North America", "South America", "Asia", "Oceania", "Africa"]})

    elif size_facet_line_type is not None and len(size_facet_line_type) == 3:
        dff_date = df_long[df_long['date'] == date_value]
        dff_x = dff_date[dff_date['metrics'] == xaxis_column_name]
        dff_y = dff_date[dff_date['metrics'] == yaxis_column_name]
        dff_size = dff_date[dff_date['metrics'] == size_column_name]

        dff = pd.merge(left=dff_x, right=dff_y, how="inner", on=['continent', 'location', 'date'])
        dff = pd.merge(left=dff, right=dff_size, how="inner", on=['continent', 'location', 'date'])
        dff = dff.dropna()
        dff = dff.rename(columns = {"values_x":xaxis_column_name, 'values_y':yaxis_column_name, 'values':size_column_name})
        
        fig = px.scatter(dff,
                x=xaxis_column_name,
                y=yaxis_column_name,
                color='continent',
                hover_name='location',
                size=size_column_name,
                facet_col="continent",
                trendline="ols",
                category_orders={"continent": ["Europe", "North America", "South America", "Asia", "Oceania", "Africa"]})

    else:
        dff_date = df_long[df_long['date'] == date_value]
        dff_x = dff_date[dff_date['metrics'] == xaxis_column_name]
        dff_y = dff_date[dff_date['metrics'] == yaxis_column_name]
        
        dff = pd.merge(left=dff_x, right=dff_y, how="inner", on=['continent', 'location', 'date'])
        dff = dff.dropna()
        dff = dff.rename(columns = {"values_x":xaxis_column_name, 'values_y':yaxis_column_name})

        fig = px.scatter(dff,
                        x=xaxis_column_name,
                        y=yaxis_column_name,
                        color='continent',
                        hover_name='location',
                        category_orders={"continent": ["Europe", "North America", "South America", "Asia", "Oceania", "Africa"]})

    if size_facet_line_type is not None and 'Uwzględnij fasety dla kontynentów' in size_facet_line_type:
        fig.update_xaxes(title='',
                            type='linear' if xaxis_type == 'Liniowa' else 'log')

        fig.update_yaxes(title='',
                            type='linear' if yaxis_type == 'Liniowa' else 'log')
    else:
        fig.update_xaxes(title=xaxis_column_name,
                            type='linear' if xaxis_type == 'Liniowa' else 'log')

        fig.update_yaxes(title=yaxis_column_name,
                            type='linear' if yaxis_type == 'Liniowa' else 'log')

    if size_facet_line_type is not None and 'Uwzględnij fasety dla kontynentów' in size_facet_line_type:
        fig.update_layout(
            title=dict(text="Wykres punktowy",
                    y=1,
                    x=0.5,
                    xanchor='center',
                    yanchor='top',
                    font=dict(color='white',
                                family='Lucida Console',
                                size=18)),
            font_family="Lucida Console",
            font_color="white",
            xaxis=dict(title='',
                        showline=True,
                        showgrid=True,
                        zeroline=False,
                        showticklabels=True,
                        linecolor='rgb(204, 204, 204)',
                        linewidth=2,
                        ticks='outside',
                        titlefont=dict(family='Lucida Console',
                                        size=14,
                                        color='white'),
                        tickfont=dict(family='Lucida Console',
                                        size=14,
                                        color='white')),                              
                yaxis=dict(title=yaxis_column_name,
                        showgrid=True,
                        zeroline=False,
                        showline=True,
                        showticklabels=True,
                        titlefont=dict(family='Lucida Console',
                                        size=14,
                                        color='white'),
                        tickfont=dict(family='Lucida Console',
                                        size=14,
                                        color='white')),
                autosize=True,
                plot_bgcolor='#e8e8e8',
                paper_bgcolor=colors['background'],
                legend=dict(
                    font=dict(size=14),
                    title='Kontynent',
                    orientation="h",
                    xanchor="center",
                    x=0.5,
                    yanchor="top",
                    y=-0.2))
    else:
        fig.update_layout(
            title=dict(text="Wykres punktowy",
                    y=1,
                    x=0.5,
                    xanchor='center',
                    yanchor='top',
                    font=dict(color='white',
                                family='Lucida Console',
                                size=18)),
            font_family="Lucida Console",
            font_color="white",
            xaxis=dict(title=xaxis_column_name,
                        showline=True,
                        showgrid=True,
                        zeroline=False,
                        showticklabels=True,
                        linecolor='rgb(204, 204, 204)',
                        linewidth=2,
                        ticks='outside',
                        titlefont=dict(family='Lucida Console',
                                        size=14,
                                        color='white'),
                        tickfont=dict(family='Lucida Console',
                                        size=14,
                                        color='white')),                              
                yaxis=dict(title=yaxis_column_name,
                        showgrid=True,
                        zeroline=False,
                        showline=True,
                        showticklabels=True,
                        titlefont=dict(family='Lucida Console',
                                        size=14,
                                        color='white'),
                        tickfont=dict(family='Lucida Console',
                                        size=14,
                                        color='white')),
                autosize=True,
                plot_bgcolor='#e8e8e8',
                paper_bgcolor=colors['background'],
                legend=dict(
                    font=dict(size=14),
                    title='Kontynent',
                    orientation="h",
                    xanchor="center",
                    x=0.5,
                    yanchor="top",
                    y=-0.2))

    return fig



#####################################################################################################################################################################
# Wykresy

# Wykres 1
@app.callback(Output('fig1', 'figure'), [Input("dropdown_compare", "value"), Input("country", "children"), Input('dropdown1', 'value'), Input('dropdown2', 'value')])
def update_figure1(dropdown_compare, country, data_od, data_do):
    if dropdown_compare is None:
        filtered_df = df.loc[df['location'].isin([country])]
    elif dropdown_compare is not None:
        filtered_df = df.loc[df['location'].isin([country for country in dropdown_compare]+[country])]

    if data_od is not None and data_do is None:
        filtered_df = filtered_df[filtered_df['date'] >= data_od]
    elif data_do is not None and data_od is None:
        filtered_df = filtered_df[filtered_df['date'] <= data_do]
    elif data_do is not None and data_od is not None:
        filtered_df = filtered_df[(filtered_df['date'] >= data_od) & (df['date'] <= data_do)]

    fig = px.line(filtered_df, x='date', y='total_cases_per_million', color='location')

    fig.update_layout(
        font_family="Lucida Console",
        font_color="white",
        title=dict(text=variables_dict['total_cases_per_million'],
                    y=0.9,
                    x=0.5,
                    xanchor='center',
                    yanchor='top',
                    font=dict(color='white',
                                family='Lucida Console',
                                size=12)),
        xaxis=dict(title='',
                    showline=True,
                    showgrid=False,
                    showticklabels=True,
                    linecolor='rgb(204, 204, 204)',
                    linewidth=2,
                    ticks='outside',
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),                              
        yaxis=dict(title='Liczba zachorowań / mln mieszkańców',
                    showgrid=True,
                    zeroline=False,
                    showline=False,
                    showticklabels=True,
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),
        autosize=True,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        legend=dict(
            title='',
            orientation="h",
            xanchor="center",
            x=0.5,
            yanchor="top",
            y=-0.2))

    return fig



# Wykres 2
@app.callback(Output('fig2', 'figure'), [Input("dropdown_compare", "value"), Input("country", "children"), Input('dropdown1', 'value'), Input('dropdown2', 'value')])
def update_figure2(dropdown_compare, country, data_od, data_do):
    if dropdown_compare is None:
        filtered_df = df.loc[df['location'].isin([country])]
    elif dropdown_compare is not None:
        filtered_df = df.loc[df['location'].isin([country for country in dropdown_compare]+[country])]

    if data_od is not None and data_do is None:
        filtered_df = filtered_df[filtered_df['date'] >= data_od]
    elif data_do is not None and data_od is None:
        filtered_df = filtered_df[filtered_df['date'] <= data_do]
    elif data_do is not None and data_od is not None:
        filtered_df = filtered_df[(filtered_df['date'] >= data_od) & (df['date'] <= data_do)]

    fig = px.bar(filtered_df, x='date', y='new_cases_per_million', color='location')

    fig.update_layout(
        font_family="Lucida Console",
        font_color="white",
        title=dict(text=variables_dict['new_cases_per_million'],
                    y=0.9,
                    x=0.5,
                    xanchor='center',
                    yanchor='top',
                    font=dict(color='white',
                                family='Lucida Console',
                                size=12)),
        xaxis=dict(title='',
                    showline=True,
                    showgrid=False,
                    showticklabels=True,
                    linecolor='rgb(204, 204, 204)',
                    linewidth=2,
                    ticks='outside',
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),                              
        yaxis=dict(title='Nowe przypadki / mln mieszkańców',
                    showgrid=True,
                    zeroline=False,
                    showline=False,
                    showticklabels=True,
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),
        autosize=True,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        legend=dict(
            title='',
            orientation="h",
            xanchor="center",
            x=0.5,
            yanchor="top",
            y=-0.2))

    return fig



# Wykres 3
@app.callback(Output('fig3', 'figure'), [Input("dropdown_compare", "value"), Input("country", "children"), Input('dropdown1', 'value'), Input('dropdown2', 'value')])
def update_figure3(dropdown_compare, country, data_od, data_do):
    if dropdown_compare is None:
        filtered_df = df.loc[df['location'].isin([country])]
    elif dropdown_compare is not None:
        filtered_df = df.loc[df['location'].isin([country for country in dropdown_compare]+[country])]

    if data_od is not None and data_do is None:
        filtered_df = filtered_df[filtered_df['date'] >= data_od]
    elif data_do is not None and data_od is None:
        filtered_df = filtered_df[filtered_df['date'] <= data_do]
    elif data_do is not None and data_od is not None:
        filtered_df = filtered_df[(filtered_df['date'] >= data_od) & (df['date'] <= data_do)]

    fig = px.line(filtered_df, x='date', y='total_deaths_per_million', color='location')

    fig.update_layout(
        font_family="Lucida Console",
        font_color="white",
        title=dict(text=variables_dict['total_deaths_per_million'],
                    y=0.9,
                    x=0.5,
                    xanchor='center',
                    yanchor='top',
                    font=dict(color='white',
                                family='Lucida Console',
                                size=12)),
        xaxis=dict(title='',
                    showline=True,
                    showgrid=False,
                    showticklabels=True,
                    linecolor='rgb(204, 204, 204)',
                    linewidth=2,
                    ticks='outside',
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),                              
        yaxis=dict(title='Liczba zgonów / mln mieszkańców',
                    showgrid=True,
                    zeroline=False,
                    showline=False,
                    showticklabels=True,
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),
        autosize=True,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        legend=dict(
            title='',
            orientation="h",
            xanchor="center",
            x=0.5,
            yanchor="top",
            y=-0.2))

    return fig



# Wykres 4
@app.callback(Output('fig4', 'figure'), [Input("dropdown_compare", "value"), Input("country", "children"), Input('dropdown1', 'value'), Input('dropdown2', 'value')])
def update_figure4(dropdown_compare, country, data_od, data_do):
    if dropdown_compare is None:
        filtered_df = df.loc[df['location'].isin([country])]
    elif dropdown_compare is not None:
        filtered_df = df.loc[df['location'].isin([country for country in dropdown_compare]+[country])]

    if data_od is not None and data_do is None:
        filtered_df = filtered_df[filtered_df['date'] >= data_od]
    elif data_do is not None and data_od is None:
        filtered_df = filtered_df[filtered_df['date'] <= data_do]
    elif data_do is not None and data_od is not None:
        filtered_df = filtered_df[(filtered_df['date'] >= data_od) & (df['date'] <= data_do)]

    fig = px.bar(filtered_df, x='date', y='new_deaths_per_million', color='location')

    fig.update_layout(
        font_family="Lucida Console",
        font_color="white",
        title=dict(text=variables_dict['new_deaths_per_million'],
                    y=0.9,
                    x=0.5,
                    xanchor='center',
                    yanchor='top',
                    font=dict(color='white',
                                family='Lucida Console',
                                size=12)),
        xaxis=dict(title='',
                    showline=True,
                    showgrid=False,
                    showticklabels=True,
                    linecolor='rgb(204, 204, 204)',
                    linewidth=2,
                    ticks='outside',
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),                              
        yaxis=dict(title='Liczba zgonów / mln mieszkańców',
                    showgrid=True,
                    zeroline=False,
                    showline=False,
                    showticklabels=True,
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),
        autosize=True,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        legend=dict(
            title='',
            orientation="h",
            xanchor="center",
            x=0.5,
            yanchor="top",
            y=-0.2))

    return fig




# Wykres 5
@app.callback(Output('fig5', 'figure'), [Input("dropdown_compare", "value"), Input("country", "children"), Input('dropdown1', 'value'), Input('dropdown2', 'value')])
def update_figure5(dropdown_compare, country, data_od, data_do):
    if dropdown_compare is None:
        filtered_df = df.loc[df['location'].isin([country])]
    elif dropdown_compare is not None:
        filtered_df = df.loc[df['location'].isin([country for country in dropdown_compare]+[country])]

    if data_od is not None and data_do is None:
        filtered_df = filtered_df[filtered_df['date'] >= data_od]
    elif data_do is not None and data_od is None:
        filtered_df = filtered_df[filtered_df['date'] <= data_do]
    elif data_do is not None and data_od is not None:
        filtered_df = filtered_df[(filtered_df['date'] >= data_od) & (df['date'] <= data_do)]

    fig = px.line(filtered_df, x='date', y='hosp_patients_per_million', color='location')

    fig.update_layout(
        font_family="Lucida Console",
        font_color="white",
        title=dict(text=variables_dict['hosp_patients_per_million'],
                    y=0.9,
                    x=0.5,
                    xanchor='center',
                    yanchor='top',
                    font=dict(color='white',
                                family='Lucida Console',
                                size=12)),
        xaxis=dict(title='',
                    showline=True,
                    showgrid=False,
                    showticklabels=True,
                    linecolor='rgb(204, 204, 204)',
                    linewidth=2,
                    ticks='outside',
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),                              
        yaxis=dict(title='Liczba hospitalizacji / mln mieszkańców',
                    showgrid=True,
                    zeroline=False,
                    showline=False,
                    showticklabels=True,
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),
        autosize=True,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        legend=dict(
            title='',
            orientation="h",
            xanchor="center",
            x=0.5,
            yanchor="top",
            y=-0.2))

    return fig



# Wykres 6
@app.callback(Output('fig6', 'figure'), [Input("dropdown_compare", "value"), Input("country", "children"), Input('dropdown1', 'value'), Input('dropdown2', 'value')])
def update_figure6(dropdown_compare, country, data_od, data_do):
    if dropdown_compare is None:
        filtered_df = df.loc[df['location'].isin([country])]
    elif dropdown_compare is not None:
        filtered_df = df.loc[df['location'].isin([country for country in dropdown_compare]+[country])]
    
    if data_od is not None and data_do is None:
        filtered_df = filtered_df[filtered_df['date'] >= data_od]
    elif data_do is not None and data_od is None:
        filtered_df = filtered_df[filtered_df['date'] <= data_do]
    elif data_do is not None and data_od is not None:
        filtered_df = filtered_df[(filtered_df['date'] >= data_od) & (df['date'] <= data_do)]

    fig = px.bar(filtered_df, x='date', y='weekly_hosp_admissions_per_million', color='location')

    fig.update_layout(
        font_family="Lucida Console",
        font_color="white",
        title=dict(text=variables_dict['weekly_hosp_admissions_per_million'],
                    y=0.9,
                    x=0.5,
                    xanchor='center',
                    yanchor='top',
                    font=dict(color='white',
                                family='Lucida Console',
                                size=12)),
        xaxis=dict(title='',
                    showline=True,
                    showgrid=False,
                    showticklabels=True,
                    linecolor='rgb(204, 204, 204)',
                    linewidth=2,
                    ticks='outside',
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),                              
        yaxis=dict(title='Nowe hospitalizacje / mln mieszkańców',
                    showgrid=True,
                    zeroline=False,
                    showline=False,
                    showticklabels=True,
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),
        autosize=True,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        legend=dict(
            title='',
            orientation="h",
            xanchor="center",
            x=0.5,
            yanchor="top",
            y=-0.2))

    return fig



# Wykres 7
@app.callback(Output('fig7', 'figure'), [Input("dropdown_compare", "value"), Input("country", "children"), Input('dropdown1', 'value'), Input('dropdown2', 'value')])
def update_figure7(dropdown_compare, country, data_od, data_do):
    if dropdown_compare is None:
        filtered_df = df.loc[df['location'].isin([country])]
    elif dropdown_compare is not None:
        filtered_df = df.loc[df['location'].isin([country for country in dropdown_compare]+[country])]

    if data_od is not None and data_do is None:
        filtered_df = filtered_df[filtered_df['date'] >= data_od]
    elif data_do is not None and data_od is None:
        filtered_df = filtered_df[filtered_df['date'] <= data_do]
    elif data_do is not None and data_od is not None:
        filtered_df = filtered_df[(filtered_df['date'] >= data_od) & (df['date'] <= data_do)]

    fig = px.line(filtered_df, x='date', y='total_tests_per_thousand', color='location')

    fig.update_layout(
        font_family="Lucida Console",
        font_color="white",
        title=dict(text=variables_dict['total_tests_per_thousand'],
                    y=0.9,
                    x=0.5,
                    xanchor='center',
                    yanchor='top',
                    font=dict(color='white',
                                family='Lucida Console',
                                size=12)),
        xaxis=dict(title='',
                    showline=True,
                    showgrid=False,
                    showticklabels=True,
                    linecolor='rgb(204, 204, 204)',
                    linewidth=2,
                    ticks='outside',
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),                              
        yaxis=dict(title='Liczba testów / tys. mieszkańców',
                    showgrid=True,
                    zeroline=False,
                    showline=False,
                    showticklabels=True,
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),
        autosize=True,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        legend=dict(
            title='',
            orientation="h",
            xanchor="center",
            x=0.5,
            yanchor="top",
            y=-0.2))

    return fig



# Wykres 8
@app.callback(Output('fig8', 'figure'), [Input("dropdown_compare", "value"), Input("country", "children"), Input('dropdown1', 'value'), Input('dropdown2', 'value')])
def update_figure8(dropdown_compare, country, data_od, data_do):
    if dropdown_compare is None:
        filtered_df = df.loc[df['location'].isin([country])]
    elif dropdown_compare is not None:
        filtered_df = df.loc[df['location'].isin([country for country in dropdown_compare]+[country])]
    
    if data_od is not None and data_do is None:
        filtered_df = filtered_df[filtered_df['date'] >= data_od]
    elif data_do is not None and data_od is None:
        filtered_df = filtered_df[filtered_df['date'] <= data_do]
    elif data_do is not None and data_od is not None:
        filtered_df = filtered_df[(filtered_df['date'] >= data_od) & (df['date'] <= data_do)]

    fig = px.bar(filtered_df, x='date', y='new_tests_per_thousand', color='location')

    fig.update_layout(
        font_family="Lucida Console",
        font_color="white",
        title=dict(text=variables_dict['new_tests_per_thousand'],
                    y=0.9,
                    x=0.5,
                    xanchor='center',
                    yanchor='top',
                    font=dict(color='white',
                                family='Lucida Console',
                                size=12)),
        xaxis=dict(title='',
                    showline=True,
                    showgrid=False,
                    showticklabels=True,
                    linecolor='rgb(204, 204, 204)',
                    linewidth=2,
                    ticks='outside',
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),                              
        yaxis=dict(title='Nowe testy / tys. mieszkańców',
                    showgrid=True,
                    zeroline=False,
                    showline=False,
                    showticklabels=True,
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),
        autosize=True,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        legend=dict(
            title='',
            orientation="h",
            xanchor="center",
            x=0.5,
            yanchor="top",
            y=-0.2))

    return fig




# Wykres 9
@app.callback(Output('fig9', 'figure'), [Input("dropdown_compare", "value"), Input("country", "children"), Input('dropdown1', 'value'), Input('dropdown2', 'value')])
def update_figure9(dropdown_compare, country, data_od, data_do):
    if dropdown_compare is None:
        filtered_df = df.loc[df['location'].isin([country])]
    elif dropdown_compare is not None:
        filtered_df = df.loc[df['location'].isin([country for country in dropdown_compare]+[country])]

    if data_od is not None and data_do is None:
        filtered_df = filtered_df[filtered_df['date'] >= data_od]
    elif data_do is not None and data_od is None:
        filtered_df = filtered_df[filtered_df['date'] <= data_do]
    elif data_do is not None and data_od is not None:
        filtered_df = filtered_df[(filtered_df['date'] >= data_od) & (df['date'] <= data_do)]

    fig = px.line(filtered_df, x='date', y='people_fully_vaccinated_per_hundred', color='location')

    fig.update_layout(
        font_family="Lucida Console",
        font_color="white",
        title=dict(text=variables_dict['people_fully_vaccinated_per_hundred'],
                    y=0.9,
                    x=0.5,
                    xanchor='center',
                    yanchor='top',
                    font=dict(color='white',
                                family='Lucida Console',
                                size=12)),
        xaxis=dict(title='',
                    showline=True,
                    showgrid=False,
                    showticklabels=True,
                    linecolor='rgb(204, 204, 204)',
                    linewidth=2,
                    ticks='outside',
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),                              
        yaxis=dict(title='Liczba pełnych szczepień / sto mieszkańców',
                    showgrid=True,
                    zeroline=False,
                    showline=False,
                    showticklabels=True,
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),
        autosize=True,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        legend=dict(
            title='',
            orientation="h",
            xanchor="center",
            x=0.5,
            yanchor="top",
            y=-0.2))

    return fig



# Wykres 10
@app.callback(Output('fig10', 'figure'), [Input("dropdown_compare", "value"), Input("country", "children"), Input('dropdown1', 'value'), Input('dropdown2', 'value')])
def update_figure10(dropdown_compare, country, data_od, data_do):
    if dropdown_compare is None:
        filtered_df = df.loc[df['location'].isin([country])]
    elif dropdown_compare is not None:
        filtered_df = df.loc[df['location'].isin([country for country in dropdown_compare]+[country])]
    
    if data_od is not None and data_do is None:
        filtered_df = filtered_df[filtered_df['date'] >= data_od]
    elif data_do is not None and data_od is None:
        filtered_df = filtered_df[filtered_df['date'] <= data_do]
    elif data_do is not None and data_od is not None:
        filtered_df = filtered_df[(filtered_df['date'] >= data_od) & (df['date'] <= data_do)]

    fig = px.bar(filtered_df, x='date', y='new_vaccinations_smoothed_per_million', color='location')

    fig.update_layout(
        font_family="Lucida Console",
        font_color="white",
        title=dict(text=variables_dict['new_vaccinations_smoothed_per_million'],
                    y=0.9,
                    x=0.5,
                    xanchor='center',
                    yanchor='top',
                    font=dict(color='white',
                                family='Lucida Console',
                                size=12)),
        xaxis=dict(title='',
                    showline=True,
                    showgrid=False,
                    showticklabels=True,
                    linecolor='rgb(204, 204, 204)',
                    linewidth=2,
                    ticks='outside',
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),                              
        yaxis=dict(title='Nowe szczepienia / mln mieszkańców',
                    showgrid=True,
                    zeroline=False,
                    showline=False,
                    showticklabels=True,
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),
        autosize=True,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        legend=dict(
            title='',
            orientation="h",
            xanchor="center",
            x=0.5,
            yanchor="top",
            y=-0.2))

    return fig



# Wykres 11
@app.callback(Output('fig11', 'figure'), [Input("dropdown_compare", "value"), Input("country", "children"), Input('dropdown1', 'value'), Input('dropdown2', 'value')])
def update_figure11(dropdown_compare, country, data_od, data_do):
    if dropdown_compare is None:
        filtered_df = df.loc[df['location'].isin([country])]
    elif dropdown_compare is not None:
        filtered_df = df.loc[df['location'].isin([country for country in dropdown_compare]+[country])]
    
    if data_od is not None and data_do is None:
        filtered_df = filtered_df[filtered_df['date'] >= data_od]
    elif data_do is not None and data_od is None:
        filtered_df = filtered_df[filtered_df['date'] <= data_do]
    elif data_do is not None and data_od is not None:
        filtered_df = filtered_df[(filtered_df['date'] >= data_od) & (df['date'] <= data_do)]

    fig = px.line(filtered_df, x='date', y='stringency_index', color='location')

    fig.update_layout(
        font_family="Lucida Console",
        font_color="white",
        title=dict(text=variables_dict['stringency_index'],
                    y=0.9,
                    x=0.5,
                    xanchor='center',
                    yanchor='top',
                    font=dict(color='white',
                                family='Lucida Console',
                                size=12)),
        xaxis=dict(title='',
                    showline=True,
                    showgrid=False,
                    showticklabels=True,
                    linecolor='rgb(204, 204, 204)',
                    linewidth=2,
                    ticks='outside',
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),                              
        yaxis=dict(title='',
                    showgrid=True,
                    zeroline=False,
                    showline=False,
                    showticklabels=True,
                    titlefont=dict(family='Lucida Console',
                                    size=10,
                                    color='white'),
                    tickfont=dict(family='Lucida Console',
                                    size=10,
                                    color='white')),
        autosize=True,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        legend=dict(
            title='',
            orientation="h",
            xanchor="center",
            x=0.5,
            yanchor="top",
            y=-0.2))

    return fig

#####################################################################################################################################################################


if __name__ == '__main__':
    app.run_server(debug=True)