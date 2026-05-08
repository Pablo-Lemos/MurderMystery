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


if __name__ == "__main__":
    from simple_murder_mystery import MurderMystery

    llm = LLMPlayer(model="ollama:llama3.1:8b")
    game = MurderMystery(
        num_players=5,
        noise_level=0.1,
        num_accomplices=1,
        seed=42,
        llm_player=llm,
        verbosity=1,  # 0=minimal, 1=show choices before outcome, 2=full output
    )
    game.play_game()
