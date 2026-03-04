# Blackjack Simulator: Probabilistic Decision Modeling & Bankroll Optimization

Author: Zachary Niccoli

Tools: Python, Streamlit

## Project Overview

This project is an interactive Blackjack simulation engine built in Python using Streamlit. It combines probability modeling, card counting, Monte Carlo simulation, and fractional Kelly Criterion betting to simulate intelligent decision-making under uncertainty.

The goal of the project was to explore:

- Risk-adjusted capital allocation

- Expected value optimization

- Simulation-based decision modeling

- Bankroll growth vs. volatility tradeoffs

Rather than building a simple card game, this project focuses on applying quantitative reasoning and optimization principles to a dynamic betting environment.

## Core Concepts Implemented
### Multi-Deck Blackjack Engine

- 6-deck shoe

- Proper shuffle and depletion logic

- Soft/hard hand detection

- Dealer rule logic (stand on 17)

- Natural blackjack (3:2 payout)

### Hi-Lo Card Counting System

- Running count tracking

- True count adjustment based on decks remaining

- Edge estimation based on count

### Monte Carlo Simulation

Each hand can be evaluated using simulation to estimate:

- Hit win probability

- Stand win probability

- Bust probability

This enables probabilistic decision comparisons rather than rule-based play alone.

### Fractional Kelly Criterion Betting (Quarter Kelly)

The betting strategy uses a simplified Quarter Kelly model:

f∗ = 2p − 1

Where:

- p = estimated win probability

- Fraction scaled to 25% to reduce volatility

This approach balances:

- Capital growth

- Risk control

- Volatility reduction

If no edge exists (p ≤ 0.5), the model recommends no bet.

## Tech Stack

- Python

- Streamlit

- Probability modeling

- Monte Carlo simulation

- Custom CSS styling for UI control

## Key Features

- Dynamic bankroll tracking

- AI betting recommendations

- Real-time win probability modeling

- Risk-adjusted bet sizing

- Clean casino-style UI (dark theme)

- Performance metrics:

  - Bankroll

  - Hi-Lo count

  - True count

  - Win rate

  - Hands played



# Demo blackjack-simulator-niccoli.streamlit.app

<img width="1920" height="1006" alt="Blackjack App 3" src="https://github.com/user-attachments/assets/a26c4910-e931-4b36-977c-eab72380f163" />
<img width="1920" height="1001" alt="Blackjack App 2" src="https://github.com/user-attachments/assets/9074b8cf-9383-4c24-b1b3-037dfc5e1cf1" />
<img width="1920" height="1004" alt="Blackjack App 1" src="https://github.com/user-attachments/assets/9086abda-3c6a-40cd-9a2d-61e661efbb88" />

