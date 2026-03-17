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
        "content": "There are 3 commands: tool_calls read_file <path>\ntool_calls list_files <path>\nanswer <path><newline><content>\n\nUse this commands to read files and list files in the current directory. You can use these commands to answer the user's question. If you need to read a file, use the read_file command with the path to the file. If you need to list files in a directory, use the list_files command with the path to the directory. Always use these commands when you need to read or list files. Do not answer questions about file contents without using these commands. answer command - the final answer to user. Paths are relative. Use read_files when you need read file. User list_files when you need to get list of files. Example: tool_calls read_file /path/to/file.txt. Example: answer /test.txt\nYES SIR!"
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
        # set timeout for the request in 60 seconds
        response = requests.post(
            url=f"{secret['LLM_API_BASE']}",
            headers={
                "Authorization": f"Bearer {secret['LLM_API_KEY']}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": secret['LLM_MODEL'],
                "messages": messages,
                "stream": False
            }),
            timeout=60,
        )

        ncnt += 1

        content = response.json()['choices'][0]['message']['content'].split("\n\n<details>", 1)[0]

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
            if response.status_code == 200:
                print(json.dumps({
                    "answer": content,
                    "source": "",
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

except Exception as e:
    print(json.dumps({
        "answer": str(e),
        "source": "",
        "tool_calls": tool_calls2
    }))

print("ERROR!!!", messages, tool_calls2)