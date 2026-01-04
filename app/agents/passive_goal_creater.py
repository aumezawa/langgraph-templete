"""
passive-goal-creater.py

Version : 1.4.0
Author  : aumezawa
"""

from pydantic import BaseModel, Field


class Goal(BaseModel):
    """Goal Model."""

    description: str = Field(..., description="目標の説明")

    @property
    def text(self) -> str:
        """Return the text representation of the goal."""
        return f"Goal: {self.description}"


class PassiveGoalCreater:
    """Passive Goal Creater Class."""

    from langchain_core.language_models import BaseChatModel
    from langchain_core.prompts import ChatPromptTemplate

    DEFAULT_LLM_MODEL = "gemini-2.5-flash"

    PROMPT_TEMPLATE = ChatPromptTemplate.from_template(
        "ユーザの入力を分析し、明確で実行可能な目標を生成してください。\n"
        "要件:\n"
        "1. 目標は具体的かつ明確であり、実行可能なレベルで詳細化されていること\n"
        "2. あなたが実行可能な行動は以下の行動のみであること\n"
        "    - インターネットを利用して、目標を達成するための調査を行う\n"
        "    - ユーザのためにレポートを生成する\n"
        "3. 決して2.以外の行動を取らないこと\n"
        "ユーザの入力: {query}",
    )

    def __init__(
        self,
        model: BaseChatModel | None = None,
    ) -> None:
        """Initialize Passive Goal Creater."""
        from langchain_google_genai import ChatGoogleGenerativeAI

        self.model = model or ChatGoogleGenerativeAI(model=self.DEFAULT_LLM_MODEL)

    def run(self, query: str) -> Goal:
        """Run Passive Goal Creater."""
        prompt = self.PROMPT_TEMPLATE

        chain = prompt | self.model.with_structured_output(Goal)
        result = chain.invoke({"query": query})

        if isinstance(result, Goal):
            return result
        return Goal(description=str(result))
