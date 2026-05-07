import random
from abc import ABC, abstractmethod

NAMES = [
    "Alice",
    "Bob",
    "Charlie",
    "David",
    "Eve",
    "Frank",
    "Grace",
    "Heidi",
    "Ivan",
    "Judy",
    "Karl",
    "Leo",
    "Mallory",
    "Nina",
    "Oscar",
    "Peggy",
    "Quentin",
    "Rupert",
    "Sybil",
    "Trent",
    "Uma",
    "Victor",
    "Walter",
    "Xavier",
    "Yvonne",
    "Zara",
]


class Player:
    def __init__(self, name, type, noise_level):
        assert type in [
            "Innocent",
            "Accomplice",
            "Guilty",
        ], "Type must be 'Innocent', 'Accomplice', or 'Guilty'"
        self._name = name
        self._type = type
        self._noise_level = noise_level

    def get_name(self):
        return self._name

    def get_type(self):
        return self._type

    def ask_about_player(self, other_player):
        print(f"{self._name} is asking about {other_player.get_name()}.")
        other_type = other_player.get_type()
        r = random.random()
        if self._type == "Innocent" and other_type in ["Innocent", "Accomplice"]:
            if r < self._noise_level:
                return "They are guilty."
            else:
                return "They are innocent."
        elif self._type == "Innocent" and other_type == "Guilty":
            if r < 1 - 2 * self._noise_level:
                return "They are guilty."
            else:
                return "They are innocent."
        elif self._type == "Guilty" and other_type == "Guilty":
            raise ValueError("There cannot be two guilty players")
        elif self._type in ["Accomplice", "Guilty"] and other_type == "Innocent":
            # The accomplice is more likely to blame the innocent player
            # if r < 2 * self._noise_level:
            if r < 1 - 2 * self._noise_level:
                return "They are guilty."
            else:
                return "They are innocent."
        elif self._type in ["Accomplice", "Guilty"] and other_type in [
            "Accomplice",
            "Guilty",
        ]:
            if r < self._noise_level:
                return "They are guilty."
            else:
                return "They are innocent."

    def check_alibi(self):
        r = random.random()
        if self._type == "Innocent":
            if r < self._noise_level:
                return "Alibi is weak"
            else:
                return "Alibi is solid"
        elif self._type == "Accomplice":
            if r < 2 * self._noise_level:
                return "Alibi is weak"
            else:
                return "Alibi is solid"
        elif self._type == "Guilty":
            if r < 1 - 2 * self._noise_level:
                return "Alibi is weak"
            else:
                return "Alibi is solid"

    def examine_evidence(self):
        r = random.random()
        if self._type == "Innocent":
            if r < self._noise_level:
                return "The evidence is incriminating."
            else:
                return "The evidence is NOT incriminating."
        elif self._type == "Accomplice":
            if r < 2 * self._noise_level:
                return "The evidence is incriminating."
            else:
                return "The evidence is NOT incriminating."
        elif self._type == "Guilty":
            if r < 1 - 2 * self._noise_level:
                return "The evidence is incriminating."
            else:
                return "The evidence is NOT incriminating."


class MurderMystery:
    def __init__(
        self,
        num_players,
        noise_level,
        num_accomplices=None,
        frac_accomplices=None,
        seed=None,
        memory_file=None,
    ):
        if seed is not None:
            random.seed(seed)
        assert num_players >= 3, "There must be at least 3 players"
        assert num_players <= len(
            NAMES
        ), f"There cannot be more than {len(NAMES)} players"
        assert 0 <= noise_level <= 0.25, "Noise level must be between 0 and 0.25"
        assert (num_accomplices is None) or (
            frac_accomplices is None
        ), "Only one of num_accomplices or frac_accomplices can be specified"
        if num_accomplices is not None:
            assert (
                0 <= num_accomplices <= num_players - 2
            ), "Number of accomplices must be between 0 and num_players - 2"
        if frac_accomplices is not None:
            assert (
                0 <= frac_accomplices <= 1
            ), "Fraction of accomplices must be between 0 and 1"
            num_accomplices = int(
                frac_accomplices * (num_players - 2)
            )  # Calculate number of accomplices based on fraction
        if num_accomplices is None and frac_accomplices is None:
            num_accomplices = 0  # Default to no accomplices if neither is specified
        if memory_file is not None:
            assert isinstance(memory_file, str), "Memory file must be a string"
            assert memory_file.endswith(".md"), "Memory file must be a markdown file"
            self._memory_file = memory_file
            self._has_memory_file = True
        else:
            self._has_memory_file = False

        self._players = []
        self._noise_level = noise_level
        types = (
            ["Innocent"] * (num_players - num_accomplices - 1)
            + ["Accomplice"] * num_accomplices
            + ["Guilty"]
        )
        random.shuffle(types)
        for i in range(num_players):
            self._players.append(Player(NAMES[i], types[i], noise_level))

        print("=" * 40)
        print(f"WHO IS THE MURDERER?")
        print("=" * 40)
        print(
            f"There has been a murder! You are a wise and smart detective, tasked with solving the case. There are {num_players} suspects: {', '.join([player.get_name() for player in self._players])}"
        )
        print(
            "You must use your deduction skills to identify the murderer. Do not forget, people lie, and even the evidence can be misleading!"
        )
        self._memory_human_readable = []
        self._memory_set = []
        self._choice_no = 0
        self._game_over = False

    def _make_choice(self):
        print("=" * 40)
        print("What would you like to do?")
        print("=" * 40)
        print("1. Ask a suspect about another")
        print("2. Check a suspect's alibi")
        print("3. Examine the evidence")
        print("4. Check your past choices")
        print("5. Accuse a suspect")
        print("6. Quit")

        print("=" * 40)
        choice = input("Choose your next action:")
        print("=" * 40)

        if choice == "1":
            print("Who would you like to question?")
            for i, player in enumerate(self._players):
                print(f"{i + 1}. {player.get_name()}")
            player_to_question = input("Select a player: ")
            print("Who would you like to ask about?")
            for i, player in enumerate(self._players):
                print(f"{i + 1}. {player.get_name()}")
            player_to_ask_about = input("Select a player: ")
            if [
                1,
                int(player_to_question) - 1,
                int(player_to_ask_about) - 1,
            ] in self._memory_set:
                print("You have already made that choice.")
                return
            elif player_to_question == player_to_ask_about:
                print("You cannot ask a player about themselves.")
                return
            else:
                self._choice_no += 1
                response = self._players[int(player_to_question) - 1].ask_about_player(
                    self._players[int(player_to_ask_about) - 1]
                )
                print(
                    f"{self._players[int(player_to_question) - 1].get_name()} says: {response}"
                )
                self._memory_human_readable.append(
                    f"Choice {self._choice_no}: Asked {self._players[int(player_to_question) - 1].get_name()} about {self._players[int(player_to_ask_about) - 1].get_name()} and got response: {response}"
                )
                self._memory_set.append(
                    [1, int(player_to_question) - 1, int(player_to_ask_about) - 1]
                )
                if self._has_memory_file:
                    with open(self._memory_file, "a") as f:
                        f.write(
                            f"Choice {self._choice_no}: Asked {self._players[int(player_to_question) - 1].get_name()} about {self._players[int(player_to_ask_about) - 1].get_name()} and got response: {response}\n"
                        )
        elif choice == "2":
            print("Who would you like to question?")
            for i, player in enumerate(self._players):
                print(f"{i + 1}. {player.get_name()}")
            player_to_question = input("Select a player: ")
            if [2, int(player_to_question) - 1] in self._memory_set:
                print("You have already made that choice.")
                return
            else:
                self._choice_no += 1
                response = self._players[int(player_to_question) - 1].check_alibi()

                print(
                    f"{self._players[int(player_to_question) - 1].get_name()} says: {response}"
                )
                self._memory_human_readable.append(
                    f"Choice {self._choice_no}: Checked {self._players[int(player_to_question) - 1].get_name()}'s alibi and got response: {response}"
                )
                self._memory_set.append([2, int(player_to_question) - 1])
                if self._has_memory_file:
                    with open(self._memory_file, "a") as f:
                        f.write(
                            f"Choice {self._choice_no}: Checked {self._players[int(player_to_question) - 1].get_name()}'s alibi and got response: {response}\n"
                        )
        elif choice == "3":
            print("Which piece of evidence would you like to examine?")
            print("1. The murder weapon")
            print("2. The crime scene")
            print("3. The victim's body")
            print("4. The suspect's whereabouts")
            print("5. The timeline")
            evidence_choice = input("Select a piece of evidence: ")
            if [3, int(evidence_choice) - 1] in self._memory_set:
                print("You have already made that choice.")
                return
            else:
                self._choice_no += 1
                # responses = [player.examine_evidence() for player in self._players]
                # print("Examination of evidence results")
                # for i, response in enumerate(responses):
                #     print(f"{self._players[i].get_name()}: {response}")

                # self._memory_human_readable.append(
                #     f"Choice {self._choice_no}: Examined evidence and got responses"
                # )
                # for player, response in zip(self._players, responses):
                #     self._memory_human_readable.append(
                #         f"       {player.get_name()} said: {response}"
                #     )
                # self._memory_set.append([3, int(evidence_choice) - 1])
                responses = []
                for player in self._players:
                    if (
                        random.random() < 1 - 2 * self._noise_level
                    ):  # chance to appear decreases with noise level
                        responses.append((player.get_name(), player.examine_evidence()))
                if len(responses) > 0:
                    self._memory_human_readable.append(
                        f"Choice {self._choice_no}: Examined evidence and got responses"
                    )
                    for player_name, response in responses:
                        print(f"{player_name}: {response}")
                        self._memory_human_readable.append(
                            f"       {player_name}: {response}"
                        )
                        if self._has_memory_file:
                            with open(self._memory_file, "a") as f:
                                f.write(f"       {player_name}: {response}\n")
                else:
                    print("Evidence was inconclusive")
                    self._memory_human_readable.append(
                        f"Choice {self._choice_no}: Examined evidence but got no responses."
                    )
                    if self._has_memory_file:
                        with open(self._memory_file, "a") as f:
                            f.write(
                                f"Choice {self._choice_no}: Examined evidence but got no responses.\n"
                            )
                self._memory_set.append([3, int(evidence_choice) - 1])

        elif choice == "4":
            print("Your past choices:")
            for memory in self._memory_human_readable:
                print(memory)
        elif choice == "5":
            print("Who would you like to accuse?")
            for i, player in enumerate(self._players):
                print(f"{i + 1}. {player.get_name()}")
            player_to_accuse = input("Select a player: ")
            if self._players[int(player_to_accuse) - 1].get_type() == "Guilty":
                print(
                    f"You have accused {self._players[int(player_to_accuse) - 1].get_name()} and they are the murderer!"
                )
                print("You have solved the mystery! Well done!")
            else:
                print(
                    f"You have accused {self._players[int(player_to_accuse) - 1].get_name()} but they are NOT the murderer!"
                )
                print(
                    "You have failed to solve the mystery, and the murderer is still at large!"
                )
            self._game_over = True
        elif choice == "6":
            print("Exiting the game.")
            self._game_over = True
        else:
            print("Invalid choice. Please try again.")

    def play_game(self):
        while not self._game_over:
            self._make_choice()


if __name__ == "__main__":
    game = MurderMystery(
        num_players=5, num_accomplices=2, noise_level=0.25, memory_file="game_memory.md"
    )
    game.play_game()
