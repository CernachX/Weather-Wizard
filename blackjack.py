from flask import Flask, render_template, jsonify, session, redirect, url_for
import random

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session management
app.template_folder = 'templates_bj'  # Specify the template folder

# Function to create a standard deck of 52 playing cards
def create_deck():
    """Creates a standard deck of 52 playing cards."""
    deck = []
    for suit in ['Hearts', 'Diamonds', 'Spades', 'Clubs']:
        for card in ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']:
            deck.append(f'{card} of {suit}')
    random.shuffle(deck)  # Shuffle the deck
    return deck

# Function to get the numeric value of a card
def get_card_value(card):
    """Helper function to get the numeric value of a card."""
    card_value = card.split(' ')[0]  # Extract the card's value (e.g., "10", "Jack")
    if card_value.isdigit():
        return int(card_value)  # Return numeric value for number cards
    elif card_value in ['Jack', 'Queen', 'King']:
        return 10  # Face cards are worth 10
    elif card_value == 'Ace':
        return 11  # Ace is worth 11 by default
    return 0  # Fallback for invalid cards

# Function to calculate the total value of a hand, accounting for Aces
def calculate_hand_value(hand):
    """Calculate the total value of a hand, accounting for Aces."""
    value = 0
    num_aces = 0
    for card in hand:
        card_value = get_card_value(card)
        if card_value == 11:
            num_aces += 1
        value += card_value

    # Adjust Aces from 11 to 1 if the total value exceeds 21
    while value > 21 and num_aces > 0:
        value -= 10
        num_aces -= 1
    return value
# Function to check if the player's hand contains a pair
def is_pair(hand):
    """
    Check if the player's hand contains a pair (two cards of the same rank).
    """
    if len(hand) == 2:  # Ensure the hand has exactly two cards
        return get_card_value(hand[0]) == get_card_value(hand[1])  # Compare card values
    return False
# Function to get a random card from the deck
def get_random_card(deck):
    """Gets a random card from the deck."""
    if not deck:
        return None  # Return None if the deck is empty
    return deck.pop()

# Function to handle the dealer's turn
def dealer_turn():
    """Dealer's turn logic (simplified)."""
    while calculate_hand_value(session['dealer_hand']) < 17:
        card = get_random_card(session['deck'])
        if card:
            session['dealer_hand'].append(card)
    session['game_over'] = True  # Mark the game as over after the dealer's turn

# Function to determine the result of the game
def get_result():
    """Determines the result of the game."""
    player_value = calculate_hand_value(session['player_hand'])
    dealer_value = calculate_hand_value(session['dealer_hand'])

    if player_value > 21:
        return 'You Busted! Dealer Wins!'
    elif dealer_value > 21:
        return 'Dealer Busted! You Win!'
    elif session['game_over']:
        if player_value > dealer_value:
            return 'You Win!'
        elif dealer_value > player_value:
            return 'Dealer Wins!'
        else:
            return 'Tie!'
    else:
        return 'Game in progress'

# Redirect the root URL to the Blackjack game
@app.route('/')
def to_bj():
    return redirect(url_for('blackjack'))

# Route to handle the initial game setup and display the game state
@app.route('/blackjack')
def blackjack():
    """Handles the initial game setup and displays the game state."""
    if 'deck' not in session:
        # Initialize the game state if it doesn't already exist
        session['deck'] = create_deck()
        session['player_hand'] = []
        session['dealer_hand'] = []
        session['game_over'] = False

        # Deal initial hands
        session['player_hand'].append(get_random_card(session['deck']))
        session['player_hand'].append(get_random_card(session['deck']))
        session['dealer_hand'].append(get_random_card(session['deck']))
        session['dealer_hand'].append(get_random_card(session['deck']))

    return render_template('blackjack.html',  # Render the Blackjack template
        player_hand=session['player_hand'],
        dealer_hand=session['dealer_hand'],
        result=get_result(),
        game_over=session['game_over'],
        is_pair=is_pair(session['player_hand'])  # Include pair information
    )

# Route to handle the player's "Hit" action
@app.route('/blackjack/hit')
def blackjack_hit():
    """Handles the player's 'Hit' action."""
    if not session['game_over']:
        card = get_random_card(session['deck'])
        if card:
            session['player_hand'].append(card)
        
        player_value = calculate_hand_value(session['player_hand'])
        if player_value >= 21:  # Player busts or hits exactly 21
            session['game_over'] = True
            dealer_turn()

    return jsonify(
        player_hand=session['player_hand'],
        dealer_hand=session['dealer_hand'],
        result=get_result(),
        game_over=session['game_over'],
        is_pair=is_pair(session['player_hand'])  # Include pair information
    )
# Route to handle the player's "Stand" action
@app.route('/blackjack/stand')
def blackjack_stand():
    """Handles the player's 'Stand' action."""
    if not session['game_over']:
        session['game_over'] = True
        dealer_turn()  # Trigger the dealer's turn
    return jsonify(  # Return the updated game state as JSON
        player_hand=session['player_hand'],
        dealer_hand=session['dealer_hand'],
        result=get_result(),
        game_over=session['game_over']
    )

# Route to handle starting a new game
@app.route('/blackjack/new_game')
def blackjack_new_game():
    """Handles starting a new game."""
    session.clear()  # Clear the session to reset the game state
    session['deck'] = create_deck()
    session['player_hand'] = []
    session['dealer_hand'] = []
    session['game_over'] = False

    # Deal initial hands
    session['player_hand'].append(get_random_card(session['deck']))
    session['player_hand'].append(get_random_card(session['deck']))
    session['dealer_hand'].append(get_random_card(session['deck']))
    session['dealer_hand'].append(get_random_card(session['deck']))
    return jsonify(  # Return the initial game state as JSON
        player_hand=session['player_hand'],
        dealer_hand=session['dealer_hand'],
        result=get_result(),
        game_over=session['game_over']
    )

# Route to handle the player's "Double Down" action
@app.route('/blackjack/double_down', methods=['POST'])
def blackjack_double_down():
    """Handles the player's 'Double Down' action."""
    if not session.get('game_over', False):  # Ensure the game is not already over
        # Player gets one additional card
        card = get_random_card(session['deck'])
        if card:
            session['player_hand'].append(card)
        
        # Calculate the player's hand value
        player_value = calculate_hand_value(session['player_hand'])
        if player_value > 21:  # Player busts
            session['game_over'] = True
        else:
            # Automatically stand after doubling down
            session['game_over'] = True
            dealer_turn()

    return jsonify(  # Return the updated game state as JSON
        player_hand=session['player_hand'],
        dealer_hand=session['dealer_hand'],
        result=get_result(),
        game_over=session['game_over']
    )

# Route to handle the player's "Split Pairs" action
@app.route('/blackjack/split_pairs', methods=['POST'])
def blackjack_split_pairs():
    """Handles the player's 'Split Pairs' action."""
    if not session.get('game_over', False):  # Ensure the game is not already over
        player_hand = session['player_hand']

        # Check if the player has exactly two cards and they form a pair
        if len(player_hand) == 2 and get_card_value(player_hand[0]) == get_card_value(player_hand[1]):
            # Create two separate hands
            session['split_hands'] = [[player_hand[0]], [player_hand[1]]]

            # Deal one additional card to each split hand
            session['split_hands'][0].append(get_random_card(session['deck']))
            session['split_hands'][1].append(get_random_card(session['deck']))

            # Remove the original hand
            session.pop('player_hand', None)

    return jsonify(  # Return the updated game state as JSON
        split_hands=session.get('split_hands', []),
        dealer_hand=session['dealer_hand'],
        result=get_result(),
        game_over=session['game_over']
    )

# Run the Flask application
if __name__ == "__main__":
    app.run(debug=False)