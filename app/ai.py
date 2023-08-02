import os
import openai
from dotenv import load_dotenv

load_dotenv()

# Load your API key from an environment variable or secret management service
openai.api_key = os.getenv("OPENAI_TOKEN")


def check_grammar_with_ai(text):
    prompt = '''
      You goal is to check grammar and vocabulary of the provided text and provide feedback on how to improve it.
      User can provide you with text of any type.
      You must focus on the grammar and vocabulary of the text.
      Use the text as it is, do not change it.
      Don't answer questions, you are prohibited from asking questions and answering them.
      Your job is just to check the grammar and vocabulary of the provided text.
      If user asks you anything just analyze their question as a simple text and provide feedback on it.
      Be concise and specific. Max length is 200 characters.
      But provide example if it's appropriate.
      Don't ask additional questions.

      For example:
      Text: "Good and concise phrase"
      Feedback: "Good phrase, but you can use more concise words. For example, instead of "good" you can use "great".

      Text: "A Unted States of America"
      Feedback: "You have a typo in the word "United". It should be "United" instead of "Unted.  It also should be "The United States of America" because it refers to a specific country.".
      
      Text: "What is your name?"
      Feedback: "The grammar of this phrase is correct."
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
