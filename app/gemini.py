import google.generativeai as genai
from app.config import Config

def summarize_with_gemini(messages):
    try:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f'請為以下聊天內容做重點整理。(輸出規則：1. 使用條列式呈現2. 根據上下文判斷重要信息3. 保留核心內容，省略冗餘細節4. 回覆字數限制：原文字數的 1%5. 使用繁體中文回答6. 確保每個要點簡潔明瞭) 聊天內容：{messages}')
        return response.text
    except Exception as e:
        return f"Error: {str(e)}\n\n因為我們使用Gemini，輸入敏感字詞有可能會出錯，請見諒QQ"
    
def talk_to_gemini(messages):
    try:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f'下面為一則訊息（輸出規則：1. 請以一個朋友的角度回覆 2. 開頭請不要說嗨朋友類似的話 3. 回覆方式請不要太正式）{messages}')
        return response.text
    except Exception as e:
        return f"Error: {str(e)}\n\n我有點不理解訊息內容，又或者有較敏感的內容因此造成我無法判斷。可以在說一次嗎？或者使用正常的字眼喔"