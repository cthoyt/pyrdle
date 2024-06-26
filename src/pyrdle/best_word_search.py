"""This script is supposed to help find the best word to start with."""

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from tqdm import tqdm

from .wordle import (
    CachedGreedyInitialGuesser,
    Configuration,
    Controller,
)

HERE = Path(__file__).parent.resolve()
ROOT = HERE.parent.parent.resolve()
RESULTS = ROOT.joinpath("results")


def main(
    k: int = 1,
    n: Optional[int] = None,
    length: Optional[int] = None,
    height: Optional[int] = None,
    language: Optional[str] = None,
):
    """Run the best word search."""
    configuration = Configuration(length=length, height=height, language=language)

    rows = []
    columns = [f"word{i}" for i in range(k)]
    columns.extend(("score", "success", "speed"))

    if k == 1:
        unit = "word"
    elif k == 2:
        unit = "pair"
    elif k == 3:
        unit = "triple"
    else:
        unit = f"{k}-tuple"

    it = tqdm(
        configuration.get_top_words(k=k, n=n),
        unit_scale=True,
        unit=unit,
        desc=f"{k=},{n=},l-{configuration.length},h={configuration.height}",
    )
    for words, score in it:
        it.set_postfix(words=",".join(words), score=score)
        controller = Controller(
            player_cls=CachedGreedyInitialGuesser,
            player_kwargs={"initial": words},
            configuration=configuration,
        )
        counter = controller.play_all()
        rows.append(
            (
                *words,
                score,
                configuration.success(counter),
                configuration.speed(counter),
            )
        )

    if n is None:
        stem_str = (
            f"k_{k}_l_{configuration.length}_h_{configuration.height}_lang_{configuration.language}"
        )
    else:
        stem_str = f"k_{k}_n_{n}_l_{configuration.length}_h_{configuration.height}_lang_{configuration.language}"

    stem = RESULTS.joinpath(stem_str)
    path = stem.with_suffix(".tsv")
    df = pd.DataFrame(rows, columns=columns)
    df.to_csv(path, sep="\t", index=False)
    print(f"Writing results to {path}")

    img_path = stem.with_suffix(".png")
    sns.scatterplot(data=df, x="score", y="success", alpha=0.3)
    plt.savefig(img_path, dpi=300)


if __name__ == "__main__":
    main()
