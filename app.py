# app.py
import streamlit as st

st.title("我的第一个 Python 网页应用")
st.write("✅ 用 Streamlit 免费发布，国内可访问")

name = st.text_input("请输入你的名字：")
if name:
    st.success(f"你好，{name}！发布成功啦～")

st.button("点我试试！")