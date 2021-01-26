import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State,ClientsideFunction

import numpy as np
import pandas as pd
import datetime
from datetime import datetime as dt
import pathlib

app = dash.Dash()
# app.css.append_css({'external_url': 'https://codepen.io/amyoshino/pen/jzXypZ.css'})  # noqa: E501

# server = app.server
# app.config.suppress_callback_exceptions = True

# Path
BASE_PATH = pathlib.Path(__file__).parent.resolve()
DATA_PATH = BASE_PATH.joinpath("data").resolve()

doctors = ["Dr.Ale", "Dr.Akhil", "Dr.Smith", "Dr.Fauci", "Dr.Sphan", "Dr.TC", "Dr.Mehta", "Dr.Beatini"]
doc_enc_dict =  {idx:doc for idx, doc in enumerate(doctors,1)}
dep_dict  = {'Cardiology' : [1,2], 'Neurology':[3,4], 'Orthopaedics': [5,6], 'Pediatrician': [7,8]}
encoding_services = {0: "Electrocardiography", 1:"general-visit"}
doc_service_dict = {0: [0,1], 1 : [0,1], 2 : [0,1],3: [0,1],4 :[0,1],5 : [0,1], 6: [0,1],7 : [0,1]}
departments = list(dep_dict.keys())
totem_names = ['corridor 1', 'corridor 2', 'pharmacy 1', 'pharmacy 2', 'emergency', 'corridor 3', 'elevator 1', 'main reception']
totem_names_dict = {idx: name for idx, name in enumerate(totem_names,1)}

df = pd.read_csv(DATA_PATH.joinpath("sz_analytics.csv"))
df_app = pd.read_csv(DATA_PATH.joinpath("appointments.csv"))

def get_key_for_value(dict_search, value):
    for item in list(dict_search.items()) :
        if item[1] == value:
            return item[0]



def generate_control_card():
    """

    :return: A Div containing controls for graphs.
    """
    return html.Div(
        id="control-card",
        children=[
            html.P("Select Department"),
            dcc.Dropdown(
                id="department-select",
                options=[{"label": i, "value": i} for i in departments],
                value=departments[0],
            ),
            html.Br(),

            html.P("Select Doctor"),
            dcc.Dropdown(
                id="doctor-select",
                options=[{"label": i, "value": i} for i in doctors],
                value=doctors[0],
                # multi=True,
            ),
            html.P("Select Check-In Time"),
            dcc.DatePickerRange(
                id="date-picker-select",
                start_date=dt(2021, 1, 1),
                end_date=dt(2021, 1, 15),
                min_date_allowed=dt(2021, 1, 1),
                max_date_allowed=dt(2021, 12, 31),
                initial_visible_month=dt(2021, 1, 1),
            ),
            html.Br(),
            html.Br(),

            html.Br(),
            html.Div(
                id="reset-btn-outer",
                children=html.Button(id="reset-btn", children="Generate", n_clicks=0),
            ),
        ],

    )

def generate_piechart(id):
    return dcc.Graph(
        id=id,
        figure={
            "data": [
                {
                    "values": [10,15,20],
                    "labels": ['a','b','c'],
                    "type": "pie",
                    "marker": {"line": {"color": "black", "width": 1}},
                    "hoverinfo": "label",
                    "textinfo": "label",
                }
            ],
            "layout": {
                # "margin": dict(l=20, r=20, t=20, b=20),
                            "margin": dict(t=20, b=30),
"showlegend": True,
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"color": "black"},
                "height" : 300,
            },
        },
    )

def generate_barchart(id):
    return dcc.Graph(
        id=id,
        figure={
            "data": [
                {
                    "y": [10,15,20,15],
                    "x": ['a','b','c','d'],
                    "type": "bar",
                    # 'name': 'frequency',
                    # "marker": {"line": {"color": "white", "width": 1}},
                    # "hoverinfo": "label",
                    # "textinfo": "label",
                }
            ],
            "layout": {
                "title" : "Histogram of Totems",
                "margin": dict(l=20, r=20, t=40, b=20),
                # "showlegend": True,
                "height" : 300,
                "width":600,
                # "paper_bgcolor": "#0000FF",
                "plot_bgcolor": "rgba(0,0,0,0)",
                # "font": {"color": "white"},
                # "autosize": True,
            },
        },
    )

def generate_barchart_totems(id):
    totems = df['totem_ids'].apply(lambda x: x.split(',')).sum()
    totems_count = dict()
    for totem in totems:
        if totem in totems_count:
            totems_count[totem] += 1
        else:
            totems_count[totem] = 1

    return dcc.Graph(
        id=id,
        figure={
            "data": [
                {
                    "y": list(totems_count.values()),
                    "x": [totem_names_dict[int(idx)] for idx in list(totems_count.keys())],  #list(totems_count.keys()),
                    "type": "bar",
                    'name': 'frequency',
                    # "marker": {"line": {"color": "white", "width": 1}},
                    # "hoverinfo": "label",
                    # "textinfo": "label",
                }
            ],
            "layout": {
                "title" : "Number of times device used",
                "margin": dict(l=50, r=20, t=40, b=60),
                # "showlegend": True,
                "height" : 300,
                # "paper_bgcolor": "#0000FF",
                "plot_bgcolor": "rgba(0,0,0,0)",
    "yaxis" : dict(
        title='Frequency',
        # titlefont_size=16,
        tickfont_size=14,
    ),
                # "font": {"color": "white"},
                # "autosize": True,
            },
        },
    )

def generate_table_row(id, style, col1, col2, col3, col4, col5):
    """ Generate table rows.
    :param id: The ID of table row.
    :param style: Css style of this row.
    :param col1 (dict): Defining id and children for the first column.
    :param col2 (dict): Defining id and children for the second column.
    :param col3 (dict): Defining id and children for the third column.
    """

    return html.Div(
        id=id,
        className="row table-row",
        style=style,
        children=[
            html.Div(
                id=col1["id"],
                style={"display": "table", "height": "100%"},
                className="three columns",
                children=col1["children"],
            ),
            html.Div(
                id=col2["id"],
                style={"textAlign": "center", "height": "100%"},
                className="two columns",
                children=col2["children"],
            ),
            html.Div(
                id=col3["id"],
                style={"textAlign": "center", "height": "100%"},
                className="two columns",
                children=col3["children"],
            ),
            html.Div(
                id=col4["id"],
                style={"textAlign": "center", "height": "100%"},
                className="two columns",
                children=col4["children"],
            ),
            html.Div(
                id=col5["id"],
                style={"textAlign": "center", "height": "100%"},
                className="two columns",
                children=col5["children"],
            ),
        ],
    )

def initialize_table(doctor_enc):
    """
    :return: empty table children. This is intialized for registering all figure ID at page load.
    """

    # header_row
    header = [
        generate_table_row(
            "header",
            {},
            # {"height": "50px"},
            {"id": "header_service", "children": html.B("Service")},
            {"id": "header_time", "children": html.B("Avg. time")},
            {"id": "header_time_office", "children": html.B("Avg.  ofice")},
            {"id": "header_app_book", "children": html.B("Appt. booked")},
            {"id": "header_app_miss", "children": html.B("Appt. missed")},

        )
    ]

    # doctor_enc = 2
    doctor = doc_enc_dict[doctor_enc]
    print("callback 2")
    print(doctor)
        # department_row
    services = doc_service_dict[doctor_enc]

    rows = [generate_table_row_helper(doctor, encoding_services[service]) for service in services]
    header.extend(rows)
    empty_table = header

    return empty_table


def  generate_table_row_helper(doctor,service):
    """Helper function.
    :param: department (string): Name of department.
    :return: Table row.
    """

    df_app_filtered = df_app[(df_app['place'] == doctor) & (df_app['service'] == service) ]
    df_filtered = df[(df['place'] == doctor) & (df['service'] == service)]
    avg_time = round(df_filtered['time_diff'].apply(lambda x: list(map(float,x.split(',')))[-1]).mean(),2)
    num_appointments = len((df_app_filtered['name'] + df_app_filtered['surname']).unique())
    num_tags = len(df_filtered['patient_id'].unique())
    return generate_table_row(
        service,
        {},
        {"id": service + "_service", "children": html.B(service)},
        {
            "id": service + "_time",
            "children": str(avg_time)
        },
        {
            "id": service + "_time_office",
            "children": str(avg_time),
        },
        {
            "id": service + "_app_book",
            "children": str(num_appointments),
        },
        {
            "id": service + "_app_miss",
            "children": str(num_appointments - num_tags),
        },
    )


app.layout = html.Div(
    id="app-container",
    children=[
        # Banner
        # html.Div(
        #     id="banner",
        #     className="banner",
        #     children= html.H2("Saarzeit"),
        #     style={
        #         'textAlign': 'center',
        #         #   'color': colors['text']
        #     }
        #     #'#html.Img(src=app.get_asset_url("plotly_logo.png"))],
        # ),
        html.Div(children=html.H2('Saarzeit Dashboard'), style={
            'textAlign': 'center',
            # 'color': colors['text']
        }),
        # Left column
        html.Div(
            id="left-column",
            className="three columns",
            children=[generate_control_card()]
            # children=[generate_control_card()]
            + [
                html.Div(
                    ["initial child"], id="output-clientside", style={"display": "none"}
                )
            ],
        ),
        # Right column
        html.Div(
            id="right-column",
            className="nine columns",
            children=[
            html.Div(
            id="second-right-column",
            children=[
                html.Div(
                    id="wait_time_card",
                    className="eight columns",
                    children=[
                        html.B("Patient Time and Satisfactory Scores"),
                        html.Hr(),
                        html.Div(id="wait_time_table",
                                 children=initialize_table(1)),
                    ],
                ),
                html.Div(
                    id="wait_time_card_2",
                    className="four columns",
                    children=[
                        html.B("% of appointments in the department"),
                        #generate_section_banner("% OOC per Parameter"),
                        generate_piechart("piechart"),
                    ],
                ),
            ],
        ),
            html.Div(
                id="third-right-column",
                children=[
                html.Div(
                    id='testing',
                    className='eight columns',
                    children=[
                        html.B("Average time"),
                        generate_barchart("barchart2"), ]
                ),
                html.Div(
                    id="testing-2-2",
                    className="four columns",
                    children=[html.B("% of appointments missed in the department"),
                        #generate_section_banner("% OOC per Parameter"),
                        generate_piechart("piechart2"),
                        ]
                )
                ]
            ),
                html.Div(
                    id="fourth-right-column",
                    children=[
                    html.Div(
                        id='testing2',
                        className='eight columns',
                        children=[html.B("Histogram of Totems"),
                                generate_barchart_totems("barchart")]

                        # html.B("Patient Wait Time and Satisfactory Scores drjg drjg dprjg dorj goprdj rppoheopprpohhjro jhproth prtohj oprth protjh potrjh portj hporth"),]
                    ),
                    # html.Div(
                    #     id="testing-3-2",
                    #     className="four columns",
                    #     children=[html.B("Patient Wait Time and Satisfactory Scores"),
                    #               # generate_section_banner("% OOC per Parameter"),
                    #               generate_piechart("piechart3"),
                    #               ]
                    # )
                ],
            )

            ]
       )
    ],
)

@app.callback(output=[Output('wait_time_table', "children"), Output("piechart", "figure"),Output("piechart2", "figure"),
                      Output("barchart2", "figure")],
              inputs=[Input("reset-btn", "n_clicks"),],
              state=[State("doctor-select", "value"), State("department-select", "value")])
def update_table(n_click, doctor, department):
    print(doctor)
    print("Entered callback")
    colors= ["#91dfd2", "#000000"]
    df_app_filtered = df_app[df_app['department'] == department]

    doc_in_dep = dep_dict[department]
    df_filtered = df[(df['place'] == doctor)]

    df_dep = pd.DataFrame()
    for doc in doc_in_dep:
        doc_name = doc_enc_dict[doc]
        df_doc = df[df['place'] == doc_name]
        df_dep = pd.concat([df_dep, df_doc])

    df_doc = df_dep[df_dep['place'] == doctor].copy()
    dep_avg_time = df_dep['time_diff'].apply(lambda x: list(map(float, x.split(',')))[-1]).mean()
    doc_avg_time = df_doc['time_diff'].apply(lambda x: list(map(float, x.split(',')))[-1]).mean()

    num_appointments_booked = dict(map(list, df_app_filtered['place'].value_counts().items())) #np.array( (map(list, df_app_filtered['place'].value_counts().items())))
    num_tags_issued = dict(map(list, df_dep['place'].value_counts().items())) #np.array(list(map(list, df_dep['place'].value_counts().items())))

    num_appointments_missed ={doc : num_appointments_booked[doc] - num_tags_issued[doc] for doc in num_appointments_booked.keys()}

    print(num_appointments_booked)
    pie_figure = {
        "data": [
            {
                "values": list(num_appointments_booked.values()),
                "labels": list(num_appointments_booked.keys()),
                "type": "pie",
                "marker": {"colors": colors, "line": dict(color="black", width=2)},
                "hoverinfo": "label",
                "textinfo": "label",
            }
        ],
        "layout": {
            "margin": dict(t=20, b=30),
            #                 "margin": dict(l=20, r=20, t=20, b=20),
        "uirevision": True,
            "font": {"color": "black"},
            # "showlegend": False,
            "paper_bgcolor": "rgba(255,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "height": 300,
        },
    }
    pie_figure_missed = {
        "data": [
            {
                "values": list(num_appointments_missed.values()),
                "labels": list(num_appointments_missed.keys()),
                "type": "pie",
                "marker": {"colors": colors, "line": dict(color="black", width=2)},
                "hoverinfo": "label",
                "textinfo": "label",
            }
        ],
        "layout": {
            "margin": dict(t=20, b=30),
            #                 "margin": dict(l=20, r=20, t=20, b=20),
            "uirevision": True,
            "font": {"color": "black"},
            # "showlegend": False,
            "paper_bgcolor": "rgba(255,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "height": 300,
        },
    }

    bar_figure = {
            "data": [
                {
                    "y": [dep_avg_time, doc_avg_time],
                    "x": [department, doctor],
                    "width": [0.3, 0.3],
                    "type": "bar",
                    'name': 'Average time',
                }
            ],
            "layout": {
                "title" : "Average Time ",
                "margin": dict(l=50, r=20, t=40, b=20),
                # "showlegend": True,
                "height" : 300,
    "yaxis" : dict(
        title='Time (in minutes)',
        # titlefont_size=16,
        tickfont_size=14,
    ),
                # "paper_bgcolor": "#0000FF",
                # "plot_bgcolor": "rgba(0,0,0,0)",
                # "font": {"color": "white"},
                # "autosize": True,
            }}

    return [html.Div(id="wait_time_table",
            children=initialize_table(get_key_for_value(doc_enc_dict, doctor))),
                pie_figure, pie_figure_missed, bar_figure
                    ]
@app.callback(output=Output('doctor-select', "options"),
              inputs=[Input("department-select", "value")])
def update_doctors(department):
    print("Department call back called")
    doctors_in_dep = dep_dict[department]
    doctors_in_dep = [doc_enc_dict[doc_enc] for doc_enc in doctors_in_dep]
    print(doctors_in_dep)
    return [{"label": i, "value": i} for i in doctors_in_dep]


# Run the server
if __name__ == "__main__":
    app.run_server(debug=True, port=8070)
