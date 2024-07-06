from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, JoinEvent, LeaveEvent
from app.firebase import get_messages, clear_messages, add_message, get_summary_count, set_summary_count, delete_group_data, check_fortune_usage
from app.gemini import summarize_with_gemini, talk_to_gemini
from app.config import Config
from app.exhibition import get_exhibition_data, filter_exhibitions, format_exhibition_info
from app.stock import get_stock_info, get_kline
from app.fortune import get_daily_fortune, create_fortune_flex_message
import threading
line_bot_api = LineBotApi(Config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(Config.LINE_CHANNEL_SECRET)
@handler.add(JoinEvent)
def handle_join(event):
    if event.source.type == 'group':
        group_id = event.source.group_id
        set_summary_count(group_id, 50)
        welcome_message = TextSendMessage(text="大家好！我是FoMOment，我可以幫大家的訊息做摘要:D\n\n我預設每50則訊息會為您做一次摘要，但您可以在群組中使用下方列出的指令進行設定：\n\n· 輸入「設定摘要訊息數 [數字]」，更改每幾則訊息要做摘要的設定。例如輸入「設定摘要訊息數 5」，我將更改成每5則訊息為您做一次摘要。\n\n· 輸入「立即摘要」，我會立即為您摘要。\n\nP.S. 輸入文字即可，不需輸入「」喔！\n\nP.P.S 我還有其他功能，歡迎加我好友了解>.0")
        line_bot_api.push_message(group_id, welcome_message)
@handler.add(LeaveEvent)
def handle_leave(event):
    if event.source.type == 'group':
        group_id = event.source.group_id
    try:
        delete_group_data(group_id)
    except Exception as e:
        print(f"Error deleting data for group {group_id}: {str(e)}")
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        if event.source.type == 'user':
            user_id = event.source.user_id
            user_message = event.message.text
            if user_message == "每日運勢":
                if check_fortune_usage(user_id):
                    fortune, message = get_daily_fortune()
                    flex_message = create_fortune_flex_message(fortune, message)
                    line_bot_api.reply_message(event.reply_token, flex_message)
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="您今天已經查看過運勢了，明天再來吧！")
                    )
                return
            elif user_message.startswith("展覽資訊_"):
                city = user_message.split("_")[1]
                exhibitions = get_exhibition_data()
                if exhibitions:
                    filtered_exhibitions = filter_exhibitions(exhibitions, city)
                    if filtered_exhibitions:
                        response = format_exhibition_info(filtered_exhibitions)
                    else:
                        response = f"抱歉，目前沒有找到{city}的展覽資訊。請確保城市名稱正確，例如：臺北、臺中、高雄等。"
                else:
                    response = "抱歉，無法獲取展覽資訊。請稍後再試。"

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=response)
                )
                return
            elif user_message.startswith("股票_"):
                stock_code = user_message.split("_")[1]
                stock_info = get_stock_info(stock_code)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=stock_info)
                )
                return
            elif user_message.startswith("我需要聊聊"):
                message = user_message[6:].strip()
                reply = talk_to_gemini(message)
                
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply)
                )
                return
        elif event.source.type == 'group':
            group_id = event.source.group_id
            user_message = event.message.text
        user_profile = line_bot_api.get_group_member_profile(group_id, event.source.user_id)
        user_name = user_profile.display_name
        if user_message.startswith("設定摘要訊息數"):
            try:
                count = int(user_message.split(" ")[1])
                set_summary_count(group_id, count)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"好的！每經過 {count} 則訊息會整理摘要給您")
                )
            except (ValueError, IndexError):
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="請輸入有效的數字，例如：設定摘要訊息數 5")
                )
            return

        if user_message == "立即摘要":
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="正在整理訊息，請稍候...")
            )
            
            def process_summary():
                messages = get_messages(group_id)
                if messages:
                    summary = summarize_with_gemini(messages)
                    line_bot_api.push_message(
                        event.source.group_id,
                        TextSendMessage(text=f"訊息摘要\n\n{summary}")
                    )
                    clear_messages(group_id)
                else:
                    line_bot_api.push_message(
                        event.source.group_id,
                        TextSendMessage(text="沒有新訊息")
                    )
            
            threading.Thread(target=process_summary).start()
            return
        
        add_message(group_id, user_message, user_name)
        
        summary_count = get_summary_count(group_id)
        messages = get_messages(group_id)
        
        if len(messages) >= summary_count:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="正在整理訊息，請稍候...")
            )
            
            def process_summary():
                messages = get_messages(group_id)
                if messages:
                    summary = summarize_with_gemini(messages)
                    line_bot_api.push_message(
                        event.source.group_id,
                        TextSendMessage(text=f"訊息摘要\n\n{summary}")
                    )
                    clear_messages(group_id)
                else:
                    line_bot_api.push_message(
                        event.source.group_id,
                        TextSendMessage(text="沒有新訊息")
                    )

                threading.Thread(target=process_summary).start()
                return
    except Exception as e:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"Error in handle_message: {str(e)}")
        )
def handle_line_event(body, signature):
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        raise ValueError("Invalid signature. Check your channel access token/channel secret.")