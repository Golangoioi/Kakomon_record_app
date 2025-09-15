# 既存の同名校を削除
                st.session_state.user_data["schools"] = [
                    s for s in st.session_state.user_data["schools"] 
                    if s.get("school_name") != school_name
                ]
                
                # 新しい学校を追加
                st.session_state.user_data["schools"].append(new_school)
                
                # Google Driveに保存
                save_user_data()
                
                st.success(f"🎉 {school_name}を保存しました！")
                st.balloons()
                st.rerun()
                
            except Exception as e:
                st.error(f"データ処理エラー: {e}")

def score_input_page():
    """得点入力ページ"""
    st.title("📝 得点入力")
    st.markdown("テストの結果を記録して成績を管理しましょう")
    
    # タブで共通テストと志望校を分ける
    tab1, tab2 = st.tabs(["🧪 共通テスト", "🎯 志望校別テスト"])
    
    with tab1:
        st.subheader("📋 共通テスト結果入力")
        
        # 共通テスト設定を取得
        kyotsu_subjects = st.session_state.user_data["kyotsu_settings"].get("subjects", [])
        kyotsu_original_scores = st.session_state.user_data["kyotsu_settings"].get("original_scores", [])
        
        if not kyotsu_subjects:
            st.warning("⚠️ まず共通テスト設定を行ってください")
            st.info("「志望校登録/更新」ページで共通テストの科目を設定できます")
            return
        
        # テスト情報入力
        st.subheader("📋 テスト情報")
        col1, col2 = st.columns(2)
        
        with col1:
            test_name = st.text_input(
                "📝 テスト名", 
                placeholder="例：第1回共通テスト模試、本試験",
                key="kyotsu_test_name"
            )
        
        with col2:
            test_date = st.date_input("📅 実施日", key="kyotsu_test_date")
        
        if test_name:
            st.subheader("📊 得点入力")
            st.caption("共通テストの各科目の得点を入力してください")
            
            # 各科目の得点入力
            scores_dict = {}
            
            col1, col2 = st.columns(2)
            for i, (subject, max_score) in enumerate(zip(kyotsu_subjects, kyotsu_original_scores)):
                col = col1 if i % 2 == 0 else col2
                with col:
                    score = st.number_input(
                        f"📚 {subject}",
                        min_value=0.0,
                        max_value=float(max_score),
                        value=0.0,
                        step=0.5,
                        key=f"kyotsu_score_input_{subject}",
                        help=f"{int(max_score)}点満点"
                    )
                    scores_dict[subject] = score
                    
                    # リアルタイム得点率表示
                    percentage = (score / max_score * 100) if max_score > 0 else 0
                    st.markdown(create_progress_bar(score, max_score, f"{percentage:.1f}%"), unsafe_allow_html=True)
            
            # 合計スコア表示
            total_score = sum(scores_dict.values())
            total_max = sum(kyotsu_original_scores)
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
            if st.button("💾 共通テスト結果を保存", key="save_kyotsu_scores", use_container_width=True, type="primary"):
                try:
                    # 新しいテスト結果を作成
                    new_test = {
                        "school_name": "共通テスト",
                        "test_name": test_name,
                        "test_date": str(test_date),
                        "subjects": kyotsu_subjects,
                        "scores": [scores_dict[s] for s in kyotsu_subjects],
                        "max_scores": kyotsu_original_scores,
                        "test_type": "kyotsu"
                    }
                    
                    # 成績データに追加
                    st.session_state.user_data["scores"].append(new_test)
                    
                    # Google Driveに保存
                    save_user_data()
                    
                    st.success("🎉 共通テスト結果を保存しました！")
                    st.balloons()
                    
                    # 成績評価
                    if total_percentage >= 80:
                        st.success("🌟 優秀！目標達成です！")
                    elif total_percentage >= 60:
                        st.info("📈 良好！もう少しで目標達成です！")
                    elif total_percentage >= 40:
                        st.warning("⚡ 要努力！計画的な学習を心がけましょう！")
                    else:
                        st.error("🔥 基礎から見直しが必要です！")
                        
                except Exception as e:
                    st.error(f"データ処理エラー: {e}")
    
    with tab2:
        st.subheader("📋 志望校別テスト結果入力")
        
        # 志望校一覧を取得
        schools = st.session_state.user_data["schools"]
        
        if not schools:
            st.warning("⚠️ まず志望校を登録してください")
            st.info("「志望校登録/更新」ページで志望校を登録できます")
            return
        
        # 志望校選択
        school_names = [school["school_name"] for school in schools]
        selected_school_name = st.selectbox(
            "🎯 志望校を選択", 
            school_names, 
            key="selected_school_for_score"
        )
        
        if selected_school_name:
            # 選択した志望校の情報を取得
            selected_school = next(s for s in schools if s["school_name"] == selected_school_name)
            
            # 二次試験科目のみを対象とする
            niji_subjects = selected_school.get("niji_subjects", [])
            niji_scores = selected_school.get("niji_scores", [])
            
            if niji_subjects:
                # テスト名入力
                st.subheader("📋 テスト情報")
                col1, col2 = st.columns(2)
                
                with col1:
                    test_name = st.text_input(
                        "📝 テスト名", 
                        placeholder="例：第1回模試、過去問2023年度、記述模試",
                        key="niji_test_name"
                    )
                
                with col2:
                    test_date = st.date_input("📅 実施日", key="niji_test_date")
                
                if test_name:
                    st.subheader("📊 得点入力")
                    st.caption(f"📖 {selected_school_name} の二次試験科目の得点を入力してください")
                    
                    # 各科目の得点入力
                    scores_dict = {}
                    
                    col1, col2 = st.columns(2)
                    for i, (subject, max_score) in enumerate(zip(niji_subjects, niji_scores)):
                        col = col1 if i % 2 == 0 else col2
                        with col:
                            score = st.number_input(
                                f"📚 {subject}",
                                min_value=0.0,
                                max_value=float(max_score),
                                value=0.0,
                                step=0.5,
                                key=f"niji_score_input_{subject}",
                                help=f"{int(max_score)}点満点"
                            )
                            scores_dict[subject] = score
                            
                            # リアルタイム得点率表示
                            percentage = (score / max_score * 100) if max_score > 0 else 0
                            st.markdown(create_progress_bar(score, max_score, f"{percentage:.1f}%"), unsafe_allow_html=True)
                    
                    # 合計スコア表示
                    total_score = sum(scores_dict.values())
                    total_max = sum(niji_scores)
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
                    if st.button("💾 テスト結果を保存", key="save_niji_scores", use_container_width=True, type="primary"):
                        try:
                            # 新しいテスト結果を作成
                            new_test = {
                                "school_name": selected_school_name,
                                "test_name": test_name,
                                "test_date": str(test_date),
                                "subjects": niji_subjects,
                                "scores": [scores_dict[s] for s in niji_subjects],
                                "max_scores": niji_scores,
                                "test_type": "niji"
                            }
                            
                            # 成績データに追加
                            st.session_state.user_data["scores"].append(new_test)
                            
                            # Google Driveに保存
                            save_user_data()
                            
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
                                
                        except Exception as e:
                            st.error(f"データ処理エラー: {e}")
            else:
                st.info("この志望校には二次試験科目が設定されていません")

def calculate_converted_score(kyotsu_score: float, original_max: float, school_max: float) -> float:
    """共通テスト得点を志望校配点に換算"""
    if original_max <= 0:
        return 0.0
    return (kyotsu_score / original_max) * school_max

def results_page():
    """結果表示・分析ページ"""
    st.title("📊 成績結果・分析")
    st.markdown("あなたの成績を詳しく分析します")
    
    # データを取得
    scores_data = st.session_state.user_data["scores"]
    schools_data = st.session_state.user_data["schools"]
    
    if not scores_data:
        st.warning("⚠️ まだテスト結果が登録されていません")
        st.info("「得点入力」ページでテスト結果を登録してください")
        return
    
    # 分析対象選択
    analysis_options = ["📈 総合分析", "🧪 共通テスト分析"] + [f"🎯 {school['school_name']}" for school in schools_data]
    selected_analysis = st.selectbox(
        "📊 分析対象を選択", 
        analysis_options, 
        key="analysis_select"
    )
    
    if selected_analysis == "📈 総合分析":
        # 総合分析ページ
        st.subheader("📈 総合成績分析")
        
        # 基本統計
        kyotsu_tests = [s for s in scores_data if s.get("test_type") == "kyotsu"]
        niji_tests = [s for s in scores_data if s.get("test_type") == "niji"]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📝 総テスト数", len(scores_data))
        with col2:
            st.metric("🧪 共通テスト", len(kyotsu_tests))
        with col3:
            st.metric("🎯 二次試験", len(niji_tests))
        with col4:
            st.metric("🏫 登録志望校", len(schools_data))
        
        # 最新の共通テスト結果
        if kyotsu_tests:
            st.subheader("🧪 最新の共通テスト結果")
            latest_kyotsu = sorted(kyotsu_tests, key=lambda x: x["test_date"])[-1]
            
            subjects = latest_kyotsu["subjects"]
            scores = latest_kyotsu["scores"]
            max_scores = latest_kyotsu["max_scores"]
            percentages = [(s/m*100) if m > 0 else 0 for s, m in zip(scores, max_scores)]
            
            create_radar_chart_display(subjects, percentages)
            
            # 志望校別換算得点
            if schools_data:
                st.subheader("🎯 志望校別換算得点")
                
                for school in schools_data:
                    school_name = school["school_name"]
                    kyotsu_subjects = school.get("kyotsu_subjects", [])
                    kyotsu_school_scores = school.get("kyotsu_scores", [])
                    niji_subjects = school.get("niji_subjects", [])
                    niji_school_scores = school.get("niji_scores", [])
                    
                    with st.expander(f"📖 {school_name}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**🧪 共通テスト換算**")
                            kyotsu_converted_total = 0
                            kyotsu_max_total = 0
                            
                            # 共通テスト科目の情報を取得
                            kyotsu_settings = st.session_state.user_data["kyotsu_settings"]
                            original_subjects = kyotsu_settings.get("subjects", [])
                            original_scores = kyotsu_settings.get("original_scores", [])
                            
                            for subj, school_max in zip(kyotsu_subjects, kyotsu_school_scores):
                                if subj in subjects:
                                    # 実際の得点を取得
                                    subj_idx = subjects.index(subj)
                                    actual_score = scores[subj_idx]
                                    
                                    # 元の配点を取得
                                    if subj in original_subjects:
                                        orig_idx = original_subjects.index(subj)
                                        original_max = original_scores[orig_idx]
                                        
                                        # 換算得点計算
                                        converted_score = calculate_converted_score(actual_score, original_max, school_max)
                                        kyotsu_converted_total += converted_score
                                        kyotsu_max_total += school_max
                                        
                                        percentage = (converted_score / school_max * 100) if school_max > 0 else 0
                                        st.write(f"• **{subj}**: {converted_score:.1f}/{school_max}点 ({percentage:.1f}%)")
                            
                            if kyotsu_max_total > 0:
                                kyotsu_total_percentage = (kyotsu_converted_total / kyotsu_max_total * 100)
                                st.write(f"**合計**: {kyotsu_converted_total:.1f}/{kyotsu_max_total}点 ({kyotsu_total_percentage:.1f}%)")
                        
                        with col2:
                            st.write("**📝 二次試験（最新）**")
                            
                            # この志望校の最新二次試験結果
                            school_niji_tests = [s for s in niji_tests if s["school_name"] == school_name]
                            
                            if school_niji_tests:
                                latest_niji = sorted(school_niji_tests, key=lambda x: x["test_date"])[-1]
                                niji_subjects_actual = latest_niji["subjects"]
                                niji_scores_actual = latest_niji["scores"]
                                niji_max_actual = latest_niji["max_scores"]
                                
                                niji_total = sum(niji_scores_actual)
                                niji_max_total = sum(niji_max_actual)
                                
                                for subj, score, max_score in zip(niji_subjects_actual, niji_scores_actual, niji_max_actual):
                                    percentage = (score / max_score * 100) if max_score > 0 else 0
                                    st.write(f"• **{subj}**: {score:.1f}/{max_score}点 ({percentage:.1f}%)")
                                
                                if niji_max_total > 0:
                                    niji_total_percentage = (niji_total / niji_max_total * 100)
                                    st.write(f"**合計**: {niji_total:.1f}/{niji_max_total}点 ({niji_total_percentage:.1f}%)")
                                    st.write(f"📅 **実施日**: {latest_niji['test_date']}")
                            else:
                                st.write("二次試験の結果がまだありません")
        
    elif selected_analysis == "🧪 共通テスト分析":
        # 共通テスト専用分析
        st.subheader("🧪 共通テスト分析")
        
        kyotsu_tests = [s for s in scores_data if s.get("test_type") == "kyotsu"]
        
        if not kyotsu_tests:
            st.warning("⚠️ 共通テストの結果がありません")
            return
        
        # タブ分け
        tab1, tab2, tab3 = st.tabs(["📈 成績推移", "🎯 科目別分析", "📋 テスト一覧"])
        
        with tab1:
            st.subheader("📈 共通テスト成績推移")
            
            # 推移データを準備
            test_summary = []
            for test in sorted(kyotsu_tests, key=lambda x: x["test_date"]):
                total_score = sum(test["scores"])
                total_max = sum(test["max_scores"])
                percentage = (total_score / total_max * 100) if total_max > 0 else 0
                
                test_summary.append({
                    "テスト名": test["test_name"],
                    "日付": test["test_date"],
                    "総得点": total_score,
                    "満点": total_max,
                    "得点率": percentage
                })
            
            if test_summary:
                # 推移チャート表示
                test_names = [t["テスト名"] for t in test_summary]
                percentages = [t["得点率"] for t in test_summary]
                create_trend_chart_display(test_names, percentages)
                
                # 推移分析
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
            st.subheader("🎯 科目別詳細分析")
            
            # 最新テスト結果でレーダーチャート
            latest_test = sorted(kyotsu_tests, key=lambda x: x["test_date"])[-1]
            subjects = latest_test["subjects"]
            scores = latest_test["scores"]
            max_scores = latest_test["max_scores"]
            percentages = [(s/m*100) if m > 0 else 0 for s, m in zip(scores, max_scores)]
            
            st.write(f"📝 **最新テスト: {latest_test['test_name']}**")
            create_radar_chart_display(subjects, percentages)
            
            # 科目別詳細分析
            st.subheader("📚 科目別詳細")
            for subject in subjects:
                with st.expander(f"📖 {subject}"):
                    # この科目の全テスト結果
                    subject_data = []
                    for test in sorted(kyotsu_tests, key=lambda x: x["test_date"]):
                        if subject in test["subjects"]:
                            idx = test["subjects"].index(subject)
                            score = test["scores"][idx]
                            max_score = test["max_scores"][idx]
                            percentage = (score / max_score * 100) if max_score > 0 else 0
                            
                            subject_data.append({
                                "test_name": test["test_name"],
                                "date": test["test_date"],
                                "score": score,
                                "max_score": max_score,
                                "percentage": percentage
                            })
                    
                    if len(subject_data) > 1:
                        # 推移表示
                        st.write("**📈 得点推移**")
                        scores_list = [d["score"] for d in subject_data]
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
                    
                    # 統計情報
                    if subject_data:
                        scores_list = [d["score"] for d in subject_data]
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("平均", f"{np.mean(scores_list):.1f}")
                        with col2:
                            st.metric("最高", f"{max(scores_list):.1f}")
                        with col3:
                            st.metric("最低", f"{min(scores_list):.1f}")
                        with col4:
                            st.metric("最新", f"{scores_list[-1]:.1f}")
        
        with tab3:
            st.subheader("📋 共通テスト一覧")
            
            for test in sorted(kyotsu_tests, key=lambda x: x["test_date"], reverse=True):
                with st.expander(f"📝 {test['test_name']} ({test['test_date']})"):
                    
                    # 科目別結果表示
                    result_data = []
                    total_score = 0
                    total_max = 0
                    
                    for subj, score, max_score in zip(test["subjects"], test["scores"], test["max_scores"]):
                        percentage = (score / max_score * 100) if max_score > 0 else 0
                        result_data.append({
                            "科目": subj,
                            "得点": f"{score:.1f}",
                            "満点": f"{max_score:.0f}",
                            "得点率": f"{percentage:.1f}%"
                        })
                        total_score += score
                        total_max += max_score
                    
                    # テーブル表示
                    result_df = pd.DataFrame(result_data)
                    st.dataframe(result_df, use_container_width=True, hide_index=True)
                    
                    # 総合結果
                    total_percentage = (total_score / total_max * 100) if total_max > 0 else 0
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("総得点", f"{total_score:.1f}")
                    with col2:
                        st.metric("総満点", f"{total_max:.0f}")
                    with col3:
                        st.metric("総得点率", f"{total_percentage:.1f}%")
                    
                    # 削除ボタン
                    if st.button(f"🗑️ 削除", key=f"delete_kyotsu_{test['test_name']}_{test['test_date']}"):
                        st.session_state.user_data["scores"] = [
                            s for s in st.session_state.user_data["scores"] 
                            if not (s.get("test_type") == "kyotsu" and 
                                   s["test_name"] == test["test_name"] and 
                                   s["test_date"] == test["test_date"])
                        ]
                        save_user_data()
                        st.success("テスト結果を削除しました")
                        st.rerun()
    
    else:
        # 個別志望校分析
        school_name = selected_analysis[2:]  # "🎯 "を除去
        selected_school = next((s for s in schools_data if s["school_name"] == school_name), None)
        
        if not selected_school:
            st.error("志望校が見つかりません")
            return
        
        st.subheader(f"🎯 {school_name} - 詳細分析")
        
        # この志望校の二次試験結果
        school_tests = [s for s in scores_data if s.get("test_type") == "niji" and s["school_name"] == school_name]
        
        # タブ分け
        tab1, tab2, tab3 = st.tabs(["📈 成績推移", "🎯 科目別分析", "📋 テスト一覧"])
        
        with tab1:
            st.subheader(f"📈 {school_name} - 成績推移")
            
            if school_tests:
                # 推移データを準備
                test_summary = []
                for test in sorted(school_tests, key=lambda x: x["test_date"]):
                    total_score = sum(test["scores"])
                    total_max = sum(test["max_scores"])
                    percentage = (total_score / total_max * 100) if total_max > 0 else 0
                    
                    test_summary.append({
                        "テスト名": test["test_name"],
                        "日付": test["test_date"],
                        "総得点": total_score,
                        "満点": total_max,
                        "得点率": percentage
                    })
                
                # 推移チャート表示
                test_names = [t["テスト名"] for t in test_summary]
                percentages = [t["得点率"] for t in test_summary]
                create_trend_chart_display(test_names, percentages)
                
                # 詳細テーブル
                display_df = pd.DataFrame(test_summary)
                display_df["総得点"] = display_df["総得点"].round(1).astype(str) + "/" + display_df["満点"].round(0).astype(str)
                display_df["得点率"] = display_df["得点率"].round(1).astype(str) + "%"
                display_df = display_df[["テスト名", "日付", "総得点", "得点率"]]
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("まだテスト結果がありません")
        
        with tab2:
            st.subheader(f"🎯 {school_name} - 科目別分析")
            
            if school_tests:
                # 最新テスト結果でレーダーチャート
                latest_test = sorted(school_tests, key=lambda x: x["test_date"])[-1]
                subjects = latest_test["subjects"]
                scores = latest_test["scores"]
                max_scores = latest_test["max_scores"]
                percentages = [(s/m*100) if m > 0 else 0 for s, m in zip(scores, max_scores)]
                
                st.write(f"📝 **最新テスト: {latest_test['test_name']}**")
                create_radar_chart_display(subjects, percentages)
            else:
                st.info("まだテスト結果がありません")
        
        with tab3:
            st.subheader(f"📋 {school_name} - テスト一覧")
            
            for test in sorted(school_tests, key=lambda x: x["test_date"], reverse=True):
                with st.expander(f"📝 {test['test_name']} ({test['test_date']})"):
                    
                    # 科目別結果表示
                    result_data = []
                    total_score = 0
                    total_max = 0
                    
                    for subj, score, max_score in zip(test["subjects"], test["scores"], test["max_scores"]):
                        percentage = (score / max_score * 100) if max_score > 0 else 0
                        result_data.append({
                            "科目": subj,
                            "得点": f"{score:.1f}",
                            "満点": f"{max_score:.0f}",
                            "得点率": f"{percentage:.1f}%"
                        })
                        total_score += score
                        total_max += max_score
                    
                    # テーブル表示
                    result_df = pd.DataFrame(result_data)
                    st.dataframe(result_df, use_container_width=True, hide_index=True)
                    
                    # 総合結果
                    total_percentage = (total_score / total_max * 100) if total_max > 0 else 0
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("総得点", f"{total_score:.1f}")
                    with col2:
                        st.metric("総満点", f"{total_max:.0f}")
                    with col3:
                        st.metric("総得点率", f"{total_percentage:.1f}%")
                    
                    # 削除ボタン
                    if st.button(f"🗑️ 削除", key=f"delete_niji_{test['test_name']}_{test['test_date']}"):
                        st.session_state.user_data["scores"] = [
                            s for s in st.session_state.user_data["scores"] 
                            if not (s.get("test_type") == "niji" and 
                                   s["school_name"] == school_name and
                                   s["test_name"] == test["test_name"] and 
                                   s["test_date"] == test["test_date"])
                        ]
                        save_user_data()
                        st.success("テスト結果を削除しました")
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
        st.write(f"👤 **{st.session_state.user_name}**")
        st.write(f"📧 {st.session_state.user_email}")
        
        # Google Drive連携状態表示
        if st.session_state.google_credentials:
            st.markdown("""
            <div class="sync-status">
                ☁️ Google Driveと同期中
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ デモモード（データは保存されません）")
        
        st.write("---")
        
        # ページ選択
        page = st.selectbox(
            "📱 ページを選択",
            ["🎯 志望校登録/更新", "📝 得点入力", "📊 成績結果・分析"]
        )
        
        st.write("---")
        
        # 統計情報表示
        try:
            scores_data = st.session_state.user_data["scores"]
            schools_data = st.session_state.user_data["schools"]
            
            st.write("📈 **あなたの統計**")
            st.metric("🎯 志望校数", len(schools_data))
            st.metric("📝 テスト数", len(scores_data))
            
            # 最新テスト情報
            if scores_data:
                latest_test = sorted(scores_data, key=lambda x: x["test_date"])[-1]
                st.write(f"📋 **最新テスト**")
                st.caption(f"{latest_test['test_name']}")
                st.caption(f"実施日: {latest_test['test_date']}")
        
        except Exception:
            pass
        
        st.write("---")
        
        # クイックアクション
        st.write("⚡ **クイックアクション**")
        if st.button("➕ 志望校を登録", use_container_width=True):
            pass
        
        if st.button("📝 テスト結果入力", use_container_width=True):
            pass
        
        if st.button("📊 成績を分析", use_container_width=True):
            pass
        
        st.write("---")
        
        # データ管理
        if st.session_state.google_credentials:
            st.write("💾 **データ管理**")
            if st.button("🔄 手動保存", use_container_width=True):
                save_user_data()
        
        st.write("---")
        
        # ログアウトボタン
        if st.button("🚪 ログアウト", use_container_width=True, type="secondary"):
            # セッション状態をクリア
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
    main()import streamlit as st
import pandas as pd
import json
from typing import Optional, Dict, List
import re
from datetime import datetime
import numpy as np
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io
import os

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
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 15px;
        padding: 25px;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 15px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    .radar-item {
        text-align: center;
        padding: 15px;
        border-radius: 12px;
        background: white;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .radar-item:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    .kyotsu-section {
        background: #e3f2fd;
        border: 2px solid #2196F3;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .niji-section {
        background: #fff3e0;
        border: 2px solid #FF9800;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .google-login-btn {
        background: #4285f4;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 16px;
        font-weight: 500;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        width: 100%;
        margin: 10px 0;
    }
    .sync-status {
        background: #e8f5e8;
        border: 1px solid #4caf50;
        border-radius: 8px;
        padding: 10px;
        margin: 10px 0;
        color: #2e7d32;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# Google Drive API設定
SCOPES = ['https://www.googleapis.com/auth/drive.file']
APP_DATA_FOLDER = "成績管理アプリ"
USER_DATA_FILE = "user_data.json"

# 科目一覧（数学を追加）
ALL_SUBJECTS = [
    "英語", "数学", "数学I・A", "数学II・B", "数学III", "国語", 
    "現代文", "古文", "漢文", "物理", "化学", "生物", 
    "地学", "日本史", "世界史", "地理", "公民", "倫理", 
    "政治経済", "現代社会", "英語リーディング", "英語リスニング",
    "情報", "小論文", "面接"
]

# 共通テスト科目一覧
KYOTSU_SUBJECTS = [
    "英語リーディング", "英語リスニング", "数学I・A", "数学II・B", 
    "国語", "現代文", "古文", "漢文", "物理", "化学", "生物", 
    "地学", "日本史", "世界史", "地理", "公民", "倫理", 
    "政治経済", "現代社会", "情報"
]

def init_session_state():
    """セッション状態を初期化"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = ""
    if 'user_name' not in st.session_state:
        st.session_state.user_name = ""
    if 'google_credentials' not in st.session_state:
        st.session_state.google_credentials = None
    if 'drive_service' not in st.session_state:
        st.session_state.drive_service = None
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {
            "schools": [],
            "scores": [],
            "kyotsu_settings": {"subjects": [], "original_scores": []}
        }

class GoogleDriveManager:
    """Google Drive操作を管理するクラス"""
    
    def __init__(self, credentials):
        self.service = build('drive', 'v3', credentials=credentials)
        
    def get_or_create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """フォルダを取得または作成"""
        try:
            # フォルダ検索
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.service.files().list(q=query).execute()
            items = results.get('files', [])
            
            if items:
                return items[0]['id']
            else:
                # フォルダ作成
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                if parent_id:
                    folder_metadata['parents'] = [parent_id]
                
                folder = self.service.files().create(body=folder_metadata).execute()
                return folder.get('id')
        
        except Exception as e:
            st.error(f"フォルダ操作エラー: {e}")
            return None
    
    def save_user_data(self, data: dict) -> bool:
        """ユーザーデータをGoogle Driveに保存"""
        try:
            # アプリ専用フォルダを取得または作成
            folder_id = self.get_or_create_folder(APP_DATA_FOLDER)
            if not folder_id:
                return False
            
            # JSONファイルとして保存
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            
            # 既存ファイルを検索
            query = f"name='{USER_DATA_FILE}' and '{folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=query).execute()
            items = results.get('files', [])
            
            # 一時ファイルに書き込み
            with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
                f.write(json_data)
            
            if items:
                # 既存ファイルを更新
                file_id = items[0]['id']
                media = MediaFileUpload(USER_DATA_FILE, mimetype='application/json')
                self.service.files().update(fileId=file_id, media_body=media).execute()
            else:
                # 新規ファイル作成
                file_metadata = {
                    'name': USER_DATA_FILE,
                    'parents': [folder_id]
                }
                media = MediaFileUpload(USER_DATA_FILE, mimetype='application/json')
                self.service.files().create(body=file_metadata, media_body=media).execute()
            
            # 一時ファイル削除
            if os.path.exists(USER_DATA_FILE):
                os.remove(USER_DATA_FILE)
            
            return True
        
        except Exception as e:
            st.error(f"データ保存エラー: {e}")
            return False
    
    def load_user_data(self) -> dict:
        """ユーザーデータをGoogle Driveから読み込み"""
        try:
            # アプリ専用フォルダを検索
            folder_results = self.service.files().list(
                q=f"name='{APP_DATA_FOLDER}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            ).execute()
            folders = folder_results.get('files', [])
            
            if not folders:
                # フォルダがない場合はデフォルトデータ
                return {
                    "schools": [],
                    "scores": [],
                    "kyotsu_settings": {"subjects": [], "original_scores": []}
                }
            
            folder_id = folders[0]['id']
            
            # ファイルを検索
            file_results = self.service.files().list(
                q=f"name='{USER_DATA_FILE}' and '{folder_id}' in parents and trashed=false"
            ).execute()
            files = file_results.get('files', [])
            
            if not files:
                # ファイルがない場合はデフォルトデータ
                return {
                    "schools": [],
                    "scores": [],
                    "kyotsu_settings": {"subjects": [], "original_scores": []}
                }
            
            file_id = files[0]['id']
            
            # ファイル内容を取得
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # JSON解析
            json_data = file_content.getvalue().decode('utf-8')
            return json.loads(json_data)
        
        except Exception as e:
            st.error(f"データ読み込みエラー: {e}")
            # エラー時はデフォルトデータ
            return {
                "schools": [],
                "scores": [],
                "kyotsu_settings": {"subjects": [], "original_scores": []}
            }

def setup_google_auth():
    """Google認証を設定"""
    try:
        # Streamlit SecretsからOAuth情報を取得
        client_config = {
            "web": {
                "client_id": st.secrets["google"]["client_id"],
                "client_secret": st.secrets["google"]["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [st.secrets["google"]["redirect_uri"]]
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=st.secrets["google"]["redirect_uri"]
        )
        
        return flow
    
    except Exception as e:
        st.error(f"Google認証設定エラー: {e}")
        st.info("Google Cloud Consoleでの設定が必要です")
        return None

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

def create_radar_chart_display(subjects: List[str], percentages: List[float]) -> None:
    """科目別得点率を表示"""
    try:
        # グリッドレイアウトでの表示
        cols = st.columns(min(len(subjects), 3))
        
        for i, (subject, percentage) in enumerate(zip(subjects, percentages)):
            col_idx = i % len(cols)
            
            with cols[col_idx]:
                # 得点率に基づく色とアイコン
                if percentage >= 80:
                    color = "#4CAF50"
                    emoji = "🎯"
                    status = "優秀"
                elif percentage >= 60:
                    color = "#FF9800"
                    emoji = "📈"
                    status = "良好"
                elif percentage >= 40:
                    color = "#2196F3"
                    emoji = "📊"
                    status = "要努力"
                else:
                    color = "#F44336"
                    emoji = "🔥"
                    status = "要改善"
                
                # カスタムメトリック表示
                st.markdown(f"""
                <div style="
                    text-align: center;
                    padding: 15px;
                    border-radius: 12px;
                    background: white;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
                    border-left: 4px solid {color};
                    margin: 10px 0;
                ">
                    <div style="font-size: 20px; margin-bottom: 5px;">{emoji}</div>
                    <div style="font-weight: bold; margin-bottom: 5px;">{subject}</div>
                    <div style="font-size: 18px; color: {color}; font-weight: bold;">{percentage:.1f}%</div>
                    <div style="font-size: 12px; color: #666;">{status}</div>
                </div>
                """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"表示エラー: {e}")

def create_trend_chart_display(test_names: List[str], percentages: List[float]) -> None:
    """推移チャートを表示"""
    try:
        if not test_names or not percentages:
            st.info("データがありません")
            return
        
        # Streamlitの標準チャート機能を使用
        chart_data = pd.DataFrame({
            'テスト': test_names,
            '得点率': percentages
        })
        
        st.line_chart(
            chart_data.set_index('テスト'),
            height=300,
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"グラフ作成エラー: {e}")

def save_user_data():
    """ユーザーデータをGoogle Driveに保存"""
    if st.session_state.drive_service:
        drive_manager = GoogleDriveManager(st.session_state.google_credentials)
        success = drive_manager.save_user_data(st.session_state.user_data)
        if success:
            st.success("🔄 Google Driveに保存しました")
        else:
            st.error("❌ 保存に失敗しました")

def load_user_data():
    """ユーザーデータをGoogle Driveから読み込み"""
    if st.session_state.drive_service:
        drive_manager = GoogleDriveManager(st.session_state.google_credentials)
        st.session_state.user_data = drive_manager.load_user_data()

def login_page():
    """Google認証ログインページ"""
    st.title("📚 成績管理アプリ")
    st.markdown("**Google Drive連携で安全にデータを管理**")
    
    # Google認証の説明
    st.info("""
    🔐 **安全なGoogle認証**
    - あなたのGoogleアカウントでログイン
    - データは**あなた専用のGoogle Drive**に保存
    - 他の人のデータは一切見えません
    - Streamlitが再起動してもデータは安全
    """)
    
    # Google認証ボタン
    if st.button("🚀 Googleでログイン", key="google_login", use_container_width=True, type="primary"):
        flow = setup_google_auth()
        if flow:
            # 認証URLを生成
            auth_url, _ = flow.authorization_url(prompt='consent')
            st.markdown(f'[👆 こちらをクリックしてGoogleで認証]({auth_url})')
            
            # 認証コード入力
            st.markdown("---")
            st.write("認証後、リダイレクトされたURLから認証コードをコピーして下記に入力してください")
            
            auth_code = st.text_input(
                "認証コード",
                placeholder="認証後のURLから「code=」以降の部分をコピー",
                key="auth_code"
            )
            
            if auth_code and st.button("認証を完了", key="complete_auth"):
                try:
                    # トークン取得
                    flow.fetch_token(code=auth_code)
                    credentials = flow.credentials
                    
                    # ユーザー情報を取得
                    service = build('oauth2', 'v2', credentials=credentials)
                    user_info = service.userinfo().get().execute()
                    
                    # セッションに保存
                    st.session_state.logged_in = True
                    st.session_state.user_email = user_info['email']
                    st.session_state.user_name = user_info['name']
                    st.session_state.google_credentials = credentials
                    st.session_state.drive_service = build('drive', 'v3', credentials=credentials)
                    
                    # ユーザーデータを読み込み
                    load_user_data()
                    
                    st.success("✅ ログイン成功！")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"認証エラー: {e}")
    
    # デモ/テスト用ログイン（開発時のみ）
    if st.checkbox("🧪 デモモード（Google Drive無し）"):
        st.warning("⚠️ このモードではデータは保存されません")
        demo_email = st.text_input("メールアドレス", value="demo@example.com")
        demo_name = st.text_input("名前", value="デモユーザー")
        
        if st.button("デモでログイン"):
            st.session_state.logged_in = True
            st.session_state.user_email = demo_email
            st.session_state.user_name = demo_name
            st.session_state.google_credentials = None
            st.session_state.drive_service = None
            st.session_state.user_data = {
                "schools": [],
                "scores": [],
                "kyotsu_settings": {"subjects": [], "original_scores": []}
            }
            st.success("✅ デモモードでログイン")
            st.rerun()

def school_registration_page():
    """志望校登録/更新ページ"""
    st.title("🎯 志望校登録/更新")
    st.markdown("受験する志望校の情報を登録しましょう")
    
    # 共通テスト設定セクション
    st.subheader("📋 共通テスト設定")
    
    with st.expander("🔧 共通テストの科目・配点を設定", expanded=False):
        st.write("**共通テストで受験する科目を選択してください**")
        
        selected_kyotsu_subjects = []
        col1, col2, col3 = st.columns(3)
        
        # 既存の設定を取得
        existing_subjects = st.session_state.user_data["kyotsu_settings"].get("subjects", [])
        existing_scores = st.session_state.user_data["kyotsu_settings"].get("original_scores", [])
        
        for i, subject in enumerate(KYOTSU_SUBJECTS):
            col = [col1, col2, col3][i % 3]
            with col:
                default_checked = subject in existing_subjects
                if st.checkbox(subject, key=f"kyotsu_check_{subject}", value=default_checked):
                    selected_kyotsu_subjects.append(subject)
        
        if selected_kyotsu_subjects:
            st.write("**各科目の満点（実際の共通テストの配点）**")
            kyotsu_scores_dict = {}
            col1, col2 = st.columns(2)
            for i, subject in enumerate(selected_kyotsu_subjects):
                col = col1 if i % 2 == 0 else col2
                with col:
                    # 既存の配点があれば使用
                    default_score = 100
                    if subject in existing_subjects:
                        idx = existing_subjects.index(subject)
                        if idx < len(existing_scores):
                            default_score = int(existing_scores[idx])
                    
                    score = st.number_input(
                        f"{subject} の満点",
                        min_value=1,
                        max_value=300,
                        value=default_score,
                        step=1,
                        key=f"kyotsu_score_{subject}"
                    )
                    kyotsu_scores_dict[subject] = score
            
            if st.button("共通テスト設定を保存", key="save_kyotsu"):
                # 共通テスト設定を更新
                st.session_state.user_data["kyotsu_settings"] = {
                    "subjects": selected_kyotsu_subjects,
                    "original_scores": [kyotsu_scores_dict[s] for s in selected_kyotsu_subjects]
                }
                
                save_user_data()
                st.success("共通テスト設定を保存しました！")
                st.rerun()
    
    # 既存の志望校一覧表示
    schools = st.session_state.user_data["schools"]
    if schools:
        st.subheader("📋 登録済み志望校")
        for idx, school in enumerate(schools):
            school_name = school.get("school_name", "Unknown")
            
            with st.expander(f"📖 {school_name}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**🧪 共通テスト配点**")
                    kyotsu_subjects = school.get("kyotsu_subjects", [])
                    kyotsu_scores = school.get("kyotsu_scores", [])
                    
                    for subj, score in zip(kyotsu_subjects, kyotsu_scores):
                        st.write(f"• **{subj}**: {score}点")
                
                with col2:
                    st.write("**📝 二次試験配点**")
                    niji_subjects = school.get("niji_subjects", [])
                    niji_scores = school.get("niji_scores", [])
                    
                    for subj, score in zip(niji_subjects, niji_scores):
                        st.write(f"• **{subj}**: {score}点")
                
                if st.button(f"🗑️ {school_name}を削除", key=f"delete_school_{idx}"):
                    # 該当の学校を削除
                    st.session_state.user_data["schools"].pop(idx)
                    save_user_data()
                    st.success(f"{school_name}を削除しました")
                    st.rerun()
    
    # 新規志望校登録フォーム
    st.subheader("➕ 新しい志望校を登録")
    
    school_name = st.text_input(
        "🏫 学校名", 
        key="school_name",
        placeholder="例：○○大学 △△学部"
    )
    
    if school_name:
        # 共通テスト配点設定
        st.markdown('<div class="kyotsu-section">', unsafe_allow_html=True)
        st.write("🧪 **共通テスト配点設定**")
        st.caption("この志望校での共通テストの配点を設定してください")
        
        # 共通テスト科目を取得
        kyotsu_subjects = st.session_state.user_data["kyotsu_settings"].get("subjects", [])
        
        if kyotsu_subjects:
            kyotsu_school_scores = {}
            col1, col2 = st.columns(2)
            for i, subject in enumerate(kyotsu_subjects):
                col = col1 if i % 2 == 0 else col2
                with col:
                    score = st.number_input(
                        f"{subject} 配点",
                        min_value=0,
                        max_value=1000,
                        value=100,
                        step=1,
                        key=f"kyotsu_school_{subject}"
                    )
                    kyotsu_school_scores[subject] = score
        else:
            st.warning("まず共通テスト設定を行ってください")
            kyotsu_school_scores = {}
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 二次試験科目選択
        st.markdown('<div class="niji-section">', unsafe_allow_html=True)
        st.write("📝 **二次試験科目・配点設定**")
        st.caption("二次試験で使用する科目を選択してください")
        
        selected_niji_subjects = []
        col1, col2, col3 = st.columns(3)
        
        for i, subject in enumerate(ALL_SUBJECTS):
            col = [col1, col2, col3][i % 3]
            with col:
                if st.checkbox(subject, key=f"niji_check_{subject}"):
                    selected_niji_subjects.append(subject)
        
        niji_scores_dict = {}
        if selected_niji_subjects:
            st.write("📊 **各科目の配点**")
            col1, col2 = st.columns(2)
            for i, subject in enumerate(selected_niji_subjects):
                col = col1 if i % 2 == 0 else col2
                with col:
                    score = st.number_input(
                        f"{subject} 配点",
                        min_value=1,
                        max_value=1000,
                        value=100,
                        step=1,
                        key=f"niji_score_{subject}"
                    )
                    niji_scores_dict[subject] = score
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 保存ボタン
        if st.button("💾 志望校を保存", key="save_school", use_container_width=True, type="primary"):
            try:
                # 新しい志望校データを作成
                new_school = {
                    "school_name": school_name,
                    "kyotsu_subjects": [s for s in kyotsu_school_scores.keys() if kyotsu_school_scores[s] > 0],
                    "kyotsu_scores": [kyotsu_school_scores[s] for s in kyotsu_school_scores.keys() if kyotsu_school_scores[s] > 0],
                    "niji_subjects": selected_niji_subjects,
                    "niji_scores": [niji_scores_dict[s] for s in selected_niji_subjects]
                }
                
                # 既存の同名校を削除
                st.session_state.user_data["schools"] = [
                    s for s in st.session_state.user_data["schools"] 
                    if s.get("school_name") !=