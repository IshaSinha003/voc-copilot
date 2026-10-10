from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic()

msg = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=50,
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(msg.content[0].text)