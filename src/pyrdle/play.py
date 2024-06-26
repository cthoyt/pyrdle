"""Interactively play wordle."""

import click
from rich.console import Console

from .wordle import CALL_COLORS, Configuration, Game, get_constraints, valid_under_constraints


@click.command()
@click.option("--language", type=click.Choice(["en", "de"]), default="en", show_default=True)
@click.option("--length", type=int, default=5, show_default=True, help="Number of letters per word")
@click.option("--height", type=int, default=6, show_default=True, help="Maximum number of guesses")
def main(language: str, length: int, height: int):
    """Interactively play wordle."""
    console = Console()

    configuration = Configuration(
        language=language,
        height=height,
        length=length,
    )

    # Play with a random word
    game = Game(configuration=configuration)
    while game.state() is None:
        # for _ in range(len(game.calls)):
        #     sys.stdout.write("\033[F") # up one line
        #     sys.stdout.write("\033[K") # clear line
        console.clear()
        print_game(console, game)

        guess = input("Guess: ")
        if guess == "help":
            positions, appears, no_appears = get_constraints(game.guesses, game.calls)
            valid = sorted(
                word
                for word in configuration.words
                if valid_under_constraints(word, positions, appears, no_appears)
            )
            print(",".join(valid))

        while len(guess) != game.configuration.length or guess not in game.configuration.words:
            guess = input("Guess: ")
        game.append_guess(guess)

    if game.state():
        console.clear()
        print_game(console, game)
        console.print("You won!")
    else:
        console.clear()
        print_game(console, game)
        console.print("       ", end="")
        console.print(game.word, style="on red")


def print_game(console: Console, game: Game) -> None:
    """Write a game to the console."""
    console.print(
        f"Wordle (lang: {game.configuration.language}, width: {game.configuration.length})",
        style="underline",
    )
    for call, guess in zip(game.calls, game.guesses):
        console.print("       ", end="")
        for c, g in zip(call, guess):
            console.print(g, style=f"on {CALL_COLORS[c]}", end="")
        console.print()


if __name__ == "__main__":
    main()
