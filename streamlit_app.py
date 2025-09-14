import streamlit as st
import pandas as pd
import os
from typing import Optional, Dict, List
import re

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
</style>
""", unsafe_allow_html=True)

# データファイルのパス
USERS_FILE = "users.csv"
SCORES_FILE = "scores.csv"
SCHOOLS_FILE = "schools.csv"

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

def score_input_page():
    """得点入力ページ"""
    st.title("📝 得点入力")
    
    # 基本科目リスト
    default_subjects = ["英語", "数学", "国語", "物理", "化学", "生物", "日本史", "世界史", "地理", "公民"]
    
    # 現在の得点データを取得
    scores_df = safe_read_csv(SCORES_FILE, ["Email", "Subject", "Score"])
    user_scores = scores_df[scores_df["Email"] == st.session_state.user_email] if not scores_df.empty else pd.DataFrame()
    
    st.subheader("科目別得点入力")
    
    # 入力フォームを縦に配置
    updated_scores = {}
    
    for subject in default_subjects:
        # 現在の得点を取得（安全化）
        current_score = 0
        if not user_scores.empty:
            subject_row = user_scores[user_scores["Subject"] == subject]
            if not subject_row.empty and "Score" in subject_row.columns:
                try:
                    current_score = int(subject_row.iloc[0]["Score"])
                except (ValueError, IndexError):
                    current_score = 0
        
        score = st.number_input(
            f"{subject}",
            min_value=0,
            max_value=200,
            value=current_score,
            step=1,
            key=f"score_{subject}"
        )
        updated_scores[subject] = score
    
    # カスタム科目追加
    st.subheader("カスタム科目追加")
    custom_subject = st.text_input("科目名", key="custom_subject")
    custom_score = st.number_input("得点", min_value=0, max_value=200, value=0, step=1, key="custom_score")
    
    if st.button("カスタム科目を追加", key="add_custom", use_container_width=True):
        if custom_subject:
            updated_scores[custom_subject] = custom_score
            st.success(f"{custom_subject}: {custom_score}点を追加しました")
    
    # 保存ボタン
    if st.button("得点を保存", key="save_scores", use_container_width=True):
        # 既存のユーザーデータを削除（安全化）
        if not scores_df.empty:
            scores_df = scores_df[scores_df["Email"] != st.session_state.user_email]
        
        # 新しい得点データを作成
        new_scores = []
        for subject, score in updated_scores.items():
            if score > 0:  # 0点より大きい場合のみ保存
                new_scores.append({
                    "Email": st.session_state.user_email,
                    "Subject": subject,
                    "Score": score
                })
        
        if new_scores:
            new_scores_df = pd.DataFrame(new_scores)
            
            if scores_df.empty:
                final_df = new_scores_df
            else:
                final_df = pd.concat([scores_df, new_scores_df], ignore_index=True)
            
            if safe_save_csv(final_df, SCORES_FILE):
                st.success("得点を保存しました！")
            else:
                st.error("保存に失敗しました")
        else:
            # 空のDataFrameでも保存（既存データの削除）
            if safe_save_csv(scores_df, SCORES_FILE):
                st.success("得点を更新しました！")

def school_registration_page():
    """志望校登録/更新ページ"""
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
            st.write(f"**{school_name}**")
            st.write(f"科目: {subjects}")
            st.write(f"最大点: {max_scores}")
            st.write("---")
    
    # 新規登録フォーム
    st.subheader("新しい志望校を登録")
    
    school_name = st.text_input("学校名", key="school_name")
    
    st.write("科目と最大点を入力してください")
    subjects_input = st.text_area(
        "科目（カンマ区切り）",
        placeholder="英語,数学,国語,物理,化学",
        key="subjects_input"
    )
    
    max_scores_input = st.text_area(
        "各科目の最大点（カンマ区切り）",
        placeholder="150,200,200,100,100",
        key="max_scores_input"
    )
    
    # 共通テスト用のフィールド
    st.subheader("共通テスト（オプション）")
    kyotsu_subjects = st.text_input(
        "共通テスト科目（カンマ区切り）",
        placeholder="英語R,英語L,数学IA,数学IIB",
        key="kyotsu_subjects"
    )
    kyotsu_max_scores = st.text_input(
        "共通テスト最大点（カンマ区切り）",
        placeholder="100,100,100,100",
        key="kyotsu_max_scores"
    )
    
    if st.button("志望校を保存", key="save_school", use_container_width=True):
        if not school_name or not subjects_input or not max_scores_input:
            st.error("学校名、科目、最大点をすべて入力してください")
            return
        
        try:
            # 科目と最大点を結合（共通テストも含める）
            all_subjects = subjects_input
            all_max_scores = max_scores_input
            
            if kyotsu_subjects and kyotsu_max_scores:
                all_subjects += "," + kyotsu_subjects
                all_max_scores += "," + kyotsu_max_scores
            
            # データの整合性チェック
            subjects_list = [s.strip() for s in all_subjects.split(",") if s.strip()]
            scores_list = [s.strip() for s in all_max_scores.split(",") if s.strip()]
            
            if len(subjects_list) != len(scores_list):
                st.error("科目数と最大点数が一致しません")
                return
            
            # 既存のデータから同じ学校名のデータを削除（安全化）
            if not schools_df.empty:
                schools_df_filtered = schools_df[
                    ~((schools_df["Email"] == st.session_state.user_email) & 
                      (schools_df["SchoolName"] == school_name))
                ]
            else:
                schools_df_filtered = pd.DataFrame(columns=["Email", "SchoolName", "Subjects", "MaxScores"])
            
            # 新しいデータを追加
            new_school = pd.DataFrame({
                "Email": [st.session_state.user_email],
                "SchoolName": [school_name],
                "Subjects": [all_subjects],
                "MaxScores": [all_max_scores]
            })
            
            if schools_df_filtered.empty:
                final_df = new_school
            else:
                final_df = pd.concat([schools_df_filtered, new_school], ignore_index=True)
            
            if safe_save_csv(final_df, SCHOOLS_FILE):
                st.success("志望校を保存しました！")
                st.rerun()
            else:
                st.error("保存に失敗しました")
                
        except Exception as e:
            st.error(f"データ処理エラー: {e}")

def conversion_page():
    """志望校換算ページ"""
    st.title("📊 志望校換算")
    
    # データ読み込み（安全化）
    scores_df = safe_read_csv(SCORES_FILE, ["Email", "Subject", "Score"])
    schools_df = safe_read_csv(SCHOOLS_FILE, ["Email", "SchoolName", "Subjects", "MaxScores"])
    
    user_scores = scores_df[scores_df["Email"] == st.session_state.user_email] if not scores_df.empty else pd.DataFrame()
    user_schools = schools_df[schools_df["Email"] == st.session_state.user_email] if not schools_df.empty else pd.DataFrame()
    
    if user_scores.empty:
        st.warning("得点が入力されていません。「得点入力」ページで得点を入力してください。")
        return
    
    if user_schools.empty:
        st.warning("志望校が登録されていません。「志望校登録/更新」ページで志望校を登録してください。")
        return
    
    # ユーザーの得点データを辞書に変換（安全化）
    score_dict = {}
    for _, row in user_scores.iterrows():
        subject = str(row.get("Subject", ""))
        try:
            score = float(row.get("Score", 0))
            score_dict[subject] = score
        except (ValueError, TypeError):
            score_dict[subject] = 0
    
    st.subheader("換算結果")
    
    # 各志望校について換算計算
    for idx, school_row in user_schools.iterrows():
        school_name = str(school_row.get("SchoolName", "Unknown"))
        subjects_str = str(school_row.get("Subjects", ""))
        max_scores_str = str(school_row.get("MaxScores", ""))
        
        st.write(f"### {school_name}")
        
        try:
            subjects_list = [s.strip() for s in subjects_str.split(",") if s.strip()]
            max_scores_list = [float(s.strip()) for s in max_scores_str.split(",") if s.strip()]
            
            if len(subjects_list) != len(max_scores_list):
                st.error(f"{school_name}: 科目数と最大点数が一致しません")
                continue
            
            total_converted = 0
            total_max = 0
            conversion_details = []
            
            for subject, max_score in zip(subjects_list, max_scores_list):
                user_score = score_dict.get(subject, 0)
                
                # 換算計算（ユーザーの得点が0でも計算する）
                if max_score > 0:
                    # 一般的な換算: (ユーザー得点 / 満点) × 志望校の最大点
                    # ここでは満点を100点と仮定
                    converted_score = (user_score / 100) * max_score
                    converted_score = min(converted_score, max_score)  # 最大点を超えないように
                else:
                    converted_score = 0
                
                total_converted += converted_score
                total_max += max_score
                
                conversion_details.append({
                    "科目": subject,
                    "あなたの得点": user_score,
                    "最大点": max_score,
                    "換算得点": round(converted_score, 1)
                })
            
            # 結果表示
            for detail in conversion_details:
                st.write(f"**{detail['科目']}**: {detail['あなたの得点']}点 → {detail['換算得点']}/{detail['最大点']}点")
            
            # 合計とパーセンテージ
            percentage = (total_converted / total_max * 100) if total_max > 0 else 0
            st.write(f"**合計**: {round(total_converted, 1)}/{round(total_max, 1)}点 ({round(percentage, 1)}%)")
            
            # パフォーマンス評価
            if percentage >= 80:
                st.success("🎉 優秀！合格圏内です")
            elif percentage >= 60:
                st.info("📈 良好！もう少しで合格圏内です")
            elif percentage >= 40:
                st.warning("⚠️ 要努力！勉強を頑張りましょう")
            else:
                st.error("🔥 危険圏！大幅な得点アップが必要です")
            
            st.write("---")
            
        except Exception as e:
            st.error(f"{school_name}のデータ処理でエラーが発生しました: {e}")

def main():
    """メイン関数"""
    init_session_state()
    
    # ログインチェック
    if not st.session_state.logged_in:
        login_page()
        return
    
    # サイドバー
    with st.sidebar:
        st.write(f"ようこそ、{st.session_state.user_name}さん")
        st.write(f"Email: {st.session_state.user_email}")
        st.write("---")
        
        # ページ選択
        page = st.selectbox(
            "ページを選択",
            ["得点入力", "志望校登録/更新", "志望校換算"]
        )
        
        st.write("---")
        
        # ログアウトボタン
        if st.button("ログアウト", use_container_width=True):
            # セッション状態をクリア（安全化）
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("ログアウトしました")
            st.rerun()
    
    # 選択されたページを表示
    if page == "得点入力":
        score_input_page()
    elif page == "志望校登録/更新":
        school_registration_page()
    elif page == "志望校換算":
        conversion_page()

if __name__ == "__main__":
    main()