import os
import json
from pathlib import Path
from tools import read_profile, get_practice_task
from dotenv import load_dotenv
from openai import OpenAI
from db import get_recent_chats

# 读取 main.py 同一文件夹里的 .env
load_dotenv(Path(__file__).with_name(".env"))


# 配置连接：使用哪个密钥，请求发到哪里
client = OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url=os.environ["DASHSCOPE_BASE_URL"],
)

tool_definitions = [
    {
        "type": "function",
        "function": {
            "name": "read_profile",
            "description": "读取用户的技能档案，用于分析用户与岗位要求的差距。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_practice_task",
            "description": "根据技能名称，查询练习库中的练习任务。",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill": {
                        "type": "string",
                        "description": "技能名称，例如 Python、FastAPI、SQL。",
                    }
                },
                "required": ["skill"],
            },
        },
    },
]

def run_agent(question, session_id="default"):
    question = question.strip()
    if not question:
        raise ValueError("问题不能为空。")

    # 每次调用函数，都创建本次任务自己的消息列表
    messages = [
        {
            "role": "system",
            "content": (
                "你是一名求职辅导助手。"
                "当问题涉及用户本人的技能、岗位匹配或个人学习建议时，"
                "使用 read_profile 获取档案；一般知识问题直接回答。"
                "档案未提及的能力应标为未知，不能认定用户不会。"
                "不能仅凭一次 API 调用就判断用户掌握 Python。"
                "区分岗位原文要求与补充建议，回答不超过300字。"
                "如果技能档案读取失败，明确告知用户，并请用户提供技能信息，不要猜测。"
                "用户明确指定技能并索要练习时，调用 get_practice_task，无需读取个人档案。"
                "用户索要练习时，先提供练习题目，不主动提供参考代码或完整答案；用户明确索要答案时再提供。"
                "描述用户能力时，严格保留档案中的程度表述："
                "例如，'尚未掌握'不能改写为'零基础'、'从未接触'或'没有任何实践'。"
                "选择练习时，只根据档案中明确记录的信息说明理由。"
            ),
        },
    ]
        # 数据库返回最新的 5 条问答，最新记录在前
    history = get_recent_chats(session_id)

    # 反向遍历，让模型按从旧到新的顺序阅读
    for record in reversed(history):
        messages.append(
            {
                "role": "user",
                "content": record["question"],
            }
        )
        messages.append(
            {
                "role": "assistant",
                "content": record["answer"],
            }
        )

    # 当前问题放在所有历史问答之后
    messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    print(f"本次加载了 {len(history)} 条历史问答")

    max_rounds = 5

    for round_number in range(1, max_rounds + 1):
        print(f"\n第 {round_number} 次请求模型，本次携带 {len(messages)} 条消息")
        print("本轮发送的消息角色：", [m["role"] for m in messages])

        response = client.chat.completions.create(
            model=os.environ["DASHSCOPE_MODEL"],
            messages=messages,
            tools=tool_definitions,
            tool_choice="auto",
        )

        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            # 返回回答，并立即结束整个函数
            return message.content or "模型未返回回答内容。"

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            print("正在执行工具：", tool_name)

            if tool_name == "read_profile":
                try:
                    result = read_profile()
                except FileNotFoundError:
                    result = "工具读取失败：技能档案文件不存在，无法获取用户技能。"

            elif tool_name == "get_practice_task":
                try:
                    arguments = json.loads(tool_call.function.arguments)

                    if not isinstance(arguments, dict):
                        result = "工具参数错误：参数必须是 JSON 对象。"
                    else:
                        skill = arguments.get("skill")

                        if not isinstance(skill, str) or not skill.strip():
                            result = "工具参数错误：skill 必须是非空字符串。"
                        else:
                            print("模型传入的技能：", skill)
                            result = get_practice_task(skill)

                except json.JSONDecodeError:
                    result = "工具参数错误：无法解析 JSON。"

            else:
                result = "错误：未知工具，未执行。"

            print("工具结果：", result)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

    return "已达到最多 5 次模型请求，任务尚未完成。"


if __name__ == "__main__":
    question = input("请输入你的问题：").strip()

    if not question:
        raise SystemExit("问题不能为空，请重新运行。")

    answer = run_agent(question)
    print("\n模型分析：")
    print(answer)