"""Run Wordle."""

import itertools as itt
import math
import random
from collections import Counter
from functools import lru_cache
from typing import Any, Literal, Mapping, Optional, Sequence, Type

from class_resolver import Hint, Resolver
from english_words import english_words_alpha_set
from tabulate import tabulate
from tqdm import tqdm

Call = Literal["correct", "somewhere", "incorrect"]

CALLS: Mapping[Call, str] = {
    "correct": "🟩",
    "somewhere": "🟨",
    "incorrect": "⬛",
}


@lru_cache
def _get_words(length: int) -> set[str]:
    return {word.lower() for word in english_words_alpha_set if length == len(word)}


class Configuration:
    """Represents the configuration of a Wordle game."""

    def __init__(self, length: int = 5, height: int = 6):
        """Instantiate the configuration.

        :param length: The length of the words. The canonical game uses 5.
        :param height: The number of guesses. The canonical game uses 6.
        """
        self.length = length
        self.height = height
        self.allowed = _get_words(self.length)
        self.allowed_tuple = tuple(self.allowed)

    def choice(self) -> str:
        """Randomly choose a word."""
        return random.choice(self.allowed_tuple)  # noqa:S311

    def combinations(self, n: int, use_tqdm: bool = False):
        """Iterate over combinations of allowed words."""
        it = itt.combinations(self.allowed, n)
        if use_tqdm:
            it = tqdm(it, total=math.comb(len(self.allowed), n), unit="comb", unit_scale=True)
        yield from it

    @staticmethod
    def success(counter) -> float:
        """Calculate the percentage of words that were solved."""
        successes = sum(value for key, value in counter.items() if isinstance(key, int))
        total = sum(counter.values())
        return successes / total

    def quality(self, counter) -> float:
        """Calculate a quality score for successes."""
        # worst case is it takes self.length for each, so len(self.allowed) * len(self.height)
        numerator = sum(key * value for key, value in counter.items() if isinstance(key, int))
        denominator = sum(
            self.height * value for key, value in counter.items() if isinstance(key, int)
        )
        return numerator / denominator


class Game:
    """Represents a game of Wordle."""

    configuration: Configuration
    word: str
    guesses: list[str]
    calls: list[Sequence[Call]]

    def __init__(self, configuration: Configuration, word: Optional[str] = None):
        """Instantiate the game.

        :param configuration: The configuration (length, height, allowed words)
        :param word: The secret word
        """
        self.configuration = configuration
        self.word = word or self.configuration.choice()
        self.guesses = []
        self.calls = []

    def state(self) -> Optional[bool]:
        """Return the state of the game -> true=win, false=lose, None=still playing."""
        if len(self.guesses) > self.configuration.height:
            return False
        elif 0 < len(self.guesses) and self.guesses[-1] == self.word:
            return True
        return None

    def append_guess(self, word: str):
        """Make a guess."""
        if self.configuration.length != len(word):
            raise ValueError(f"Word wrong length: {word} (should be {self.configuration.length}")
        if word not in self.configuration.allowed:
            raise KeyError(f"Word not found: {word}")
        self.guesses.append(word)
        self.calls.append(
            tuple(
                self._call(actual_character, given_character)
                for actual_character, given_character in zip(self.word, word)
            )
        )

    def _call(self, actual_character: str, given_character: str) -> Call:
        if actual_character == given_character:
            return "correct"
        elif given_character in self.word:
            return "somewhere"
        else:
            return "incorrect"

    def print(self) -> None:
        """Print the game to the console."""
        for guess, call in zip(self.guesses, self.calls):
            print("".join(map(CALLS.__getitem__, call)), guess)

    def play(self, player, verbose: bool = False):
        """Play a full game."""
        if verbose:
            print("Word is", self.word)
        while self.state() is None:
            if verbose:
                print("\nplaying round", 1 + len(self.guesses))
            guess = player.guess(guesses=self.guesses, calls=self.calls)
            self.append_guess(guess)
            if verbose:
                self.print()


class Player:
    """An abstract class for a player."""

    def __init__(self, *, configuration: Configuration, **kwargs):
        """Instantiate the game.

        :param configuration: The configuration (length, height, allowed words)
        """
        self.configuration = configuration

    def guess(self, guesses: list[str], calls: list[Sequence[Call]]) -> str:
        """Return the next row to play."""
        raise NotImplementedError


class RandomPlayer(Player):
    """A player that always makes a random valid guess."""

    def guess(self, guesses: list[str], calls: list[Sequence[Call]]) -> str:
        """Guess a random valid word."""
        return self.configuration.choice()


class InitialGuesser(Player):
    """A player that starts with a given sequence of initial guesses."""

    initial: Sequence[str]

    def __init__(self, *, configuration: Configuration, initial: Sequence[str]):  # noqa:D107
        super().__init__(configuration=configuration)
        for guess in initial:
            if len(guess) != self.configuration.length:
                raise ValueError(f"Initial {guess=} is not {self.configuration.length=}")
        self.initial = initial
        self.n = 0

    def guess(self, guesses: list[str], calls: list[Sequence[Call]]) -> str:
        """Guess the initial guesses, then defer to :func:`guess_late_game`."""
        if self.n < len(self.initial):
            guess = self.initial[self.n]
            self.n += 1
            return guess
        else:
            return self.guess_late_game(guesses, calls)

    def guess_late_game(self, guesses: list[str], calls: list[Sequence[Call]]) -> str:
        """Guess after the initial guesses."""
        raise NotImplementedError


class GreedyInitialGuesser(InitialGuesser):
    """Guess the initial guesses then use process of elimitation to make new guesses."""

    def guess_late_game(self, guesses: list[str], calls: list[Sequence[Call]]) -> str:
        """Guess the first word that matches the constraints given by all past guesses."""
        constraints = {}
        appears = set()
        no_appears = set()
        for call, guess in zip(calls, guesses):
            for i, c, x in zip(itt.count(), call, guess):
                if c == "correct":
                    constraints[i] = x
                elif c == "somewhere":
                    appears.add(x)
                elif c == "incorrect":
                    no_appears.add(x)
        for word in self.configuration.allowed:
            if (
                word not in guesses
                and all(word[i] == x for i, x in constraints.items())
                and all(char in word for char in appears)
                and all(char not in word for char in no_appears)
            ):
                return word
        raise ValueError("could not make a guess")


player_resolver = Resolver.from_subclasses(base=Player, skip={InitialGuesser})


class Controller:
    """A controller for running the game."""

    configuration: Configuration
    game: Game
    player_cls: Type[Player]
    player_kwargs: dict[str, Any]

    def __init__(
        self,
        player_cls: Hint[Player],
        player_kwargs: Optional[dict[str, Any]] = None,
        configuration: Optional[Configuration] = None,
    ):
        """Instantiate a contoller.

        :param player_cls: A player class. Will be instantiated automatically.
        :param configuration: A configuration. If not given, uses default configuration
            of length=5, height=6.
        """
        self.configuration = Configuration() if configuration is None else configuration
        self.player_cls = player_resolver.lookup(player_cls)
        self.player_kwargs = player_kwargs or {}

    def play(self, word: Optional[str] = None, verbose: bool = False) -> Game:
        """Play a full game."""
        game = Game(configuration=self.configuration, word=word)
        player = player_resolver.make(
            self.player_cls, self.player_kwargs, configuration=self.configuration
        )
        game.play(player, verbose=verbose)
        return game

    def play_all(self):
        """Play a game on all words."""
        counter = Counter()
        it = tqdm(sorted(self.configuration.allowed), leave=False)
        for word in it:
            it.set_postfix(word=word)
            game = self.play(word)
            if game.state():
                counter[len(game.guesses)] += 1
            else:
                counter["Failure"] += 1
        return counter


def main(length: int = 5, height: int = 6):
    """Run the controller."""
    configuration = Configuration(length=length, height=height)
    players: list[tuple[str, dict[str, Any]]] = [
        ("Random", {}),
        ("GreedyInitialGuesser", {"initial": ["snake", "batch", "chart"]}),
        ("GreedyInitialGuesser", {"initial": ["handy", "crime", "lotus"]}),
        ("GreedyInitialGuesser", {"initial": ["lunch", "metro", "daisy"]}),
    ]
    rows = []
    for player_cls, player_kwargs in players:
        controller = Controller(
            player_cls=player_cls, player_kwargs=player_kwargs, configuration=configuration
        )
        counter = controller.play_all()
        rows.append(
            (
                player_cls,
                player_kwargs,
                configuration.success(counter),
                configuration.quality(counter),
            )
        )
    print(tabulate(rows, headers=["cls", "kwargs", "success", "quality"], tablefmt="github"))


if __name__ == "__main__":
    main()
