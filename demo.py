# from llm.ollama import OllamaLLM
# llm = OllamaLLM('qwen3.5:9b')
# print(llm.simple_chat('你好，一句话介绍自己'))


from tools import ReadFileTool, WriteFileTool

write = WriteFileTool()
read = ReadFileTool()

print(write.run(path="test.txt", content="hello neoclaw"))
print(read.run(path="test.txt"))