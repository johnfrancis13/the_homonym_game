from flask import Flask, request, session, url_for, redirect, render_template,g, flash,session
from markupsafe import Markup 
from markdown import markdown
import pickle as pkl
import random
import os
import re

app = Flask(__name__)
app.secret_key = 'BAD_SECRET_KEY'

# In-memory storage for player scores and game state
player_scores = {}
current_round = 1
num_rounds = 0
current_player_index = 0

LEADERBOARD_FILE = 'leaderboard.pkl'

def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'rb') as f:
            return pkl.load(f)
    return []

def save_leaderboard(leaderboard):
    with open(LEADERBOARD_FILE, 'wb') as f:
        pkl.dump(leaderboard, f)

# Define the model for game results
#class GameResult(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    player = db.Column(db.String(50), nullable=False)
#    score = db.Column(db.Integer, nullable=False)



# Load the dataset
with open('test_homonyms.pkl', 'rb') as handle:
	homonym_data = pkl.load(handle)



globalTitle = "The Homonym Game"
app = Flask(__name__)

@app.before_request
def before_request():
    g.globalTitle = globalTitle

@app.route('/game_setup', methods=['GET'])
def game_setup():
    """Render the file upload form."""
    return render_template('game_setup.html', title="Game Setup", open_window=False)


@app.route('/')
def defaultlanding():
    """Shows the about page by default.
    """
    return redirect(url_for('about'))

@app.route('/about')
def about():
    """Displays a markdown doc describing the game.
    """
    file = open('./static/about.md', 'r')
    rawText = file.read()
    file.close()
    content = Markup(markdown(rawText, 
        extensions=['markdown.extensions.fenced_code', 'markdown.extensions.tables']))
    return render_template('markdowntemplate.html', 
                           title='About', 
                           content=content)

@app.route('/setup_players', methods=['POST'])
def setup_players():
    global num_rounds
    num_players = int(request.form['num_of_players'])
    num_rounds = int(request.form['num_rounds'])
    return render_template('setup_players.html', num_players=num_players,num_rounds=num_rounds)

@app.route('/initialize_players', methods=['POST'])
def initialize_players():
    global player_scores, current_round, current_player_index, players
    players = [request.form[f'player{i}'] for i in range(1, len(request.form) + 1)]
    player_scores = {player: 0 for player in players}
    session['current_round'] = 1
    current_player_index = 0
    return redirect(url_for('next_turn'))

@app.route('/next_turn')
def next_turn():
    global current_round, current_player_index
    if session['current_round'] > num_rounds:
        return redirect(url_for('game_over'))

    session['current_player']  = players[current_player_index]
    return redirect(url_for('index'))

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    global current_player_index, current_round
    player = request.form['player']
    player_scores[player] += 1


    current_player_index = (current_player_index + 1) % len(players)
    if current_player_index == 0:
        session['current_round'] += 1

    return redirect(url_for('next_turn'))

def generate_question():
    return random.choice(homonym_data)

#@app.route('/assign_points', methods=['POST'])
#def assign_points():
#    player = request.form['player']
#    player_scores[player] += 1
#    return redirect(url_for('index'))

@app.route('/game_over')
def game_over():
    # Find the winner(s)
    max_score = max(player_scores.values())
    winners = [player for player, score in player_scores.items() if score == max_score]

    # Load current leaderboard
    leaderboard = load_leaderboard()

    # Update the leaderboard with the winner(s)
    for winner in winners:
        found = False
        for entry in leaderboard:
            if entry['player'] == winner:
                entry['total_wins'] += 1
                if max_score > entry['high_score']:
                    entry['high_score'] = max_score
                found = True
                break
        if not found:
            leaderboard.append({'player': winner, 'total_wins': 1, 'high_score': max_score})

    # Save updated leaderboard
    save_leaderboard(leaderboard)


    return render_template('game_over.html', player_scores=player_scores, winners=winners)


@app.route('/play_game')
def index():
    if session['current_round'] > num_rounds:
        return redirect(url_for('game_over'))
    #session['current_round'] += 1
    homonym = generate_question()
    selected_word = list(homonym.keys())[0]#.title()
    pronunciation = homonym[selected_word]['Pronunciation']
    pos = homonym[selected_word]['part_of_speech']
    etym = re.sub("Etym: ","",homonym[selected_word]['Etymology'])
    #defs = re.sub("Syn.","",homonym[selected_word]['Definitions']) 
    #defs_cleaned = Markup("<br/><br/>".join([str(i+1)+"."+j for i,j in enumerate([a for a in re.split(r'(\d+.)', defs) if len(a)>10])]))
    defs_cleaned = Markup("<br/><br/>".join([str(i+1)+"."+j for i,j in enumerate(homonym[selected_word]['Definitions']) if "Etym:" not in j ]))
    syno = re.sub("Syn.","",homonym[selected_word]['Synonyms']) 

    return render_template('play_game.html',
     selected_word=selected_word.title(),
     pronunciation= pronunciation,
     parts_of_speech= pos,
     etymology = etym,
     definitions = defs_cleaned,
     synonyms= syno,
     current_player=session['current_player'],
     players=player_scores.keys(), 
     player_scores=player_scores,
     current_round=session['current_round'], 
     num_rounds=num_rounds)

@app.route('/generate_new_homonym', methods=['POST'])
def generate_new_homonym():
    homonym = generate_question()
    selected_word = list(homonym.keys())[0]#.title()
    pronunciation = homonym[selected_word]['Pronunciation']
    pos = homonym[selected_word]['part_of_speech']
    etym = re.sub("Etym: ","",homonym[selected_word]['Etymology'])
    #defs = re.sub("Syn.","",homonym[selected_word]['Definitions']) 
    #defs_cleaned = Markup("<br/><br/>".join([str(i+1)+"."+j for i,j in enumerate([a for a in re.split(r'(\d+.)', defs) if len(a)>10])]))
    defs_cleaned = Markup("<br/><br/>".join([str(i+1)+"."+j for i,j in enumerate(homonym[selected_word]['Definitions']) if "Etym:" not in j ]))
    #defs_cleaned = defs_cleaned.split('<br>')
    syno = re.sub("Syn.","",homonym[selected_word]['Synonyms']) 

    return render_template('play_game.html',
     selected_word=selected_word.title(),
     pronunciation= pronunciation,
     parts_of_speech= pos,
     etymology = etym,
     definitions = defs_cleaned,
     synonyms= syno,
     current_player=session['current_player'],
     players=player_scores.keys(), 
     player_scores=player_scores,
     current_round=session['current_round'], 
     num_rounds=num_rounds)

@app.route('/leaderboard')
def leaderboard():
    # Retrieve the leaderboard data from the database
    leaderboard_data = load_leaderboard()
    sorted_leaderboard = sorted(leaderboard_data, key=lambda x: x['total_wins'], reverse=True)
    return render_template('leaderboard.html', leaderboard=sorted_leaderboard)


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.run(debug=True)

