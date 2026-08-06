import json

with open(r'C:\Users\Mridhul\.gemini\antigravity\brain\4f0cdf4b-1b5d-4681-bf38-a510ac4fcdcb\.system_generated\logs\transcript_full.jsonl', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            if data.get('type') == 'USER_INPUT':
                content = data.get('content', '')
                if 'Phase H' in content:
                    start = content.find('## Part 12')
                    end = content.find('## Output Rules', start)
                    if end == -1: end = len(content)
                    print(content[start:end])
                    break
        except Exception:
            pass
