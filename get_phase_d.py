import json

with open(r'C:\Users\Mridhul\.gemini\antigravity\brain\4f0cdf4b-1b5d-4681-bf38-a510ac4fcdcb\.system_generated\logs\transcript_full.jsonl', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            if data.get('type') == 'USER_INPUT':
                content = data.get('content', '')
                if 'Phase D' in content and '## Part 8 — Phase D' in content:
                    start = content.find('## Part 8 — Phase D')
                    end = content.find('## Part 9')
                    print(content[start:end])
                    break
        except Exception:
            pass
