"""
math.py

Version : 1.3.2
Author  : aumezawa
"""

from langchain_core.tools import tool, BaseTool


###
# Define Tools
###
@tool
async def multiply_function(x: int, y: int) -> int:
    """
    2つのint型の値を引数で受け取り、掛け算の結果をint型で返す

    Args:
        x (int): 1つ目のint型の引数
        y (int): 2つ目のint型の引数

    Returns:
        int: x * y
    """
    return x * y


@tool
async def add_function(x: int, y: int) -> int:
    """
    2つのint型の値を引数で受け取り、足し算の結果をint型で返す

    Args:
        x (int): 1つ目のint型の引数
        y (int): 2つ目のint型の引数

    Returns:
        int: x + y
    """
    return x + y


###
# Export Tools
###
tools: list[BaseTool] = [
    multiply_function,
    add_function,
]
