import aisuite


class LLMPlayer:
    SYSTEM_PROMPT = """You are a detective solving a murder mystery.
Analyze the evidence carefully and make logical deductions.
When asked to choose, respond with ONLY the number (1, 2, 3, etc.).
Think about who might be lying and who has weak alibis.
Remember: ALL information can be misleading - people lie!"""

    def __init__(self, model="ollama:llama3.1:8b"):
        self.client = aisuite.Client()
        self.model = model
        self.messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

    def get_choice(self, prompt: str) -> str:
        """Get a choice from the LLM given the current game state."""
        self.messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model, messages=self.messages
        )

        answer = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": answer})

        # Extract just the digit
        return self._extract_choice(answer)

    def _extract_choice(self, response: str) -> str:
        """Extract first digit from LLM response."""
        for char in response:
            if char.isdigit():
                return char
        return "1"  # Fallback default


class CoTLLMPlayer(LLMPlayer):
    SYSTEM_PROMPT = """You are a detective solving a murder mystery. Analyze the evidence carefully and make logical deductions.
    Think about who might be lying and who has weak alibis.

    Think step by step:

    1. What evidence have I gathered so far?
    2. Who seems most/least suspicious based on this evidence?                                                                                                                        │
    3. What information would be most valuable to gather next?                                                                                                                        │

    Provide your reasoning and then provide your choice as a single number
    Remember: ALL information can be misleading - people lie!
    End your response with 'ANSWER: X' where X is your choice.
    """

    def __init__(self, model="ollama:llama3.1:8b", show_reasoning=False):
        self.client = aisuite.Client()
        self.model = model
        self.messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        self.verbose = show_reasoning

    def get_choice(self, prompt: str) -> str:
        """Get a choice from the LLM given the current game state."""
        self.messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model, messages=self.messages
        )

        answer = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": answer})

        if self.verbose:
            print("LLM Reasoning:\n", answer)
            print("-" * 50)

        # Extract just the digit
        return self._extract_choice(answer)

    def _extract_choice(self, response):
        """Extract last digit from LLM response, assuming reasoning may contain numbers."""
        if "ANSWER:" in response:
            answer_part = response.split("ANSWER:")[-1].strip()
            for char in answer_part:
                if char.isdigit():
                    return char
        # Fallback to last digit in entire response if ANSWER: format is not followed
        for char in reversed(response):
            if char.isdigit():
                return char
        return "1"  # Fallback default


if __name__ == "__main__":
    from murdermystery import MurderMystery

    llm = CoTLLMPlayer(model="ollama:llama3.1:8b", show_reasoning=True)
    game = MurderMystery(
        num_players=5,
        noise_level=0.1,
        num_accomplices=1,
        seed=42,
        llm_player=llm,
        verbosity=2,  # 0=minimal, 1=show choices before outcome, 2=full output
    )
    game.play_game()
