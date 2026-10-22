import datetime
from datetime import date
import streamlit as st
import sxtwl  # 用於農曆與天干地支計算

# 設定網頁標題與排版
st.set_page_config(
    page_title="龍天宮萬年曆與法會服務",
    page_icon="🏮",
    layout="wide",
)

# --- 龍天宮年度固定/丁未年(116年/2027)行事曆資料 ---
LONGTIAN_EVENTS = [
    {
        "name": "丙午年十二月祭改",
        "lunar": "12月07日",
        "solar": "2027-01-24",
        "desc": "丙午年十二正月祭改",
        "link": "https://longtiangong.github.io/homepage/Jigai.html",
    },
    {
        "name": "丁未年正月光明燈太歲平安年斗",
        "lunar": "1月09日",
        "solar": "2027-02-14",
        "desc": "開燈開斗日",
        "link": "https://longtiangong.github.io/homepage/Guangming.html",
    },
    {
        "name": "二月南巡進香",
        "lunar": "2月06日-07日",
        "solar": "2027-03-13",
        "desc": "南巡進香日（兩日）",
        "link": "https://longtiangong.github.io/homepage/Jinxiang.html",
    },
    {
        "name": "三月玄天上帝聖誕補運及補財庫",
        "lunar": "3月03日",
        "solar": "2027-04-09",
        "desc": "補運補財庫日",
        "link": "https://longtiangong.github.io/homepage/Shendanfamily.html",
    },
    {
        "name": "六月關聖帝君聖誕補運及補財庫",
        "lunar": "6月15日",
        "solar": "2027-07-18",
        "desc": "補運補財庫日",
        "link": "https://longtiangong.github.io/homepage/Shendan.html",
    },
    {
        "name": "七月中元普度大會",
        "lunar": "7月28日",
        "solar": "2027-08-29",
        "desc": "普度日",
        "link": "https://longtiangong.github.io/homepage/Pudu.html",
    },
    {
        "name": "九月北巡進香",
        "lunar": "9月01日",
        "solar": "2027-10-01",
        "desc": "北巡進香日",
        "link": "https://longtiangong.github.io/homepage/Jinxiang.html",
    },
    {
        "name": "九月法主聖君聖誕補運及補財庫",
        "lunar": "9月04日",
        "solar": "2027-10-03",
        "desc": "補運補財庫日",
        "link": "https://longtiangong.github.io/homepage/Shendan.html",
    },
]

# 天干與地支陣列
TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = [
    "子",
    "丑",
    "寅",
    "卯",
    "辰",
    "巳",
    "午",
    "未",
    "申",
    "酉",
    "戌",
    "亥",
]


def get_shichen(hour):
  """根據24小時制判斷傳統十二時辰"""
  if hour == 23 or hour == 0:
    return "子時 (23:00 - 01:00)"
  elif 1 <= hour <= 2:
    return "丑時 (01:00 - 03:00)"
  elif 3 <= hour <= 4:
    return "寅時 (03:00 - 05:00)"
  elif 5 <= hour <= 6:
    return "卯時 (05:00 - 07:00)"
  elif 7 <= hour <= 8:
    return "辰時 (07:00 - 09:00)"
  elif 9 <= hour <= 10:
    return "巳時 (09:00 - 11:00)"
  elif 11 <= hour <= 12:
    return "午時 (11:00 - 13:00)"
  elif 13 <= hour <= 14:
    return "未時 (13:00 - 15:00)"
  elif 15 <= hour <= 16:
    return "申時 (15:00 - 17:00)"
  elif 17 <= hour <= 18:
    return "酉時 (17:00 - 19:00)"
  elif 19 <= hour <= 20:
    return "戌時 (19:00 - 21:00)"
  else:
    return "亥時 (21:00 - 23:00)"


def generate_ics(event_name, event_date, description, url):
  """產生 Google 日曆匯入用的 .ics 檔案內容"""
  d_str = event_date.strftime("%Y%m%d")
  ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//LongTianGong//Calendar//ZH
BEGIN:VEVENT
SUMMARY:{event_name}
DESCRIPTION:{description}\\n報名連結: {url}
DTSTART;VALUE=DATE:{d_str}
DTEND;VALUE=DATE:{d_str}
END:VEVENT
END:VCALENDAR"""
  return ics_content


def get_ganzhi(day_obj, target):
  """相容新版/舊版 sxtwl 的干支取值 API。"""
  getter_name = {
      "year": "getYearGZ",
      "month": "getMonthGZ",
      "day": "getDayGZ",
  }.get(target)
  if not getter_name:
    raise ValueError(f"Unsupported Ganzhi target: {target}")

  getter = getattr(day_obj, getter_name, None)
  if callable(getter):
    gz = getter()
  else:
    legacy_getter = getattr(day_obj, f"{target}GZ", None)
    if callable(legacy_getter):
      gz = legacy_getter()
    else:
      raise AttributeError(f"{type(day_obj).__name__} object has no attribute '{getter_name}'")

  if hasattr(gz, "gz"):
    return gz.gz
  return gz


# --- 側邊欄導覽 ---
st.sidebar.title("🏮 龍天宮導覽選單")
app_mode = st.sidebar.radio(
    "選擇功能選項：", ["一、 萬年曆與個人提醒", "二、 龍天宮法會及進香活動"]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **提示**：本 App 可直接加入手機主畫面瀏覽，隨時查看農曆、宮中行事曆及專屬報名連結！"
)

# ==========================================
# 選項一：萬年曆與個人提醒
# ==========================================
if app_mode == "一、 萬年曆與個人提醒":
  st.title("📅 龍天宮萬年曆與時辰換算")
  st.write(
    "查詢國曆/農曆對照、天干地支、生辰時辰，並可自訂活動與設定提醒（支援匯出至 Google"
    " 日曆）。"
  )

  tab1, tab2 = st.tabs(["🔍 日期與生辰反查", "⏰ 龍天宮行事曆與個人提醒設定"])

  with tab1:
    st.subheader("1. 國曆 / 農曆 / 生辰時辰轉換")
    col1, col2 = st.columns(2)

    with col1:
      selected_date = st.date_input(
          "選擇查詢日期（國曆）", value=date.today()
      )

    with col2:
      has_birth_time = st.checkbox("是否加入生辰時辰換算？")
      birth_hour = 12
      if has_birth_time:
        birth_hour = st.slider(
            "選擇出生小時 (24小時制)", 0, 23, 12, format="%d點"
        )

    # 利用 sxtwl 庫進行曆法計算
    try:
      day_obj = sxtwl.fromSolar(
          selected_date.year, selected_date.month, selected_date.day
      )
      lunar_year = day_obj.getLunarYear()
      lunar_month = day_obj.getLunarMonth()
      lunar_day = day_obj.getLunarDay()

      # 農曆月份字串處理（支援閏月）
      month_cn = [
          "正",
          "二",
          "三",
          "四",
          "五",
          "六",
          "七",
          "八",
          "九",
          "十",
          "冬",
          "臘",
      ]
      day_cn = [
          "初一",
          "初二",
          "初三",
          "初四",
          "初五",
          "初六",
          "初七",
          "初八",
          "初九",
          "初十",
          "十一",
          "十二",
          "十三",
          "十四",
          "十五",
          "十六",
          "十七",
          "十八",
          "十九",
          "二十",
          "廿一",
          "廿二",
          "廿三",
          "廿四",
          "廿五",
          "廿六",
          "廿七",
          "廿八",
          "廿九",
          "三十",
      ]

      m_str = (
          f"閏{month_cn[abs(lunar_month)-1]}月"
          if lunar_month < 0
          else f"{month_cn[lunar_month-1]}月"
      )
      d_str = day_cn[lunar_day - 1] if 0 <= lunar_day < 30 else "初一"
      lunar_str = f"農曆 {lunar_year}年 {m_str}{d_str}"

      # 天干地支 (年月日干支)
      year_gz = get_ganzhi(day_obj, "year")
      month_gz = get_ganzhi(day_obj, "month")
      day_gz = get_ganzhi(day_obj, "day")
      y_gz = f"{TIANGAN[year_gz.tg]}{DIZHI[year_gz.dz]}年"
      m_gz = f"{TIANGAN[month_gz.tg]}{DIZHI[month_gz.dz]}月"
      d_gz = f"{TIANGAN[day_gz.tg]}{DIZHI[day_gz.dz]}日"

      st.success("✨ 查詢結果對照：")
      res_col1, res_col2, res_col3 = st.columns(3)
      with res_col1:
        st.metric("國曆日期", selected_date.strftime("%Y年%m月%d日"))
      with res_col2:
        st.metric("中國農曆", lunar_str)
      with res_col3:
        st.metric("天干地支", f"{y_gz} {m_gz} {d_gz}")

      if has_birth_time:
        st.info(
            f"🔮 生辰時辰轉換結果：**{get_shichen(birth_hour)}**（對應時間點："
            f" {birth_hour:02d}:00）"
        )

    except Exception as e:
      st.error(f"日期計算發生錯誤：{e}")

  with tab2:
    st.subheader("2. 龍天宮行事曆與個人提醒設定")
    st.write(
        "您可以檢視龍天宮年度行事曆，並透過下方工具產生 **Google 日曆提醒檔"
        " (.ics)**，或設定每月初一、十五提醒。"
    )

    # 顯示每月初一十五快速提示
    st.markdown("### 🌕 每月農曆初一、十五固定參拜提醒")
    st.write(
        "每逢農曆初一與十五，建議信眾敬香祈福。您可以手動將這兩日加入您的私人行程。"
    )

    st.markdown("### 🏮 龍天宮年度行事曆活動快速匯出")
    for ev in LONGTIAN_EVENTS:
      with st.expander(
          f"📌 {ev['name']} ({ev['lunar']} / 國曆 {ev['solar']})"
      ):
        st.write(f"**活動說明**：{ev['desc']}")
        st.markdown(f"**報名連結**：[點擊前往報名]({ev['link']})")

        # 產生 .ics 下載按鈕
        ev_date = datetime.datetime.strptime(ev["solar"], "%Y-%m-%d").date()
        ics_data = generate_ics(
            f"【龍天宮】{ev['name']}", ev_date, ev["desc"], ev["link"]
        )

        st.download_button(
            label=f"📥 下載「{ev['name']}」Google日曆提醒 (.ics)",
            data=ics_data,
            file_name=f"{ev['name']}.ics",
            mime="text/calendar",
        )

    st.markdown("---")
    st.markdown("### ➕ 新增您的個人自訂活動與提醒")
    with st.form("custom_event_form"):
      c_name = st.text_input("活動名稱", placeholder="例如：點光明燈 / 個人還願")
      c_date = st.date_input("活動日期", value=date.today())
      c_desc = st.text_area("備註事項", placeholder="輸入想提醒自己的內容...")
      submitted = st.form_submit_button("產生個人日曆提醒檔")

      if submitted:
        c_ics = generate_ics(
            f"【個人提醒】{c_name}", c_date, c_desc, "https://longtiangong.github.io/homepage/"
        )
        st.success("✅ 您的個人提醒檔已產生！")
        st.download_button(
            label="📥 儲存至手機/Google日曆",
            data=c_ics,
            file_name=f"custom_reminder.ics",
            mime="text/calendar",
        )


# ==========================================
# 選項二：龍天宮法會及進香活動
# ==========================================
elif app_mode == "二、 龍天宮法會及進香活動":
  st.title("🏮 龍天宮法會及進香活動專區")
  st.markdown("歡迎隨時查詢丁未年（民國116年 / 2027年）各項法會、點燈及進香日程。")
  st.markdown(
      "官方網站首頁：[龍天宮官方網站](https://longtiangong.github.io/homepage/)"
  )
  st.markdown("---")

  # 用卡片/表格條列展示所有活動
  events_data = [
      (
          "丙午年十二月祭改",
          "農曆十二月七日 (116年國曆1/24) 星期日",
          "丙午年十二正月祭改",
          "https://longtiangong.github.io/homepage/Jigai.html",
      ),
      (
          "丁未年正月光明燈太歲平安年斗",
          "農曆正月初九日 (國曆2/14) 星期日",
          "開燈開斗日",
          "https://longtiangong.github.io/homepage/Guangming.html",
      ),
      (
          "二月南巡進香日",
          "農曆二月初六初七兩日 (國曆3/13 & 3/14) 星期六日",
          "南巡進香日",
          "https://longtiangong.github.io/homepage/Jinxiang.html",
      ),
      (
          "三月玄天上帝聖誕補運及補財庫",
          "農曆三月初三日 (國曆4/9) 星期五",
          "補運補財庫日",
          "https://longtiangong.github.io/homepage/Shendanfamily.html",
      ),
      (
          "六月關聖帝君聖誕補運及補財庫",
          "農曆六月十五日 (國曆7/18) 星期日",
          "補運補財庫日",
          "https://longtiangong.github.io/homepage/Shendan.html",
      ),
      (
          "七月中元普度大會",
          "農曆七月廿八日 (國曆8/29) 星期日",
          "普度日",
          "https://longtiangong.github.io/homepage/Pudu.html",
      ),
      (
          "九月北巡進香日",
          "農曆九月初一日 (國曆10/1) 星期一",
          "北巡進香日",
          "https://longtiangong.github.io/homepage/Jinxiang.html",
      ),
      (
          "九月法主聖君聖誕補運及補財庫",
          "農曆九月初四日 (國曆10/3) 星期日",
          "補運補財庫日",
          "https://longtiangong.github.io/homepage/Shendan.html",
      ),
  ]

  for title, time_info, desc, link in events_data:
    with st.container():
      st.subheader(f"✨ {title}")
      st.markdown(f"🕒 **時間**：{time_info}")
      st.markdown(f"📝 **說明**：{desc}")
      st.markdown(f"👉 **線上報名**：[點擊前往報名專區]({link})")
      st.markdown("---")