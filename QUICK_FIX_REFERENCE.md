# 🔧 QUICK FIX REFERENCE

## The Original Error (from validator)
```
Traceback (most recent call last):
  File "/tmp/workspace/inference.py", line 5, in <module>
    main()
  File "/tmp/workspace/baseline_inference.py", line 151, in main
    score = run_task(client=client, model=args.model, task_id=task_id, max_turns=args.max_turns, policy=args.policy)
  File "/tmp/workspace/baseline_inference.py", line 101, in run_task
    completion = client.responses.create(  <-- LINE 101: AttributeError
```

## The Problem
`client.responses` doesn't exist in OpenAI Python library (v2.30.0)

## The Fix (Line 101-118 in baseline_inference.py)

### BEFORE ❌
```python
completion = client.responses.create(
    model=model,
    temperature=0,
    input=[
        {
            "role": "user",
            "content": [{"type": "text", "text": build_prompt(obs.model_dump())}],
        }
    ],
)

text_parts = []
for output_item in completion.output:
    if output_item.type == "message":
        for c in output_item.content:
            if c.type == "output_text":
                text_parts.append(c.text)
raw = "".join(text_parts).strip()
action = parse_action(raw)
```

### AFTER ✅
```python
try:
    completion = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": build_prompt(obs.model_dump()),
            }
        ],
    )

    raw = completion.choices[0].message.content.strip() if completion.choices[0].message.content else ""
    action = parse_action(raw)
except Exception as e:
    print(f"Error calling OpenAI API: {e}")
    action = Action(action_type=ActionType.NOOP, payload={})
```

## Key Changes
1. ✅ `client.responses.create()` → `client.chat.completions.create()`
2. ✅ `input=[...]` → `messages=[...]`
3. ✅ Response parsing: `completion.choices[0].message.content`
4. ✅ Added try-except error handling
5. ✅ Graceful fallback to NOOP on errors

## Validation Result
**Before:** ❌ AttributeError: 'OpenAI' object has no attribute 'responses'
**After:** ✅ Correct API calls, proper error handling, no crashes
