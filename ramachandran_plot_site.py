import base64
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc #componenti grafiche
from werkzeug.security import generate_password_hash, check_password_hash #password criptate
import psycopg2 #connessione a postgres
#{per ramachandran plot
import numpy as np
from Bio import PDB
import plotly.graph_objects as go
#}
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

connection = psycopg2.connect(
    host='localhost',
    dbname='postgres',
    user='postgres',
    password='33Fillo33$',
    port='5432'
)

cur=connection.cursor()


class User:
    def __init__(self, username, password, is_admin='False'):
        self.username = username
        self.is_admin = is_admin
        self.password_hash = generate_password_hash(password)

    def get_username(self):
        return self.username

    def check_password(self, password):
        """Verifica se la password inserita è corretta"""
        return check_password_hash(self.password_hash, password)
    
    def delete_user(self, Userd):
        if(self.is_admin):
            cur.execute("DELETE FROM users WHERE username=%s",(Userd.get_username(),))

    @staticmethod
    def get_user_by_username(username):
        """Recupera un utente dal database"""
        cur.execute("SELECT username, pw, is_admin FROM users WHERE username = %s", (username,))
        user_data = cur.fetchone()
        if user_data:
            user = User(username=user_data[0], password="", is_admin=user_data[2])  # Evita di hashare di nuovo
            user.password_hash = user_data[1]  # Assegna direttamente l'hash dal database
            return user
        return None

    def save_to_db(self):
        """Salva il nuovo utente nel database"""
        cur.execute("INSERT INTO users (username, pw, is_admin) VALUES (%s, %s, %s)", 
                    (self.username, self.password_hash, self.is_admin))
        connection.commit()

    def delete_user(self, user_to_delete):
        """Elimina un utente, solo se l'utente corrente è admin"""
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



# Layout principale
app.layout = html.Div([
    dcc.Store(id='session-store', storage_type='session'),  # Memorizza lo stato dell'utente
    dcc.Location(id='url', refresh=False),  # Per gestire la navigazione
    html.Div(id='navbar-container'),
    html.Div(id='page-content')  # Div che cambia contenuto in base all'URL
])

@app.callback(
    Output('navbar-container', 'children',allow_duplicate=True),
    Input('session-store', 'data'),
    prevent_initial_call='initial_duplicate',
    

)
def update_navbar(session_data):
    """Aggiorna la navbar in base allo stato dell'utente"""
    
    is_logged_in = session_data and session_data.get("logged_in", False)
    return generate_navbar(is_logged_in)

# Callback per aggiornare la pagina in base all'URL
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
                multiple=False  # Permettiamo solo un file alla volta
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
prevent_initial_call='initial_duplicate'
# Callback per il login
@app.callback(
    [Output('login-output', 'children'),
    Output('session-store','data')],
    Input('submit-button', 'n_clicks'),
    State('username-input', 'value'),
    State('pw-input', 'value')
)
def login(n_clicks, user, pw):
    if n_clicks > 0:
        u = User.get_user_by_username(user)
        if u is None:
            return 'Username not registered', {'logged_in': False}
        else:
            if u.check_password(pw):
                return dcc.Link("Login successful! Go to plot generator", href="/plot_generator"), {'logged_in': True,'username': u.get_username()}

            return 'Username or password incorrect!', {'logged_in': False}
    
    return '', {'logged_in': False} 

#callback per il logout
@app.callback(
        Output('url','pathname'),
        Output('navbar-container','children',allow_duplicate=True),
        Input('logout-button','n_clicks'),
        prevent_initial_call='initial_duplicate',
        allow_duplicate=True
) 
def logout(n_clicks):
    if n_clicks > 0:
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
        return '/', navbar
    else:
        navbar=dbc.NavbarSimple(
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
        return '/profile', navbar



# Callback per la registrazione
@app.callback(
    Output('register-output', 'children'),
    Input('register-button', 'n_clicks'),
    State('new-username', 'value'),
    State('new-password', 'value')
)
def register(n_clicks, new_user, new_pw):
    if n_clicks > 0:
        if len(new_pw) < 6 or '$' not in new_pw:
            return 'Password must be at least 6 characters and contain $!'

        if User.get_user_by_username(new_user) is None:
            new_user_obj = User(new_user, new_pw)
            new_user_obj.save_to_db()
            return dcc.Link("Registration successful! Go to plot generator", href="/plot_generator")
        
        return 'Error: Username already taken or invalid input!'
    
    return ''

# Callback per il ricreare la password
@app.callback(
    Output('restore-output', 'children'),
    Input('restore-pw-button', 'n_clicks'),
    State('old-username-input', 'value'),
    State('new-pw-input', 'value')
)
def restore_password(n_clicks, username, new_pw):
    if n_clicks > 0:
        user = User.get_user_by_username(username)
        if user:
            if len(new_pw) < 6 or '$' not in new_pw:
                return 'Password must be at least 6 characters and contain $!'
            
            hashed_pw = generate_password_hash(new_pw)
            cur.execute("UPDATE users SET pw = %s WHERE username = %s", (hashed_pw, username))
            connection.commit()
            return dcc.Link("New password was set successfully! Go to plot generator", href="/plot_generator")

        return 'Username incorrect!'
    return ''


#permetto di far vedere il profilo aggiornato
@app.callback(
    Output('user-info', 'children'),  # Cambia la pagina
    Input('url', 'pathname'),
    State('session-store', 'data')
)
def update_profile(path,data):
    if path=='/profile':
        username = data.get('username')
        #user = User.get_user_by_username()
        return f"welcome back {username}!"   
    return ''




def calculate_phi_psi(structure):
    """Calcola gli angoli phi e psi per ogni residuo della proteina."""
    phi_psi_angles = []
    
    # Parco attraverso tutte le catene della proteina
    for model in structure:
        for chain in model:
            polypeptides = PDB.PPBuilder().build_peptides(chain)
            for poly_index, poly in enumerate(polypeptides):
                # Ottieni la lista degli angoli φ (phi) e ψ (psi)
                phi_psi_list = poly.get_phi_psi_list()  # Restituisce una lista di tuple (phi, psi)
                
                # Aggiungi gli angoli a phi_psi_angles se non sono None
                for phi_psi in phi_psi_list:
                    if None not in phi_psi:  # Se entrambi gli angoli non sono None
                        phi_psi_angles.append(phi_psi)
    
    # Converti gli angoli da radianti a gradi
    phi_psi_angles = np.degrees(phi_psi_angles)
    
    return np.array(phi_psi_angles)

def plot_ramachandran(phi_psi_angles):
    """Genera il Ramachandran plot."""
    # Angoli φ (phi) e ψ (psi)
    phi = phi_psi_angles[:, 0]
    psi = phi_psi_angles[:, 1]
    
    plot= go.Figure(
        data=go.Scatter(x=phi,y=psi,mode='markers')
    ) 
    plot.update_layout(
        xaxis_title="Phi (°)",
        yaxis_title="Psi (°)",
        width=600,  # Imposta una larghezza fissa
        height=600,  # Imposta un'altezza uguale per renderlo quadrato
        xaxis=dict(scaleanchor="y"),  # Mantiene proporzioni 1:1
        yaxis=dict(scaleanchor="x")   # Blocca le scale assi per farlo quadrato
    )
    return plot



#callback per la selezione delle unità di misura
import os

@app.callback(
    Output('plot-output', 'children'),
    Input("upload-file", "contents"),
    State("upload-file", "filename")
)
def generate_plot(contents, filename):
    if contents is None:
        return "Nessun file caricato."

    if not filename.endswith(".pdb"):  # Controlla l'estensione
        return "Errore: Carica un file con estensione .pdb"

    # Decodifica il file PDB
    _, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)

    # **Salva il file con il percorso corretto**
    file_path = f"uploaded_{filename}"  # Salviamo il file nella cartella corrente
    with open(file_path, "wb") as f:
        f.write(decoded)

    # Usa il percorso corretto per il parser
    parser = PDB.PDBParser(QUIET=True)
    structure = parser.get_structure("protein", file_path)  # Usa il file salvato
    
    # Calcola gli angoli φ e ψ
    phi_psi_angles = calculate_phi_psi(structure)
    
    # Genera il Ramachandran plot
    return dcc.Graph(figure=plot_ramachandran(phi_psi_angles))




# Avvia l'app
if __name__ == '__main__':
    app.run_server(debug=True)
