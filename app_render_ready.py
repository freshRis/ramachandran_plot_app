
import base64
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import os
from dotenv import load_dotenv

# Carica variabili da .env se esiste (utile per test locali)
load_dotenv()

# Connessione al database tramite variabili d'ambiente
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")

connection = psycopg2.connect(
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    port=DB_PORT
)

cur = connection.cursor()

import numpy as np
from Bio import PDB
import plotly.graph_objects as go

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

class User:
    def __init__(self, username, password, is_admin='False'):
        self.username = username
        self.is_admin = is_admin
        self.password_hash = generate_password_hash(password)

    def get_username(self):
        return self.username

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def delete_user(self, Userd):
        if(self.is_admin):
            cur.execute("DELETE FROM users WHERE username=%s",(Userd.get_username(),))

    @staticmethod
    def get_user_by_username(username):
        cur.execute("SELECT username, pw, is_admin FROM users WHERE username = %s", (username,))
        user_data = cur.fetchone()
        if user_data:
            user = User(username=user_data[0], password="", is_admin=user_data[2])
            user.password_hash = user_data[1]
            return user
        return None

    def save_to_db(self):
        cur.execute("INSERT INTO users (username, pw, is_admin) VALUES (%s, %s, %s)", 
                    (self.username, self.password_hash, self.is_admin))
        connection.commit()

    def delete_user(self, user_to_delete):
        if self.is_admin:
            cur.execute("DELETE FROM users WHERE username=%s", (user_to_delete.get_username(),))
            connection.commit()

def generate_navbar(is_logged_in):
    if not is_logged_in:
        navbar = dbc.NavbarSimple(
            brand="Ramachandran plot generator",
            brand_href="/",
            color="primary",
            dark=True,
            children=[
                dbc.NavItem(dbc.NavLink("Home", href="/")),
                dbc.NavItem(dbc.NavLink("Login", href="/login")),
                dbc.NavItem(dbc.NavLink("Register", href="/register")),
            ],
        )
    else:
        navbar = dbc.NavbarSimple(
            brand="Ramachandran plot generator",
            brand_href="/",
            color="primary",
            dark=True,
            children=[
                dbc.NavItem(dbc.NavLink("Home", href="/")),
                dbc.NavItem(dbc.NavLink("Plot generator", href="/plot_generator")),
                dbc.NavItem(dbc.NavLink("Profile", href="/profile")),
            ],
        )
    return navbar

app.layout = html.Div([
    dcc.Store(id='session-store', storage_type='session'),
    dcc.Location(id='url', refresh=False),
    html.Div(id='navbar-container'),
    html.Div(id='page-content')
])

@app.callback(
    Output('navbar-container', 'children', allow_duplicate=True),
    Input('session-store', 'data'),
    prevent_initial_call='initial_duplicate',
)
def update_navbar(session_data):
    is_logged_in = session_data and session_data.get("logged_in", False)
    return generate_navbar(is_logged_in)

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/login':
        return html.Div([
            html.H1('Login'),
            dcc.Input(id='username-input', type='text', placeholder='username'),
            html.Br(),
            dcc.Input(id='pw-input', type='password', placeholder='password'),
            html.Br(),
            html.Button('Submit', id='submit-button', n_clicks=0),
            html.Div(id='login-output'),
            html.Br(),
            dcc.Link('forgot password? create a new one!', href='/restore_pw'),
            html.Br(),
        ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justifyContent': 'center', 'height': '50vh'})
    
    elif pathname == '/register':
        return html.Div([
            html.H1('Register'),
            dcc.Input(id='new-username', type='text', placeholder='Choose a username'),
            html.Br(),
            dcc.Input(id='new-password', type='password', placeholder='Choose a password'),
            html.Br(),
            html.Button('Register', id='register-button', n_clicks=0),
            html.Div(id='register-output'),
            html.Br(),
        ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justifyContent': 'center', 'height': '50vh'})
    
    elif pathname == '/restore_pw':
        return html.Div([
            html.H1('Generate a new password'),
            dcc.Input(id='old-username-input', type='text', placeholder='insert your username'),
            html.Br(),
            dcc.Input(id='new-pw-input', type='password', placeholder='insert the new password'),
            html.Br(),
            html.Button('Submit', id='restore-pw-button', n_clicks=0),
            html.Div(id='restore-output'),
            html.Br(),
            dcc.Link('Back to home', href='/'),
        ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justifyContent': 'center', 'height': '50vh'})
    
    elif pathname == '/plot_generator':
        return html.Div([
            html.H1('Insert the .pdb file!'),
            html.Br(),
            dcc.Upload(
                id="upload-file",
                children=html.Button("Insert the file .pdb", className="btn btn-primary"),
                multiple=False
            ),
            html.Br(),
            html.Div(id='plot-output'),
            html.Br(),
        ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justifyContent': 'center', 'height': '100vh'})
    
    elif pathname == '/profile':
        return html.Div([
            html.Div(id='user-info'),
            html.Br(),
            html.Button("logout", id="logout-button", n_clicks=0),
            html.Br(),
        ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justifyContent': 'center', 'height': '50vh'})
    
    return html.Div([
        html.H1("Welcome to ramachandran plot App", className="text-center"),
        html.Br(),
        html.Img(
            src="https://ars.els-cdn.com/content/image/3-s2.0-B9780081010358500274-f27-21-9780081010358.jpg",
            style={"width": "60%", "display": "block", "margin": "auto"}
        )
    ])
