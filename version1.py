import streamlit as st
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 1. 페이지 설정
st.set_page_config(page_title="베이지안 지형 탐색 게임", layout="wide")
st.title("🗺️ 베이지안 지형 탐색: 사라진 보물을 찾아라!")

# 2. 지형 및 확률 상수 설정
TERRAIN_TYPES = np.array([
    ["산", "산", "산", "평지"],
    ["산", "산", "평지", "바다"],
    ["산", "평지", "바다", "바다"],
    ["평지", "평지", "바다", "바다"]
])

# 지형별 설정 (확률 합계: 산 0.5, 평지 0.3, 바다 0.2)
TERRAIN_PRIORS = {"산": 0.5 / 6, "평지": 0.3 / 5, "바다": 0.2 / 5}
TERRAIN_DETECTION = {"산": 0.5, "평지": 0.9, "바다": 0.3}

# 3. 초기화 함수
def reset_game():
    # 사전 확률 초기화
    init_p = np.zeros((4, 4))
    for i in range(4):
        for j in range(4):
            init_p[i, j] = TERRAIN_PRIORS[TERRAIN_TYPES[i, j]]
    st.session_state.prior = init_p
    
    # 실제 보물 위치 결정 (사전 확률 기반으로 랜덤하게 한 곳 선정)
    flat_prior = init_p.flatten()
    chosen_idx = np.random.choice(16, p=flat_prior)
    st.session_state.treasure_pos = (chosen_idx // 4, chosen_idx % 4)
    
    st.session_state.game_over = False
    st.session_state.history = []
    st.session_state.message = "게임을 시작합니다! 보물이 숨겨졌습니다."

if 'prior' not in st.session_state:
    reset_game()

# 4. 베이지안 업데이트 로직
def probe_cell(r, c):
    if st.session_state.game_over:
        return

    # 보물을 찾았는지 확인
    if (r, c) == st.session_state.treasure_pos:
        # 우도(Detection Prob)에 따라 찾을 수도, 못 찾을 수도 있음
        terrain = TERRAIN_TYPES[r, c]
        if np.random.random() < TERRAIN_DETECTION[terrain]:
            st.session_state.game_over = True
            st.session_state.message = f"🎊 축하합니다! {terrain} {chr(65+r)}{c+1}에서 보물을 찾았습니다!"
            return
    
    # 보물을 찾지 못했을 경우 (확률 업데이트)
    p = st.session_state.prior
    d_prob = TERRAIN_DETECTION[TERRAIN_TYPES[r, c]]
    
    # 베이즈 정리 분모: P(Fail) = 1 - (P(Cell) * P(Find|Cell))
    total_fail_prob = 1 - (p[r, c] * d_prob)
    
    new_p = np.copy(p)
    for i in range(4):
        for j in range(4):
            if i == r and j == c:
                new_p[i, j] = (p[i, j] * (1 - d_prob)) / total_fail_prob
            else:
                new_p[i, j] = p[i, j] / total_fail_prob
    
    st.session_state.prior = new_p
    st.session_state.history.append(f"{TERRAIN_TYPES[r, c]} {chr(65+r)}{c+1} 수색 실패")
    st.session_state.message = f"아쉽네요. {TERRAIN_TYPES[r, c]} {chr(65+r)}{c+1}에는 보물이 없거나 발견하지 못했습니다."

# 5. UI 레이아웃
col1, col2 = st.columns([1, 1.3])

with col1:
    st.subheader("🕹️ 수색 지역 선택")
    st.info(st.session_state.message)
    
    rows = ["A", "B", "C", "D"]
    for i in range(4):
        cols = st.columns(4)
        for j in range(4):
            terrain = TERRAIN_TYPES[i, j]
            label = f"{terrain}\n{rows[i]}{j+1}"
            if cols[j].button(label, key=f"btn_{i}_{j}", use_container_width=True, disabled=st.session_state.game_over):
                probe_cell(i, j)
                st.rerun()
    
    if st.button("🔄 게임 리셋 / 보물 재배치", type="primary"):
        reset_game()
        st.rerun()

    st.write("---")
    st.write("**최근 활동:**")
    for log in st.session_state.history[-3:]:
        st.write(f"- {log}")

with col2:
    st.subheader("📊 실시간 확률 분포 지도")
    
    # 텍스트 레이블 생성
    display_labels = []
    for i in range(4):
        row_labels = []
        for j in range(4):
            terrain = TERRAIN_TYPES[i, j]
            prob = st.session_state.prior[i, j] * 100
            label = f"{terrain}\n({rows[i]}{j+1})\n{prob:.1f}%"
            row_labels.append(label)
        display_labels.append(row_labels)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        st.session_state.prior * 100, 
        annot=np.array(display_labels), 
        fmt="", 
        cmap="YlOrRd", 
        ax=ax,
        cbar_kws={'label': '보물 존재 확률 (%)'}
    )
    plt.xlabel("열 (1-4)")
    plt.ylabel("행 (A-D)")
    st.pyplot(fig)

# 지형별 특성 안내
with st.expander("📝 지형별 데이터 정보"):
    st.table(pd.DataFrame({
        "지형": ["산", "평지", "바다"],
        "전체 확률": ["50%", "30%", "20%"],
        "탐색 성공률(우도)": ["50%", "90%", "30%"],
        "설명": ["유력하지만 수색이 어려움", "확률은 보통이나 수색이 쉬움", "가능성은 낮고 수색도 어려움"]
    }))
