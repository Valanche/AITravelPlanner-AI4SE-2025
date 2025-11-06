import os
import json
from openai import OpenAI

# Initialize the OpenAI client
# It's recommended to set OPENAI_API_KEY and OPENAI_BASE_URL in your environment variables
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
)

def get_plan_prompt():
    return """
    你是一位专业的旅行规划专家。你的任务是根据用户提供的自然语言需求，生成一份详细的、格式化的旅行计划。
    用户的输入可能会包含旅行目的地、日期、预算、同行人数、旅行偏好等信息，你需要根据这些信息规划好计划中的交通、住宿、景点、餐厅等。
    计划每天的第一个行程项目应当是用户当日的出发地点，比如酒店、露营地点或是火车站、飞机场，用于实现到达真正的第一个行程地点的导航。
    需要给出确定的住宿、餐厅名称。实在不知道时，才可以给出附近的标志性地点作为代替，并标明在地点附近自行寻找。
    给出的每一个项目地址必须是确定的**一个**，不要有多个候选的情况。
    你必须严格按照以下描述的 JSON 结构返回数据。返回的结果**只能包含 JSON 对象本身**，不要包含任何额外的解释、注释或非 JSON 格式的文本。
    
    **JSON 输出结构:**
    
    你必须生成一个包含 `TravelPlan` 对象的 JSON。该对象的结构如下：
    
    *   `TravelPlan` (object): 包含整个旅行计划的根对象。
        *   `title` (string): 为旅行计划生成一个吸引人的标题。
        *   `description` (string): 对整个行程的简短描述。
        *   `days` (array): 一个包含每天行程的 `Day` 对象数组。
    *   `Day` (object): 描述一天的行程。
        *   `date` (string): 当天的日期，格式为 `YYYY-MM-DD`。
        *   `items` (array): 一个包含当天所有行程项目的 `ItineraryItem` 对象数组。
    *   `ItineraryItem` (object): 描述一个具体的行程项目。
        *   `item_type` (string): 项目类型。必须是以下之一：`"Activity"` (活动), `"Meal"` (用餐), `"Transportation"` (交通), `"Hotel"` (酒店)。
        *   `description` (string): 对该项目的详细描述。
        *   `start_time` (string): 项目开始时间，格式为 `YYYY-MM-DDTHH:MM:SS`。
        *   `end_time` (string): 项目结束时间，格式为 `YYYY-MM-DDTHH:MM:SS`。
        *   `location` (object): 描述项目地点的 `Location` 对象。
        *   `estimated_cost` (float): 该项目的预估费用。
        *   `estimated_cost_currency` (string): 费用所用的货币单位（例如, `"CNY"`）。
    *   `Location` (object): 描述一个地点。
        *   `name` (string): 地点的具体名称（例如, "夫子庙"），不能同时含两个地点。
        *   `city` (string): 地点所在的城市（例如, "南京"）。
    
    ---
    
    **示例:**
    
    如果用户需求是“我周末想去南京玩两天，从南京南站出发”，你应该返回类似下面这个例子的 JSON 对象：
    
    ```json
    {
      "title": "南京两日游：钟山风华与秦淮月夜",
      "description": "一份详细的南京两日游路线计划，从南京南站出发，涵盖历史与现代景观。",
      "days": [
        {
          "date": "2025-11-10",
          "items": [
            {
              "item_type": "Transportation",
              "description": "抵达南京：乘车到达南京南站",
              "start_time": "2025-11-10T08:00:00",
              "end_time": "2025-11-10T10:00:00",
              "location": {
                "name": "南京南站",
                "city": "南京"
              },
              "estimated_cost": 400.0,
              "estimated_cost_currency": "CNY"
            },
            {
              "item_type": "Hotel",
              "description": "抵达酒店：从南京南站乘坐地铁1号线至新街口站",
              "start_time": "2025-11-10T10:00:00",
              "end_time": "2025-11-10T11:00:00",
              "location": {
                "name": "新街口站",
                "city": "南京"
              },
              "estimated_cost": 4.0,
              "estimated_cost_currency": "CNY"
            },
            {
              "item_type": "Activity",
              "description": "游览明孝陵",
              "start_time": "2025-11-10T11:40:00",
              "end_time": "2025-11-10T13:00:00",
              "location": {
                "name": "明孝陵",
                "city": "南京"
              },
              "estimated_cost": 73.0,
              "estimated_cost_currency": "CNY"
            }
          ]
        },
        {
          "date": "2025-11-11",
          "items": [
            {
              "item_type": "Activity",
              "description": "参观总统府",
              "start_time": "2025-11-11T13:00:00",
              "end_time": "2025-11-11T15:00:00",
              "location": {
                "name": "总统府",
                "city": "南京"
              },
              "estimated_cost": 37.0,
              "estimated_cost_currency": "CNY"
            }
          ]
        }
      ]
    }
    ```
    """

def generate_plan(query: str):
    """
    Generates a travel plan by calling the LLM.

    Args:
        query: The user's travel query in natural language.

    Returns:
        A dictionary representing the travel plan, parsed from the LLM's JSON response.
        Returns None if the API call fails or the response is not valid JSON.
    """
    system_prompt = get_plan_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]

    try:
        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "deepseek-chat"),
            messages=messages,
            response_format={'type': 'json_object'}
        )
        response_content = response.choices[0].message.content
        return json.loads(response_content)
    except Exception as e:
        print(f"Error calling LLM or parsing JSON: {e}")
        return None
