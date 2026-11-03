import json

with open(r'C:\Users\dopamine\.gemini\antigravity-cli\brain\70438d07-0b94-4a55-9b01-b98de199e471\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as fp:
    for line in fp:
        obj = json.loads(line)
        idx = obj.get('step_index')
        if 1280 <= idx <= 1304:
            tc = obj.get('tool_calls')
            if tc:
                for c in tc:
                    print(f"Step {idx}: {c.get('name')} -> {c.get('args')}")
