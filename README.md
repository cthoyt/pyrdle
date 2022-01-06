# ruin-wordle

Wordle is fun, so let's ruin it with computers.

## How to Play

Install the requirements then run `play.py`. Will add packaging soon with a
vanity CLI.

## Metrics

This repository assesses two metrics about each algorithm:

1. Success: how many of the words of the given length and number of guesses can
   it successfully solve?
2. Speed: what's the average number of guesses needed over all successful words?

Later, this repository will run multiple trials in order to assign confidence
intervals for success and quality for randomized algorithms.

## Strategies

This repository is a playground for implementing new solve strategies. Feel
free to send a PR with your own (just subclass the `Player` class)!

Terminology:

1. **Perfect guess**: a guess that uses all previous information available,
   including knowledge about correct positions, unused letters, and used letters

### Three word initial guess

This strategy involves deterministically guessing three words that cover a wide
variety of vowels and consonants. For example, (lunch, metro, daisy) covers all
five vowels and 10 different consonants.

It's pretty likely that with these choices, you will be able to
deterministically solve for the word after one more perfect guess. It turns out
that with this example, you can solve 96.9% of the time with an average of 4.27
guesses. That's pretty surprising, but also assumes you have computer-like
recall of words.


## Warnings

- This code uses https://pypi.org/project/english-words/. This has some weird stuff missing from it.

## See also

- https://github.com/coolbutuseless/wordle
