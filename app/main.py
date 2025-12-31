"""
main.py

Version : 1.3.2
Author  : aumezawa
"""

import os
import sys
from dotenv import load_dotenv
from uuid import uuid4

sys.path.append(os.path.curdir)


###
# Set API Key
###
load_dotenv()


def exec_chatbot() -> None:
    """Execute chatbot."""
    from app.agents.chatbot import Chatbot
    from app.tools.math import tools as math_tools

    chatbot = Chatbot(
        tools=math_tools,
    )

    # Execute
    thread_id = uuid4().hex
    result = chatbot.run(
        query="100掛ける200の計算と1足す2の計算をそれぞれしてください",
        thread_id=thread_id,
    )

    print("=== Result ===")
    print(result)
    print("=== Checkpoint ===")
    print(chatbot.checkpoint(thread_id))


if __name__ == "__main__":
    exec_chatbot()
