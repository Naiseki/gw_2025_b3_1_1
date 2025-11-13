import streamlit as st
from transformers import pipeline
from html import escape
import base64

def get_base64_of_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

img_base64 = get_base64_of_image("src/background.png")

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
     .title-section {{
     background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
     padding: 20px;
     border-radius: 10px;
     color: white;
     margin-bottom: 20px;
    }}
    .title-section h1 {{
        margin: 0;
        font-size: 28px;
    }}
    .title-section p {{
        margin: 5px 0 0 0;
        font-size: 14px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.set_page_config(page_title="おじさん構文ジェネレーター", page_icon="📱", layout="centered")
st.markdown("""
    <div class="title-section">
        <h1>📱 おじさん構文ジェネレーター</h1>
        <p>入力した文章を「おじさん構文」に変換します。</p>
    </div>
""", unsafe_allow_html=True)

# ===============================
# モデルロード（変更なし）
# ===============================
@st.cache_resource
def load_model():
    return pipeline("text-generation", model="Qwen/Qwen3-4B-Instruct-2507")

generator = load_model()

# ===============================
# session_state 初期化
# ===============================
if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []  # ← 履歴を保存するリスト

# ---- LINE風デザイン ----
st.markdown("""
<style>
:root{
  --bg:#a7ddff;
  --left:#ffffff;
  --right:#c6f5a9;
  --border:#d1d5db;
}
.block-container{ max-width:820px; padding-top:4rem; padding-bottom:2.5rem; }

.chat-wrap{
  width:100%;
  background:#bfe5ff;
  border-radius:18px;
  box-shadow:0 8px 20px rgba(0,0,0,.08);
  overflow:hidden;
  margin-top:15px;
}
.chat-header{
  height:56px;
  display:flex; align-items:center; gap:10px;
  padding:0 14px;
  background:#e6f4ff;
  border-bottom:1px solid var(--border);
  font-weight:600; color:#111827;
}
.chat-body{
  height:420px;
  background:#9ad4ff;
  padding:12px 12px 16px;
  overflow-y:auto;
}
.msg-row{ display:flex; margin:8px 0; }
.msg-left{ justify-content:flex-start; }
.msg-right{ justify-content:flex-end; }
.bubble{
  max-width:72%;
  padding:10px 12px;
  font-size:15px; line-height:1.5;
  border-radius:14px;
  position:relative;
  word-break:break-word;
}
.bubble.left{
  background:var(--left);
  border:1px solid rgba(0,0,0,.06);
}
.bubble.right{
  background:var(--right);
  border:1px solid rgba(0,0,0,.05);
}
.bubble.left:after{
  content:""; position:absolute; left:-6px; bottom:4px;
  border-width:6px; border-style:solid;
  border-color:transparent var(--left) transparent transparent;
}
.bubble.right:after{
  content:""; position:absolute; right:-6px; bottom:4px;
  border-width:6px; border-style:solid;
  border-color:transparent transparent transparent var(--right);
}
</style>
""", unsafe_allow_html=True)

# ====== チャット + 入力欄 ======
with st.container():

    # ------------------------------
    # チャット部分の描画（履歴を全表示）
    # ------------------------------
    chat_html = '<div class="chat-wrap"><div class="chat-header"><div>＜おじさん</div></div><div class="chat-body">'
    
    for msg_type, msg_text in st.session_state["chat_history"]:
        if msg_type == "user":
            chat_html += f'<div class="msg-row msg-right"><div class="bubble right">{escape(msg_text).replace(chr(10), "<br>")}</div></div>'
        else:  # ojisan
            chat_html += f'<div class="msg-row msg-left"><div class="bubble left">{escape(msg_text).replace(chr(10), "<br>")}</div></div>'
    
    chat_html += '</div></div>'
    
    st.markdown(chat_html, unsafe_allow_html=True)

    # ------------------------------
    # 下の入力欄（本物の st.text_input）
    # ------------------------------
    col1, col2 = st.columns([5,1])
    with col1:
        st.session_state["input_text"] = st.text_input(
            label="",
            value=st.session_state["input_text"],
            placeholder="テキストを入力してください．．．",
            label_visibility="collapsed"
        )
    with col2:
        send_clicked = st.button("送信")

# ====== ボタンクリック時の処理 ======
if send_clicked:
    text = st.session_state["input_text"]
    
    if text.strip():
        # ユーザーメッセージを履歴に追加
        st.session_state["chat_history"].append(("user", text))
        st.session_state["input_text"] = ""
        
        with st.spinner("おじさんっぽく変換中...💦"):
            prompt = f"次の文を、絵文字や語尾を多めに使った「おじさん構文」にしてください。出力するのは入力文をおじさん構文に変換したものだけで，それ以外の説明などは含めないこと．\n\n文：{text}\n\nおじさん構文："
            result = generator(
                prompt,
                max_length=150,
                num_return_sequences=1,
                do_sample=True,
                temperature=0.8
            )[0]['generated_text']

            converted = result.split("おじさん構文：")[-1].strip()
            # おじさんの返信を履歴に追加
            st.session_state["chat_history"].append(("ojisan", converted))

        st.rerun()