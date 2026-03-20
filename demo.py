# from llm.ollama import OllamaLLM
# llm = OllamaLLM('qwen3.5:9b')
# print(llm.simple_chat('你好，一句话介绍自己'))


# from tools import ReadFileTool, WriteFileTool
#
# write = WriteFileTool()
# read = ReadFileTool()
#
# print(write.run(path="test.txt", content="hello neoclaw"))
# print(read.run(path="test.txt"))


# from tools.youtube_summary import YouTubeSummaryTool
# tool = YouTubeSummaryTool()
# result = tool.run('https://www.youtube.com/watch?v=ajFXykT9Joo&list=PLREQ8S3NPaQsSGm4w6AUmRWYZwwl9glxP')
# print(result.output)


# from llm.ollama import OllamaLLM
# from tools.youtube_summary import YouTubeSummaryTool
# import config
# llm = OllamaLLM(model=config.LLM_MODEL, base_url=config.LLM_BASE_URL)
# tool = YouTubeSummaryTool(llm=llm)
# result = tool.run('https://www.youtube.com/watch?v=ajFXykT9Joo&list=PLREQ8S3NPaQsSGm4w6AUmRWYZwwl9glxP')
# print(result.output)


from openai import OpenAI
import os

# 从环境变量中获取您的API KEY，配置方法见：https://www.volcengine.com/docs/82379/1399008
api_key = os.getenv('ARK_API_KEY')

client = OpenAI(
    base_url='https://ark.cn-beijing.volces.com/api/v3',
    api_key=api_key
)

tools = [{
    "type": "web_search",
    "max_keyword": 2,
}]

# 创建一个对话请求
response = client.responses.create(
    model="deepseek-v3-2-251201",
    input=[{"role": "user", "content": "北京的天气怎么样？"}],
    tools=tools,
)

print(response)