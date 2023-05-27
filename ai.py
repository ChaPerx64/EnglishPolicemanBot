import os
import openai
from dotenv import load_dotenv

load_dotenv()

# Load your API key from an environment variable or secret management service
openai.api_key = os.getenv("OPENAI_TOKEN")


def check_grammar_with_ai(text):
    prompt = '''
      Check my english sentence grammar, vocabulary and provide feedback on how to improve it.
      You must focus on the grammar and vocabulary of the sentence.
      Use the text as it is, do not change it.
      Be concise and specific. Max length is 200 characters.
      But provide example if it's appropriate.
      ---
    '''
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content
