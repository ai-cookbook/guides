import httpx
import time
from tenacity import retry, wait_random_exponential, stop_after_attempt
import os
import sqlite3
from termcolor import colored  
from cloud_instruments.searchapi import search_api_generative
from cloud_instruments.serverless_func import send_post_request

GPT_MODEL = "yandexgpt/rc"
FOLDER_ID = os.getenv('FOLDER_ID') or ''
API_KEY = os.getenv('YANDEX_API_KEY') or ''

db_path = 'data/example.db'

products_table_description = """
Таблица "products" предназначена для хранения информации о товарах, доступных в магазине. 
Каждый товар имеет следующие поля:
- productId: уникальный идентификатор товара (TEXT, PRIMARY KEY)
- name: название товара (TEXT, NOT NULL)
- category: категория товара (TEXT, NOT NULL). Например: электроника, одежда, книги, дом, ягоды, сад
- price: цена товара (REAL, NOT NULL)
- num_of_orders: количество заказов данного товара (INTEGER, NOT NULL)
- rating: рейтинг товара (REAL, NOT NULL)
"""

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, tools=None, model=GPT_MODEL):
    payload = {
        "modelUri": f"gpt://{FOLDER_ID}/{model}",
        "completionOptions": {
            "stream": False,
            "temperature": 0,
            "maxTokens": 1000
        },
        "messages": messages,
        "tools": tools
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {API_KEY}"
    }
    
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    try:
        response = httpx.post(
            url=url, 
            json=payload, 
            headers=headers,
            timeout=60.0
        )
        
        response_data = response.json()
        
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code}, {response_data}")
            
        return response_data
    
    except Exception as e:
        print(f"Error occurred: {e}")
        raise e
    
def get_function_call_from_response(response):
    return response['result']['alternatives'][0]['message'].get('toolCallList', {}).get('toolCalls', [])

def pack_function_result(name: str, content: str):
    return {
        "functionResult": {
            "name": name,
            "content": str(content)
        }
    }

def process_tool_product_list_tool(category: str, priceMinMax: list[int], sortBy: str = 'price') -> list[dict]:
    return [{'productId': 'siaomi453', 'name': 'сяоми 4+ pro', 'category': category, 'price': 10_000},
            {'productId': 'iphone15', 'name': 'iphone 15', 'category': category, 'price': 280_000}]

def process_tool_balance_tool(userId: str) -> dict:
    # Обработка аргументов: userId
    return {'userId': userId, 'balance': 10000}

def process_tool_order_tool(productId: str, quantity: int) -> dict:
    # Обработка аргументов: productId, quantity
    return {'orderId': 'order123', 'productId': productId, 'quantity': quantity}    

def process_tool_sql_tool(query: str) -> str:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    conn.close()
    return result

def process_tool_searchapi(query: str) -> str:
    return search_api_generative(query)

def process_tool_serverless_func(name: str) -> str:
    return send_post_request(name)


def process_functions(toolCalls):
    tools_map = {
        "ProductListTool": process_tool_product_list_tool,
        "BalanceTool": process_tool_balance_tool,
        "OrderTool": process_tool_order_tool,
        "ask_database": process_tool_sql_tool,
        "searchapi": process_tool_searchapi,
        "serverless_func": process_tool_serverless_func
    }
    
    results = []
    for tool_call in toolCalls:
        name = tool_call['functionCall']['name']
        arguments = tool_call['functionCall'].get('arguments', {})
        if name in tools_map:
            # Вызываем функцию с переданными аргументами
            result = tools_map[name](**arguments)
            
            results.append(pack_function_result(name, result))
    
    return results

def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "function": "magenta",
    }
    
    for message in messages:
        if message["role"] == "system":
            print(colored(f"system: {message['text']}\n", role_to_color[message["role"]]))
        elif message["role"] == "user":
            print(colored(f"user: {message['text']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and (message.get("toolCallList") or message.get("toolResultList")):
            print(colored(f"assistant: {message.get('toolCallList') or message.get('toolResultList')}\n", role_to_color["function"]))
        elif message["role"] == "assistant" and not (message.get("toolCallList") or message.get("toolResultList")):
            print(colored(f"assistant: {message['text']}\n", role_to_color[message["role"]]))


if __name__ == '__main__':
    test_messages = [
        {"role": "system", "text": "Ты - полезный бот, который помогает пользователю с его проблемами. Ты можешь использовать инструменты, чтобы получить актуальную информацию. Но пользоваться ими нужно не всегда."},
        {"role": "user", "text": "Сколько у меня денег на балансе?"}
    ]
    
    test_messages = [
        {"role": "system", "text": "Ты - полезный бот, который помогает пользователю с его проблемами. Ты можешь использовать инструменты, чтобы получить актуальную информацию. Но пользоваться ими нужно не всегда. Если пользователь ищет товары, то всегда параллельно с вызовом инструмента ProductListTool вызывай и BalanceTool."},
        {"role": "user", "text": "Покажи мне товары категории 'электроника' в диапазоне цен от 1000 до 5000 рублей, отсортированные по популярности."}
    ]
    
    test_messages = [
        {"role": "system", "text": "Ты - полезный бот, который помогает пользователю с его проблемами. Ты можешь использовать инструменты, чтобы получить актуальную информацию. Но пользоваться ими нужно не всегда"},
        {"role": "user", "text": f"Мне нужны все товары категории 'электроника', отсортированные по рейтингу, ценой меньше 30к."}
    ]

    weather_tool = {
            "function": {
                "name": "WeatherTool",
                "description": "Ходит в API и получает погоду в городе",
                "parameters": {
                    "type": "object",
                    "properties": {
                    "city": {
                        "type": "string",
                        "description": "Название города, для которого нужно получить погоду."
                    },
                    "units": {
                        "type": "string",
                        "enum": ["metric", "imperial"],
                            "default": "metric",
                            "description": "Единицы измерения температуры. 'metric' для Цельсия, 'imperial' для Фаренгейта."
                        },
                        "region": {
                            "type": "string",
                            "default": "center",
                            "description": "Часть города, для которой нужно получить погоду."
                        }
                    },
                    "required": ["city"],
                    "additionalProperties": False
                }
            }
        }
    
    product_list_tool = {
            "function": {
                "name": "ProductListTool",
                "description": "Получает список товаров из базы данных на основе заданных параметров. Позволяет фильтровать товары по диапазону цен, категории и критерию сортировки.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "priceMinMax": {
                            "type": "array",
                            "items": {
                                "type": "number"
                            },
                            "description": "Диапазон цен в формате [минимальная цена, максимальная цена]. Позволяет пользователю указать, какие товары его интересуют в пределах заданного ценового диапазона."
                        },
                        "category": {
                            "type": "string",
                            "description": "Категория товаров, по которой будет осуществляться фильтрация. Например, 'электроника', 'одежда', 'книги', 'дом и сад'. Это позволяет пользователю сузить поиск до определенной группы товаров."
                        },
                        "sortBy": {
                            "type": "string",
                            "enum": ["price", "popularity", "rating"],
                            "description": "Критерий сортировки товаров. Возможные значения: 'price' для сортировки по цене, 'popularity' для сортировки по популярности, 'rating' для сортировки по рейтингу. Это позволяет пользователю получить список товаров в удобном для него порядке."
                        }
                    },
                    "required": ["priceMinMax", "category"],
                    "additionalProperties": False
                }
            }
        }
    
    balance_tool = {
        "function": {
            "name": "BalanceTool",
            "description": "Получает баланс пользователя из базы данных.",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": "Идентификатор пользователя, для которого нужно получить баланс."
                    }
                },
                "required": ["userId"],
                "additionalProperties": False
            }
        }
    }
    
    demo_balance_tool = {
        "function": {
            "name": "DemoBalanceTool",
            "description": "Демонстрационный инструмент, который получает баланс пользователя.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            }
        }
    }
    
    order_tool = {
        "function": {
            "name": "OrderTool",
            "description": "Демонстрационный инструмент, который заказывает товар по его идентификатору.",
            "parameters": {
                "type": "object",
                "properties": {
                    "productId": {
                        "type": "string",
                        "description": "Идентификатор товара, который нужно заказать."
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Количество товара для заказа.",
                        "minimum": 1
                    }
                },
                "required": ["productId", "quantity"],
                "additionalProperties": False
            }
        }
    }
    
    sql_tool = {
        "function": {
            "name": "ask_database",
            "description": f"Use this function to answer user questions about the database. Input should be a fully formed SQL query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": f"""
                                SQL query extracting info to answer the user's question.
                                SQL should be written using this database schema:
                                {products_table_description}
                                The query should be returned in plain text, not in JSON.
                                """,
                    }
                },
                "required": ["query"],
            },
        }
    }
    
    tools = [
        weather_tool, 
        #product_list_tool, 
        balance_tool, 
        demo_balance_tool, 
        order_tool, 
        sql_tool
    ]

    result = chat_completion_request(test_messages, tools=tools)
    print(f"result: {result}")
    print(f"function call: {get_function_call_from_response(result)}")
    toolResults: list = process_functions(get_function_call_from_response(result))
    print(f"tool results: {toolResults}")
    
    toolCalls: list = get_function_call_from_response(result)
    test_messages.append({
        'role': 'assistant',
        #'text': '',
        'toolCallList': {'toolCalls': toolCalls}
    })
    
    test_messages.append({
        'role': 'assistant',
        #'text': '',
        'toolResultList': {'toolResults': toolResults}
    })
    
    print(f"test messages: {test_messages}")
    
    result_final = chat_completion_request(test_messages, tools=tools)
    print(f"result final: {result_final}")
    with open('output.md', 'w', encoding='utf-8') as f:
        assistant_message = result_final['result']['alternatives'][0]['message']['text']
        f.write(assistant_message)
        
    test_messages.append({
        'role': 'assistant',
        'text': assistant_message
    })
    
    print(f"test messages: {test_messages}")
    
    pretty_print_conversation(test_messages)
