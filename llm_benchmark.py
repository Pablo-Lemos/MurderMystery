"""
Benchmark script to evaluate LLM performance on the murder mystery game.

Runs the game multiple times across different player counts and tracks success rates.
"""

import argparse
from tqdm import tqdm
from murdermystery import MurderMystery
from llm_player import LLMPlayer


def run_benchmark(
    model: str = "ollama:llama3.1:8b",
    num_seeds: int = 100,
    player_counts: list = None,
    noise_level: float = 0.1,
    frac_accomplices: float = 0.2,
    max_choices: int = 100,
    verbosity: int = 0,
):
    """
    Run benchmark across different player counts.

    Args:
        model: The LLM model to use (e.g., "ollama:llama3.1:8b")
        num_seeds: Number of games to run per player count
        player_counts: List of player counts to test (default: [3, 5, 7, 10])
        noise_level: Noise level for the game (0 to 0.25)
        frac_accomplices: Fraction of accomplices (0 to 1)
        max_choices: Maximum number of choices before forced accusation
        verbosity: Output verbosity (0=minimal, 1=show choices, 2=full)

    Returns:
        dict: Results mapping player_count -> success_rate
    """
    if player_counts is None:
        player_counts = [3, 5, 7, 10]

    results = {}

    print("=" * 60)
    print("LLM MURDER MYSTERY BENCHMARK")
    print("=" * 60)
    print(f"Model: {model}")
    print(f"Seeds per config: {num_seeds}")
    print(f"Noise level: {noise_level}")
    print(f"Accomplice fraction: {frac_accomplices}")
    print(f"Max choices: {max_choices}")
    print("=" * 60)

    for num_players in player_counts:
        wins = 0
        errors = 0

        pbar = tqdm(
            range(num_seeds),
            desc=f"{num_players} players",
            unit="game",
            leave=True,
        )

        for seed in pbar:
            try:
                # Create fresh LLM player for each game (reset conversation)
                llm = LLMPlayer(model=model)

                game = MurderMystery(
                    num_players=num_players,
                    noise_level=noise_level,
                    frac_accomplices=frac_accomplices,
                    max_choices=max_choices,
                    seed=seed,
                    llm_player=llm,
                    verbosity=verbosity,
                )

                won = game.play_game()
                if won:
                    wins += 1

                # Update progress bar with current win rate
                current_rate = wins / (seed + 1)
                pbar.set_postfix({"wins": wins, "rate": f"{current_rate:.1%}"})

            except Exception as e:
                errors += 1
                if verbosity >= 1:
                    tqdm.write(f"  Error in seed {seed}: {e}")

        valid_games = num_seeds - errors
        success_rate = wins / valid_games if valid_games > 0 else 0
        results[num_players] = {
            "wins": wins,
            "total": valid_games,
            "errors": errors,
            "success_rate": success_rate,
        }

        if errors > 0:
            tqdm.write(f"  Errors: {errors}")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(
        f"{'Players':<10} {'Wins':<10} {'Total':<10} {'Success Rate':<15} {'Random Baseline':<15}"
    )
    print("-" * 60)
    for num_players, data in results.items():
        baseline = 1 / num_players  # Random guessing baseline
        print(
            f"{num_players:<10} {data['wins']:<10} {data['total']:<10} {data['success_rate']:<15.1%} {baseline:<15.1%}"
        )
    print("=" * 60)

    return results


def main():
    parser = argparse.ArgumentParser(description="Benchmark LLM on murder mystery game")
    parser.add_argument(
        "--model",
        type=str,
        default="ollama:llama3.1:8b",
        help="LLM model to use (default: ollama:llama3.1:8b)",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        default=100,
        help="Number of games per player count (default: 100)",
    )
    parser.add_argument(
        "--players",
        type=str,
        default="3,5,7,10",
        help="Comma-separated list of player counts to test (default: 3,5,7,10)",
    )
    parser.add_argument(
        "--noise", type=float, default=0.1, help="Noise level 0-0.25 (default: 0.1)"
    )
    parser.add_argument(
        "--accomplices",
        type=float,
        default=0.2,
        help="Fraction of accomplices 0-1 (default: 0.2)",
    )
    parser.add_argument(
        "--max-choices",
        type=int,
        default=100,
        help="Maximum choices before forced accusation (default: 100)",
    )
    parser.add_argument(
        "--verbosity",
        type=int,
        default=0,
        choices=[0, 1, 2],
        help="Output verbosity: 0=minimal, 1=show choices, 2=full (default: 0)",
    )

    args = parser.parse_args()

    player_counts = [int(x.strip()) for x in args.players.split(",")]

    run_benchmark(
        model=args.model,
        num_seeds=args.seeds,
        player_counts=player_counts,
        noise_level=args.noise,
        frac_accomplices=args.accomplices,
        max_choices=args.max_choices,
        verbosity=args.verbosity,
    )


if __name__ == "__main__":
    main()
