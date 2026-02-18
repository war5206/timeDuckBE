from http import HTTPStatus
from dashscope import Application

# 工作流/智能体编排应用调用（非流式）
def workflow_application_call(
  api_key: str,
  app_id: str,
  prompt: str,
  user_todo: str,
  time_stamp: str,
  date: str,
  week: str,
  debug: bool = False
):
  try:
      biz_params = {
          "user_todo": user_todo,
          "time_stamp": time_stamp,
          "date": date,
          "week": week,
      }

      response = Application.call(
          api_key=api_key,
          app_id=app_id,
          prompt=prompt,
          biz_params=biz_params,
      )

      if response.status_code != HTTPStatus.OK:
          error_info = (
              f"request_id={response.request_id}\n"
              f"code={response.status_code}\n"
              f"message={response.message}"
          )
          if debug:
              print("[接口错误]", error_info)
          return { "type": "error", "delta": error_info }

      return { "type": "message", "delta": response.output.text }
  except Exception as e:
      error_info = f"[系统异常] {str(e)}\n"
      if debug:
          print(error_info)
      return { "type": "error", "delta": error_info }
