# app.py
import streamlit as st
from transformers import pipeline

st.title("📱 おじさん構文ジェネレーター")
st.write("入力した文章を“おじさん構文”に変換します。")

@st.cache_resource
def load_model():
    return pipeline("text-generation", model="Qwen/Qwen3-4B-Instruct-2507")

generator = load_model()

# 入力欄
text = st.text_area("文章を入力", "おはよう！今日も頑張ろうね！")

if st.button("おじさん化する"):
    with st.spinner("おじさんっぽく変換中...💦"):
        prompt = f"次の文を、絵文字や語尾を多めに使った“おじさん構文”にしてください。出力するのは入力文をおじさん構文に変換したものだけで，それ以外の説明などは含めないこと．\n\n文：{text}\n\nおじさん構文："
        result = generator(prompt, max_length=150, num_return_sequences=1, do_sample=True, temperature=0.8)[0]['generated_text']

        # プロンプト部分を除いて出力を整える
        converted = result.split("変換文：")[-1].strip()
        st.success(f"💬 結果:\n\n{converted}")

