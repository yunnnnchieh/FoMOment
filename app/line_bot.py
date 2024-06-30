from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from app.firebase import get_messages, clear_messages, add_message, get_summary_count, set_summary_count
from app.config import Config

line_bot_api = LineBotApi(Config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(Config.LINE_CHANNEL_SECRET)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    group_id = event.source.group_id
    user_message = event.message.text

    if user_message.startswith("設定總結數量"):
        try:
            count = int(user_message.split(" ")[1])
            set_summary_count(group_id, count)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"總結數量已設定為 {count} 則訊息")
            )
        except ValueError:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請輸入有效的數字")
            )
        return
    
    if user_message == "立即總結":
        messages = get_messages(group_id)
        if messages:
            summary = "\n".join(messages)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=summary)
            )
            clear_messages(group_id)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="沒有要總結的訊息")
            )
        return
    
    add_message(group_id, user_message)
    
    summary_count = get_summary_count(group_id)
    messages = get_messages(group_id)
    
    if len(messages) >= summary_count:
        summary = "\n".join(messages)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=summary)
        )
        clear_messages(group_id)
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="訊息已儲存")
        )

def handle_line_event(body, signature):
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        raise ValueError("Invalid signature. Check your channel access token/channel secret.")
