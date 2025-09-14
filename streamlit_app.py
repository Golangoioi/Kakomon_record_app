import streamlit as st
import pandas as pd
import os

# ファイル名
USERS_CSV = "users.csv"
SCORES_CSV = "scores.csv"
SCHOOLS_CSV = "schools.csv"

# CSVがなければ作る
for file, cols in [(USERS_CSV, ["Email","Name"]),
                   (SCORES_CSV, ["Email","Subject","Score"]),
                   (SCHOOLS_CSV, ["Email","SchoolName","Subjects","MaxScores"])]:
    if not os.path.exists(file):
        pd.DataFrame(columns=cols).to_csv(file, index=False)

st.title("成績管理アプリ（CSVベースMVP）")

# --- ログイン/新規登録 ---
st.subheader("ログイン / 新規登録")
email = st.text_input("メールアドレス")
name = ""
users_df = pd.read_csv(USERS_CSV)

if email:
    if email in users_df["Email"].values:
        name = users_df.loc[users_df["Email"]==email, "Name"].values[0]
        st.success(f"ログイン成功: {name}")
    else:
        name = st.text_input("名前を入力して登録")
        if st.button("新規登録"):
            if name:
                users_df = pd.concat([users_df, pd.DataFrame([[email,name]], columns=["Email","Name"])])
                users_df.to_csv(USERS_CSV, index=False)
                st.success(f"新規登録完了: {name}")
            else:
                st.warning("名前を入力してください")

# --- 共通テスト入力 ---
if name:
    st.subheader("共通テスト得点入力")
    subjects = ["英語","数学","物理"]  # 必要に応じて増やす
    score_inputs = {}
    for sub in subjects:
        score_inputs[sub] = st.number_input(f"{sub}得点", min_value=0, max_value=200, step=1)

    if st.button("保存"):
        scores_df = pd.read_csv(SCORES_CSV)
        for sub, val in score_inputs.items():
            # 既存データは上書き
            scores_df = scores_df[scores_df["Email"] != email]
            scores_df = pd.concat([scores_df, pd.DataFrame([[email,sub,val]], columns=["Email","Subject","Score"])])
        scores_df.to_csv(SCORES_CSV, index=False)
        st.success("共通テスト得点を保存しました")

# --- 志望校換算 ---
if name:
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
                converted = score / 100 * max_score  # 共通テスト最大点100と仮定
                converted_scores.append(converted)
            st.write(f"**{row['SchoolName']}**: {converted_scores}")
