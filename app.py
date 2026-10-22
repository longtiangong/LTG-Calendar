import calendar
import datetime
import html  #! 新增：安全輸出月曆活動名稱
import uuid
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
        #! 新增：月曆上顯示的精簡活動名稱
        "calendar_label": "正月光明燈太歲平安年斗",
        "lunar": "1月09日",
        "solar": "2027-02-14",
        "desc": "開燈開斗日",
        "link": "https://longtiangong.github.io/homepage/Guangming.html",
    },
    {
        "name": "二月南巡進香",
        #! 新增：南巡進香為期兩日，月曆標註兩天
        "solar_end": "2027-03-14",
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
LUNAR_DAY_CN = [
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
MIN_DATE = date(1911, 1, 1)


def get_lunar_day_label(lunar_day):
  if not 1 <= lunar_day <= len(LUNAR_DAY_CN):
    raise ValueError(f"Unsupported lunar day: {lunar_day}")
  return LUNAR_DAY_CN[lunar_day - 1]


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


def escape_ics_text(value):
  """Escape text values according to the iCalendar text format."""
  return (
      str(value)
      .replace("\\", "\\\\")
      .replace("\r\n", "\n")
      .replace("\r", "\n")
      .replace("\n", "\\n")
      .replace(",", "\\,")
      .replace(";", "\\;")
  )


def generate_ics(
    event_name,
    event_date,
    description,
    url,
    event_time=None,
    reminder_days=14,
    event_end_date=None,
):
  """產生含日曆提醒的 Google 日曆匯入用 .ics 檔案內容。"""
  uid = uuid.uuid5(
      uuid.NAMESPACE_URL,
      f"longtiangong:{event_name}:{event_date}:{event_time or 'all-day'}",
  )
  stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
  event_lines = [
      "BEGIN:VEVENT",
      f"UID:{uid}@longtiangong.calendar",
      f"DTSTAMP:{stamp}",
      f"SUMMARY:{escape_ics_text(event_name)}",
      f"DESCRIPTION:{escape_ics_text(description)}"
      + (
          f"\\n報名連結: {escape_ics_text(url)}"
          if url
          else ""
      ),
  ]

  if event_time is None:
    end_date = event_end_date or event_date
    event_lines.extend(
        [
            f"DTSTART;VALUE=DATE:{event_date:%Y%m%d}",
            f"DTEND;VALUE=DATE:{end_date + datetime.timedelta(days=1):%Y%m%d}",
        ]
    )
  else:
    start_datetime = datetime.datetime.combine(event_date, event_time)
    end_datetime = start_datetime + datetime.timedelta(hours=1)
    event_lines.extend(
        [
            f"DTSTART:{start_datetime:%Y%m%dT%H%M%S}",
            f"DTEND:{end_datetime:%Y%m%dT%H%M%S}",
        ]
    )

  if reminder_days is not None:
    trigger = f"-P{reminder_days}D" if reminder_days else "PT0M"
    event_lines.extend(
        [
            "BEGIN:VALARM",
            f"TRIGGER:{trigger}",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{escape_ics_text(event_name)}",
            "END:VALARM",
        ]
    )
  event_lines.append("END:VEVENT")
  return "\r\n".join(
      [
          "BEGIN:VCALENDAR",
          "VERSION:2.0",
          "PRODID:-//LongTianGong//Calendar//ZH",
          *event_lines,
          "END:VCALENDAR",
          "",
      ]
  )


def generate_lunar_monthly_ics(year, reminder_time):
  """產生指定國曆年度農曆初一、十五的提醒日曆。"""
  event_components = []
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

  current_date = date(year, 1, 1)
  final_date = date(year, 12, 31)
  while current_date <= final_date:
    lunar_day_obj = sxtwl.fromSolar(
        current_date.year, current_date.month, current_date.day
    )
    lunar_day = lunar_day_obj.getLunarDay()
    if lunar_day in (1, 15):
      lunar_month_value = lunar_day_obj.getLunarMonth()
      lunar_month = abs(lunar_month_value)
      day_label = "初一" if lunar_day == 1 else "十五"
      event_name = (
          f"龍天宮農曆{'閏' if lunar_month_value < 0 else ''}"
          f"{month_cn[lunar_month - 1]}月{day_label}參拜提醒"
      )
      single_event_ics = generate_ics(
          event_name,
          current_date,
          "農曆初一、十五敬香祈福提醒。",
          "",
          event_time=reminder_time,
          reminder_days=0,
      )
      event_lines = single_event_ics.splitlines()
      event_start = event_lines.index("BEGIN:VEVENT")
      event_end = event_lines.index("END:VEVENT", event_start)
      event_components.append(event_lines[event_start:event_end + 1])
    current_date += datetime.timedelta(days=1)

  calendar_lines = [
      "BEGIN:VCALENDAR",
      "VERSION:2.0",
      "PRODID:-//LongTianGong//Calendar//ZH",
  ]
  for event_lines in event_components:
    calendar_lines.extend(event_lines)
  calendar_lines.extend(["END:VCALENDAR", ""])
  return "\r\n".join(calendar_lines)


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
    today = date.today()
    if "selected_solar_date" not in st.session_state:
      st.session_state.selected_solar_date = today
    selected_date = st.session_state.selected_solar_date
    st.session_state.setdefault("calendar_year", selected_date.year)
    st.session_state.setdefault("calendar_month", selected_date.month)
    # 2 保存手機月曆與結果文字的縮放倍率
    st.session_state.setdefault("calendar_text_zoom", 1.0)
    # 3 跑馬燈提醒：選中宮中活動時，於月曆正下方顯示

    date_heading, today_button = st.columns([4, 1])
    with date_heading:
      st.markdown(
          f"<h2 style='text-align:center; margin-bottom:0.5rem'>"
          f"{selected_date:%Y年%m月%d日}</h2>",
          unsafe_allow_html=True,
      )
    with today_button:
      if st.button("📅 回到今天", use_container_width=True):
        st.session_state.selected_solar_date = today
        st.session_state.calendar_year = today.year
        st.session_state.calendar_month = today.month
        st.rerun()

    with st.container(key="calendar_controls"):
      # 3 直接輸入年份，避免長下拉清單佔版面且難以快速定位
      year_col, month_col = st.columns([1, 1])
      with year_col:
        calendar_year = st.number_input(
            "選擇年份",
            min_value=1911,
            max_value=2066,
            step=1,
            format="%d",
            key="calendar_year",
            label_visibility="collapsed",
        )
      with month_col:
        available_months = list(range(1, 13))
        if st.session_state.calendar_month not in available_months:
          st.session_state.calendar_month = available_months[-1]
        calendar_month = st.selectbox(
            "選擇月份",
            options=available_months,
            format_func=lambda month: f"{month}月",
            key="calendar_month",
            label_visibility="collapsed",
        )

      # 2 手機字體縮放：提供不依賴瀏覽器手勢的放大/縮小按鈕
      zoom_out_col, zoom_in_col = st.columns([1, 1])
      with zoom_out_col:
        if st.button(
            "A−",
            key="calendar_zoom_out",
            use_container_width=True,
            disabled=st.session_state.calendar_text_zoom <= 0.7,
        ):
          st.session_state.calendar_text_zoom = max(
              0.7, round(st.session_state.calendar_text_zoom - 0.2, 1)
          )
      with zoom_in_col:
        if st.button(
            "A+",
            key="calendar_zoom_in",
            use_container_width=True,
            disabled=st.session_state.calendar_text_zoom >= 1.8,
        ):
          st.session_state.calendar_text_zoom = min(
              1.8, round(st.session_state.calendar_text_zoom + 0.2, 1)
          )
      calendar_text_zoom = st.session_state.calendar_text_zoom
      st.caption(f"文字大小：{round(calendar_text_zoom * 100)}%")

    month_weeks = calendar.Calendar(firstweekday=calendar.SUNDAY).monthdayscalendar(
        calendar_year, calendar_month
    )
    #! 新增：將年度活動日期展開為月曆查詢索引（支援多日活動）
    calendar_events_by_date = {}
    for event in LONGTIAN_EVENTS:
      event_date = datetime.datetime.strptime(
          event["solar"], "%Y-%m-%d"
      ).date()
      event_end_date = datetime.datetime.strptime(
          event.get("solar_end", event["solar"]), "%Y-%m-%d"
      ).date()
      while event_date <= event_end_date:
        calendar_events_by_date.setdefault(event_date, []).append(
            event.get("calendar_label", event["name"])
        )
        event_date += datetime.timedelta(days=1)
    #! 新增結束

    # 1 手機月曆：縮小日期格字體，並讓農曆文字完整顯示
    #! 新增：窄螢幕維持七欄月曆，避免 Streamlit 自動堆疊欄位
    st.markdown(
        f"""
        <style>
        /* # 1 手機月曆：縮小文字並讓農曆標籤完整顯示 */
        /* # 1 手機查詢結果：縮小文字並允許換行，避免內容遭截斷 */
        /* # 2 A−／A+ 縮放倍率同步套用至月曆格與查詢結果 */
        @keyframes calendar-event-scroll {{
          from {{ transform: translateX(0); }}
          to {{ transform: translateX(-50%); }}
        }}
        .st-key-calendar_event_ticker {{
          overflow: hidden;
          margin: 0.5rem 0;
          padding: 0.65rem 0;
          color: #c00;
          background: #fff3f3;
          border-radius: 0.4rem;
          font-weight: bold;
          font-size: {0.9 * calendar_text_zoom:.2f}rem;
          line-height: 1.6;
        }}
        # * 5 跑馬燈文字垂直置中，避免貼近背景邊緣而被裁切
        /* # 5 跑馬燈文字垂直置中，避免貼近背景邊緣而被裁切 */
        .st-key-calendar_event_ticker [data-testid="stMarkdownContainer"] {{
          display: flex;
          align-items: center;
          min-height: 2.6em;
        }}
        /* # *6 微調跑馬燈文字位置，避免視覺上偏低 */
        .st-key-calendar_event_ticker .event-marquee-track span {{
          position: relative;
          top: -3px;
        }}
        .st-key-calendar_event_ticker .event-marquee-track {{
          display: flex;
          align-items: center;
          width: max-content;
          min-height: 100%;
          animation: calendar-event-scroll 16s linear infinite;
        }}
        .st-key-calendar_event_ticker .event-marquee-track span {{
          flex: 0 0 auto;
          display: block;
          padding-right: 2rem;
          line-height: 1.6;
        }}
        @media (prefers-reduced-motion: reduce) {{
          .st-key-calendar_event_ticker .event-marquee-track {{
            animation: none;
          }}
        }}
        @media (max-width: 768px) {{
          .st-key-calendar_controls [data-testid="stHorizontalBlock"] {{
            flex-wrap: nowrap !important;
            gap: 0.35rem !important;
          }}
          .st-key-calendar_controls [data-testid="stColumn"] {{
            flex: 1 1 0% !important;
            width: 0 !important;
            min-width: 0 !important;
            padding: 0 !important;
          }}
          .st-key-calendar_month_grid [data-testid="stVerticalBlock"] {{
            gap: 0.12rem !important;
          }}
          .st-key-calendar_month_grid [data-testid="stHorizontalBlock"] {{
            flex-wrap: nowrap !important;
            gap: 0.08rem !important;
          }}
          .st-key-calendar_month_grid [data-testid="stColumn"] {{
            flex: 1 1 0% !important;
            width: 0 !important;
            min-width: 0 !important;
            padding: 0 !important;
          }}
          .st-key-calendar_month_grid button {{
            min-height: {1.2 * calendar_text_zoom:.2f}rem !important;
            height: {1.2 * calendar_text_zoom:.2f}rem !important;
            padding: 0 !important;
            font-size: {0.65 * calendar_text_zoom:.2f}rem !important;
            line-height: 1 !important;
          }}
          .st-key-calendar_month_grid [data-testid="stMarkdownContainer"] p {{
            margin: 0 !important;
            padding: 0 !important;
            font-size: {0.55 * calendar_text_zoom:.2f}rem !important;
            line-height: {0.75 * calendar_text_zoom:.2f}rem !important;
          }}
          .st-key-calendar_month_grid [data-testid="stMarkdownContainer"] {{
            overflow: visible;
          }}
          .st-key-calendar_month_grid [data-testid="stMarkdownContainer"] div {{
            white-space: normal;
            overflow: visible;
            overflow-wrap: anywhere;
          }}
          .st-key-calendar_month_grid .lunar-label {{
            font-size: {0.55 * calendar_text_zoom:.2f}rem !important;
            line-height: {0.75 * calendar_text_zoom:.2f}rem !important;
            overflow-wrap: normal !important;
            word-break: keep-all;
          }}
          .st-key-calendar_month_grid .event-label {{
            font-size: {0.5 * calendar_text_zoom:.2f}rem !important;
            line-height: {0.65 * calendar_text_zoom:.2f}rem !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: clip;
          }}
        }}
        @media (max-width: 768px) {{
          .st-key-calendar_results [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
            gap: 0.25rem !important;
          }}
          .st-key-calendar_results [data-testid="stColumn"] {{
            flex: 1 1 100% !important;
            width: 100% !important;
            min-width: 100% !important;
          }}
          .st-key-calendar_results [data-testid="stMetricLabel"] {{
            font-size: {0.7 * calendar_text_zoom:.2f}rem !important;
          }}
          .st-key-calendar_results [data-testid="stMetricValue"],
          .st-key-calendar_results [data-testid="stMetricValue"] p {{
            font-size: {0.85 * calendar_text_zoom:.2f}rem !important;
            line-height: {1.2 * calendar_text_zoom:.2f} !important;
            margin: 0 !important;
            white-space: normal !important;
            overflow: visible !important;
            overflow-wrap: anywhere !important;
            word-break: normal !important;
          }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="calendar_month_grid"):
      weekdays = st.columns(7)
      for column, weekday in zip(
          weekdays, ["日", "一", "二", "三", "四", "五", "六"]
      ):
        column.markdown(
            f"<div style='text-align:center;font-weight:bold'>{weekday}</div>",
            unsafe_allow_html=True,
        )

      for week in month_weeks:
        day_columns = st.columns(7)
        for column, day in zip(day_columns, week):
          if day == 0:
            continue
          solar_date = date(calendar_year, calendar_month, day)
          lunar_day_label = get_lunar_day_label(
              sxtwl.fromSolar(
                  solar_date.year, solar_date.month, solar_date.day
              ).getLunarDay()
          )
          calendar_event_labels = calendar_events_by_date.get(solar_date, [])
          with column:
            if st.button(
                str(day),
                key=f"calendar-day-{calendar_year}-{calendar_month}-{day}",
                type="primary" if solar_date == selected_date else "secondary",
                use_container_width=True,
            ):
              st.session_state.selected_solar_date = solar_date
              st.rerun()
            st.markdown(
                f"<div class='lunar-label' style='text-align:center;"
                f"font-size:0.75rem;line-height:1;margin-top:-0.25rem'>"
                f"{lunar_day_label}</div>",
                unsafe_allow_html=True,
            )
            #! 新增：在農曆日期下方以紅字顯示宮中活動
            for event_label in calendar_event_labels:
              st.markdown(
                  f"<div class='event-label' style='text-align:center;"
                  f"color:#d00;font-size:0.7rem;"
                  f"line-height:1;white-space:nowrap;overflow:hidden;"
                  f"text-overflow:clip'>{html.escape(event_label)}</div>",
                  unsafe_allow_html=True,
              )
            #! 新增結束

    # 3 選到年度活動日期時，在月曆下方顯示醒目的活動跑馬燈
    selected_calendar_events = calendar_events_by_date.get(selected_date, [])
    if selected_calendar_events:
      ticker_text = "　 🏮　✦　 ".join(selected_calendar_events)
      with st.container(key="calendar_event_ticker"):
        st.markdown(
            f"<div class='event-marquee-track'>"
            f"<span>{html.escape(ticker_text)}</span>"
            f"<span aria-hidden='true'>{html.escape(ticker_text)}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    has_birth_time = st.checkbox("是否加入生辰時辰換算？")
    birth_hour = 12
    if has_birth_time:
      birth_hour = st.number_input(
          "輸入出生小時（24小時制）",
          min_value=0,
          max_value=23,
          value=12,
          step=1,
          format="%d",
          help="請輸入 0 至 23，例如下午 3 點請輸入 15。",
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
      m_str = (
          f"閏{month_cn[abs(lunar_month)-1]}月"
          if lunar_month < 0
          else f"{month_cn[lunar_month-1]}月"
      )
      d_str = get_lunar_day_label(lunar_day)
      lunar_str = f"農曆 {lunar_year}年 {m_str}{d_str}"

      # 天干地支 (年月日干支)
      year_gz = get_ganzhi(day_obj, "year")
      month_gz = get_ganzhi(day_obj, "month")
      day_gz = get_ganzhi(day_obj, "day")
      y_gz = f"{TIANGAN[year_gz.tg]}{DIZHI[year_gz.dz]}年"
      m_gz = f"{TIANGAN[month_gz.tg]}{DIZHI[month_gz.dz]}月"
      d_gz = f"{TIANGAN[day_gz.tg]}{DIZHI[day_gz.dz]}日"

      st.success("✨ 查詢結果對照：")
      #! 新增：手機上讓日期換行並縮小字體，避免查詢結果被截斷
      # 1 手機查詢結果：將三項結果放入專屬容器，套用手機版樣式
      with st.container(key="calendar_results"):
        res_col1, res_col2, res_col3 = st.columns(3)
        with res_col1:
          st.metric("國曆日期", selected_date.strftime("%Y年%m月%d日"))
        with res_col2:
          st.metric("農曆日期", lunar_str)
        with res_col3:
          st.metric("天干地支", f"{y_gz} {m_gz} {d_gz}")
      #! 新增結束
      #! 新增：提示手機可使用雙指縮放檢視內容
      # 1 提示使用者可用雙指縮放
      st.caption("手機請使用 A−／A+ 按鈕調整文字大小。")

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
    st.info(
        "下載 .ics 後匯入 Google 日曆，並確認日曆通知已開啟；"
        "匯入後 Google 日曆會依每個活動的提醒設定自動通知。"
    )

    # 4 保留可直接匯出的農曆初一、十五提醒，預設提供 2027 年
    st.markdown("### 🌕 每月農曆初一、十五固定參拜提醒")
    st.write(
        "產生所選國曆年度的農曆初一、十五參拜行程，並可設定當日提醒時間。"
    )
    lunar_year_col, lunar_time_col = st.columns(2)
    with lunar_year_col:
      lunar_calendar_year = st.number_input(
          "產生年度",
          min_value=1911,
          max_value=2066,
          value=2027,
          step=1,
          format="%d",
          key="lunar_reminder_year",
      )
    with lunar_time_col:
      lunar_reminder_time = st.time_input(
          "初一、十五提醒時間",
          value=datetime.time(9, 0),
          key="lunar_reminder_time",
      )
    lunar_reminder_ics = generate_lunar_monthly_ics(
        lunar_calendar_year, lunar_reminder_time
    )
    st.download_button(
        label=f"📥 下載 {lunar_calendar_year} 年初一、十五提醒 (.ics)",
        data=lunar_reminder_ics,
        file_name=f"longtiangong_lunar_reminders_{lunar_calendar_year}.ics",
        mime="text/calendar",
        key="download_lunar_reminders",
    )

    st.markdown("### 🏮 龍天宮年度行事曆活動快速匯出")
    # 3 年度行事曆提醒提前天數套用至各活動匯出檔
    annual_reminder_days = st.selectbox(
        "年度活動提醒時間",
        options=[14, 7, 1, 0],
        format_func=lambda days: {
            14: "活動前 2 週",
            7: "活動前 1 週",
            1: "活動前 1 天",
            0: "活動當日",
        }[days],
        index=0,
        key="annual_reminder_days",
    )
    for ev in LONGTIAN_EVENTS:
      with st.expander(
          f"📌 {ev['name']} ({ev['lunar']} / 國曆 {ev['solar']})"
      ):
        st.write(f"**活動說明**：{ev['desc']}")
        st.markdown(f"**報名連結**：[點擊前往報名]({ev['link']})")

        # 產生 .ics 下載按鈕
        ev_date = datetime.datetime.strptime(ev["solar"], "%Y-%m-%d").date()
        ev_end_date = datetime.datetime.strptime(
            ev.get("solar_end", ev["solar"]), "%Y-%m-%d"
        ).date()
        ics_data = generate_ics(
            f"【龍天宮】{ev['name']}",
            ev_date,
            ev["desc"],
            ev["link"],
            reminder_days=annual_reminder_days,
            event_end_date=ev_end_date,
        )

        st.download_button(
            label=f"📥 下載「{ev['name']}」Google日曆提醒 (.ics)",
            data=ics_data,
            file_name=f"{ev['name']}.ics",
            mime="text/calendar",
        )

    st.markdown("---")
    st.markdown("### ➕ 新增您的個人自訂活動與提醒")
    # 3 個人活動加入開始時間與提醒，提交後的下載按鈕置於表單外
    with st.form("custom_event_form"):
      c_name = st.text_input("活動名稱", placeholder="例如：點光明燈 / 個人還願")
      c_date = st.date_input(
          "活動日期", value=date.today(), min_value=MIN_DATE
      )
      c_time = st.time_input(
          "活動時間",
          value=datetime.time(9, 0),
          key="custom_event_time",
          help="請輸入活動開始時間；行事曆事件會設定為一小時。",
      )
      c_desc = st.text_area("備註事項", placeholder="輸入想提醒自己的內容...")
      c_reminder_days = st.selectbox(
          "提醒時間",
          options=[14, 7, 1, 0],
          format_func=lambda days: {
              14: "活動前 2 週",
              7: "活動前 1 週",
              1: "活動前 1 天",
              0: "活動當日",
          }[days],
          index=0,
      )
      submitted = st.form_submit_button("產生個人日曆提醒檔")

    if submitted:
      if not c_name.strip():
        st.session_state.pop("custom_event_ics", None)
        st.error("請先輸入活動名稱，再產生日曆提醒檔。")
      else:
        st.session_state.custom_event_ics = generate_ics(
            f"【個人提醒】{c_name.strip()}",
            c_date,
            c_desc,
            "https://longtiangong.github.io/homepage/",
            event_time=c_time,
            reminder_days=c_reminder_days,
        )
        st.success("✅ 您的個人提醒檔已產生！")

    if st.session_state.get("custom_event_ics"):
      st.download_button(
          label="📥 儲存至手機/Google日曆",
          data=st.session_state.custom_event_ics,
          file_name="custom_reminder.ics",
          mime="text/calendar",
          key="download_custom_reminder",
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