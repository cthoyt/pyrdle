import random
from functools import lru_cache
from typing import Literal, Optional, Type

from english_words import english_words_set


@lru_cache
def _get_words(length: int) -> set[str]:
    return {
        word for word in english_words_set if length == len(word)
    }


Call = Literal["correct", "somewhere", "incorrect"]


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
        return random.choice(self.allowed_tuple)


class Game:
    def __init__(self, configuration: Configuration, word: Optional[str] = None):
        self.configuration = configuration
        self.word = word or self.configuration.choice()
        self.guesses = []
        self.calls = []

    def lost(self):
        return len(self.guesses) > self.configuration.height

    def won(self):
        return self.guesses and self.guesses[-1] == self.word

    def append_guess(self, word: str) -> Optional[list[Call]]:
        if self.configuration.length != len(word):
            raise ValueError(f"Word wrong length: {word} (should be {self.configuration.length}")
        if word not in self.configuration.allowed:
            raise KeyError(f"Word not allowed: {word}")
        self.guesses.append(word)
        calls = [
            self.call(actual_character, given_character)
            for actual_character, given_character in zip(self.word, word)
        ]
        self.calls.append(calls)
        return calls

    def call(self, actual_character: str, given_character: str) -> Call:
        if actual_character == given_character:
            return "correct"
        elif given_character in self.word:
            return "somewhere"
        else:
            return "incorrect"

    def print(self):
        for call in self.calls:
            print("".join(map(d.__getitem__, call)))


d = {
    "correct": "🟩",
    "somewhere": "🟨",
    "incorrect": "⬛",
}


class Player:
    def __init__(self, configuration: Configuration):
        self.configuration = configuration

    def guess(self, calls: list[Call]) -> str:
        """Return the next row to play."""
        raise NotImplementedError


class RandomPlayer(Player):
    def guess(self, calls: list[Call]) -> str:
        return self.configuration.choice()


class HandyCrimeLotusPlayer(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.n = 0

class Controller:
    configuration: Configuration
    game: Game
    player: Player

    def __init__(self, player: Type[Player], configuration: Optional[Configuration] = None, word: Optional[str] = None):
        self.configuration = configuration or Configuration()
        self.game = Game(configuration)
        self.player = player(configuration)

    def play(self) -> bool:
        """"""
        x = 1
        while not self.game.won() and not self.game.lost():
            print("playing round", x)
            x += 1
            guess = self.player.guess(self.game.guesses)
            self.game.append_guess(guess)
            self.game.print()
            print()
        return self.game.won()


def main(length: int = 5, height: int = 6):
    configuration = Configuration(length=length, height=height)
    controller = Controller(player=RandomPlayer, configuration=configuration)
    controller.play()


if __name__ == '__main__':
    main()
