import streamlit as st
import pandas as pd
import os

# --- CSVファイル ---
USERS_CSV = "users.csv"
SCORES_CSV = "scores.csv"
SCHOOLS_CSV = "schools.csv"

# --- CSV初期化 ---
for file, cols in [(USERS_CSV, ["Email","Name"]),
                   (SCORES_CSV, ["Email","Subject","Score"]),
                   (SCHOOLS_CSV, ["Email","SchoolName","Subjects","MaxScores"])]:
    if not os.path.exists(file):
        pd.DataFrame(columns=cols).to_csv(file, index=False)

# --- セッション初期化 ---
if "user_email" not in st.session_state:
    st.session_state.user_email = None
    st.session_state.user_name = None
if "logout_flag" not in st.session_state:
    st.session_state.logout_flag = False

# --- ログアウト関数 ---
def logout():
    st.session_state.logout_flag = True

# --- ログイン画面 ---
if st.session_state.user_email is None or st.session_state.logout_flag:
    st.session_state.logout_flag = False
    st.session_state.user_email = None
    st.session_state.user_name = None

    st.title("ログイン")
    email = st.text_input("メールアドレス")
    name = ""
    users_df = pd.read_csv(USERS_CSV)

    if email:
        if email in users_df["Email"].values:
            st.session_state.user_email = email
            st.session_state.user_name = users_df.loc[users_df["Email"]==email, "Name"].values[0]
            st.experimental_rerun()
        else:
            name = st.text_input("名前を入力して新規登録")
            if st.button("新規登録"):
                if name:
                    users_df = pd.concat([users_df, pd.DataFrame([[email,name]], columns=["Email","Name"])])
                    users_df.to_csv(USERS_CSV, index=False)
                    st.session_state.user_email = email
                    st.session_state.user_name = name
                    st.experimental_rerun()
                else:
                    st.warning("名前を入力してください")
else:
    # --- アプリ本体 ---
    email = st.session_state.user_email
    name = st.session_state.user_name

    st.title(f"{name} の成績管理アプリ")

    # --- サイドバーでタブ切り替え ---
    page = st.sidebar.selectbox("ページ選択", ["得点入力","志望校登録/更新","志望校換算"])
    st.sidebar.button("ログアウト", on_click=logout)

    # --- ページごとの処理 ---
    if page == "得点入力":
        st.subheader("得点入力（共通テスト含む）")
        subjects = ["英語","数学","物理"]
        score_inputs = {}
        for sub in subjects:
            score_inputs[sub] = st.number_input(f"{sub}得点", min_value=0, max_value=200, step=1)

        if st.button("保存", key="save_scores"):
            scores_df = pd.read_csv(SCORES_CSV)
            scores_df = scores_df[scores_df["Email"] != email]
            for sub, val in score_inputs.items():
                scores_df = pd.concat([scores_df, pd.DataFrame([[email,sub,val]], columns=["Email","Subject","Score"])])
            scores_df.to_csv(SCORES_CSV, index=False)
            st.success("得点を保存しました")

    elif page == "志望校登録/更新":
        st.subheader("志望校登録 / 更新")
        new_school = st.text_input("学校名（共通テストもここでOK）", key="school_name")
        new_subjects = st.text_input("科目（カンマ区切り）", key="school_subjects")
        new_max_scores = st.text_input("各科目の最大点（カンマ区切り）", key="school_max")
        if st.button("登録/更新", key="save_school"):
            if new_school and new_subjects and new_max_scores:
                schools_df = pd.read_csv(SCHOOLS_CSV)
                schools_df = schools_df[~((schools_df["Email"]==email) & (schools_df["SchoolName"]==new_school))]
                schools_df = pd.concat([schools_df, pd.DataFrame([[email,new_school,new_subjects,new_max_scores]],
                                                                columns=["Email","SchoolName","Subjects","MaxScores"])])
                schools_df.to_csv(SCHOOLS_CSV, index=False)
                st.success(f"{new_school} を登録/更新しました")
            else:
                st.warning("すべて入力してください")

    elif page == "志望校換算":
        st.subheader("志望校換算")
        schools_df = pd.read_csv(SCHOOLS_CSV)
        user_schools = schools_df[schools_df["Email"]==email]
        if user_schools.empty:
            st.info("志望校情報が登録されていません")
        else:
            scores_df = pd.read_csv(SCORES_CSV)
            user_scores = scores_df[scores_df["Email"]==email].set_index("Subject")["Score"].to_dict()
            for _, row in user_schools.iterrows():
                school_subjects = row["Subjects"].split(",")
                max_scores = list(map(float,row["MaxScores"].split(",")))
                converted_scores = []
                for sub, max_score in zip(school_subjects, max_scores):
                    score = user_scores.get(sub,0)
                    converted = score / 100 * max_score
                    converted_scores.append(converted)
                st.write(f"**{row['SchoolName']}**: {converted_scores}")
