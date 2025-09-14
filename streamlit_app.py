import streamlit as st
import pandas as pd
import os
from typing import Optional, Dict, List
import re
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import numpy as np

# ページ設定
st.set_page_config(
    page_title="成績管理アプリ",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS for mobile responsiveness
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

def login_page():
    """ログイン・新規登録ページ"""
    st.title("📚 成績管理アプリ")
    
    tab1, tab2 = st.tabs(["ログイン", "新規登録"])
    
    with tab1:
        st.subheader("ログイン")
        email = st.text_input("メールアドレス", key="login_email")
        
        if st.button("ログイン", key="login_btn", use_container_width=True):
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
        new_name = st.text_input("名前", key="register_name")
        new_email = st.text_input("メールアドレス", key="register_email")
        
        if st.button("登録", key="register_btn", use_container_width=True):
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
    
    schools_df = safe_read_csv(SCHOOLS_FILE, ["Email", "SchoolName", "Subjects", "MaxScores"])
    user_schools = schools_df[schools_df["Email"] == st.session_state.user_email] if not schools_df.empty else pd.DataFrame()
    
    # 既存の志望校一覧表示
    if not user_schools.empty:
        st.subheader("登録済み志望校")
        for idx, row in user_schools.iterrows():
            school_name = str(row.get("SchoolName", "Unknown"))
            subjects = str(row.get("Subjects", ""))
            max_scores = str(row.get("MaxScores", ""))
            
            with st.expander(f"📖 {school_name}"):
                subjects_list = [s.strip() for s in subjects.split(",") if s.strip()]
                max_scores_list = [s.strip() for s in max_scores.split(",") if s.strip()]
                
                for subj, max_score in zip(subjects_list, max_scores_list):
                    st.write(f"• **{subj}**: {max_score}点満点")
                
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
    st.subheader("📝 新しい志望校を登録")
    
    school_name = st.text_input("🏫 学校名", key="school_name")
    
    if school_name:
        st.write("📚 **受験科目を選択してください**")
        
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
            
            max_scores_dict = {}
            col1, col2 = st.columns(2)
            for i, subject in enumerate(selected_subjects):
                col = col1 if i % 2 == 0 else col2
                with col:
                    max_score = st.number_input(
                        f"{subject} の満点",
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
                        st.rerun()
                    else:
                        st.error("保存に失敗しました")
                        
                except Exception as e:
                    st.error(f"データ処理エラー: {e}")

def score_input_page():
    """得点入力ページ（志望校選択→テスト名→得点入力）"""
    st.title("📝 得点入力")
    
    # 志望校データを取得
    schools_df = safe_read_csv(SCHOOLS_FILE, ["Email", "SchoolName", "Subjects", "MaxScores"])
    user_schools = schools_df[schools_df["Email"] == st.session_state.user_email] if not schools_df.empty else pd.DataFrame()
    
    if user_schools.empty:
        st.warning("⚠️ まず志望校を登録してください")
        st.info("「志望校登録/更新」ページで志望校を登録できます")
        return
    
    # 志望校選択
    school_names = user_schools["SchoolName"].tolist()
    selected_school = st.selectbox("🎯 志望校を選択", school_names, key="selected_school_for_score")
    
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
            test_name = st.text_input(
                "📝 テスト名", 
                placeholder="例：第1回模試、期末試験、過去問2023年度",
                key="test_name"
            )
            
            test_date = st.date_input("📅 実施日", key="test_date")
            
            if test_name:
                st.subheader("📊 得点入力")
                
                # 各科目の得点入力
                scores_dict = {}
                
                col1, col2 = st.columns(2)
                for i, (subject, max_score) in enumerate(zip(subjects_list, max_scores_list)):
                    col = col1 if i % 2 == 0 else col2
                    with col:
                        score = st.number_input(
                            f"{subject} ({int(max_score)}点満点)",
                            min_value=0.0,
                            max_value=float(max_score),
                            value=0.0,
                            step=0.5,
                            key=f"score_input_{subject}"
                        )
                        scores_dict[subject] = score
                
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
                            
                            # 簡易結果表示
                            total_score = sum(scores_dict.values())
                            total_max = sum(max_scores_list)
                            percentage = (total_score / total_max * 100) if total_max > 0 else 0
                            
                            st.info(f"📈 **{test_name}** 総得点: {total_score:.1f}/{total_max:.1f}点 ({percentage:.1f}%)")
                            
                        else:
                            st.error("保存に失敗しました")
                            
                    except Exception as e:
                        st.error(f"データ処理エラー: {e}")

def create_radar_chart(subjects: List[str], scores: List[float], max_scores: List[float]) -> go.Figure:
    """レーダーチャートを作成"""
    try:
        # パーセンテージに変換
        percentages = [(score / max_score * 100) if max_score > 0 else 0 
                      for score, max_score in zip(scores, max_scores)]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=percentages,
            theta=subjects,
            fill='toself',
            name='得点率(%)',
            line=dict(color='rgb(0, 123, 255)', width=2),
            fillcolor='rgba(0, 123, 255, 0.3)',
            marker=dict(size=8, color='rgb(0, 123, 255)')
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    ticksuffix='%',
                    gridcolor='rgba(0,0,0,0.1)'
                ),
                angularaxis=dict(
                    gridcolor='rgba(0,0,0,0.1)'
                )
            ),
            showlegend=False,
            title="科目別得点率",
            title_x=0.5,
            height=500,
            font=dict(size=12)
        )
        
        return fig
        
    except Exception as e:
        st.error(f"レーダーチャート作成エラー: {e}")
        return None

def results_page():
    """結果表示ページ"""
    st.title("📊 成績結果・分析")
    
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
    selected_school = st.selectbox("🎯 志望校を選択", schools, key="result_school_select")
    
    if selected_school:
        school_data = user_scores[user_scores["SchoolName"] == selected_school]
        
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
                # 線グラフで推移表示
                fig = px.line(
                    test_summary_df, 
                    x="テスト名", 
                    y="得点率",
                    title="総合得点率の推移",
                    markers=True,
                    line_shape='linear'
                )
                fig.update_layout(
                    yaxis_title="得点率(%)", 
                    xaxis_title="テスト",
                    yaxis=dict(range=[0, 100]),
                    height=400,
                    font=dict(size=12)
                )
                fig.update_traces(
                    line=dict(width=3, color='#1f77b4'), 
                    marker=dict(size=10, color='#1f77b4')
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # サマリー表示
                st.subheader("📊 テスト結果サマリー")
                for _, row in test_summary_df.iterrows():
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("テスト", row["テスト名"])
                    with col2:
                        st.metric("日付", row["日付"])
                    with col3:
                        st.metric("総得点", f"{row['総得点']:.1f}/{row['満点']:.1f}")
                    with col4:
                        color = "normal" if row['得点率'] >= 70 else "inverse"
                        st.metric("得点率", f"{row['得点率']:.1f}%", delta_color=color)
                    st.write("---")
        
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
                
                st.write(f"📝 **最新テスト: {latest_test}**")
                
                # レーダーチャート
                radar_fig = create_radar_chart(subjects, scores, max_scores)
                if radar_fig:
                    st.plotly_chart(radar_fig, use_container_width=True)
                
                # 科目別詳細
                st.subheader("📚 科目別詳細")
                for subject in subjects:
                    subject_data = school_data[school_data["Subject"] == subject].sort_values("TestDate")
                    
                    with st.expander(f"📖 {subject}"):
                        if len(subject_data) > 1:
                            # 科目の推移グラフ
                            fig_subject = px.line(
                                subject_data,
                                x="TestName",
                                y="Score",
                                title=f"{subject} 得点推移",
                                markers=True
                            )
                            fig_subject.update_layout(
                                height=300,
                                yaxis_title="得点",
                                xaxis_title="テスト"
                            )
                            st.plotly_chart(fig_subject, use_container_width=True)
                        
                        # 統計情報
                        avg_score = subject_data["Score"].mean()
                        max_score_achieved = subject_data["Score"].max()
                        min_score_achieved = subject_data["Score"].min()
                        latest_score = subject_data["Score"].iloc[-1]
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("平均点", f"{avg_score:.1f}")
                        with col2:
                            st.metric("最高点", f"{max_score_achieved:.1f}")
                        with col3:
                            st.metric("最低点", f"{min_score_achieved:.1f}")
                        with col4:
                            st.metric("最新", f"{latest_score:.1f}")
        
        with tab3:
            st.subheader(f"📋 {selected_school} - テスト一覧")
            
            # テスト結果一覧表（日付順にソート）
            test_names = school_data.sort_values("TestDate", ascending=False)["TestName"].unique()
            
            for test_name in test_names:
                with st.expander(f"📝 {test_name}"):
                    test_data = school_data[school_data["TestName"] == test_name]
                    
                    # テスト情報
                    test_date = test_data["TestDate"].iloc[0]
                    st.write(f"**実施日**: {test_date}")
                    
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
                        st.metric("総得点", f"{total_score:.1f}")
                    with col2:
                        st.metric("総満点", f"{total_max:.0f}")
                    with col3:
                        color = "normal" if total_percentage >= 70 else "inverse"
                        st.metric("総合得点率", f"{total_percentage:.1f}%", delta_color=color)
                    
                    # 削除ボタン
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
            scores_df = safe_read_csv(SCORES_FILE, ["Email", "TestName"])
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
                latest_test_data = user_scores.sort_values("TestDate", ascending=False).head(1)
                if not latest_test_data.empty:
                    latest_test = latest_test_data.iloc[0]["TestName"]
                    st.write(f"📋 **最新テスト**: {latest_test}")
            
        except Exception:
            pass  # エラーが発生しても継続
        
        st.write("---")
        
        # クイックアクション
        st.write("⚡ **クイックアクション**")
        if st.button("➕ 新しい志望校", use_container_width=True):
            st.session_state.page = "🎯 志望校登録/更新"
        
        if st.button("📝 テスト結果入力", use_container_width=True):
            st.session_state.page = "📝 得点入力"
        
        st.write("---")
        
        # ログアウトボタン
        if st.button("🚪 ログアウト", use_container_width=True):
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