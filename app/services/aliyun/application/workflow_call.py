import json

from openai import OpenAI
from app.config import require_env


def workflow_application_call(
    prompt: str,
    debug: bool = False,
):
    try:
        workflow_api_key = require_env("WORKFLOW_API_KEY")
        base_url = require_env("WORKFLOW_BASE_URL")

        client = OpenAI(
            api_key=workflow_api_key,
            base_url=base_url,
        )

        response = client.chat.completions.create(
            # model="qwen3.5-plus",
            model="qwen3-max",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        output_text = (response.choices[0].message.content or "").strip()

        if not output_text:
            return {"type": "error", "delta": "模型返回为空"}

        try:
            parsed = json.loads(output_text)
            return {"type": "message", "delta": parsed}
        except json.JSONDecodeError:
            if debug:
                print("[解析告警] 模型返回非JSON，按文本透传")
            return {"type": "message", "delta": output_text}
    except Exception as e:
        error_info = f"[系统异常] {str(e)}\n"
        if debug:
            print(error_info)
        return {"type": "error", "delta": error_info}
