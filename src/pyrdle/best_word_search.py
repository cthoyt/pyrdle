"""This script is supposed to help find the best word to start with."""

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from tqdm import tqdm

from .lang import Language
from .wordle import Configuration, Controller, GreedyInitialGuesser

HERE = Path(__file__).parent.resolve()
ROOT = HERE.parent.parent.resolve()
RESULTS = ROOT.joinpath("results")


def main(
    k: int = 2,
    n: Optional[int] = 3000,
    length: int = 5,
    height: int = 6,
    language: Optional[str] = None,
):
    """Run the best word search."""
    lang = Language(length=length, language=language)
    configuration = Configuration(length=length, height=height)

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
        lang.get_top_words(k=k, n=n),
        unit_scale=True,
        unit=unit,
        desc=f"{k=},{n=},{length=},{height=}",
    )
    for words, score in it:
        it.set_postfix(words=",".join(words), score=score)
        controller = Controller(
            player_cls=GreedyInitialGuesser,
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
        stem = RESULTS.joinpath(f"k_{k}_l_{length}_h_{height}_lang_{lang.language}")
    else:
        stem = RESULTS.joinpath(f"k_{k}_n_{n}_l_{length}_h_{height}_lang_{lang.language}")

    path = stem.with_suffix(".tsv")
    df = pd.DataFrame(rows, columns=columns)
    df.to_csv(path, sep="\t", index=False)

    img_path = stem.with_suffix(".png")
    sns.scatterplot(data=df, x="score", y="success")
    plt.savefig(img_path, dpi=300)


if __name__ == "__main__":
    main()
