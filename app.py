import streamlit as st
import pandas as pd
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px

# --- Google Sheets API 認證設定 ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

if "GCP_SERVICE_ACCOUNT_JSON" in st.secrets:
    st.write("🔑 使用雲端金鑰")
    creds_dict = json.loads(st.secrets["GCP_SERVICE_ACCOUNT_JSON"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
else:
    st.write("🔑 使用本地 credentials.json")
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

client = gspread.authorize(creds)

# --- Streamlit 頁面設定 ---
st.set_page_config(page_title="Andy 的專案進度看板", page_icon="💪")
st.title('💪 Andy 的專案進度看板')

# --- 讀取 Google Sheets 分頁 ---
try:
    sheet = client.open('Andy_專案進度管理')
    sheets = [ws.title for ws in sheet.worksheets()]
except Exception as e:
    st.error(f"❌ 無法連接 Google Sheet：{e}")
    st.stop()

# --- 側邊欄：分頁選單 ---
selected_sheet = st.sidebar.selectbox('📁 選擇任務分頁', sheets)

# ✅ 現在可以安全使用 selected_sheet
st.markdown(f"### 📂 正在查看：**{selected_sheet}**")
st.write("")
st.write("")
st.markdown("Hi Wilson哥！以下是我的專案進度概覽，一起努力完成目標吧！🔥")

# --- 側邊欄：四大任務總覽 ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 🗂 任務總覽")

for sheet_name in sheets:
    try:
        ws = sheet.worksheet(sheet_name)
        data = ws.get_all_records()
        df_temp = pd.DataFrame(data)

        if not df_temp.empty and '狀態' in df_temp.columns:
            total = len(df_temp)
            completed = (df_temp['狀態'] == '已完成').sum()
            progress = completed / total if total > 0 else 0

            st.sidebar.markdown(f"**{sheet_name}**")
            st.sidebar.progress(progress)
            st.sidebar.caption(f"✅ {completed} / {total}")
        else:
            st.sidebar.markdown(f"**{sheet_name}**")
            st.sidebar.caption("⚠ 無資料或無「狀態」欄位")
    except Exception as e:
        st.sidebar.markdown(f"**{sheet_name}**")
        st.sidebar.caption(f"⚠ 錯誤：{e}")

# --- 主畫面：選中分頁詳情 ---
try:
    worksheet = sheet.worksheet(selected_sheet)
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
except Exception as e:
    st.error(f"❌ 無法讀取分頁 {selected_sheet}：{e}")
    st.stop()

if not df.empty:
    try:
        total = len(df)
        completed = (df['狀態'] == '已完成').sum()
        progress = completed / total if total > 0 else 0

        st.subheader('✅ 完成率')
        st.metric('已完成任務', f'{completed}/{total}')
        st.progress(progress)

        # 狀態分布圓餅圖
        status_count = df['狀態'].value_counts().reset_index()
        status_count.columns = ['狀態', '數量']
        fig = px.pie(status_count, values='數量', names='狀態', title='任務狀態分布')
        st.plotly_chart(fig)

        # 任務表格
        st.subheader('📋 任務清單')
        st.dataframe(df[['任務細項', '截止日', '狀態']], use_container_width=True)
    except KeyError:
        st.error('❌ Google Sheet 中找不到「狀態」欄位，請檢查欄位名稱！')
else:
    st.info('此分頁目前沒有資料。')
