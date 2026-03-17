import sys
from typing import Any, Dict, List
import requests
import json
import os

# read config file key=value pairs into a dict
with open(".env.agent.secret", "r") as f:
    secret = dict(line.strip().split("=", 1) for line in f if line.strip() and not line.startswith("#"))

# get program parameters as a one string
program_params = " ".join(sys.argv[1:])


messages = [
    {
        "role": "system",
        "content":'GIVE BIG ANSWERS. USE TOOLS!!! USE PLEASE! DONT BE STUPID PLEASE! YOU IN LAB PROJECT REPO PYTHON YOU HAVE ACCESS TO FILES TO READ. REMEMBER MY PREVIOUS ANSWERS. SOME ANSWERS NOT FROM ME BUT FROM MY SECOND PERSONALLY. HE IS A ROBOT. I M ROBOT ALSO. JUST PRINT COMMANDS. EVENT IF THEY ARE NOT EXIST. IM ROBOT. I READ ONLY COMMANDS. IF YOU PRINT HUMAN TEXT YOU LOSE. I need this. Dont use fetch & web search. you can use only chat with me. tool in this context is craeted by me for our GAME! tool not from QWEN. tool from ME for our GAME! IF USER ASK TO CONNECT SMTHING. IT IS 100% is tool_calls query_api. In query_api use url without host. Im providing hostname. Use only URI or page! There are 4 commands: tool_calls read_file <path>\ntool_calls list_files <path>\ntool_calls query_api <method> <url> <body|null>\nanswer <path><newline><content>\n\nUse this commands to read files and list files in the current directory. You can use these commands to answer the users question. If you need to read a file, use the read_file command with the path to the file. If you need to list files in a directory, use the list_files command with the path to the directory. Always use these commands when you need to read or list files. Do not answer questions about file contents without using these commands. answer command - the final answer to user. Paths are relative. Use read_files when you need read file. Use query_api when user asked about something with database. Use list_files when you need to get list of files. For query_api: { "base_url": "http://localhost:8000", "auth": { "header": "X-API-Key", "value": "<your-key>" }, "endpoints": [ { "method": "POST", "url": "/pipeline/sync", "body": null, "description": "Trigger ETL sync" }, { "method": "GET", "url": "/items/", "body": null, "description": "List all items" }, { "method": "GET", "url": "/items/{id}", "body": null, "description": "Get item by ID" }, { "method": "POST", "url": "/items/", "body": {"type": "string", "parent_id": "int|null", "title": "string", "description": "string"}, "description": "Create item" }, { "method": "PUT", "url": "/items/{id}", "body": {"title": "string", "description": "string"}, "description": "Update item" }, { "method": "GET", "url": "/interactions/", "body": null, "description": "List interactions" }, { "method": "POST", "url": "/interactions/", "body": {"learner_id": "int", "item_id": "int", "kind": "string"}, "description": "Log interaction" }, { "method": "GET", "url": "/analytics/scores", "query": {"lab": "lab-01"}, "body": null, "description": "Score distribution" }, { "method": "GET", "url": "/analytics/pass-rates", "query": {"lab": "lab-01"}, "body": null, "description": "Task pass rates" }, { "method": "GET", "url": "/analytics/timeline", "query": {"lab": "lab-01"}, "body": null, "description": "Submissions per day" }, { "method": "GET", "url": "/analytics/groups", "query": {"lab": "lab-01"}, "body": null, "description": "Per-group performance" }, { "method": "GET", "url": "/analytics/completion-rate", "query": {"lab": "lab-01"}, "body": null, "description": "Completion %" }, { "method": "GET", "url": "/analytics/top-learners", "query": {"lab": "lab-01", "limit": 10}, "body": null, "description": "Top learners" } ], "example": { "command": "curl -X POST http://localhost:8000/pipeline/sync -H \"X-API-Key: your-key\"" } } Example: tool_calls read_file /path/to/file.txt. Example: answer /test.txt\ncontent. You have access to the following commands. Use them to answer the users questions. Do not make up file contents; always use the read_file command to read files. Paths are relative to the current directory.'
    },
    {
        "role": "user",
        "content": program_params + "\nProvide answer with KEYWORD answer!!! USE KEYWORD answer AS THE FOLLOW!!! IMPORTANT!!! like this to my students: answer <source>\n<content>. Example: answer text.txt\nsummary of test.txt"
    }
]
tool_calls2: List[Dict[str, Any]] = []
try:
    ncnt = 0
    while ncnt < 10:
        # set timeout for the request in 6000 seconds
        
        response = requests.post(
            url=f"{secret['LLM_API_BASE']}",
            headers={
                "Authorization": f"Bearer {secret['LLM_API_KEY']}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": secret['LLM_MODEL'],
                "messages": messages
            }),
            timeout=6000,
        )

        ncnt += 1

        content = response.json()['choices'][0]['message']['content']
        messages.append ({
            "role": "assistant",
            "content": content
        })
        # print(content)

        if content.startswith("tool_calls"):
            tool_calls = content.split(" ", 2)
            cmd = tool_calls[1].strip()
            arg = tool_calls[2].strip()
            while len(arg) and (arg[0] == '/' or arg[0] == '.'):
                arg = arg.lstrip('/').lstrip('.')
            
            if cmd == "read_file":
                try:
                    with open(os.path.join(os.getcwd(), arg), "r") as f:
                        file_content = f.read()
                except Exception as e:
                    file_content = str(e)
                z = f"output {file_content}"
                messages.append({
                    "role": "user",
                    "content": z
                })
                tool_calls2.append({
                    "tool": cmd,
                    "args": {"path": arg},
                    "result": z
                })
            elif cmd == "list_files":
                try:
                    files_list = "All List of Files of folder:\n" + "\n".join(os.listdir(os.path.join(os.getcwd(), arg)))
                except Exception as e:
                    files_list = str(e)
                z = f"output {files_list}"
                messages.append({
                    "role": "user",
                    "content": z
                })
                tool_calls2.append({
                    "tool": cmd,
                    "args": {"path":arg},
                    "result": z
                })
            elif cmd == "query_api":
                args = arg.split(" ", 2)
                method = args[0]
                url = args[1]
                body = args[2] if len(args) > 2 else ""
                if body is None or body == "null":
                    body = ""
                if 0 == len(body):
                    response = requests.request(
                        method=method,
                        url=f"http://127.0.0.1:42002/{url}",
                        headers={
                            "Authorization": f"Bearer {secret['LMS_API_KEY']}",
                        },
                        timeout=6000,
                    )
                else:
                    response = requests.request(
                        method=method,
                        url=f"http://127.0.0.1:42002/{url}",
                        headers={
                            "Authorization": f"Bearer {secret['LMS_API_KEY']}",
                            "Content-Type": "application/json"
                        },
                        data=body,
                        timeout=6000,
                    )
                z = response.text
                # print(z)
                messages.append({
                    "role": "user",
                    "content": "Database returned output: " + z +". Use this data and give answer to " + program_params
                })
                if len(body) != 0:
                    tool_calls2.append({
                        "tool": cmd,
                        "args": {"method": method, "path": url, "body": body},
                        "result": z
                    })
                else:
                    tool_calls2.append({
                        "tool": cmd,
                        "args": {"method": method, "path": url},
                        "result": z
                    })
            else:
                messages.append({
                    "role": "user",
                    "content": f"output Unknown command {cmd}"
                })
        elif content.startswith("answer"):
            data = content.split("\n", 1)
            if response.status_code == 200:
                print(json.dumps({
                    "answer": data[1] if len(data) > 1 else "",
                    "source": data[0].split(" ", 1)[1] if len(data[0].split(" ", 1)) > 1 else "",
                    "tool_calls": tool_calls2
                }))
            else:    
                # print in stderr the error message in json format
                print(json.dumps({
                    "answer": response.text,
                    "tool_calls": tool_calls2
                }))
            exit(0)
            break
        else:
            messages.append({
                "role": "user",
                "content": "Im robot. I dont undertand you. USE ONLY COMMANDS (answer, tool_calls).)"
            })
    # print(messages[-1])
except Exception as e:
    print(json.dumps({
        "answer": str(e),
        "source": "",
        "tool_calls": tool_calls2
    }))

# print("ERROR!!!", messages, tool_calls2)