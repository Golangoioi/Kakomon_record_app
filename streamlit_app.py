import streamlit as st
import pandas as pd
import os
from typing import Optional, Dict, List
import re
from datetime import datetime
import numpy as np

# ページ設定
st.set_page_config(
    page_title="成績管理アプリ",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS for mobile responsiveness and custom charts
st.markdown("""
<style>
    .stSelectbox > div > div > div {
        max-width: 100%;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    .stNumberInput > div > div > input {
        font-size: 16px;
    }
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .progress-bar {
        background-color: #e0e0e0;
        border-radius: 10px;
        padding: 3px;
        margin: 5px 0;
        height: 25px;
    }
    .progress-bar-fill {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        border-radius: 8px;
        color: white;
        font-size: 12px;
        font-weight: bold;
        transition: width 0.3s ease;
    }
    .radar-chart {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 10px;
        padding: 20px;
        background: white;
        border-radius: 10px;
        margin: 10px 0;
        border: 1px solid #e0e0e0;
    }
    .radar-item {
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        background: #f8f9fa;
    }
    .chart-container {
        background: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border: 1px solid #e0e0e0;
    }
    .trend-chart {
        display: flex;
        align-items: end;
        height: 200px;
        padding: 20px;
        background: linear-gradient(to top, #f8f9fa 0%, #ffffff 100%);
        border-radius: 10px;
        margin: 10px 0;
        overflow-x: auto;
    }
    .trend-bar {
        min-width: 40px;
        margin: 0 5px;
        border-radius: 4px 4px 0 0;
        display: flex;
        align-items: end;
        justify-content: center;
        color: white;
        font-size: 10px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .trend-bar:hover {
        transform: scale(1.05);
    }
</style>
""", unsafe_allow_html=True)

# データファイルのパス
USERS_FILE = "users.csv"
SCHOOLS_FILE = "schools.csv"
SCORES_FILE = "test_scores.csv"

# 科目一覧
ALL_SUBJECTS = [
    "英語", "数学I・A", "数学II・B", "数学III", "国語", 
    "現代文", "古文", "漢文", "物理", "化学", "生物", 
    "地学", "日本史", "世界史", "地理", "公民", "倫理", 
    "政治経済", "現代社会", "英語リーディング", "英語リスニング",
    "情報", "小論文", "面接"
]

def safe_read_csv(filepath: str, columns: List[str]) -> pd.DataFrame:
    """CSVファイルを安全に読み込む関数。ファイルが存在しない場合は空のDataFrameを作成"""
    try:
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            # 必要な列が存在しない場合は追加
            for col in columns:
                if col not in df.columns:
                    df[col] = None
            return df
        else:
            # ファイルが存在しない場合は空のDataFrameを作成
            return pd.DataFrame(columns=columns)
    except Exception as e:
        st.error(f"ファイル読み込みエラー: {e}")
        return pd.DataFrame(columns=columns)

def safe_save_csv(df: pd.DataFrame, filepath: str) -> bool:
    """DataFrameを安全にCSVに保存する関数"""
    try:
        # 空のDataFrameでも保存可能
        df.to_csv(filepath, index=False, encoding='utf-8')
        return True
    except Exception as e:
        st.error(f"ファイル保存エラー: {e}")
        return False

def validate_email(email: str) -> bool:
    """メールアドレスの形式をチェック"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def init_session_state():
    """セッション状態を初期化"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = ""
    if 'user_name' not in st.session_state:
        st.session_state.user_name = ""

def create_progress_bar(value: float, max_value: float, label: str = "") -> str:
    """CSSベースのプログレスバーを作成"""
    try:
        percentage = min((value / max_value * 100), 100) if max_value > 0 else 0
        
        if percentage >= 80:
            color = "#4CAF50"  # 緑
        elif percentage >= 60:
            color = "#FF9800"  # オレンジ
        elif percentage >= 40:
            color = "#2196F3"  # 青
        else:
            color = "#F44336"  # 赤
        
        return f"""
        <div class="progress-bar">
            <div class="progress-bar-fill" style="width: {percentage}%; background-color: {color};">
                {label} {percentage:.1f}%
            </div>
        </div>
        """
    except Exception:
        return f"<div>{label}: エラー</div>"

def create_radar_chart_html(subjects: List[str], percentages: List[float]) -> str:
    """HTMLとCSSでレーダーチャート風の表示を作成"""
    try:
        html_content = "<div class='radar-chart'>"
        
        for subject, percentage in zip(subjects, percentages):
            if percentage >= 80:
                color = "#4CAF50"
                emoji = "🎯"
            elif percentage >= 60:
                color = "#FF9800"
                emoji = "📈"
            elif percentage >= 40:
                color = "#2196F3"
                emoji = "📊"
            else:
                color = "#F44336"
                emoji = "🔥"
            
            html_content += f"""
            <div class="radar-item" style="border-left: 4px solid {color};">
                <div style="font-size: 20px; margin-bottom: 5px;">{emoji}</div>
                <div style="font-weight: bold; margin-bottom: 5px;">{subject}</div>
                <div style="font-size: 18px; color: {color}; font-weight: bold;">{percentage:.1f}%</div>
            </div>
            """
        
        html_content += "</div>"
        return html_content
        
    except Exception as e:
        return f"<div>チャート作成エラー: {e}</div>"

def create_trend_chart_html(test_names: List[str], percentages: List[float]) -> str:
    """HTMLとCSSで推移チャートを作成"""
    try:
        if not test_names or not percentages:
            return "<div>データがありません</div>"
        
        max_percentage = max(percentages) if percentages else 100
        
        html_content = "<div class='chart-container'>"
        html_content += "<h4 style='text-align: center; margin-bottom: 20px;'>📈 成績推移</h4>"
        html_content += "<div class='trend-chart'>"
        
        for test_name, percentage in zip(test_names, percentages):
            # 高さを計算（最大200px）
            height = (percentage / 100) * 180
            
            if percentage >= 80:
                color = "#4CAF50"
            elif percentage >= 60:
                color = "#FF9800"
            elif percentage >= 40:
                color = "#2196F3"
            else:
                color = "#F44336"
            
            html_content += f"""
            <div style="display: flex; flex-direction: column; align-items: center; margin: 0 5px;">
                <div class="trend-bar" style="
                    height: {height}px; 
                    background-color: {color};
                    writing-mode: vertical-lr;
                    text-orientation: mixed;
                    padding: 5px 2px;
                    min-width: 30px;
                ">
                    {percentage:.0f}%
                </div>
                <div style="
                    margin-top: 5px; 
                    font-size: 10px; 
                    text-align: center; 
                    transform: rotate(-45deg); 
                    white-space: nowrap;
                    width: 60px;
                ">
                    {test_name[:8]}...
                </div>
            </div>
            """
        
        html_content += "</div></div>"
        return html_content
        
    except Exception as e:
        return f"<div>グラフ作成エラー: {e}</div>"

def login_page():
    """ログイン・新規登録ページ"""
    st.title("📚 成績管理アプリ")
    st.markdown("高校生のための成績管理・志望校分析ツール")
    
    tab1, tab2 = st.tabs(["ログイン", "新規登録"])
    
    with tab1:
        st.subheader("ログイン")
        email = st.text_input("メールアドレス", key="login_email", placeholder="example@email.com")
        
        if st.button("ログイン", key="login_btn", use_container_width=True, type="primary"):
            if not email:
                st.error("メールアドレスを入力してください")
                return
            
            if not validate_email(email):
                st.error("正しいメールアドレス形式で入力してください")
                return
            
            # ユーザー情報を取得
            users_df = safe_read_csv(USERS_FILE, ["Email", "Name"])
            
            # 安全にユーザーを検索
            user_row = users_df[users_df["Email"] == email] if not users_df.empty else pd.DataFrame()
            
            if not user_row.empty:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_name = str(user_row.iloc[0]["Name"]) if "Name" in user_row.columns else "Unknown"
                st.success("ログインしました！")
                st.rerun()
            else:
                st.error("ユーザーが見つかりません")
    
    with tab2:
        st.subheader("新規登録")
        new_name = st.text_input("名前", key="register_name", placeholder="田中太郎")
        new_email = st.text_input("メールアドレス", key="register_email", placeholder="tanaka@email.com")
        
        if st.button("登録", key="register_btn", use_container_width=True, type="primary"):
            if not new_name or not new_email:
                st.error("名前とメールアドレスを入力してください")
                return
            
            if not validate_email(new_email):
                st.error("正しいメールアドレス形式で入力してください")
                return
            
            users_df = safe_read_csv(USERS_FILE, ["Email", "Name"])
            
            # メールアドレスの重複チェック（安全化）
            if not users_df.empty and new_email in users_df["Email"].values:
                st.error("このメールアドレスは既に登録されています")
                return
            
            # 新規ユーザーを追加
            new_user = pd.DataFrame({"Email": [new_email], "Name": [new_name]})
            
            if users_df.empty:
                users_df = new_user
            else:
                users_df = pd.concat([users_df, new_user], ignore_index=True)
            
            if safe_save_csv(users_df, USERS_FILE):
                st.success("登録完了！ログインしてください")
            else:
                st.error("登録に失敗しました")

def school_registration_page():
    """志望校登録/更新ページ（チェックボックス形式）"""
    st.title("🎯 志望校登録/更新")
    st.markdown("受験する志望校の情報を登録しましょう")
    
    schools_df = safe_read_csv(SCHOOLS_FILE, ["Email", "SchoolName", "Subjects", "MaxScores"])
    user_schools = schools_df[schools_df["Email"] == st.session_state.user_email] if not schools_df.empty else pd.DataFrame()
    
    # 既存の志望校一覧表示
    if not user_schools.empty:
        st.subheader("📋 登録済み志望校")
        for idx, row in user_schools.iterrows():
            school_name = str(row.get("SchoolName", "Unknown"))
            subjects = str(row.get("Subjects", ""))
            max_scores = str(row.get("MaxScores", ""))
            
            with st.expander(f"📖 {school_name}"):
                subjects_list = [s.strip() for s in subjects.split(",") if s.strip()]
                max_scores_list = [s.strip() for s in max_scores.split(",") if s.strip()]
                
                col1, col2 = st.columns(2)
                for i, (subj, max_score) in enumerate(zip(subjects_list, max_scores_list)):
                    col = col1 if i % 2 == 0 else col2
                    with col:
                        st.write(f"📚 **{subj}**: {max_score}点満点")
                
                if st.button(f"🗑️ {school_name}を削除", key=f"delete_{idx}"):
                    # 該当の学校を削除
                    schools_df_filtered = schools_df[
                        ~((schools_df["Email"] == st.session_state.user_email) & 
                          (schools_df["SchoolName"] == school_name))
                    ]
                    if safe_save_csv(schools_df_filtered, SCHOOLS_FILE):
                        st.success(f"{school_name}を削除しました")
                        st.rerun()
    
    # 新規登録フォーム
    st.subheader("➕ 新しい志望校を登録")
    
    school_name = st.text_input(
        "🏫 学校名", 
        key="school_name",
        placeholder="例：○○大学 △△学部"
    )
    
    if school_name:
        st.write("📚 **受験科目を選択してください**")
        st.caption("必要な科目にチェックを入れてください")
        
        # チェックボックスで科目選択
        selected_subjects = []
        col1, col2, col3 = st.columns(3)
        
        for i, subject in enumerate(ALL_SUBJECTS):
            col = [col1, col2, col3][i % 3]
            with col:
                if st.checkbox(subject, key=f"subject_check_{subject}"):
                    selected_subjects.append(subject)
        
        if selected_subjects:
            st.write("📊 **各科目の満点を入力してください**")
            st.caption("志望校の配点に合わせて設定してください")
            
            max_scores_dict = {}
            col1, col2 = st.columns(2)
            for i, subject in enumerate(selected_subjects):
                col = col1 if i % 2 == 0 else col2
                with col:
                    max_score = st.number_input(
                        f"📝 {subject} の満点",
                        min_value=1,
                        max_value=1000,
                        value=100,
                        step=1,
                        key=f"max_score_{subject}"
                    )
                    max_scores_dict[subject] = max_score
            
            # 保存ボタン
            if st.button("💾 志望校を保存", key="save_school", use_container_width=True, type="primary"):
                try:
                    # 既存のデータから同じ学校名のデータを削除（安全化）
                    if not schools_df.empty:
                        schools_df_filtered = schools_df[
                            ~((schools_df["Email"] == st.session_state.user_email) & 
                              (schools_df["SchoolName"] == school_name))
                        ]
                    else:
                        schools_df_filtered = pd.DataFrame(columns=["Email", "SchoolName", "Subjects", "MaxScores"])
                    
                    # 新しいデータを準備
                    subjects_str = ",".join(selected_subjects)
                    max_scores_str = ",".join([str(max_scores_dict[subj]) for subj in selected_subjects])
                    
                    # 新しいデータを追加
                    new_school = pd.DataFrame({
                        "Email": [st.session_state.user_email],
                        "SchoolName": [school_name],
                        "Subjects": [subjects_str],
                        "MaxScores": [max_scores_str]
                    })
                    
                    if schools_df_filtered.empty:
                        final_df = new_school
                    else:
                        final_df = pd.concat([schools_df_filtered, new_school], ignore_index=True)
                    
                    if safe_save_csv(final_df, SCHOOLS_FILE):
                        st.success(f"🎉 {school_name}を保存しました！")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("保存に失敗しました")
                        
                except Exception as e:
                    st.error(f"データ処理エラー: {e}")

def score_input_page():
    """得点入力ページ（志望校選択→テスト名→得点入力）"""
    st.title("📝 得点入力")
    st.markdown("テストの結果を記録して成績を管理しましょう")
    
    # 志望校データを取得
    schools_df = safe_read_csv(SCHOOLS_FILE, ["Email", "SchoolName", "Subjects", "MaxScores"])
    user_schools = schools_df[schools_df["Email"] == st.session_state.user_email] if not schools_df.empty else pd.DataFrame()
    
    if user_schools.empty:
        st.warning("⚠️ まず志望校を登録してください")
        st.info("「志望校登録/更新」ページで志望校を登録できます")
        return
    
    # 志望校選択
    school_names = user_schools["SchoolName"].tolist()
    selected_school = st.selectbox(
        "🎯 志望校を選択", 
        school_names, 
        key="selected_school_for_score",
        help="テスト結果を記録する志望校を選んでください"
    )
    
    if selected_school:
        # 選択した志望校の科目情報を取得
        school_row = user_schools[user_schools["SchoolName"] == selected_school].iloc[0]
        subjects_str = str(school_row.get("Subjects", ""))
        max_scores_str = str(school_row.get("MaxScores", ""))
        
        subjects_list = [s.strip() for s in subjects_str.split(",") if s.strip()]
        max_scores_list = [float(s.strip()) for s in max_scores_str.split(",") if s.strip()]
        
        if subjects_list:
            # テスト名入力
            st.subheader("📋 テスト情報")
            col1, col2 = st.columns(2)
            
            with col1:
                test_name = st.text_input(
                    "📝 テスト名", 
                    placeholder="例：第1回模試、期末試験、過去問2023年度",
                    key="test_name",
                    help="テストの種類や回数を入力してください"
                )
            
            with col2:
                test_date = st.date_input(
                    "📅 実施日", 
                    key="test_date",
                    help="テストを受けた日付を選択してください"
                )
            
            if test_name:
                st.subheader("📊 得点入力")
                st.caption(f"📖 {selected_school} の各科目の得点を入力してください")
                
                # 各科目の得点入力
                scores_dict = {}
                
                col1, col2 = st.columns(2)
                for i, (subject, max_score) in enumerate(zip(subjects_list, max_scores_list)):
                    col = col1 if i % 2 == 0 else col2
                    with col:
                        score = st.number_input(
                            f"📚 {subject}",
                            min_value=0.0,
                            max_value=float(max_score),
                            value=0.0,
                            step=0.5,
                            key=f"score_input_{subject}",
                            help=f"{int(max_score)}点満点"
                        )
                        scores_dict[subject] = score
                        
                        # リアルタイム得点率表示
                        percentage = (score / max_score * 100) if max_score > 0 else 0
                        st.markdown(create_progress_bar(score, max_score, f"{percentage:.1f}%"), unsafe_allow_html=True)
                
                # 合計スコア表示
                total_score = sum(scores_dict.values())
                total_max = sum(max_scores_list)
                total_percentage = (total_score / total_max * 100) if total_max > 0 else 0
                
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 総得点", f"{total_score:.1f}")
                with col2:
                    st.metric("🎯 満点", f"{total_max:.0f}")
                with col3:
                    st.metric("📈 得点率", f"{total_percentage:.1f}%")
                
                # 保存ボタン
                if st.button("💾 テスト結果を保存", key="save_test_scores", use_container_width=True, type="primary"):
                    try:
                        # テスト結果データを読み込み
                        scores_df = safe_read_csv(SCORES_FILE, [
                            "Email", "SchoolName", "TestName", "TestDate", 
                            "Subject", "Score", "MaxScore"
                        ])
                        
                        # 新しいテスト結果を追加
                        new_scores = []
                        for subject, score in scores_dict.items():
                            max_score = max_scores_list[subjects_list.index(subject)]
                            new_scores.append({
                                "Email": st.session_state.user_email,
                                "SchoolName": selected_school,
                                "TestName": test_name,
                                "TestDate": str(test_date),
                                "Subject": subject,
                                "Score": score,
                                "MaxScore": max_score
                            })
                        
                        new_scores_df = pd.DataFrame(new_scores)
                        
                        if scores_df.empty:
                            final_df = new_scores_df
                        else:
                            final_df = pd.concat([scores_df, new_scores_df], ignore_index=True)
                        
                        if safe_save_csv(final_df, SCORES_FILE):
                            st.success("🎉 テスト結果を保存しました！")
                            st.balloons()
                            
                            # 成績評価
                            if total_percentage >= 80:
                                st.success("🌟 優秀！合格圏内です！")
                            elif total_percentage >= 60:
                                st.info("📈 良好！もう少しで合格圏内です！")
                            elif total_percentage >= 40:
                                st.warning("⚡ 要努力！勉強を頑張りましょう！")
                            else:
                                st.error("🔥 危険圏！大幅な得点アップが必要です！")
                                
                        else:
                            st.error("保存に失敗しました")
                            
                    except Exception as e:
                        st.error(f"データ処理エラー: {e}")

def results_page():
    """結果表示ページ"""
    st.title("📊 成績結果・分析")
    st.markdown("あなたの成績を詳しく分析します")
    
    # データ読み込み
    scores_df = safe_read_csv(SCORES_FILE, [
        "Email", "SchoolName", "TestName", "TestDate", 
        "Subject", "Score", "MaxScore"
    ])
    
    user_scores = scores_df[scores_df["Email"] == st.session_state.user_email] if not scores_df.empty else pd.DataFrame()
    
    if user_scores.empty:
        st.warning("⚠️ まだテスト結果が登録されていません")
        st.info("「得点入力」ページでテスト結果を登録してください")
        return
    
    # 志望校選択
    schools = user_scores["SchoolName"].unique().tolist()
    selected_school = st.selectbox(
        "🎯 分析する志望校を選択", 
        schools, 
        key="result_school_select",
        help="詳細分析を行う志望校を選んでください"
    )
    
    if selected_school:
        school_data = user_scores[user_scores["SchoolName"] == selected_school]
        
        # 基本統計情報
        test_count = len(school_data["TestName"].unique())
        latest_test_data = school_data.sort_values("TestDate", ascending=False)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🏫 志望校", selected_school)
        with col2:
            st.metric("📝 テスト数", test_count)
        with col3:
            if not latest_test_data.empty:
                latest_test = latest_test_data.iloc[0]["TestName"]
                st.metric("📋 最新テスト", latest_test)
        with col4:
            # 平均得点率
            total_scores = []
            for test_name in school_data["TestName"].unique():
                test_data = school_data[school_data["TestName"] == test_name]
                total_score = test_data["Score"].sum()
                total_max = test_data["MaxScore"].sum()
                percentage = (total_score / total_max * 100) if total_max > 0 else 0
                total_scores.append(percentage)
            avg_percentage = np.mean(total_scores) if total_scores else 0
            st.metric("📈 平均得点率", f"{avg_percentage:.1f}%")
        
        # タブで表示内容を分ける
        tab1, tab2, tab3 = st.tabs(["📈 成績推移", "🎯 科目別分析", "📋 テスト一覧"])
        
        with tab1:
            st.subheader(f"📈 {selected_school} - 成績推移")
            
            # テスト別の総合得点推移
            test_summary = []
            for test_name in school_data["TestName"].unique():
                test_data = school_data[school_data["TestName"] == test_name]
                total_score = test_data["Score"].sum()
                total_max = test_data["MaxScore"].sum()
                percentage = (total_score / total_max * 100) if total_max > 0 else 0
                test_date = test_data["TestDate"].iloc[0] if not test_data.empty else ""
                
                test_summary.append({
                    "テスト名": test_name,
                    "日付": test_date,
                    "総得点": total_score,
                    "満点": total_max,
                    "得点率": percentage
                })
            
            test_summary_df = pd.DataFrame(test_summary)
            test_summary_df = test_summary_df.sort_values("日付")
            
            if not test_summary_df.empty:
                # CSS推移チャート
                test_names = test_summary_df["テスト名"].tolist()
                percentages = test_summary_df["得点率"].tolist()
                chart_html = create_trend_chart_html(test_names, percentages)
                st.markdown(chart_html, unsafe_allow_html=True)
                
                # 詳細テーブル
                st.subheader("📊 テスト結果詳細")
                display_df = test_summary_df.copy()
                display_df["総得点"] = display_df["総得点"].round(1).astype(str) + "/" + display_df["満点"].round(0).astype(str)
                display_df["得点率"] = display_df["得点率"].round(1).astype(str) + "%"
                display_df = display_df[["テスト名", "日付", "総得点", "得点率"]]
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # 成績推移の分析
                if len(percentages) >= 2:
                    trend = percentages[-1] - percentages[-2]
                    if trend > 5:
                        st.success(f"📈 前回より {trend:.1f}ポイント上昇！順調に成績が向上しています！")
                    elif trend > 0:
                        st.info(f"📊 前回より {trend:.1f}ポイント上昇。着実に改善しています。")
                    elif trend > -5:
                        st.warning(f"📉 前回より {abs(trend):.1f}ポイント低下。復習を心がけましょう。")
                    else:
                        st.error(f"⚠️ 前回より {abs(trend):.1f}ポイント大幅低下。学習方法を見直しましょう。")
        
        with tab2:
            st.subheader(f"🎯 {selected_school} - 科目別分析")
            
            # 最新テストの結果でレーダーチャート
            if not school_data.empty:
                # 日付でソートして最新を取得
                school_data_sorted = school_data.sort_values("TestDate", ascending=False)
                latest_test = school_data_sorted["TestName"].iloc[0]
                latest_data = school_data[school_data["TestName"] == latest_test]
                
                subjects = latest_data["Subject"].tolist()
                scores = latest_data["Score"].tolist()
                max_scores = latest_data["MaxScore"].tolist()
                percentages = [(score / max_score * 100) if max_score > 0 else 0 
                              for score, max_score in zip(scores, max_scores)]
                
                st.write(f"📝 **最新テスト: {latest_test}**")
                
                # HTMLレーダーチャート
                radar_html = create_radar_chart_html(subjects, percentages)
                st.markdown(radar_html, unsafe_allow_html=True)
                
                # 科目別詳細分析
                st.subheader("📚 科目別詳細分析")
                
                for i, subject in enumerate(subjects):
                    subject_data = school_data[school_data["Subject"] == subject].sort_values("TestDate")
                    
                    with st.expander(f"📖 {subject} の詳細"):
                        # 統計情報
                        scores_list = subject_data["Score"].tolist()
                        max_scores_list = subject_data["MaxScore"].tolist()
                        percentages_list = [(s / m * 100) if m > 0 else 0 for s, m in zip(scores_list, max_scores_list)]
                        
                        if len(scores_list) > 1:
                            # 簡易推移表示
                            st.write("**📈 得点推移:**")
                            trend_text = " → ".join([f"{s:.1f}" for s in scores_list])
                            st.write(trend_text)
                            
                            # 推移分析
                            trend = scores_list[-1] - scores_list[0]
                            if trend > 0:
                                st.success(f"📈 初回より {trend:.1f}点向上！")
                            elif trend == 0:
                                st.info("📊 得点は横ばいです")
                            else:
                                st.warning(f"📉 初回より {abs(trend):.1f}点低下")
                        
                        # 統計サマリー
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("平均点", f"{np.mean(scores_list):.1f}")
                        with col2:
                            st.metric("最高点", f"{max(scores_list):.1f}")
                        with col3:
                            st.metric("最低点", f"{min(scores_list):.1f}")
                        with col4:
                            st.metric("最新", f"{scores_list[-1]:.1f}")
                        
                        # おすすめアクション
                        latest_percentage = percentages[i]
                        if latest_percentage >= 80:
                            st.success("🌟 素晴らしい成績です！この調子で頑張りましょう！")
                        elif latest_percentage >= 60:
                            st.info("📈 良好な成績です。さらなる向上を目指しましょう。")
                        elif latest_percentage >= 40:
                            st.warning("⚡ 改善の余地があります。重点的に学習しましょう。")
                        else:
                            st.error("🔥 基礎から見直しが必要です。計画的な学習を心がけましょう。")
        
        with tab3:
            st.subheader(f"📋 {selected_school} - テスト一覧")
            
            # テスト結果一覧表（日付順にソート）
            test_names = school_data.sort_values("TestDate", ascending=False)["TestName"].unique()
            
            for test_name in test_names:
                with st.expander(f"📝 {test_name}"):
                    test_data = school_data[school_data["TestName"] == test_name]
                    
                    # テスト情報
                    test_date = test_data["TestDate"].iloc[0]
                    st.write(f"**📅 実施日**: {test_date}")
                    
                    # 科目別得点表
                    result_table = []
                    total_score = 0
                    total_max = 0
                    
                    for _, row in test_data.iterrows():
                        subject = row["Subject"]
                        score = float(row["Score"])
                        max_score = float(row["MaxScore"])
                        percentage = (score / max_score * 100) if max_score > 0 else 0
                        
                        result_table.append({
                            "科目": subject,
                            "得点": f"{score:.1f}",
                            "満点": f"{max_score:.0f}",
                            "得点率": f"{percentage:.1f}%"
                        })
                        
                        total_score += score
                        total_max += max_score
                    
                    # 表として表示
                    result_df = pd.DataFrame(result_table)
                    st.dataframe(result_df, use_container_width=True, hide_index=True)
                    
                    # 総合結果
                    total_percentage = (total_score / total_max * 100) if total_max > 0 else 0
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📊 総得点", f"{total_score:.1f}")
                    with col2:
                        st.metric("🎯 総満点", f"{total_max:.0f}")
                    with col3:
                        color = "normal" if total_percentage >= 70 else "inverse"
                        st.metric("📈 総合得点率", f"{total_percentage:.1f}%", delta_color=color)
                    
                    # 成績評価
                    if total_percentage >= 80:
                        st.success("🌟 素晴らしい結果です！")
                    elif total_percentage >= 60:
                        st.info("📈 良好な結果です！")
                    elif total_percentage >= 40:
                        st.warning("⚡ もう少し頑張りましょう！")
                    else:
                        st.error("🔥 更なる努力が必要です！")
                    
                    # 削除ボタン
                    st.markdown("---")
                    if st.button(f"🗑️ {test_name}を削除", key=f"delete_test_{test_name}"):
                        # 該当テストのデータを削除
                        scores_df_filtered = scores_df[
                            ~((scores_df["Email"] == st.session_state.user_email) & 
                              (scores_df["SchoolName"] == selected_school) &
                              (scores_df["TestName"] == test_name))
                        ]
                        if safe_save_csv(scores_df_filtered, SCORES_FILE):
                            st.success(f"{test_name}を削除しました")
                            st.rerun()

def main():
    """メイン関数"""
    init_session_state()
    
    # ログインチェック
    if not st.session_state.logged_in:
        login_page()
        return
    
    # サイドバー
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user_name}**さん")
        st.write(f"📧 {st.session_state.user_email}")
        st.write("---")
        
        # ページ選択
        page = st.selectbox(
            "📱 ページを選択",
            ["🎯 志望校登録/更新", "📝 得点入力", "📊 成績結果・分析"]
        )
        
        st.write("---")
        
        # 統計情報表示
        try:
            scores_df = safe_read_csv(SCORES_FILE, ["Email", "TestName", "TestDate"])
            user_scores = scores_df[scores_df["Email"] == st.session_state.user_email] if not scores_df.empty else pd.DataFrame()
            test_count = len(user_scores["TestName"].unique()) if not user_scores.empty else 0
            
            schools_df = safe_read_csv(SCHOOLS_FILE, ["Email", "SchoolName"])
            user_schools = schools_df[schools_df["Email"] == st.session_state.user_email] if not schools_df.empty else pd.DataFrame()
            school_count = len(user_schools) if not user_schools.empty else 0
            
            st.write("📈 **あなたの統計**")
            st.metric("🎯 志望校数", school_count)
            st.metric("📝 テスト数", test_count)
            
            # 最新のテスト結果があれば表示
            if not user_scores.empty:
                try:
                    latest_test_data = user_scores.sort_values("TestDate", ascending=False).head(1)
                    if not latest_test_data.empty:
                        latest_test = latest_test_data.iloc[0]["TestName"]
                        latest_date = latest_test_data.iloc[0]["TestDate"]
                        st.write(f"📋 **最新テスト**")
                        st.caption(f"{latest_test}")
                        st.caption(f"実施日: {latest_date}")
                except Exception:
                    pass
            
        except Exception:
            pass  # エラーが発生しても継続
        
        st.write("---")
        
        # クイックアクション
        st.write("⚡ **クイックアクション**")
        if st.button("➕ 志望校を登録", use_container_width=True):
            st.session_state.page = "🎯 志望校登録/更新"
        
        if st.button("📝 テスト結果入力", use_container_width=True):
            st.session_state.page = "📝 得点入力"
        
        if st.button("📊 成績を分析", use_container_width=True):
            st.session_state.page = "📊 成績結果・分析"
        
        st.write("---")
        
        # アプリ情報
        st.write("ℹ️ **アプリについて**")
        st.caption("高校生向け成績管理アプリ")
        st.caption("バージョン: 2.0")
        
        st.write("---")
        
        # ログアウトボタン
        if st.button("🚪 ログアウト", use_container_width=True, type="secondary"):
            # セッション状態をクリア（安全化）
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("ログアウトしました")
            st.rerun()
    
    # 選択されたページを表示
    if page == "🎯 志望校登録/更新":
        school_registration_page()
    elif page == "📝 得点入力":
        score_input_page()
    elif page == "📊 成績結果・分析":
        results_page()

if __name__ == "__main__":
    main()