import streamlit as st
import pandas as pd
import os
from typing import List
import re
from datetime import datetime
import numpy as np
# --- ▼▼▼ Google連携ライブラリ（Firestore対応） ▼▼▼ ---
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.cloud import firestore
# --- ▲▲▲ ここまで ▲▲▲ ---

# ページ設定
st.set_page_config(
    page_title="過去問成績管理appカコレコ",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS (元のコードから変更なし)
st.markdown("""
<style>
    .stSelectbox > div > div > div { max-width: 100%; }
    .stTextInput > div > div > input { font-size: 16px; }
    .stNumberInput > div > div > input { font-size: 16px; }
    .main .block-container { padding-top: 1rem; padding-bottom: 1rem; padding-left: 1rem; padding-right: 1rem; }
    @media (max-width: 768px) { .main .block-container { padding-left: 0.5rem; padding-right: 0.5rem; } }
    .metric-card { background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; }
    .progress-bar { background-color: #e0e0e0; border-radius: 10px; padding: 3px; margin: 5px 0; height: 25px; }
    .progress-bar-fill { display: flex; align-items: center; justify-content: center; height: 100%; border-radius: 8px; color: white; font-size: 12px; font-weight: bold; transition: width 0.3s ease; }
    .radar-chart { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; padding: 20px; background: white; border-radius: 10px; margin: 10px 0; border: 1px solid #e0e0e0; }
    .radar-item { text-align: center; padding: 10px; border-radius: 8px; background: #f8f9fa; }
    .chart-container { background: white; padding: 20px; border-radius: 10px; margin: 10px 0; border: 1px solid #e0e0e0; }
    .trend-chart { display: flex; align-items: end; height: 200px; padding: 20px; background: linear-gradient(to top, #f8f9fa 0%, #ffffff 100%); border-radius: 10px; margin: 10px 0; overflow-x: auto; }
    .trend-bar { min-width: 40px; margin: 0 5px; border-radius: 4px 4px 0 0; display: flex; align-items: end; justify-content: center; color: white; font-size: 10px; font-weight: bold; transition: all 0.3s ease; }
    .trend-bar:hover { transform: scale(1.05); }
</style>
""", unsafe_allow_html=True)

# 科目一覧 (元のコードから変更なし)
ALL_SUBJECTS = [
    "英語", "数学I・A", "数学II・B", "数学III", "国語", "現代文", "古文", "漢文", "物理", "化学", "生物", "地学", "日本史", "世界史", "地理", "公民", "倫理", "政治経済", "現代社会", "英語リーディング", "英語リスニング", "情報", "小論文", "面接"
]

# --- ▼▼▼ ここからがGoogle/Firebase連携のためのコード ▼▼▼ ---

def get_google_auth_flow():
    """Google認証フローを初期化"""
    if not os.path.exists('credentials.json'):
        st.error("認証ファイル `credentials.json` が見つかりません。")
        st.stop()
    return Flow.from_client_secrets_file('credentials.json', scopes=['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email', 'openid', 'https://www.googleapis.com/auth/cloud-platform'], redirect_uri=st.secrets["google_oauth"]["redirect_uri"])

def google_login_page():
    """Googleログインボタンを表示するページ"""
    st.title("📚 成績管理アプリ")
    st.markdown("高校生のための成績管理・志望校分析ツール")
    flow = get_google_auth_flow()
    authorization_url, state = flow.authorization_url()
    st.session_state['oauth_state'] = state
    st.markdown(f'<a href="{authorization_url}" target="_self" style="text-decoration:none; display:block; text-align:center; margin-top:20px;"><button style="padding:12px 20px; font-size:18px; background-color:#4285F4; color:white; border:none; border-radius:8px; cursor:pointer;">🚀 Googleアカウントでログイン</button></a>', unsafe_allow_html=True)

def process_oauth_callback():
    """OAuthコールバックを処理し、認証情報を取得"""
    flow = get_google_auth_flow()
    try:
        code = st.query_params["code"]
        state = st.query_params["state"]
        if st.session_state.get('oauth_state') != state:
            st.error("不正なリクエストです。"); return
        flow.fetch_token(code=code)
        credentials = flow.credentials
        st.session_state['credentials_dict'] = {'token': credentials.token, 'refresh_token': credentials.refresh_token, 'token_uri': credentials.token_uri, 'client_id': credentials.client_id, 'client_secret': credentials.client_secret, 'scopes': credentials.scopes}
        user_info = build('oauth2', 'v2', credentials=credentials).userinfo().get().execute()
        st.session_state['user_email'] = user_info['email']
        st.session_state['user_name'] = user_info['name']
        st.session_state['user_id'] = user_info['id'] # ユーザーを一意に識別するID
        st.session_state['logged_in'] = True
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"認証に失敗しました: {e}"); st.session_state['logged_in'] = False

class FirestoreManager:
    """ユーザーのFirestoreデータを管理するクラス"""
    def __init__(self, creds_dict, project_id, user_id):
        self.creds = Credentials.from_authorized_user_info(creds_dict)
        self.db = firestore.Client(project=project_id, credentials=self.creds)
        self.user_id = user_id

    def _delete_collection(self, coll_ref):
        docs = coll_ref.limit(100).stream()
        deleted = 0
        for doc in docs:
            doc.reference.delete()
            deleted += 1
        if deleted >= 100: self._delete_collection(coll_ref)

    def read_collection_to_df(self, collection_name: str, columns: list) -> pd.DataFrame:
        try:
            coll_ref = self.db.collection('users', self.user_id, collection_name)
            docs = coll_ref.stream()
            data = [doc.to_dict() for doc in docs]
            df = pd.DataFrame(data)
            for col in columns:
                if col not in df.columns: df[col] = None
            return df[columns] if not df.empty else pd.DataFrame(columns=columns)
        except Exception: return pd.DataFrame(columns=columns)

    def save_df_to_collection(self, df: pd.DataFrame, collection_name: str) -> bool:
        try:
            coll_ref = self.db.collection('users', self.user_id, collection_name)
            self._delete_collection(coll_ref)
            batch = self.db.batch()
            for _, row in df.iterrows():
                doc_ref = coll_ref.document()
                batch.set(doc_ref, row.to_dict())
            batch.commit()
            return True
        except Exception as e:
            st.error(f"データベース保存エラー: {e}"); return False

# --- ▲▲▲ ここまでがGoogle/Firebase連携のためのコード ▲▲▲ ---

def init_session_state():
    """セッション状態を初期化 (元のコードから変更なし)"""
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'user_email' not in st.session_state: st.session_state.user_email = ""
    if 'user_name' not in st.session_state: st.session_state.user_name = ""

# (ここから下のUIヘルパー関数、ページ関数、main関数は元のコードと同一のロジックを維持し、
# データ読み書きの部分だけをFirestoreManagerを使うように変更しています)

def create_progress_bar(value: float, max_value: float, label: str = "") -> str:
    # (元のコードから変更なし)
    try:
        percentage = min((value / max_value * 100), 100) if max_value > 0 else 0
        if percentage >= 80: color = "#4CAF50"
        elif percentage >= 60: color = "#FF9800"
        elif percentage >= 40: color = "#2196F3"
        else: color = "#F44336"
        return f"""<div class="progress-bar"><div class="progress-bar-fill" style="width: {percentage}%; background-color: {color};">{label} {percentage:.1f}%</div></div>"""
    except Exception: return f"<div>{label}: エラー</div>"

def create_radar_chart_html(subjects: List[str], percentages: List[float]) -> str:
    # (元のコードから変更なし)
    try:
        html_content = "<div class='radar-chart'>"
        for subject, percentage in zip(subjects, percentages):
            if percentage >= 80: color, emoji = "#4CAF50", "🎯"
            elif percentage >= 60: color, emoji = "#FF9800", "📈"
            elif percentage >= 40: color, emoji = "#2196F3", "📊"
            else: color, emoji = "#F44336", "🔥"
            html_content += f"""<div class="radar-item" style="border-left: 4px solid {color};"><div style="font-size: 20px; margin-bottom: 5px;">{emoji}</div><div style="font-weight: bold; margin-bottom: 5px;">{subject}</div><div style="font-size: 18px; color: {color}; font-weight: bold;">{percentage:.1f}%</div></div>"""
        return html_content + "</div>"
    except Exception as e: return f"<div>チャート作成エラー: {e}</div>"

def create_trend_chart_html(test_names: List[str], percentages: List[float]) -> str:
    # (元のコードから変更なし)
    try:
        if not test_names or not percentages: return "<div>データがありません</div>"
        html_content = "<div class='chart-container'><h4 style='text-align: center; margin-bottom: 20px;'>📈 成績推移</h4><div class='trend-chart'>"
        for test_name, percentage in zip(test_names, percentages):
            height = (percentage / 100) * 180
            if percentage >= 80: color = "#4CAF50"
            elif percentage >= 60: color = "#FF9800"
            elif percentage >= 40: color = "#2196F3"
            else: color = "#F44336"
            html_content += f"""<div style="display: flex; flex-direction: column; align-items: center; margin: 0 5px;"><div class="trend-bar" style="height: {height}px; background-color: {color}; writing-mode: vertical-lr; text-orientation: mixed; padding: 5px 2px; min-width: 30px;">{percentage:.0f}%</div><div style="margin-top: 5px; font-size: 10px; text-align: center; transform: rotate(-45deg); white-space: nowrap; width: 60px;">{test_name[:8]}...</div></div>"""
        return html_content + "</div></div>"
    except Exception as e: return f"<div>グラフ作成エラー: {e}</div>"

def school_registration_page():
    st.title("🎯 志望校登録/更新"); st.markdown("受験する志望校の情報を登録しましょう")
    firestore_manager = st.session_state.firestore_manager
    schools_df = firestore_manager.read_collection_to_df("schools", ["SchoolName", "Subjects", "MaxScores"])
    if not schools_df.empty:
        st.subheader("📋 登録済み志望校")
        for idx, row in schools_df.iterrows():
            school_name = str(row.get("SchoolName", "Unknown")); subjects = str(row.get("Subjects", "")); max_scores = str(row.get("MaxScores", ""))
            with st.expander(f"📖 {school_name}"):
                subjects_list = [s.strip() for s in subjects.split(",") if s.strip()]; max_scores_list = [s.strip() for s in max_scores.split(",") if s.strip()]
                col1, col2 = st.columns(2)
                for i, (subj, max_score) in enumerate(zip(subjects_list, max_scores_list)): (col1 if i % 2 == 0 else col2).write(f"📚 **{subj}**: {max_score}点満点")
                if st.button(f"🗑️ {school_name}を削除", key=f"delete_{idx}"):
                    schools_df_filtered = schools_df[schools_df["SchoolName"] != school_name]
                    if firestore_manager.save_df_to_collection(schools_df_filtered, "schools"): st.success(f"{school_name}を削除しました"); st.rerun()
    st.subheader("➕ 新しい志望校を登録"); school_name = st.text_input("🏫 学校名", key="school_name", placeholder="例：○○大学 △△学部")
    if school_name:
        st.write("📚 **受験科目を選択してください**"); selected_subjects = []
        cols = st.columns(3)
        for i, subject in enumerate(ALL_SUBJECTS):
            if cols[i % 3].checkbox(subject, key=f"subject_check_{subject}"): selected_subjects.append(subject)
        if selected_subjects:
            st.write("📊 **各科目の満点を入力してください**"); max_scores_dict = {}
            cols = st.columns(2)
            for i, subject in enumerate(selected_subjects): max_scores_dict[subject] = cols[i % 2].number_input(f"📝 {subject} の満点", 1, 1000, 100, 1, key=f"max_score_{subject}")
            if st.button("💾 志望校を保存", key="save_school", use_container_width=True, type="primary"):
                try:
                    current_schools_df = firestore_manager.read_collection_to_df("schools", ["SchoolName", "Subjects", "MaxScores"])
                    schools_df_filtered = current_schools_df[current_schools_df["SchoolName"] != school_name]
                    new_school = pd.DataFrame({"SchoolName": [school_name], "Subjects": [",".join(selected_subjects)], "MaxScores": [",".join(str(max_scores_dict[s]) for s in selected_subjects)]})
                    final_df = pd.concat([schools_df_filtered, new_school], ignore_index=True)
                    if firestore_manager.save_df_to_collection(final_df, "schools"): st.success(f"🎉 {school_name}を保存しました！"); st.balloons(); st.rerun()
                    else: st.error("保存に失敗しました")
                except Exception as e: st.error(f"データ処理エラー: {e}")

def score_input_page():
    st.title("📝 得点入力"); st.markdown("テストの結果を記録して成績を管理しましょう")
    firestore_manager = st.session_state.firestore_manager
    schools_df = firestore_manager.read_collection_to_df("schools", ["SchoolName", "Subjects", "MaxScores"])
    if schools_df.empty: st.warning("⚠️ まず志望校を登録してください"); st.info("「志望校登録/更新」ページで志望校を登録できます"); return
    school_names = schools_df["SchoolName"].tolist(); selected_school = st.selectbox("🎯 志望校を選択", school_names, key="selected_school_for_score")
    if selected_school:
        school_row = schools_df[schools_df["SchoolName"] == selected_school].iloc[0]
        subjects_list = [s.strip() for s in str(school_row.get("Subjects", "")).split(",") if s.strip()]; max_scores_list = [float(s.strip()) for s in str(school_row.get("MaxScores", "")).split(",") if s.strip()]
        if subjects_list:
            st.subheader("📋 テスト情報"); col1, col2 = st.columns(2)
            with col1: test_name = st.text_input("📝 テスト名", placeholder="例：第1回模試", key="test_name")
            with col2: test_date = st.date_input("📅 実施日", key="test_date")
            if test_name:
                st.subheader("📊 得点入力"); scores_dict = {}
                cols = st.columns(2)
                for i, (subject, max_score) in enumerate(zip(subjects_list, max_scores_list)):
                    with cols[i % 2]:
                        score = st.number_input(f"📚 {subject}", 0.0, float(max_score), 0.0, 0.5, key=f"score_input_{subject}", help=f"{int(max_score)}点満点")
                        scores_dict[subject] = score
                        st.markdown(create_progress_bar(score, max_score, f"{(score/max_score*100 if max_score>0 else 0):.1f}%"), unsafe_allow_html=True)
                total_score = sum(scores_dict.values()); total_max = sum(max_scores_list); total_percentage = (total_score / total_max * 100) if total_max > 0 else 0
                st.markdown("---"); col1, col2, col3 = st.columns(3)
                with col1: st.metric("📊 総得点", f"{total_score:.1f}")
                with col2: st.metric("🎯 満点", f"{total_max:.0f}")
                with col3: st.metric("📈 得点率", f"{total_percentage:.1f}%")
                if st.button("💾 テスト結果を保存", key="save_test_scores", use_container_width=True, type="primary"):
                    try:
                        scores_df = firestore_manager.read_collection_to_df("scores", ["SchoolName", "TestName", "TestDate", "Subject", "Score", "MaxScore"])
                        scores_df_filtered = scores_df[~((scores_df['SchoolName'] == selected_school) & (scores_df['TestName'] == test_name))]
                        new_scores = []
                        for subject, score in scores_dict.items(): new_scores.append({"SchoolName": selected_school, "TestName": test_name, "TestDate": str(test_date), "Subject": subject, "Score": score, "MaxScore": max_scores_list[subjects_list.index(subject)]})
                        final_df = pd.concat([scores_df_filtered, pd.DataFrame(new_scores)], ignore_index=True)
                        if firestore_manager.save_df_to_collection(final_df, "scores"):
                            st.success("🎉 テスト結果を保存しました！"); st.balloons()
                            if total_percentage >= 80: st.success("🌟 優秀！合格圏内です！")
                            elif total_percentage >= 60: st.info("📈 良好！もう少しで合格圏内です！")
                            elif total_percentage >= 40: st.warning("⚡ 要努力！勉強を頑張りましょう！")
                            else: st.error("🔥 危険圏！大幅な得点アップが必要です！")
                        else: st.error("保存に失敗しました")
                    except Exception as e: st.error(f"データ処理エラー: {e}")

def results_page():
    # (元のコードからデータ読み書き部分のみ変更)
    st.title("📊 成績結果・分析"); st.markdown("あなたの成績を詳しく分析します")
    firestore_manager = st.session_state.firestore_manager
    scores_df = firestore_manager.read_collection_to_df("scores", ["SchoolName", "TestName", "TestDate", "Subject", "Score", "MaxScore"])
    if scores_df.empty: st.warning("⚠️ まだテスト結果が登録されていません"); st.info("「得点入力」ページでテスト結果を登録してください"); return
    schools = scores_df["SchoolName"].unique().tolist(); selected_school = st.selectbox("🎯 分析する志望校を選択", schools, key="result_school_select")
    if selected_school:
        school_data = scores_df[scores_df["SchoolName"] == selected_school].copy(); school_data['Score'] = pd.to_numeric(school_data['Score'], errors='coerce'); school_data['MaxScore'] = pd.to_numeric(school_data['MaxScore'], errors='coerce')
        test_count = len(school_data["TestName"].unique()); latest_test_data = school_data.sort_values("TestDate", ascending=False)
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("🏫 志望校", selected_school)
        with col2: st.metric("📝 テスト数", test_count)
        with col3:
            if not latest_test_data.empty: st.metric("📋 最新テスト", latest_test_data.iloc[0]["TestName"])
        with col4:
            total_scores = [(g["Score"].sum()/g["MaxScore"].sum()*100) if g["MaxScore"].sum()>0 else 0 for _, g in school_data.groupby("TestName")]; avg_percentage = np.mean(total_scores) if total_scores else 0
            st.metric("📈 平均得点率", f"{avg_percentage:.1f}%")
        tab1, tab2, tab3 = st.tabs(["📈 成績推移", "🎯 科目別分析", "📋 テスト一覧"])
        with tab1:
            st.subheader(f"📈 {selected_school} - 成績推移")
            test_summary = [{"テスト名":n, "日付":g["TestDate"].iloc[0], "総得点":g["Score"].sum(), "満点":g["MaxScore"].sum(), "得点率":(g["Score"].sum()/g["MaxScore"].sum()*100) if g["MaxScore"].sum()>0 else 0} for n,g in school_data.groupby("TestName")]
            if test_summary:
                test_summary_df = pd.DataFrame(test_summary).sort_values("日付")
                st.markdown(create_trend_chart_html(test_summary_df["テスト名"].tolist(), test_summary_df["得点率"].tolist()), unsafe_allow_html=True)
                st.subheader("📊 テスト結果詳細"); display_df = test_summary_df.copy(); display_df["総得点"] = display_df["総得点"].round(1).astype(str)+"/"+display_df["満点"].round(0).astype(str); display_df["得点率"] = display_df["得点率"].round(1).astype(str)+"%"; st.dataframe(display_df[["テスト名", "日付", "総得点", "得点率"]], use_container_width=True, hide_index=True)
                if len(test_summary_df["得点率"])>=2:
                    trend = test_summary_df["得点率"].iloc[-1]-test_summary_df["得点率"].iloc[-2]
                    if trend > 5: st.success(f"📈 前回より {trend:.1f}ポイント上昇！")
                    elif trend > 0: st.info(f"📊 前回より {trend:.1f}ポイント上昇。")
                    elif trend > -5: st.warning(f"📉 前回より {abs(trend):.1f}ポイント低下。")
                    else: st.error(f"⚠️ 前回より {abs(trend):.1f}ポイント大幅低下。")
        with tab2:
            st.subheader(f"🎯 {selected_school} - 科目別分析")
            if not school_data.empty:
                latest_test = school_data.sort_values("TestDate", ascending=False)["TestName"].iloc[0]; latest_data = school_data[school_data["TestName"] == latest_test]; subjects = latest_data["Subject"].tolist(); scores = latest_data["Score"].tolist(); max_scores = latest_data["MaxScore"].tolist(); percentages = [(s/m*100) if m>0 else 0 for s,m in zip(scores,max_scores)]; st.write(f"📝 **最新テスト: {latest_test}**"); st.markdown(create_radar_chart_html(subjects, percentages), unsafe_allow_html=True)
                st.subheader("📚 科目別詳細分析")
                for i, subject in enumerate(subjects):
                    with st.expander(f"📖 {subject} の詳細"):
                        subject_data = school_data[school_data["Subject"] == subject].sort_values("TestDate"); scores_list = subject_data["Score"].tolist()
                        if len(scores_list)>1:
                            st.write("**📈 得点推移:**"); st.write(" → ".join([f"{s:.1f}" for s in scores_list])); trend = scores_list[-1]-scores_list[0]
                            if trend > 0: st.success(f"📈 初回より {trend:.1f}点向上！")
                            elif trend == 0: st.info("📊 得点は横ばいです")
                            else: st.warning(f"📉 初回より {abs(trend):.1f}点低下")
                        c1,c2,c3,c4 = st.columns(4); c1.metric("平均点",f"{np.mean(scores_list):.1f}"); c2.metric("最高点",f"{max(scores_list):.1f}"); c3.metric("最低点",f"{min(scores_list):.1f}"); c4.metric("最新",f"{scores_list[-1]:.1f}")
                        if percentages[i]>=80: st.success("🌟 素晴らしい成績です！")
                        elif percentages[i]>=60: st.info("📈 良好な成績です。")
                        elif percentages[i]>=40: st.warning("⚡ 改善の余地があります。")
                        else: st.error("🔥 基礎から見直しが必要です。")
        with tab3:
            st.subheader(f"📋 {selected_school} - テスト一覧")
            for test_name in school_data.sort_values("TestDate", ascending=False)["TestName"].unique():
                with st.expander(f"📝 {test_name}"):
                    test_data = school_data[school_data["TestName"] == test_name]; st.write(f"**📅 実施日**: {test_data['TestDate'].iloc[0]}")
                    result_table = [{"科目":r["Subject"],"得点":f"{r['Score']:.1f}","満点":f"{r['MaxScore']:.0f}","得点率":f"{(r['Score']/r['MaxScore']*100 if r['MaxScore']>0 else 0):.1f}%"} for _,r in test_data.iterrows()]; st.dataframe(pd.DataFrame(result_table), use_container_width=True, hide_index=True)
                    total_score = test_data['Score'].sum(); total_max = test_data['MaxScore'].sum(); total_percentage = (total_score/total_max*100) if total_max>0 else 0
                    c1,c2,c3=st.columns(3); c1.metric("📊 総得点",f"{total_score:.1f}"); c2.metric("🎯 総満点",f"{total_max:.0f}"); c3.metric("📈 総合得点率",f"{total_percentage:.1f}%")
                    st.markdown("---")
                    if st.button(f"🗑️ {test_name}を削除", key=f"delete_test_{test_name}"):
                        all_scores_df = firestore_manager.read_collection_to_df("scores", ["SchoolName", "TestName", "TestDate", "Subject", "Score", "MaxScore"])
                        scores_df_filtered = all_scores_df[~((all_scores_df["SchoolName"] == selected_school) & (all_scores_df["TestName"] == test_name))]
                        if firestore_manager.save_df_to_collection(scores_df_filtered, "scores"): st.success(f"{test_name}を削除しました"); st.rerun()

def main():
    init_session_state()
    if "code" in st.query_params and not st.session_state.get('logged_in', False): process_oauth_callback()
    if not st.session_state.get('logged_in', False): google_login_page(); return
    if 'firestore_manager' not in st.session_state: st.session_state.firestore_manager = FirestoreManager(st.session_state['credentials_dict'], st.secrets["gcp"]["project_id"], st.session_state['user_id'])
    
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user_name}**さん"); st.write(f"📧 {st.session_state.user_email}"); st.write("---")
        page = st.selectbox("📱 ページを選択", ["🎯 志望校登録/更新", "📝 得点入力", "📊 成績結果・分析"])
        st.write("---")
        try:
            firestore_manager = st.session_state.firestore_manager
            scores_df = firestore_manager.read_collection_to_df("scores", ["TestName", "TestDate"])
            schools_df = firestore_manager.read_collection_to_df("schools", ["SchoolName"])
            st.write("📈 **あなたの統計**"); st.metric("🎯 志望校数", len(schools_df)); st.metric("📝 テスト数", len(scores_df["TestName"].unique()))
            if not scores_df.empty:
                latest_test = scores_df.sort_values("TestDate", ascending=False).iloc[0]
                st.write(f"📋 **最新テスト**"); st.caption(f"{latest_test['TestName']}"); st.caption(f"実施日: {latest_test['TestDate']}")
        except Exception: pass
        st.write("---"); st.write("⚡ **クイックアクション**")
        if st.button("➕ 志望校を登録", use_container_width=True): st.session_state.page = "🎯 志望校登録/更新"
        if st.button("📝 テスト結果入力", use_container_width=True): st.session_state.page = "📝 得点入力"
        if st.button("📊 成績を分析", use_container_width=True): st.session_state.page = "📊 成績結果・分析"
        st.write("---"); st.write("ℹ️ **アプリについて**"); st.caption("高校生向け成績管理アプリ"); st.caption("バージョン: 3.0 Firebase Edition")
        st.write("---")
        if st.button("🚪 ログアウト", use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.success("ログアウトしました"); st.rerun()
    
    if page == "🎯 志望校登録/更新": school_registration_page()
    elif page == "📝 得点入力": score_input_page()
    elif page == "📊 成績結果・分析": results_page()

if __name__ == "__main__":
    main()

