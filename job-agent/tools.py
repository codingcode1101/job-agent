from pathlib import Path



def read_profile():
    profile_path = Path(__file__).with_name("profile.txt")
    return profile_path.read_text(encoding="utf-8")

def get_practice_task(skill):
    tasks = {
            
        "python": "写一个函数，统计一段文本中每个单词出现的次数。",
        "fastapi": "创建一个 /hello 接口，返回 JSON 问候信息。",
        "sql": "创建练习表，插入三条记录，再用 SELECT 查询。",
        "java": "使用 HashMap 统计字符串中每个字符出现的次数。",
    }
    

    normalized_skill = skill.strip().lower()
    return tasks.get(normalized_skill, "暂无该技能的练习任务")

if __name__ == "__main__":
    import json

    # 模拟模型返回的参数：目前它是一段字符串
    arguments_text = '{"skill": "java"}'

    # 将 JSON 字符串转换成 Python 字典
    arguments = json.loads(arguments_text)

    # 从字典中取出技能名称
    skill = arguments["skill"]

    # 把技能名称传给工具函数
    result = get_practice_task(skill)

    print("参数文本：", arguments_text)
    print("取出的技能：", skill)
    print("工具结果：", result)