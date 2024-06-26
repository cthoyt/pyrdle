from pyrdle.wordle import (
    CachedGreedyInitialGuesser,
    Configuration,
    Game,
    GreedyInitialGuesser,
    MaxEntropyInitialGuesser,
)


def main(word="raise"):
    """Run the controller."""
    configuration = Configuration()

    # Demo of given word
    game = Game(configuration=configuration, word=word)
    player = GreedyInitialGuesser(configuration=configuration, initial=["handy", "crime", "lotus"])
    game.play(player)
    print(player)
    game.print()

    game = Game(configuration=configuration, word=word)
    cached_player = CachedGreedyInitialGuesser(
        configuration=configuration, initial=["handy", "crime", "lotus"]
    )
    game.play(cached_player)
    print(cached_player)
    game.print()

    game = Game(configuration=configuration, word=word)
    me_player = MaxEntropyInitialGuesser(
        configuration=configuration, initial=["handy", "crime", "lotus"]
    )
    game.play(me_player)
    print(me_player)
    game.print()


if __name__ == "__main__":
    main()
