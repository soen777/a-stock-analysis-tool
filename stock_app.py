import streamlit as st
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(
    page_title="股票相关性分析",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="auto"
)

st.title("📈 A股股票相关性分析工具")
st.subheader("数据来源：AKShare | 开发：Python+Streamlit+Pandas")
st.write("输入6位A股股票代码，选择分析天数，即可查看走势对比与相关性")

col_stock1 = st.columns(1)[0]
col_stock2 = st.columns(1)[0]
col_day = st.columns(1)[0]

with col_stock1:
    code1 = st.text_input("第一只股票代码", value="600519", max_chars=6)

with col_stock2:
    code2 = st.text_input("第二只股票代码", value="000001", max_chars=6)

with col_day:
    days = st.selectbox("分析天数", options=[30, 60, 90, 180], index=1)

btn_col, _ = st.columns([6,1])
with btn_col:
    analyze_btn = st.button("🚀 开始分析", type="primary",use_container_width=True )


@st.cache_data(ttl=3600)
def get_stock_data(code, days):
    if code.startswith("60"):
        ak_code = f"{code}-SH"
    elif code.startswith(("00", "30")):
        ak_code = f"{code}-SZ"
    else:
        return None
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    try:
        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        if df.empty:
            return None
        df["日期"] = pd.to_datetime(df["日期"])
        df = df[["日期", "收盘"]].rename(columns={"收盘": code})
        df = df.set_index("日期")
        df.index = df.index.tz_localize(None)
        df = df.dropna()

        return df
    except Exception as e:
        st.warning(f"获取{code}数据失败：{str(e)}")
        return None
if analyze_btn:
    if not (code1.isdigit() and code2.isdigit() and len(code1) == 6 and len(code2) == 6):
        st.error("❌ 请输入有效的6位数字股票代码！")
        st.stop()

    with st.spinner("🔍 正在获取股票数据，请稍候..."):
        df1 = get_stock_data(code1, days)
        df2 = get_stock_data(code2, days)
    if df1 is None or df2 is None:
        st.error("❌ 股票代码错误或无交易数据，请更换代码！")
        st.stop()
    df_merge = pd.concat([df1, df2], axis=1, join="inner")
    corr = df_merge.corr().iloc[0, 1]
    if corr > 0.7:
        corr_result = "高度正相关"
    elif corr > 0.3:
        corr_result = "中等正相关"
    elif corr > -0.3:
        corr_result = "几乎不相关"
    else:
        corr_result = "负相关"
    st.subheader("📊 股价原始数据（已清洗）")
    st.dataframe(df_merge.round(2), use_container_width=True, height=300)

    st.subheader("📉 股价走势对比图")
    st.line_chart(df_merge, use_container_width=True)

    st.subheader("📈 相关性分析结果")
    corr_col1, corr_col2 = st.columns(2)
    with corr_col1:
        st.metric("相关系数", f"{corr:.2f}")
    with corr_col2:
        st.metric("相关性结论", corr_result)

    st.subheader("📋 股价统计指标")
    stats = df_merge.agg({
        code1: ["mean", "max", "min", "std"],
        code2: ["mean", "max", "min", "std"]
    })
    st.dataframe(stats.round(2), use_container_width=True)

with st.expander("ℹ️ 使用说明 & 技术栈"):
    st.write("1. 支持上证60开头、深证00/30开头A股代码")
    st.write("2. 数据自动清洗空值，按日期对齐，采用前复权价格")
    st.write("3. 技术栈：Python、Pandas、Streamlit、AKShare")
    st.write("4. 相关系数越接近1，两只股票走势越相似")