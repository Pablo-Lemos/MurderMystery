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
        max_choices=100,
        seed=None,
        memory_file=None,
        llm_player=None,
        verbosity=2,
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

        self._llm_player = llm_player
        self._is_llm_player = llm_player is not None
        assert verbosity in [0, 1, 2], "Verbosity must be 0, 1, or 2"
        self._verbosity = verbosity

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

        if self._verbosity >= 2:
            print("=" * 40)
            print(f"WHO IS THE MURDERER?")
            print("=" * 40)
            print(
                f"There has been a murder! You are a wise and smart detective, tasked with solving the case. There are {num_players} suspects: {', '.join([player.get_name() for player in self._players])}"
            )
            print(
                "You must use your deduction skills to identify the murderer. Do not forget, people lie, and even the evidence can be misleading!"
            )
        elif self._verbosity >= 1:
            print(f"Starting game with {num_players} suspects...")
        self._memory_human_readable = []
        self._memory_set = []
        self._choice_no = 0
        self._game_over = False
        self._won = None  # None until game ends, then True/False
        self._max_choices = max_choices

    def _print(self, *args, **kwargs):
        """Print only if verbosity >= 2."""
        if self._verbosity >= 2:
            print(*args, **kwargs)

    def _print_choice_summary(self):
        """Print summary of all choices made (for verbosity >= 1)."""
        if self._verbosity >= 1 and self._memory_human_readable:
            print("\n" + "=" * 40)
            print("CHOICES MADE:")
            print("=" * 40)
            for memory in self._memory_human_readable:
                print(memory)
            print("=" * 40 + "\n")

    def _validate_choice(self, choice: str, max_value: int) -> int:
        """Validate and convert a choice string to an integer index.

        Returns a valid index (0 to max_value-1), or None if invalid.
        """
        try:
            idx = int(choice) - 1
            if 0 <= idx < max_value:
                return idx
            return None  # Out of range
        except (ValueError, TypeError):
            return None  # Not a valid integer

    def _display_and_select_player(self, prompt: str) -> tuple[str, str]:
        """Display player list and get selection.

        Returns:
            tuple: (player_choice, player_list_string)
        """
        player_list = "\n".join(f"{i+1}. {p.get_name()}" for i, p in enumerate(self._players))
        for i, player in enumerate(self._players):
            self._print(f"{i + 1}. {player.get_name()}")
        player_choice = self._get_input(prompt, menu_context=player_list, max_value=len(self._players))
        return player_choice, player_list

    def _write_to_memory(self, text: str):
        """Write a line to the memory file if it exists."""
        if self._has_memory_file:
            with open(self._memory_file, "a") as f:
                f.write(f"{text}\n")

    def _make_choice(self):
        self._print("=" * 40)
        self._print("What would you like to do?")
        self._print("=" * 40)
        self._print("1. Ask a suspect about another")
        self._print("2. Check a suspect's alibi")
        self._print("3. Examine the evidence")
        self._print("4. Check your past choices")
        self._print("5. Accuse a suspect")
        self._print("6. Quit")

        self._print("=" * 40)
        main_menu = "1. Ask a suspect about another\n2. Check a suspect's alibi\n3. Examine the evidence\n4. Check your past choices\n5. Accuse a suspect\n6. Quit"
        choice = self._get_input("Choose your next action:", menu_context=main_menu, max_value=6)
        self._print("=" * 40)

        if choice == "1":
            self._print("Who would you like to question?")
            player_to_question, _ = self._display_and_select_player("Select a player:")
            self._print("Who would you like to ask about?")
            player_to_ask_about, _ = self._display_and_select_player("Select a player:")
            q_idx = self._validate_choice(player_to_question, len(self._players))
            a_idx = self._validate_choice(player_to_ask_about, len(self._players))
            if [1, q_idx, a_idx] in self._memory_set:
                self._print("You have already made that choice.")
                return
            elif q_idx == a_idx:
                self._print("You cannot ask a player about themselves.")
                return
            else:
                self._choice_no += 1
                response = self._players[q_idx].ask_about_player(self._players[a_idx])
                self._print(
                    f"{self._players[q_idx].get_name()} says: {response}"
                )
                memory_text = f"Choice {self._choice_no}: Asked {self._players[q_idx].get_name()} about {self._players[a_idx].get_name()} and got response: {response}"
                self._memory_human_readable.append(memory_text)
                self._memory_set.append([1, q_idx, a_idx])
                self._write_to_memory(memory_text)
        elif choice == "2":
            self._print("Who would you like to question?")
            player_to_question, _ = self._display_and_select_player("Select a player:")
            q_idx = self._validate_choice(player_to_question, len(self._players))
            if [2, q_idx] in self._memory_set:
                self._print("You have already made that choice.")
                return
            else:
                self._choice_no += 1
                response = self._players[q_idx].check_alibi()

                self._print(f"{self._players[q_idx].get_name()} says: {response}")
                memory_text = f"Choice {self._choice_no}: Checked {self._players[q_idx].get_name()}'s alibi and got response: {response}"
                self._memory_human_readable.append(memory_text)
                self._memory_set.append([2, q_idx])
                self._write_to_memory(memory_text)
        elif choice == "3":
            self._print("Which piece of evidence would you like to examine?")
            self._print("1. The murder weapon")
            self._print("2. The crime scene")
            self._print("3. The victim's body")
            self._print("4. The suspect's whereabouts")
            self._print("5. The timeline")
            evidence_menu = "1. The murder weapon\n2. The crime scene\n3. The victim's body\n4. The suspect's whereabouts\n5. The timeline"
            evidence_choice = self._get_input("Select a piece of evidence:", menu_context=evidence_menu, max_value=5)
            e_idx = self._validate_choice(evidence_choice, 5)
            if [3, e_idx] in self._memory_set:
                self._print("You have already made that choice.")
                return
            else:
                self._choice_no += 1
                responses = []
                for player in self._players:
                    if (
                        random.random() < 1 - 2 * self._noise_level
                    ):  # chance to appear decreases with noise level
                        responses.append((player.get_name(), player.examine_evidence()))
                if len(responses) > 0:
                    header = f"Choice {self._choice_no}: Examined evidence and got responses"
                    self._memory_human_readable.append(header)
                    self._write_to_memory(header)
                    for player_name, response in responses:
                        self._print(f"{player_name}: {response}")
                        detail = f"       {player_name}: {response}"
                        self._memory_human_readable.append(detail)
                        self._write_to_memory(detail)
                else:
                    self._print("Evidence was inconclusive")
                    memory_text = f"Choice {self._choice_no}: Examined evidence but got no responses."
                    self._memory_human_readable.append(memory_text)
                    self._write_to_memory(memory_text)
                self._memory_set.append([3, e_idx])

        elif choice == "4":
            self._print("Your past choices:")
            for memory in self._memory_human_readable:
                self._print(memory)
        elif choice == "5":
            self._print("Who would you like to accuse?")
            player_to_accuse, _ = self._display_and_select_player("Select a player:")
            acc_idx = self._validate_choice(player_to_accuse, len(self._players))
            self._handle_accusation(acc_idx)
        elif choice == "6":
            if self._verbosity >= 1:
                print("Game ended by quit.")
            self._won = False
            self._game_over = True
        else:
            self._print("Invalid choice. Please try again.")

    def _make_last_choice(self):
        # Implementation for the last choice
        self._print(
            "Your choices are up, time to choose a suspect with the information you have!"
        )
        self._print("1. Accuse a suspect")
        self._print("2. Check your past choices")
        self._print("3. Quit")
        last_menu = "1. Accuse a suspect\n2. Check your past choices\n3. Quit"
        choice = self._get_input("Select an option:", menu_context=last_menu, max_value=3)
        if choice == "1":
            self._print("Who would you like to accuse?")
            player_to_accuse, _ = self._display_and_select_player("Select a player:")
            acc_idx = self._validate_choice(player_to_accuse, len(self._players))
            self._handle_accusation(acc_idx)
        elif choice == "2":
            self._print("Your past choices:")
            for memory in self._memory_human_readable:
                self._print(memory)
        elif choice == "3":
            if self._verbosity >= 1:
                print("Game ended by quit.")
            self._won = False
            self._game_over = True
        else:
            self._print("Invalid choice. Please try again.")

    def play_game(self):
        while not self._game_over:
            if self._choice_no >= self._max_choices:
                self._make_last_choice()
            else:
                self._make_choice()
        return self._won

    def _get_input(self, prompt: str, menu_context: str = None, max_value: int = None, max_retries: int = 3):
        """Get input from human or LLM.

        Args:
            prompt: The prompt to show
            menu_context: Optional menu options to include for LLM
            max_value: If provided, validate that choice is 1 to max_value (for LLM only)
            max_retries: Maximum retries for invalid LLM responses
        """
        if self._is_llm_player:
            context = self._build_llm_context()
            if menu_context:
                base_prompt = f"{context}\n\n{menu_context}\n\n{prompt}\n\nRespond with ONLY the number of your choice."
            else:
                base_prompt = f"{context}\n\n{prompt}\n\nRespond with ONLY the number of your choice."

            for attempt in range(max_retries + 1):
                if attempt == 0:
                    full_prompt = base_prompt
                else:
                    full_prompt = f"{base_prompt}\n\nYour previous response was invalid. Please respond with a number between 1 and {max_value}."

                response = self._llm_player.get_choice(full_prompt)
                choice = "".join(c for c in response if c.isdigit())[:1]

                # Validate if max_value is provided
                if max_value is not None:
                    idx = self._validate_choice(choice, max_value)
                    if idx is not None:
                        self._print(f"LLM chose: {choice}")
                        return choice
                    # Invalid response, will retry
                    self._print(f"LLM gave invalid response: {response!r}, retrying...")
                else:
                    self._print(f"LLM chose: {choice}")
                    return choice

            # After all retries failed, default to "1"
            self._print(f"LLM failed after {max_retries} retries, defaulting to 1")
            return "1"
        else:
            return input(prompt)

    def _handle_accusation(self, acc_idx):
        """Handle the accusation of a player and determine game outcome."""
        self._print_choice_summary()
        if self._players[acc_idx].get_type() == "Guilty":
            if self._verbosity >= 1:
                print(
                    f"You have accused {self._players[acc_idx].get_name()} and they are the murderer!"
                )
                print("You have solved the mystery! Well done!")
            self._won = True
        else:
            if self._verbosity >= 1:
                print(
                    f"You have accused {self._players[acc_idx].get_name()} but they are NOT the murderer!"
                )
                print(
                    "You have failed to solve the mystery, and the murderer is still at large!"
                )
            self._won = False
        self._game_over = True

    def _build_llm_context(self):
        """Build context for LLM based on past choices."""
        context = "You are a detective solving a murder mystery"
        context += f"The suspects are {', '.join([player.get_name() for player in self._players])}"
        context += "\nEvidence gathered so far: "
        for memory in self._memory_human_readable:
            context += f"\n{memory}"
        context += "\nUse ONLY the evidence provided to make your decision."
        return context


if __name__ == "__main__":
    game = MurderMystery(
        num_players=5,
        num_accomplices=2,
        noise_level=0.25,
        memory_file="game_memory.md",
        max_choices=2,
    )
    game.play_game()
