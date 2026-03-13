import sys

import requests
import json

# read config file key=value pairs into a dict
with open(".env.agent.secret", "r") as f:
    secret = dict(line.strip().split("=", 1) for line in f if line.strip() and not line.startswith("#"))

# get program parameters as a one string
program_params = " ".join(sys.argv[1:])


try:
    # set timeout for the request in 60 seconds
    response = requests.post(
    url=f"{secret['LLM_API_BASE']}/chat/completions",
    headers={
        "Authorization": f"Bearer {secret['LLM_API_KEY']}",
        "Content-Type": "application/json"
    },
    data=json.dumps({
        "model": secret['LLM_MODEL'],
        "messages": [
        {
            "role": "user",
            "content": program_params
        }
        ]
    }),
    timeout=60
    )

    if response.status_code == 200:
        print(json.dumps({
            "answer": response.json()['choices'][0]['message']['content'],
            "tool_calls": []
        }))
    else:    
        # print in stderr the error message in json format
        print(json.dumps({
            "answer": response.text,
            "tool_calls": []
        }))
except Exception as e:
    print(json.dumps({
        "answer": str(e),
        "tool_calls": []
    }))