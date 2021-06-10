#!/usr/bin/env python
# coding: utf-8

# In[2]:


import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import datetime
import plotly.graph_objects as go


# In[3]:


# Create game data 

def assign_xG(df):
    d = {'N':0,'F':0.01,'E':0.05,'D':0.09,'C':0.15,'B':0.24,'A/B':0.3,'A':0.4,'A++':.9,'A+':0.6,'Corner':0.18}
    
    Melita = df.columns[0]
    Opposition = df.columns[1]
    
    df[Melita + '_xG'] = df[Melita].apply(lambda x: d.get(x)).astype('float')
    df[Opposition + '_xG'] = df[Opposition].apply(lambda x: d.get(x)).astype('float')
    
    return df
df = pd.read_csv('game_data2.csv')
df['Time'] = pd.to_numeric(df['Time'])
df['Date'] = pd.to_datetime(df['Date'],dayfirst=True).dt.date
df.set_index('Time',inplace=True)
df = assign_xG(df)
df['GW'] = 0
df.reset_index(inplace=True)
dates = df['Date'].unique()
dates = list(dates)
for i in dates:
    for j in df.index:
        if i == df['Date'][j]:
            df['GW'][j] = (dates.index(i)+1)
df.set_index('Time',inplace=True)

game = df[['Opposition','Date','Mel_Reg_xG','Opp_Reg_xG','GW','H_A']]
game['Date'] = pd.to_datetime(game['Date'])
summary = pd.read_csv('Summary.csv')


# In[4]:


# gks and throws
def throw_ins(df):
    df = df.dropna()
    d = {1.0:'Own 3rd',2.0:'Middle 3rd',3.0:'Attacking 3rd'}
    df['Possession'] = pd.to_numeric(df['Possession'])
    df['Area_Cat'] = [d.get(i) for i in df['Area ']]
    cols = ['Time','Type','Possession','Area_Cat','Date']
    df['Date'] = pd.to_datetime(df['Date'],dayfirst=True)
    df = df[cols]
    return df
df2 = pd.read_csv('throws.csv')
df2 = throw_ins(df2)
df_yes= df2[df2.Possession==1]
df_no = df2[df2.Possession==0]
df_no['Possession'] = 1

def get_gk(df):
    d = {'N':0,'F':0.01,'E':0.05,'D':0.09,'C':0.15,'B':0.24,'A':0.4,'A+':0.6,'Corner':0.18}
    xg = []
    xga = []
    for i in df.index:
        xg.append(d.get(df['xG'][i]))
        xga.append(d.get(df['xGa'][i]))
    df['xg'] = xg
    df['xga'] = xga
    cols = ['type','possession_5','possession_10','xg','xga','Date']
    df = df[cols]
    return df

gk = pd.read_csv('gks.csv')
gk = get_gk(gk)


# In[5]:


gk5_yes = gk[gk.possession_5==1]
gk5_no = gk[gk.possession_5==0]
gk5_no['possession_5'] =1

gk10_yes = gk[gk.possession_10==1]
gk10_no = gk[gk.possession_10==0]
gk10_no['possession_10'] =1


# In[6]:


df = pd.read_csv('feedback.csv').dropna()
feedback = df
feedback.set_index('Name',inplace=True)


# In[7]:


# dictionary of teams 

d = {'2020-12-14':'St Andrews','2020-12-07': 'Lija','2020-12-21':'Valletta',
     '2021-01-25':'Birkikara','2021-02-01':'San Gwann','2021-02-08':'Balzan','2021-02-15':'Hamrun','2021-02-22':'Pieta'}


team_names = game['Date'].dt.date.unique()
team_names.sort()

era_marks = game['GW'].unique()


# In[8]:


# Create player basic data table

df = pd.read_csv('Player.csv')
basic = ['Name','Age','Position','VARK','Height','Weight']
big5 = ['Name','Openness','Conscientiousness','Extraversion','Agreeableness','Neuroticism']
tact = ['Name','Tactical','Technical','GameIQ','Physical']

basic_df = df[basic]
basic_df.set_index('Name',inplace=True)
big5_df = df[big5]
big5_df.set_index('Name',inplace=True)
tact_df = df[tact]
tact_df.set_index('Name',inplace=True)

players = df['Name'].unique()

traits = [big5_df.Openness.mean(),big5_df.Conscientiousness.mean(),big5_df.Extraversion.mean(),
         big5_df.Agreeableness.mean(),big5_df.Neuroticism.mean()]

tact_list = [tact_df.Tactical.mean(),tact_df.Technical.mean(),tact_df.GameIQ.mean(),tact_df.Physical.mean()]


# Match Ratings and Training Attendance

ratings = pd.read_csv('ratings.csv').fillna(0)
ratings.set_index('Name',inplace=True)

training = pd.read_csv('training.csv').fillna(0)
training.set_index('Name',inplace=True)


# In[ ]:


# set app variable with dash, set external style to bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE],
        meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'},],)
# set app server to variable for deployment
srv = app.server

# set app callback exceptions to true
app.config.suppress_callback_exceptions = True

# set applicaiton title
app.title = 'Melita FC FAF'


# Main applicaiton menu
appMenu = html.Div([
    dbc.Row(
        [
            dbc.Col(html.H4(style={'text-align': 'center'}, children='Select Match:'),
                xs={'size':'auto', 'offset':0}, sm={'size':'auto', 'offset':0}, md={'size':'auto', 'offset':3},
                lg={'size':'auto', 'offset':0}, xl={'size':'auto', 'offset':0}),
            dbc.Col(dcc.Dropdown(
                style = {'text-align': 'center', 'font-size': '18px', 'width': '210px'},
                id='era-dropdown',
                options=[{'label':i,'value':i} for i in team_names],
                value=team_names[0],
                clearable=False),
                xs={'size':'auto', 'offset':0}, sm={'size':'auto', 'offset':0}, md={'size':'auto', 'offset':0},
                lg={'size':'auto', 'offset':0}, xl={'size':'auto', 'offset':0})
        ],
        form=True,
    ),
    
],className='menu')

def Navbar():
    navbar = dbc.NavbarSimple(children=[
            dbc.NavItem(dbc.NavLink("Match", href='/match')),
            dbc.NavItem(dbc.NavLink("Player", href='/player')),
            dbc.NavItem(dbc.NavLink("Team", href='/team')),
        ],
        brand="Home",
        brand_href="/",
        sticky="top",
        color="light",
        dark=False,
        expand='lg',)
    return navbar

# Layout for Team Analysis page
teamLayout = html.Div([
    #dbc.Row(dbc.Col(html.H3(children='Team Accolades'))),
    # Display Championship titles in datatable
    #dbc.Row(dbc.Col(html.Div(id='team-data'), xs={'size':'auto', 'offset':0}, sm={'size':'auto', 'offset':0}, md={'size':7, 'offset':0}, lg={'size':'auto', 'offset':0},
    #            xl={'size':'auto', 'offset':0}),justify="center"),
    ### Graphs of Historical Team statistics ###
    html.Br(),
    #dbc.Row(dbc.Col(html.H3(children='Match Analysis'))),
    # Bar Chart of Wins and Losses
    dbc.Row(dbc.Col(dcc.Graph(id='xg-track', config={'displayModeBar': False}), xs={'size':12, 'offset':0}, sm={'size':12, 'offset':0}, md={'size': 12, 'offset': 0},lg={'size': 12, 'offset': 0})),
    # Line Chart of Batting Average, BABIP, and Strikeout Rate
    dbc.Row(dbc.Col(dcc.Graph(id='xg-cum', config={'displayModeBar': False}), xs={'size':12, 'offset':0}, sm={'size':12, 'offset':0}, md={'size': 12, 'offset': 0},lg={'size': 12, 'offset': 0})),
    # Bar Char of Errors and Double Plays
    dbc.Row(dbc.Col(html.H4(children='Throw In Analysis'))),
    dbc.Row(
        [
            # Line graph of K/BB ratio with ERA bubbles
            dbc.Col(dcc.Graph(id='throw1', config={'displayModeBar': False}), xs={'size':12, 'offset':0}, sm={'size':12, 'offset':0}, md={'size': 12, 'offset': 0},lg={'size': 6, 'offset': 0}),
            # Pie Chart, % of Completed Games, Shutouts, and Saves of Total Games played
            dbc.Col(dcc.Graph(id='throw2', config={'displayModeBar': False}), xs={'size':12, 'offset':0}, sm={'size':12, 'offset':0}, md={'size': 12, 'offset': 0},lg={'size': 6, 'offset': 0}),
        ],
        no_gutters=True,
        
    ),
    dbc.Row(dbc.Col(html.H4(children='Goal Kick Analysis'))),
    dbc.Row(
        [
            # GK xG differential
            dbc.Col(dcc.Graph(id='gk1', config={'displayModeBar': False}), xs={'size':12, 'offset':0}, sm={'size':12, 'offset':0}, md={'size': 12, 'offset': 0},lg={'size': 6, 'offset': 0}),
            # GK Possession retained graphs
            dbc.Col(dcc.Graph(id='gk2', config={'displayModeBar': False}), xs={'size':12, 'offset':0}, sm={'size':12, 'offset':0}, md={'size': 12, 'offset': 0},lg={'size': 6, 'offset': 0}),
            dbc.Col(dcc.Graph(id='gk3', config={'displayModeBar': False}), xs={'size':12, 'offset':0}, sm={'size':12, 'offset':0}, md={'size': 12, 'offset': 0},lg={'size': 6, 'offset': 0}),
        ],
        no_gutters=True,
        
    )
    ,
],className='app-page')




# Player menu used to select players after era and team are set
playerMenu = html.Div([
    dbc.Row(dbc.Col(html.H3(children='Player Profile and Statistics'))),
    html.Br(),
    #dbc.Row(dbc.Col(html.P(style={'font-size': '16px', 'opacity': '70%'},
    #    children='Available players are updated based on team selection.'))),
    dbc.Row(
        [
            dbc.Row(dbc.Col(html.H4(style={'text-align': 'center'}, children='Select Player:'), xs={'size':'auto', 'offset':0}, sm={'size':'auto', 'offset':0},
                md={'size':'auto', 'offset':0}, lg={'size':'auto', 'offset':0}, xl={'size':'auto', 'offset':0})),
            dbc.Row(dbc.Col(dcc.Dropdown(
                style={'margin-left': '2%', 'text-align': 'center', 'font-size': '18px', 'width': '218px'},
                id='player-dropdown',
                options = [{'label':i,'value':i} for i in players],
                value = players[0],
                clearable=False
                ), xs={'size':'auto', 'offset':0}, sm={'size':'auto', 'offset':0}, md={'size':'auto', 'offset':0}, lg={'size':'auto', 'offset':0},
                xl={'size':'auto', 'offset':0})),
        ],
        no_gutters=True,
    ),
    html.Br(),
    dbc.Row(dbc.Col(dash_table.DataTable(
            id='playerProfile',
            style_as_list_view=True,
            editable=False,
            style_table={
                'overflowY': 'scroll',
                'width': '100%',
                'minWidth': '100%',
            },
            style_header={
                    'backgroundColor': '#f8f5f0',
                    'fontWeight': 'bold'
                },
            style_cell={
                    'textAlign': 'center',
                    'padding': '8px',
                },
        ), xs={'size':'auto', 'offset':0}, sm={'size':'auto', 'offset':0}, md={'size':8, 'offset':0}, lg={'size':'auto', 'offset':0},
                xl={'size':'auto', 'offset':0}),justify="center"),
    html.Br()
],className = 'app-page')

fig8 = px.line_polar(feedback,r=feedback['Feedback_Type'].value_counts().values,theta=feedback['Feedback_Type'].value_counts().index, line_close=True)
fig8.update_traces(fill='toself')
fig8.update_layout(title={'text':'Feedback','x':0.5})

fig9 = px.line_polar(basic_df,r=basic_df['VARK'].value_counts().values,theta=basic_df['VARK'].value_counts().index, line_close=True)
fig9.update_traces(fill='toself')
fig9.update_layout(title={'text':'VARK','x':0.5})

fig10 = px.line_polar(big5_df,r=traits,theta=big5[1:], line_close=True)
fig10.update_traces(fill='toself')
fig10.update_layout(title={'text':'Big 5','x':0.5})

fig11 = px.line_polar(tact_df,r=tact_list,theta=tact[1:], line_close=True)
fig11.update_traces(fill='toself')
fig11.update_layout(title={'text':'Squad Summary','x':0.5})




# Player menu used to select players after era and team are set
summaryMenu = html.Div([
    dbc.Row(dbc.Col(html.H3(children='Summary Statistics'))),
    html.Br(),
    #dbc.Row(dbc.Col(html.P(style={'font-size': '16px', 'opacity': '70%'},
    #    children='Aggregated from match and player data.'))),
    
    dbc.Row(dbc.Col(
        dash_table.DataTable(
            id='summaryTable',
            columns = [{"name": i, "id": i} for i in summary.columns],
            data=summary.to_dict('records'),
            editable=False,
            style_table={
                'overflowY': 'auto',
                'width': '100%',
                'minWidth': '100%',
            },
            style_header={
                    'backgroundColor': '#f8f5f0',
                    'fontWeight': 'bold'
                },
            style_cell={
                    'textAlign': 'center',
                    'padding': '8px',
                }
        ), xs={'size':12, 'offset':0}, sm={'size':12, 'offset':0}, md={'size':10, 'offset':0}, lg={'size':10, 'offset':0},
                xl={'size':10, 'offset':0}),justify="center"),
    
    html.Br(),
    dbc.Row(dbc.Col(html.H3(style={'margin-top': '1%', 'margin-bottom': '1%'},
            children='Team Profile'))),
    dbc.Row(dbc.Col(html.P(style={'font-size': '16px', 'opacity': '70%'},
                          children = 'Averaged from player data'))),

    dbc.Row(
        [
            html.Br(),# Line/Bar Chart of On-Base Percentage, features; H BB HBP SF
            html.Br(),
            dbc.Col(dcc.Graph(figure = fig10, config={'displayModeBar': False}), xs={'size':12, 'offset':0}, sm={'size':12, 'offset':0}, md={'size': 12, 'offset': 0},lg={'size': 6, 'offset': 0}),
            # Line/Bar Chart of Slugging Average, features; 2B 3B HR
            dbc.Col(dcc.Graph(figure=fig11, config={'displayModeBar': False}), xs={'size':12, 'offset':0}, sm={'size':12, 'offset':0}, md={'size': 12, 'offset': 0},lg={'size': 6, 'offset': 0}),
            html.Br(),
            html.Br(),
            dbc.Col(dcc.Graph(figure=fig9, config={'displayModeBar': False}), xs={'size':12, 'offset':0}, sm={'size':12, 'offset':0}, md={'size': 12, 'offset': 0},lg={'size': 6, 'offset': 0}),
            dbc.Col(dcc.Graph(figure=fig8, config={'displayModeBar': False}), xs={'size':12, 'offset':0}, sm={'size':12, 'offset':0}, md={'size': 12, 'offset': 0},lg={'size': 6, 'offset': 0}),
        ],
        no_gutters=True,
    ),
    
],className = 'app-page')
    
    
    



# Batting statistics
battingLayout = html.Div([
    # Batting datatable
    dbc.Row(dbc.Col(
        dash_table.DataTable(
            id='batterTable',
            style_as_list_view=True,
            editable=False,
            style_table={
                'overflowY': 'auto',
                'width': '100%',
                'minWidth': '100%',
            },
            style_header={
                    'backgroundColor': '#f8f5f0',
                    'fontWeight': 'bold'
                },
            style_cell={
                    'textAlign': 'center',
                    'padding': '8px',
                }
        ), xs={'size':12, 'offset':0}, sm={'size':12, 'offset':0}, md={'size':10, 'offset':0}, lg={'size':10, 'offset':0},
                xl={'size':10, 'offset':0}),justify="center"),

    html.Br(),
    dbc.Row(dbc.Col(html.H3(style={'margin-top': '1%', 'margin-bottom': '1%'},
            children='Player Analysis'))),
    dbc.Row(dbc.Col(html.P(style={'font-size': '16px', 'opacity': '70%'},
            children='Information collected at the start of the 21/22 season'))),

    dbc.Row(
        [
            # Line/Bar Chart of On-Base Percentage, features; H BB HBP SF
            dbc.Col(dcc.Graph(id='big5', config={'displayModeBar': False}), xs={'size':12, 'offset':0}, sm={'size':12, 'offset':0}, md={'size': 12, 'offset': 0},lg={'size': 6, 'offset': 0}),
            # Line/Bar Chart of Slugging Average, features; 2B 3B HR
            dbc.Col(dcc.Graph(id='tactical', config={'displayModeBar': False}), xs={'size':12, 'offset':0}, sm={'size':12, 'offset':0}, md={'size': 12, 'offset': 0},lg={'size': 6, 'offset': 0})
        ],
        no_gutters=True,
    ),
    
],className = 'app-page')


# Callback to a xG Tracker Chart, takes data request from dropdown
@app.callback(
    [Output('xg-track', 'figure'),Output('xg-cum', 'figure')],
    [Input('era-dropdown', 'value')])


def update_figure1(grpname):
    fig1 = px.line(game[game.Date == grpname], x=game[game.Date == grpname].index, 
                   y=[game[game.Date == grpname].Opp_Reg_xG,game[game.Date == grpname].Mel_Reg_xG],labels={'x':' ','value':'xG'})
    fig1.update_layout(title_text="Melita vs "+d.get(grpname)+" "+ "("+(game[game.Date==grpname].H_A[1]+")"), 
                       title_x=0.5,legend_title="Teams")
    nameswap = {'wide_variable_0': d.get(grpname),'wide_variable_1': 'Melita'}
    
    for i, dat in enumerate(fig1.data):
        for elem in dat:
            if elem == 'name':
                fig1.data[i].name = nameswap[fig1.data[i].name]

    fig2 = px.line(game[game.Date==grpname],x=game[game.Date == grpname].index,y=[game[game.Date == grpname]['Opp_Reg_xG'].cumsum(),
                                                                          game[game.Date == grpname]['Mel_Reg_xG'].cumsum()],
                   labels={'x':' ','value':'Cumulative xG'})
    fig2.update_layout({'showlegend':False})
    nameswap = {'wide_variable_0': d.get(grpname),'wide_variable_1': 'Melita'}
    
    for i, dat in enumerate(fig2.data):
        for elem in dat:
            if elem == 'name':
                fig2.data[i].name = nameswap[fig2.data[i].name]                
                
    return [fig1,fig2]


# Callback to a set pieces, takes data request from dropdown
@app.callback(
    [Output('throw1', 'figure'),Output('throw2', 'figure')],
    [Input('era-dropdown', 'value')])

def gen_chart(grpname):
    fig5 = px.bar(df_no[df_no.Date==grpname],x='Type',y='Possession',color='Area_Cat')
    fig5.update_layout(title_text="Possession Lost",legend_title="Area of Pitch")
    fig6 = px.bar(df_yes[df_yes.Date==grpname],x='Type',y='Possession',color='Area_Cat')
    fig6.update_layout(title_text="Possession Retained",legend_title="Area of Pitch")
            
    
    return [fig5,fig6]


@app.callback(
    [Output('gk1', 'figure'),Output('gk2', 'figure'),Output('gk3', 'figure')],
    [Input('era-dropdown', 'value')])

def gen_chart(grpname):
    fig7 = px.bar(gk[gk.Date==grpname].groupby('type').sum(),x=gk[gk.Date==grpname].groupby('type').sum().index,
                  y=['xg','xga'],labels={'x':' ','value':'xG'})
    fig7.update_layout(barmode='group',legend_title="")
    nameswap1 = {'xg': 'xG For','xga': 'xG Against'}
    for i, dat in enumerate(fig7.data):
        for elem in dat:
                if elem == 'name':
                    fig7.data[i].name = nameswap1[fig7.data[i].name]
    
    
    fig8 = go.Figure()
    fig8.add_trace(go.Bar(x=gk5_yes[gk5_yes.Date==grpname]['type'],y=gk5_yes[gk5_yes.Date==grpname]['possession_5'],showlegend=True,name='Retained'))
    fig8.add_trace(go.Bar(x=gk5_no[gk5_no.Date==grpname]['type'],y=gk5_no[gk5_no.Date==grpname]['possession_5'],showlegend=True,name='Lost'))
    fig8.update_layout(legend_title='Possession',title={'text':'After 5 seconds','x':0.5})

    
    fig9 = go.Figure()
    fig9.add_trace(go.Bar(x=gk10_yes[gk10_yes.Date==grpname]['type'],y=gk10_yes[gk10_yes.Date==grpname]['possession_5'],showlegend=True,name='Retained'))
    fig9.add_trace(go.Bar(x=gk10_no[gk10_no.Date==grpname]['type'],y=gk10_no[gk10_no.Date==grpname]['possession_5'],showlegend=True,name='Lost'))
    fig9.update_layout(legend_title='Possession',title={'text':'After 10 seconds','x':0.5})


    return [fig7,fig8,fig9]



# Callback to Player profile datatable
@app.callback(
    [Output('playerProfile', 'data'),Output('playerProfile','columns')],
    [Input('player-dropdown', 'value')])

def update_profile_table(player):
    # Create player filter with selected player
    filter_player = basic_df[basic_df.index==player]

    # drop unneccesary columns
    data_filter = filter_player
    
    # Return player profile to datatable
    return data_filter.to_dict('records'), [{'name': x, 'id': x} for x in data_filter]



@app.callback(
    [Output('big5', 'figure'),Output('tactical', 'figure')],
    [Input('player-dropdown', 'value')])

def update_figure3(player):
    fig3 = px.line_polar(big5_df.loc[player], r=big5_df.loc[player].values, theta=big5_df.loc[player].index, line_close=True)
    fig3.update_traces(fill='toself')

    fig4 = px.line_polar(tact_df.loc[player], r=tact_df.loc[player].values, theta=tact_df.loc[player].index, line_close=True)
    fig4.update_traces(fill='toself')
    
    
    return [fig3,fig4]

@app.callback(
    [Output('batterTable', 'data'),Output('batterTable','columns')],
    [Input('player-dropdown', 'value')])
def update_batter_table(player):
    
    filter_player = feedback[feedback.index==player]
    

    return filter_player.to_dict('records'), [{'name': x, 'id': x} for x in filter_player]


# Layout variables, navbar, header, content, and container
nav = Navbar()

header = dbc.Row(
    dbc.Col(
        html.Div([
            html.H2(children='Melita FC : Data Analysis Hub',style={'text-align':'center'}),
            html.Br()])
        ),className='banner')

content = html.Div([
    dcc.Location(id='url'),
    html.Div(id='page-content')
])

container = dbc.Container([
    header,
    content,
])


# Menu callback, set and return
# Declair function  that connects other pages with content to container
@app.callback(Output('page-content', 'children'),
            [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return html.Div([dcc.Markdown('''
            ### 
            “The problem is that if you do not recognize when you have been lucky you can fool yourself into thinking your performance was the result of your own genius. 
            It rarely is. Understanding why and how you won is the key to sustaining success.”
            
       
                        
            ### Football Analysis Framework
            Through the combination of match, player and training data, we provide a framework to evaluate individual 
            and team performance. The main tool used to capture match data is expected goals, which provides an objective measure of chance
            creation and concession. Training and player data is collected using questionnaires and quizzes, as well as input from 
            the teams coach. The coach is best placed to provide the most accurate description of each players performance and ability,
            and the continuous feedback will make it easy to track each players performance and progression, while using match performance
            as a benchmark.
            
            ### Glossary of terms:
            * xG (Expected Goals) - The probability of an action leading to a goal.
            * xGa (Expected Goals Against) - The opposition xG.
            * VARK : A questionnaire that looks to identify each players best method of absorbing information.  
                * Visual, Aurel,Reading/Writing, Kinesthetic (training).
            * Cumulative xG: The running total of xG. So if a team creates one chance of 0.05 and another of 0.10, then their
            cumulative xG is 0.15.
            * Big 5 Personality : Breaks a persons personality into 5 main categories. Far from perfect, but can provide some useful
            information when dealing with different types.
            
                 1) Openness : General appreciation for art, emotion, adventure, unusual ideas, imagination, curiosity, and variety of experience.
            
                 2) Conscientiousness : Self-discipline, act dutifully, and strive for achievement against measures or outside expect.
        
                 3) Extraversion : Extraverts enjoy interacting with people, and are often perceived as full of energy. They tend to be enthusiastic, action-oriented individual.
                 3) Introversion : Lower social engagement and energy levels than extraverts. They tend to seem quiet, low-key, deliberate, and less involved in the social world. 

                 4) Agreeableness : Value getting along with others. They are generally considerate, kind, generous,trusting and trustworthy, helpful, and willing to compromise their interests with other.
            
                 5) Neuroticism : Emotionally reactive and vulnerable to stress. They are more likely to interpret ordinary situations as threatening.
            
        ''')],className='home')
    elif pathname == '/match':
        return appMenu, teamLayout
    elif pathname == '/player':
        return playerMenu, battingLayout
    elif pathname == '/team':
        return summaryMenu
    else:
        return 'ERROR 404: Page not found!'


# Main index function that will call and return all layout variables
def index():
    layout = html.Div([
            nav,
            container
        ])
    return layout

# Set layout to index function
app.layout = index()

# Call app server
if __name__ == '__main__':
    # set debug to false when deploying app
    app.run_server(debug=False)


# In[137]:





# In[ ]:




