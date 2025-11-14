import json
import streamlit as st
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
from html import escape
import base64
from datetime import datetime
import re



# ===============================
# ページ設定
# ===============================
st.set_page_config(
    page_title="おじさん構文ジェネレーター",
    page_icon="📱",
    layout="centered",
)


# ===============================
# 背景画像のBase64化
# ===============================
def get_base64_of_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


img_base64 = get_base64_of_image("src/background.png")


# ===============================
# CSS（背景＋タイトル＋チャットUI）
# ===============================
st.markdown(
    f"""
<style>
/* アプリ全体の背景 */
.stApp {{
    background-image: url("data:image/png;base64,{img_base64}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}}

.block-container {{
    max-width: 820px;
    padding-top: 4rem;
    padding-bottom: 2.5rem;
}}

/* タイトル部分 */
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

/* カラーテーマ */
:root{{
  --bg:#a7ddff;
  --left:#ffffff;
  --right:#c6f5a9;
  --border:#d1d5db;
}}

/* チャット枠全体 */
.chat-wrap{{
  width:100%;
  background:#bfe5ff;
  border-radius:18px;
  box-shadow:0 8px 20px rgba(0,0,0,.08);
  overflow:hidden;
  margin-top:15px;
}}

/* ヘッダー（相手名部分） */
.chat-header{{
  height:56px;
  display:flex;
  align-items:center;
  gap:10px;
  padding:0 14px;
  background:#e6f4ff;
  border-bottom:1px solid var(--border);
  font-weight:600;
  color:#111827;
}}

/* 本文部分（スクロール領域） */
.chat-body{{
  height:420px;
  background:#9ad4ff;
  padding:12px 12px 16px;
  overflow-y:auto;
}}

/* メッセージ行 */
.msg-row{{
  display:flex;
  align-items:flex-end;   /* バブルと時刻を下揃え */
  margin:8px 0;
}}
.msg-left{{
  justify-content:flex-start;
}}
.msg-right{{
  justify-content:flex-end;
}}

/* 吹き出し */
.bubble{{
  max-width:72%;
  padding:10px 12px;
  font-size:15px;
  line-height:1.5;
  border-radius:14px;
  word-break:break-word;
  position:relative;
}}
.bubble.left{{
  background:var(--left);
  border:1px solid rgba(0,0,0,.06);
}}
.bubble.right{{
  background:var(--right);
  border:1px solid rgba(0,0,0,.05);
}}
.bubble.left:after{{
  content:"";
  position:absolute;
  left:-6px;
  bottom:4px;
  border-width:6px;
  border-style:solid;
  border-color:transparent var(--left) transparent transparent;
}}
.bubble.right:after{{
  content:"";
  position:absolute;
  right:-6px;
  bottom:4px;
  border-width:6px;
  border-style:solid;
  border-color:transparent transparent transparent var(--right);
}}

/* 既読＋時刻表示 */
.msg-info{{
  display:flex;
  flex-direction:column;
  justify-content:flex-end;
  font-size:11px;
  line-height:1.1;
  color:#4b5563;
  margin-left:6px;
  margin-right:6px;
  min-height:20px;
}}

/* 右側（自分）情報の配置 */
.msg-right .msg-info{{
  align-items:flex-end;
}}

/* 左側（おじさん）情報の配置 */
.msg-left .msg-info{{
  align-items:flex-start;
}}

/* 既読文字 */
.read-status{{
  color:#6b7280;
  font-size:10px;
}}
</style>
""",
    unsafe_allow_html=True,
)


# ===============================
# タイトル表示
# ===============================
st.markdown(
    """
<div class="title-section">
    <h1>📱 おじさん構文ジェネレーター</h1>
    <p>入力した文章を「おじさん構文」に変換します．</p>
</div>
""",
    unsafe_allow_html=True,
)



# ===============================
# モデルロード
# ===============================
@st.cache_resource
def load_model():
    model_name = "Qwen/Qwen3-8B"

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",   # ここは省略してもOK（環境に合わせて）
        device_map="auto",    # GPU使うなら付けても良い
    )

    text_gen = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
    )
    return text_gen, tokenizer


generator, tokenizer = load_model()


# ===============================
# session_state 初期化
# ===============================
if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""
if "chat_history" not in st.session_state:
    # ("user" or "ojisan", text) のタプルを積む
    st.session_state["chat_history"] = []


# ===============================
# チャットUI描画
# ===============================
with st.container():
    # チャット部分（HTML組み立て）
    chat_html = (
        '<div class="chat-wrap">'
        '<div class="chat-header"><div>＜おじさん</div></div>'
        '<div class="chat-body">'
    )

    for msg_type, msg_text, time_str in st.session_state["chat_history"]:
        safe_text = escape(msg_text).replace("\n", "<br>")

        if msg_type == "user":
            # 右側（ユーザー）
            read_html = '<span class="read-status">既読</span>'
            chat_html += (
                '<div class="msg-row msg-right">'
                f'<div class="msg-info">{read_html}<div>{time_str}</div></div>'
                f'<div class="bubble right">{safe_text}</div>'
                "</div>"
            )
        else:
            # 左側（おじさん）
            chat_html += (
                '<div class="msg-row msg-left">'
                f'<div class="bubble left">{safe_text}</div>'
                f'<div class="msg-info">{time_str}</div>'
                "</div>"
            )

    chat_html += "</div></div>"
    st.markdown(chat_html, unsafe_allow_html=True)

    # ↓↓↓ ここを書き直し ↓↓↓
    with st.form(key="input_form"):
        # 入力欄＋送信ボタン
        col1, col2 = st.columns([5, 1])
        with col1:
            text = st.text_input(
                label="",
                placeholder="テキストを入力してください．．．",
                label_visibility="collapsed",
                key="input_text",  # 入力欄専用にする
            )
        with col2:
            send_clicked = st.form_submit_button("送信")
    # ↑↑↑ ここまでフォーム部分 ↑↑↑

# ===============================
# 送信ボタンクリック時の処理
# ===============================
if send_clicked:
    # フォーム送信時点の最新の値
    text = st.session_state["input_text"]
    time_str = datetime.now().strftime("%H:%M")

    if text.strip():
        # ユーザーのメッセージを追加
        st.session_state["chat_history"].append(("user", text, time_str))
        # 入力欄だけ空に戻す（保存は chat_history が担当）
        st.session_state.pop("input_text", None)

        with st.spinner("おじさんっぽく変換中...💦"):
            # Qwen3 用の chat 形式メッセージ
            messages = [
                {
                    "role": "system",
                    "content": (
                        "あなたは日本語の文章を「おじさん構文」に短く言い換えるアシスタントです．\n"
                        "ルール：\n"
                        "・翻訳してはいけない．英語を書いてはいけない．\n"
                        "・説明や注釈を書いてはいけない．\n"
                        "・新しい内容を付け足してはいけない．\n"
                        "・ユーザー文の意味を変えてはいけない．\n"
                        "・明るく馴れ馴れしい軽いノリにする．\n"
                        "・語尾は一部カタカナにして柔らかくする（〜ネ，〜ヨ，〜ダヨ〜など）．\n"
                        "・文末や文中に絵文字を大量に入れる．(😊✨💕💦🥰など)\n"
                        "・「！！」「⁉️」などの強調記号を入れてよい．\n"
                        "・出力は変換後の文だけを 1 回だけ出力する．\n"
                    ),
                },
                {
                    "role": "user",
                    "content": text,
                },
            ]

            # Qwen3 の chat テンプレートを使ってプロンプトに変換
            prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,  # ← <think> を出したくないので OFF
            )

            # 「新しく生成するトークン数」で制御
            out = generator(
                prompt,
                max_new_tokens=64,
                do_sample=True,
                temperature=0.8,
                top_p=0.92,
                repetition_penalty=1.25,
            )[0]["generated_text"]

            # プロンプト部分を削って，生成テキストだけ取り出す
            generated = out[len(prompt):].strip()

            # 念のため最初の1行だけ採用（説明しゃべりだした場合の保険）
            converted = generated.splitlines()[0].strip()

            # 句読点を「，」「．」にそろえる簡単な後処理
            converted = (
                converted
                .replace("、", "，")
                .replace("。", "．")
            )

            # おじさんの返信を追加
            st.session_state["chat_history"].append(("ojisan", converted, time_str))

        st.rerun()