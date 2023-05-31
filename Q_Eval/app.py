from flask import Flask, request, render_template, send_file
import pandas as pd
import requests
import json
from tqdm import tqdm
import os

app = Flask(__name__)

OPENAI_API_KEY = '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'
OUTPUT_FILE = "output.csv"

def chat_gpt4(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are ChatGPT-4, a large language model trained by OpenAI."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 4096,
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        message = response_data["choices"][0]["message"]["content"]
        return message
    else:
        raise Exception(
            f"Request failed with status code {response.status_code}: {response.text}"
        )

def analyze_question(question, options=None):
    guidelines = """
    1. The question could be better rephrased.
    2. Grammar or punctuation mistakes in the question.
    3. The question is too broad or generic.
    4. Incorrect framing of the question, not conforming to proper question format.
    5. Spelling mistakes in the question.
    6. Lack of clarity in the question, including ambiguities.
    7. The question doesn't make sense or lacks logical coherence.
    8. The question doesn't convey its full intent or expected answer.
    9. Options provided are irrelevant or not directly related to the question.
    10. Ambiguity in the options provided.
    11. Options overlap, causing confusion.
    12. Options are too similar, lacking distinctiveness.
    13. Spelling or grammar mistakes in the options.
    14. No correct option or multiple correct options, if unintended.
    """

    prompt = f"As an NCERT Social Studies expert, your task is to scrutinize the given question" 
    prompt += f" and corresponding options (if any). Identify and categorize any potential flaws using the following guidelines: {guidelines}" 
    prompt += f"Question: {question}"
    if options:
        prompt += f" Options: {options}"

    return chat_gpt4(prompt)

def correct_question(question, options=None):
    prompt = "Based on the analysis, please correct the following question and options (if any) to eliminate any potential flaws: "
    prompt += f"Question: {question}"
    if options:
        prompt += f" Options: {options}"

    return chat_gpt4(prompt)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            data = pd.read_csv(file)
            errors = []
            modified_questions = []

            for index, row in tqdm(data.iterrows(), total=data.shape[0]):
                question = row['questions']
                options = row['options'] if 'options' in row and pd.notnull(row['options']) else None

                error = analyze_question(question, options)
                errors.append(error)

                modified_question = correct_question(question, options)
                modified_questions.append(modified_question)

                data.at[index, 'errors'] = error
                data.at[index, 'Modified Question'] = modified_question

            # Write to file after every iteration
            data.to_csv(OUTPUT_FILE, index=False)
            return render_template('download.html')

    return render_template('upload.html')

@app.route('/download')
def download_file():
    path = OUTPUT_FILE
    return send_file(path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
