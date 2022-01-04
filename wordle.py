"""Run Wordle."""

import random
from functools import lru_cache
from itertools import count
from typing import ClassVar, Literal, Mapping, Optional, Sequence, Type

from english_words import english_words_set

Call = Literal["correct", "somewhere", "incorrect"]

CALLS: Mapping[Call, str] = {
    "correct": "🟩",
    "somewhere": "🟨",
    "incorrect": "⬛",
}


@lru_cache
def _get_words(length: int) -> set[str]:
    return {word for word in english_words_set if length == len(word)}


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

    def lost(self) -> bool:
        """Return if the game was lost."""
        return len(self.guesses) > self.configuration.height

    def won(self) -> bool:
        """Return if the game was won."""
        return 0 < len(self.guesses) and self.guesses[-1] == self.word

    def append_guess(self, word: str):
        """Make a guess."""
        if self.configuration.length != len(word):
            raise ValueError(f"Word wrong length: {word} (should be {self.configuration.length}")
        if word not in self.configuration.allowed:
            raise KeyError(f"Word not allowed: {word}")
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


class Player:
    """An abstract class for a player."""

    def __init__(self, configuration: Configuration):
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

    initial: ClassVar[Sequence[str]]

    def __init__(self, *args, **kwargs):  # noqa:D107
        super().__init__(*args, **kwargs)
        for guess in self.initial:
            if len(guess) != self.configuration.length:
                raise ValueError(f"Initial {guess=} is not {self.configuration.length=}")
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

    initial = ["handy", "crime", "lotus"]

    def guess_late_game(self, guesses: list[str], calls: list[Sequence[Call]]) -> str:
        """Guess the first word that matches the constraints given by all past guesses."""
        constraints = {}
        appears = set()
        no_appears = set()
        for call, guess in zip(calls, guesses):
            for i, c, x in zip(count(), call, guess):
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


class Controller:
    """A controller for running the game."""

    configuration: Configuration
    game: Game
    player: Player

    def __init__(
        self,
        player: Type[Player],
        configuration: Optional[Configuration] = None,
        word: Optional[str] = None,
    ):
        """Instantiate a contoller.

        :param player: A player class. Will be instantiated automatically.
        :param configuration: A configuration. If not given, uses default configuration
            of length=5, height=6.
        :param word: The secret word
        """
        self.configuration = Configuration() if configuration is None else configuration
        self.game = Game(configuration=self.configuration, word=word)
        self.player = player(configuration=self.configuration)

    def play(self) -> bool:
        """Play a full game."""
        print("Word is", self.game.word)
        x = 1
        while not self.game.won() and not self.game.lost():
            print("playing round", x)
            x += 1
            guess = self.player.guess(guesses=self.game.guesses, calls=self.game.calls)
            self.game.append_guess(guess)
            self.game.print()
            print()
        return self.game.won()


def main(length: int = 5, height: int = 6):
    """Run the controller."""
    configuration = Configuration(length=length, height=height)
    controller = Controller(player=GreedyInitialGuesser, configuration=configuration)
    controller.play()


if __name__ == "__main__":
    main()
