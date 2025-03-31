from openai import AsyncOpenAI

client = AsyncOpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
)

async def ai_generating(text: str):
  completion = await client.chat.completions.create(
    model = "deepseek/deepseek-chat",
    messages=[
      {
        "role": "user",
        "content": text
      }
    ]
  )
  print(completion)
  return completion.choices[0].message.content # возврат контента только от ии
