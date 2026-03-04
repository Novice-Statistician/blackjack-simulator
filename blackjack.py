#!/usr/bin/env python
# coding: utf-8

# # Blackjack Simulator
# 
# **Author:** Zachary Niccoli  
# **Tools:** Python, Streamlit  
# **Date:** February 2026
# 
# ## Overview
# 
# This project is a quantitative blackjack simulation engine designed to model
# probability-based decision making, bankroll optimization, and advantage play strategy.
# 
# It integrates:
# 
# - Hi-Lo card counting
# - True count normalization
# - Kelly Criterion bet sizing
# - Monte Carlo probability simulation
# - Rule-based basic strategy engine
# - Session-level bankroll analytics
# 
# The goal of this project is to demonstrate applied probability modeling,
# risk-adjusted capital allocation, and decision analytics under uncertainty.

# ## Game Environment
# 
# The simulator models a realistic casino environment with the following assumptions:
# 
# - 6-deck shoe
# - Dealer stands on all 17s
# - Blackjack pays 3:2
# - Continuous running count until reshuffle
# - Automatic reshuffle at 25% shoe penetration
# 
# These assumptions are important because edge estimation depends heavily
# on rule variations and deck penetration.

# In[1]:


# =============================
# IMPORTS
# =============================

import streamlit as st
import random
import copy


# In[2]:


# =============================
# CONFIGURATION
# =============================
st.set_page_config(layout="wide")

st.markdown("""
<style>
    .stApp {
        background-color: #000000;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

DECKS = 6
INITIAL_BANKROLL = 10000

st.title("Blackjack Simulator")

st.markdown("""
### System Architecture

This application is structured into five core engines:

1. **Shoe Engine** – Multi-deck card generation and shuffle logic  
2. **Counting Engine** – Running and true count updates  
3. **Strategy Engine** – Conditional rule evaluation (basic strategy)  
4. **Simulation Engine** – Monte Carlo probability estimation  
5. **Capital Engine** – Kelly-based dynamic bet sizing  

Session state persists game state across reruns, enabling deterministic simulation behavior within Streamlit’s reactive framework.
""")

with st.expander("Project Overview"):
    st.markdown("""
## Objective

This project simulates a multi-deck blackjack environment designed to model 
probabilistic decision-making and capital allocation under uncertainty.

Rather than functioning as a simple game, this simulator integrates 
card counting theory, expected value modeling, and dynamic bankroll optimization 
to demonstrate applied quantitative finance concepts within a gaming framework.

---

## Core Modeling Components

### 1. Hi-Lo Card Counting
A running count is updated with each card dealt:
- 2–6 → +1  
- 7–9 → 0  
- 10–A → -1  

This approximates shifts in deck composition.

### 2. True Count Normalization
Running count is adjusted by decks remaining:

True Count = Running Count / Decks Remaining

This standardizes advantage estimation in multi-deck environments.

### 3. Kelly Criterion Bet Sizing
Estimated player edge (derived from True Count) is applied to the Kelly formula:

Optimal Bet = Bankroll × Edge

Bet sizing is capped at 25% of bankroll to control volatility.

### 4. Monte Carlo Simulation Engine
Each decision (Hit vs Stand) runs 500 forward simulations 
to estimate win and bust probabilities.

### 5. Rule-Based Basic Strategy Engine
Implements conditional logic for:
- Hard totals
- Soft totals
- Dealer up-card scenarios

---

## Why This Matters

This system demonstrates:

- Probabilistic modeling
- Risk-adjusted capital allocation
- Simulation-based decision analysis
- State-driven UI architecture
- Applied expected value theory

The simulator bridges gaming mathematics with financial modeling principles.
""")


# In[3]:


# =============================
# SESSION STATE DEFAULTS
# =============================
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.shoe = []
    st.session_state.running_count = 0
    st.session_state.player = []
    st.session_state.dealer = []
    st.session_state.done = False
    st.session_state.bankroll = INITIAL_BANKROLL

    st.session_state.bet = 50  

    # Locked wager for the CURRENT hand
    st.session_state.current_bet = 0

    st.session_state.message = ""
    st.session_state.hands = 0
    st.session_state.wins = 0
    st.session_state.evaluated = False


# In[4]:


# =============================
# CASINO STYLE
# =============================
st.markdown("""
<style>
.big-card {
    font-size: 34px;
    padding: 8px;
}

.red { color: #ff4c4c; }
.black { color: #FFFFFF; }

h2.win { color: #4CAF50 !important; font-weight: bold; }
h2.lose { color: #ff4c4c !important; font-weight: bold; }
h2.push { color: #FFD700 !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ## Shoe & Card Engine
# 
# This section implements a multi-deck blackjack shoe and manages card distribution.
# 
# A full 6-deck shoe is generated and shuffled to approximate casino conditions. 
# Each time a card is drawn:
# 
# - The shoe size decreases
# - The running Hi-Lo count updates
# - The remaining deck estimate changes
# 
# This structure allows the simulator to model real-world card composition drift,
# which is critical for advantage estimation and true count calculation.
# 
# Key responsibilities:
# - Generate multi-deck shoe
# - Shuffle logic
# - Card draw mechanics
# - Running count updates
# 

# ## Card Counting & Advantage Estimation
# 
# This section implements the Hi-Lo card counting system.
# 
# Card weights:
# - 2–6 → +1  
# - 7–9 → 0  
# - 10–Ace → -1  
# 
# The running count tracks deck composition imbalance.
# To standardize advantage in a multi-deck shoe, the running count is converted
# into a True Count:
# 
# True Count = Running Count / Decks Remaining
# 
# True Count serves as a proxy for expected player edge and directly influences bet sizing decisions.
# 

# In[5]:


# =============================
# CARD + SHOE LOGIC
# =============================
def create_shoe(decks):
    ranks = [
        ("2",2),("3",3),("4",4),("5",5),("6",6),
        ("7",7),("8",8),("9",9),
        ("10",10),("J",10),("Q",10),("K",10),
        ("A",11)
    ]
    suits = ["♠","♥","♦","♣"]
    shoe = []
    for _ in range(decks):
        for rank, value in ranks:
            for suit in suits:
                shoe.append({"rank": rank, "suit": suit, "value": value})
    random.shuffle(shoe)
    return shoe

def hi_lo_value(card):
    if card["value"] in [2,3,4,5,6]:
        return 1
    if card["value"] == 10 or card["rank"] == "A":
        return -1
    return 0

def deal_card():
    if len(st.session_state.shoe) == 0:
        st.session_state.shoe = create_shoe(DECKS)
        st.session_state.running_count = 0
    card = st.session_state.shoe.pop()
    st.session_state.running_count += hi_lo_value(card)
    return card

def hand_value(hand):
    total = sum(card["value"] for card in hand)
    aces = sum(1 for card in hand if card["rank"]=="A")
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def is_soft(hand):
    """
    A hand is soft if at least one Ace is being counted as 11
    after bust-adjustment.
    """
    total = sum(card["value"] for card in hand)
    aces = sum(1 for card in hand if card["rank"] == "A")

    while total > 21 and aces:
        total -= 10
        aces -= 1

    return aces > 0

def true_count():
    decks_remaining = len(st.session_state.shoe) / 52
    if decks_remaining <= 0:
        return 0
    return st.session_state.running_count / decks_remaining

def kelly_bet(bankroll, edge):
    fraction = max(0, edge)
    wager = bankroll * fraction
    return max(10, min(wager, bankroll * 0.25))


# ## Basic Strategy Decision Engine
# 
# This engine applies deterministic blackjack strategy rules 
# based on player total, soft/hard classification, and dealer up-card.
# 
# The logic models mathematically optimal play assuming:
# - No card counting influence
# - Standard multi-deck rules
# 
# The decision tree distinguishes:
# - Hard totals
# - Soft totals
# - Dealer up-card ranges
# 
# This provides a rule-based benchmark strategy independent of simulation.

# In[6]:


# =============================
# BASIC STRATEGY
# =============================
def basic_strategy(player_hand, dealer_up):
    total = hand_value(player_hand)
    dealer_value = dealer_up["value"]

    soft = is_soft(player_hand)

    # Immediate checks
    if total > 21:
        return "BUST! You have over 21"
    if total == 21:
        return "Congrats, you got 21!"

    if soft:

        # Soft 20 (A,9)
        if total == 20:
            return f"Stand soft 20 vs {dealer_value}"

        # Soft 19 (A,8)
        elif total == 19:
            return f"Stand soft 19 vs {dealer_value}"

        # Soft 18 (A,7)
        elif total == 18:
            if dealer_value in [3, 4, 5, 6, 9, 10, 11]:
                return f"Hit soft 18 vs {dealer_value}"
            return f"Stand soft 18 vs {dealer_value}"

        # Soft 17 (A,6)
        elif total == 17:
            return f"Hit soft 17 vs {dealer_value}"

        # Soft 16 (A,5)
        elif total == 16:
            return f"Hit soft 16 vs {dealer_value}"

        # Soft 15 (A,4)
        elif total == 15:
            return f"Hit soft 15 vs {dealer_value}"

        # Soft 14 (A,3)
        elif total == 14:
            return f"Hit soft 14 vs {dealer_value}"

        # Soft 13 (A,2)
        elif total == 13:
            return f"Hit soft 13 vs {dealer_value}"

        # Soft 12 (A,A adjusted to 12)
        elif total == 12:
            return f"Hit soft 12 vs {dealer_value}"
    else:
        # Hard hand logic
        if total >= 17:
            return f"Stand {total} vs {dealer_value}"
        if total <= 11:
            return f"Hit {total} vs {dealer_value}"
        if total in [13,14,15,16]:
            if dealer_value in [2,3,4,5,6]:
                return f"Stand {total} vs {dealer_value}"
            return f"Hit {total} vs {dealer_value}"
        if total == 12:
            if dealer_value in [4,5,6]:
                return f"Stand 12 vs {dealer_value}"
            return f"Hit 12 vs {dealer_value}"

    return "Evaluate"


# ## Monte Carlo Simulation Engine
# 
# To complement deterministic strategy rules, this simulator performs
# forward probability estimation using Monte Carlo sampling.
# 
# For each decision (Hit vs Stand):
# - 500 simulated game continuations are generated
# - Dealer behavior is modeled according to rules
# - Win and bust probabilities are recorded
# 
# This provides short-term probabilistic outcome estimates
# based on the current shoe composition.
# 
# The simulation engine introduces stochastic modeling into the system,
# bridging theoretical strategy and empirical outcome estimation.

# In[7]:


# =============================
# MONTE CARLO HIT VS STAND
# =============================
@st.cache_data(show_spinner=False)
def monte_carlo_hit_stand(player, dealer_up, sims=500):
    stand_wins = 0
    stand_busts = 0
    hit_wins = 0
    hit_busts = 0

    for _ in range(sims):
        shoe_copy = st.session_state.shoe.copy()
        random.shuffle(shoe_copy)

        # STAND
        p_stand = player.copy()
        d = [dealer_up, shoe_copy.pop()]
        while hand_value(d) < 17:
            d.append(shoe_copy.pop())
        if hand_value(p_stand) > 21:
            stand_busts += 1
        elif hand_value(d) > 21 or hand_value(p_stand) > hand_value(d):
            stand_wins += 1

        # HIT
        p_hit = player.copy()
        p_hit.append(shoe_copy.pop())
        if hand_value(p_hit) > 21:
            hit_busts += 1
        else:
            d = [dealer_up, shoe_copy.pop()]
            while hand_value(d) < 17:
                d.append(shoe_copy.pop())
            if hand_value(d) > 21 or hand_value(p_hit) > hand_value(d):
                hit_wins += 1

    return {
        "stand_win_pct": stand_wins / sims,
        "stand_bust_pct": stand_busts / sims,
        "hit_win_pct": hit_wins / sims,
        "hit_bust_pct": hit_busts / sims
    }


# ## Capital Allocation & Kelly Optimization
# 
# This section applies the Kelly Criterion to determine optimal wager sizing.
# 
# Estimated edge is derived from True Count:
# Edge ≈ (True Count - 1) × 0.5%
# 
# The Kelly formula allocates capital proportionally to expected advantage:
# 
# Optimal Bet = Bankroll × Edge
# 
# To control variance and drawdown risk, wagers are capped at 25% of bankroll.
# 
# This models rational capital growth under positive expected value conditions.

# In[8]:


# =============================
# NEW HAND LOGIC
# =============================
def check_natural_blackjack():
    pv = hand_value(st.session_state.player)
    dv = hand_value(st.session_state.dealer)

    player_blackjack = len(st.session_state.player) == 2 and pv == 21
    dealer_blackjack = len(st.session_state.dealer) == 2 and dv == 21

    if player_blackjack and not dealer_blackjack:
        st.session_state.bankroll += st.session_state.current_bet * 1.5
        st.session_state.message = "BLACKJACK! You win"
        st.session_state.wins += 1
        st.session_state.done = True
        st.session_state.evaluated = True
    elif player_blackjack and dealer_blackjack:
        st.session_state.message = "PUSH with natural blackjack"
        st.session_state.done = True
        st.session_state.evaluated = True
    elif dealer_blackjack:
        st.session_state.bankroll -= st.session_state.current_bet
        st.session_state.message = "Dealer has blackjack! You lose"
        st.session_state.done = True
        st.session_state.evaluated = True

def new_hand():
    st.session_state.player = [deal_card(), deal_card()]
    st.session_state.dealer = [deal_card(), deal_card()]
    st.session_state.done = False
    st.session_state.message = ""
    st.session_state.evaluated = False

    # Compute Kelly bet
    edge = max(0, (true_count() - 1) * 0.005)
    st.session_state.bet = round(kelly_bet(st.session_state.bankroll, edge), 2)

    # LOCK THE WAGER FOR THIS HAND
    st.session_state.current_bet = st.session_state.bet

    check_natural_blackjack()

if len(st.session_state.player) == 0:
    new_hand()


# ## Hand Evaluation Engine
# 
# This module evaluates blackjack hand totals and determines whether a hand is “soft” or “hard.”
# 
# Aces are dynamically valued as 11 unless doing so would cause a bust, 
# in which case they are converted to 1.
# 
# The function returns:
# - Hand total
# - Soft-hand indicator (True/False)
# 
# This distinction is essential for:
# - Correct basic strategy decisions
# - Proper dealer behavior (soft 17 logic)
# - Accurate Monte Carlo simulation outcomes

# In[9]:


# =============================
# EVALUATE HAND
# =============================
def evaluate_hand():
    if st.session_state.evaluated:
        return

    pv = hand_value(st.session_state.player)
    dv = hand_value(st.session_state.dealer)

    st.session_state.hands += 1

    player_blackjack = len(st.session_state.player)==2 and pv==21
    dealer_blackjack = len(st.session_state.dealer)==2 and dv==21

    if player_blackjack and not dealer_blackjack:
        st.session_state.bankroll += st.session_state.current_bet * 1.5
        st.session_state.message = "BLACKJACK! You win"
        st.session_state.wins += 1
    elif pv > 21:
        st.session_state.bankroll -= st.session_state.current_bet
        st.session_state.message = "BUST! Dealer wins"
    elif dv > 21 or pv > dv:
        st.session_state.bankroll += st.session_state.current_bet
        st.session_state.message = "YOU WIN"
        st.session_state.wins += 1
    elif pv < dv:
        st.session_state.bankroll -= st.session_state.current_bet
        st.session_state.message = "DEALER WINS"
    else:
        st.session_state.message = "PUSH"

    st.session_state.evaluated = True


# In[10]:


# =============================
# RENDER CARD
# =============================
def render_card(card):
    color_class = "red" if card["suit"] in ["♥","♦"] else "black"
    return f"<span class='big-card {color_class}'>{card['rank']}{card['suit']}</span>"


# ## Game Flow & Bankroll Management
# 
# This module controls round progression and capital updates.
# 
# It manages:
# - Initial deal
# - Player actions
# - Dealer resolution
# - Outcome evaluation
# - Bankroll adjustment
# 
# Session state ensures continuity across UI reruns,
# allowing persistent simulation tracking within Streamlit’s reactive framework.
# 
# Performance metrics tracked:
# - Total hands played
# - Wins / losses
# - Win rate
# - Bankroll delta

# ## AI Decision Interface
# 
# The advisor integrates two decision systems:
# 
# 1. Rule-Based Basic Strategy
# 2. Monte Carlo Probability Estimation
# 
# Basic Strategy provides long-term mathematically optimal play.
# Monte Carlo estimates short-term outcome probabilities 
# based on current deck conditions.
# 
# Displaying both allows users to compare theoretical and empirical guidance.

# In[12]:


# =============================
# LAYOUT
# =============================
left, right = st.columns([2,1])

with left:
    st.subheader("Dealer")
    if st.session_state.done:
        st.markdown(" ".join([render_card(c) for c in st.session_state.dealer]), unsafe_allow_html=True)
        st.write("Value:", hand_value(st.session_state.dealer))
    else:
        dealer_up = st.session_state.dealer[0]
        st.markdown(f"{render_card(dealer_up)} ?", unsafe_allow_html=True)

    st.divider()

    st.subheader("Player")
    st.markdown(" ".join([render_card(c) for c in st.session_state.player]), unsafe_allow_html=True)
    st.write("Value:", hand_value(st.session_state.player))

    st.divider()

    if not st.session_state.done:
        c1, c2 = st.columns(2)
        if c1.button("HIT", use_container_width=True):
            st.session_state.player.append(deal_card())
            if hand_value(st.session_state.player) > 21:
                st.session_state.done = True
                evaluate_hand()
            st.rerun()

        if c2.button("STAND", use_container_width=True):
            st.session_state.done = True
            while hand_value(st.session_state.dealer) < 17:
                st.session_state.dealer.append(deal_card())
            evaluate_hand()
            st.rerun()
    else:
        if st.session_state.message in ["YOU WIN", "BLACKJACK! You win"]:
            result_class = "win"
        elif st.session_state.message in ["DEALER WINS", "BUST! Dealer wins", "Dealer has blackjack! You lose"]:
            result_class = "lose"
        else:
            result_class = "push"

        st.markdown(f"<h2 class='{result_class}'>{st.session_state.message}</h2>",unsafe_allow_html=True)
        if st.button("NEW HAND", use_container_width=True):
            new_hand()
            st.rerun()

with right:

    st.markdown("### Session Metrics")

    running = st.session_state.running_count
    tc = round(true_count(), 2)
    edge = max(0, (tc - 1) * 0.005)
    kelly = round(kelly_bet(st.session_state.bankroll, edge), 2)
    st.session_state.current_bet = kelly

    win_rate = (
        (st.session_state.wins / st.session_state.hands) * 100
        if st.session_state.hands > 0 else 0
    )

    starting_bankroll = 10000  # starting bankroll
    bankroll_delta = st.session_state.bankroll - starting_bankroll

    if "prev_running" not in st.session_state:
        st.session_state.prev_running = running
    if "prev_true" not in st.session_state:
        st.session_state.prev_true = tc

    running_delta = running - st.session_state.prev_running
    tc_delta = tc - st.session_state.prev_true

    col1, col2, col3 = st.columns(3)

    with col1:
        bankroll_delta = st.session_state.bankroll - starting_bankroll

        st.metric(
            "Bankroll",
            f"${st.session_state.bankroll:,.0f}",
            delta=int(round(bankroll_delta, 0)) if bankroll_delta != 0 else None,
            delta_color="normal" 
    )


    with col2:
        st.metric(
            "Hi-Lo Count",
            running,
            delta=f"{running_delta:+}" if running_delta != 0 else None,
            delta_color="normal"
    )

    with col3:
        st.metric(
            "True Count",
            f"{tc:.2f}",
            delta=f"{tc_delta:+.2f}" if tc_delta != 0 else None,
            delta_color="normal"
    )

    st.session_state.prev_running = running
    st.session_state.prev_true = tc

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric("Amount Wagered", f"${kelly:,.0f}")

    with col5:
        st.metric("Hands Played", st.session_state.hands)

    with col6:
        st.metric("Win Rate", f"{win_rate:.1f}%")

    st.divider()

    # -------------------------------
    # AI ADVISOR
    # -------------------------------
    st.subheader("Advisor")

    dealer_up = st.session_state.dealer[0]
    strategy = basic_strategy(st.session_state.player, dealer_up)
    probs = monte_carlo_hit_stand(st.session_state.player, dealer_up)

    st.write("Basic Strategy:", strategy)
    st.write(f"Stand - Win: {probs['stand_win_pct']*100:.1f}%, Bust: {probs['stand_bust_pct']*100:.1f}%")
    st.write(f"Hit   - Win: {probs['hit_win_pct']*100:.1f}%, Bust: {probs['hit_bust_pct']*100:.1f}%")

