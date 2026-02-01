import streamlit as st
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import koreanize_matplotlib

# 1. 페이지 설정
st.set_page_config(page_title="베이지안 지형 탐색 게임", layout="wide")

# 2. 지형 및 확률 상수 설정
TERRAIN_TYPES = np.array([
    ["산", "산", "산", "평지"],
    ["산", "산", "평지", "바다"],
    ["산", "평지", "바다", "바다"],
    ["평지", "평지", "바다", "바다"]
])

TERRAIN_PRIORS = {"산": 0.5 / 6, "평지": 0.3 / 5, "바다": 0.2 / 5}
TERRAIN_DETECTION = {"산": 0.5, "평지": 0.9, "바다": 0.3}

# 3. 초기화 함수
def reset_game():
    init_p = np.zeros((4, 4))
    for i in range(4):
        for j in range(4):
            init_p[i, j] = TERRAIN_PRIORS[TERRAIN_TYPES[i, j]]
    
    st.session_state.prior = init_p
    # 보물 위치 랜덤 배정
    flat_prior = init_p.flatten()
    chosen_idx = np.random.choice(16, p=flat_prior)
    st.session_state.treasure_pos = (chosen_idx // 4, chosen_idx % 4)
    
    st.session_state.game_over = False
    st.session_state.attempts = 0
    st.session_state.history = []
    st.session_state.message = "게임을 시작합니다! 보물이 숨겨졌습니다."
    st.session_state.win = False
    
    # 설정 초기화
    st.session_state.show_prob = False       # 확률 및 색상 표시 여부
    st.session_state.reveal_treasure = False # 보물 위치 강제 공개 여부

# 앱 시작 시 세션 상태 초기화
if 'prior' not in st.session_state:
    reset_game()

# --- 사이드바: 설정 영역 ---
with st.sidebar:
    st.header("⚙️ 게임 설정")
    max_attempts = st.number_input("최대 수색 기회 설정", min_value=1, max_value=20, value=10)
    
    st.write("---")
    # 기능 1: 확률 및 색상 토글
    if st.button("👁️ 확률 및 색상 On/Off"):
        st.session_state.show_prob = not st.session_state.show_prob
    
    # 기능 2: 보물 위치 보기 토글
    if st.button("💎 보물 위치 확인/숨기기"):
        st.session_state.reveal_treasure = not st.session_state.reveal_treasure
    
    st.write(f"확률/색상 표시: **{'ON' if st.session_state.show_prob else 'OFF'}**")
    st.write(f"보물 위치 공개: **{'ON' if st.session_state.reveal_treasure else 'OFF'}**")
    
    st.write("---")
    if st.button("🔄 새 게임 시작 (리셋)", type="primary"):
        reset_game()
        st.rerun()
    st.write(f"현재 수색: **{st.session_state.attempts} / {max_attempts}**")

# 4. 베이지안 업데이트 로직
def probe_cell(r, c):
    if st.session_state.game_over:
        return

    st.session_state.attempts += 1
    
    # 보물 확인 (성공률 반영)
    if (r, c) == st.session_state.treasure_pos:
        terrain = TERRAIN_TYPES[r, c]
        if np.random.random() < TERRAIN_DETECTION[terrain]:
            st.session_state.game_over = True
            st.session_state.win = True
            st.session_state.show_prob = True # 승리 시 자동 공개
            st.session_state.message = f"🎊 축하합니다! {terrain} {chr(65+r)}{c+1}에서 보물을 찾았습니다!"
            return
    
    # 실패 시 확률 업데이트
    p = st.session_state.prior
    d_prob = TERRAIN_DETECTION[TERRAIN_TYPES[r, c]]
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
    
    # 기회 소진 확인
    if st.session_state.attempts >= max_attempts:
        st.session_state.game_over = True
        st.session_state.win = False
        st.session_state.show_prob = True
        st.session_state.reveal_treasure = True # 종료 시 보물 위치 공개
        tr_r, tr_c = st.session_state.treasure_pos
        st.session_state.message = f"🚫 기회 소진! 보물은 {TERRAIN_TYPES[tr_r, tr_c]} {chr(65+tr_r)}{tr_c+1}에 있었습니다."
    else:
        st.session_state.message = f"아쉽네요. {TERRAIN_TYPES[r, c]} {chr(65+r)}{c+1}에는 없거나 발견하지 못했습니다."

# 5. 메인 UI 레이아웃
st.title("🗺️ 베이지안 탐색: 보물찾기 시뮬레이션")

if st.session_state.win:
    st.balloons()

col1, col2 = st.columns([1, 1.3])

with col1:
    st.subheader("🕹️ 수색 지역 선택")
    if st.session_state.game_over:
        if st.session_state.win:
            st.success(st.session_state.message)
        else:
            st.error(st.session_state.message)
    else:
        st.info(st.session_state.message)
        st.warning(f"남은 기회: **{max_attempts - st.session_state.attempts}회**")
    
    rows = ["A", "B", "C", "D"]
    for i in range(4):
        cols = st.columns(4)
        for j in range(4):
            terrain = TERRAIN_TYPES[i, j]
            label = f"{terrain}\n{rows[i]}{j+1}"
            if cols[j].button(label, key=f"btn_{i}_{j}", use_container_width=True, disabled=st.session_state.game_over):
                probe_cell(i, j)
                st.rerun()

    st.write("---")
    st.write("**최근 활동:**")
    history_list = st.session_state.get('history', [])
    for log in history_list[-3:]:
        st.write(f"- {log}")

with col2:
    st.subheader("📊 실시간 확률 분포 지도")
    
    # 텍스트 및 히트맵 데이터 준비
    display_labels = []
    # 확률 표시가 꺼져 있으면 히트맵을 단색(0)으로 표시
    if st.session_state.show_prob:
        heatmap_data = st.session_state.prior * 100
        cbar_on = True
    else:
        heatmap_data = np.zeros((4, 4)) # 모두 동일한 색상
        cbar_on = False

    for i in range(4):
        row_labels = []
        for j in range(4):
            terrain = TERRAIN_TYPES[i, j]
            prob = st.session_state.prior[i, j] * 100
            
            # 보물 위치 공개 조건: 게임 종료 또는 '보물 위치 보기' 활성화
            is_treasure = (i, j) == st.session_state.treasure_pos and (st.session_state.game_over or st.session_state.reveal_treasure)
            tr_marker = "\n★(여기!)" if is_treasure else ""
            
            if st.session_state.show_prob:
                label = f"{terrain}\n({rows[i]}{j+1})\n{prob:.1f}%{tr_marker}"
            else:
                label = f"{terrain}\n({rows[i]}{j+1}){tr_marker}"
            
            row_labels.append(label)
        display_labels.append(row_labels)
    
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(
        heatmap_data, 
        annot=np.array(display_labels), 
        fmt="", 
        cmap="YlOrRd", 
        ax=ax,
        cbar=cbar_on,
        # 확률이 꺼져 있을 때 색상이 변하지 않도록 범위 고정
        vmin=0, vmax=100 if st.session_state.show_prob else 1,
        annot_kws={"size": 18, "weight": "bold", "va": "center"}
    )
    ax.tick_params(axis='both', which='major', labelsize=15)
    plt.xlabel("열 (1-4)", fontsize=15)
    plt.ylabel("행 (A-D)", fontsize=15)
    st.pyplot(fig)

with st.expander("📝 지형별 데이터 정보"):
    st.table(pd.DataFrame({
        "지형": ["산", "평지", "바다"],
        "전체 확률": ["50%", "30%", "20%"],
        "탐색 성공률": ["50%", "90%", "30%"],
        "특징": ["가장 유력함, 발견 어려움", "중간 확률, 발견 매우 쉬움", "낮은 확률, 발견 매우 어려움"]
    }))
