import streamlit as st
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="베이지안 탐색 시뮬레이터", layout="wide")
st.title("🎲 실시간 베이지안 보물찾기 (랜덤 지도)")

# 2. 초기화 함수 (랜덤 설정)
def reset_game():
    # 4x4 랜덤 확률 생성 (디리클레 분포를 사용하여 합이 1이 되도록 설정)
    random_prior = np.random.dirichlet(np.ones(16), size=1).reshape(4, 4)
    st.session_state.prior = random_prior
    
    # 구역별 탐색 성공률도 랜덤하게 설정 (0.3 ~ 0.9 사이)
    # 어떤 구역은 찾기 쉽고, 어떤 구역은 험난하도록 만듭니다.
    st.session_state.detection = np.random.uniform(0.3, 0.9, (4, 4))
    st.session_state.history = []

# 세션 상태 초기화
if 'prior' not in st.session_state:
    reset_game()

# 3. 베이지안 업데이트 로직
def update_probability(r, c):
    p = st.session_state.prior
    d = st.session_state.detection
    
    # 전체 실패 확률 계산 (분모)
    total_fail_prob = 1 - (p[r, c] * d[r, c])
    
    new_p = np.copy(p)
    for i in range(4):
        for j in range(4):
            if i == r and j == c:
                new_p[i, j] = (p[i, j] * (1 - d[i, j])) / total_fail_prob
            else:
                new_p[i, j] = p[i, j] / total_fail_prob
    
    st.session_state.prior = new_p
    st.session_state.history.append(f"구역 {chr(65+r)}{c+1} 수색 실패")

# 4. 화면 레이아웃
col1, col2 = st.columns([1, 1.3])

with col1:
    st.subheader("📍 수색 지점 선택")
    rows = ["A", "B", "C", "D"]
    
    for i in range(4):
        cols = st.columns(4)
        for j in range(4):
            button_label = f"{rows[i]}{j+1}"
            if cols[j].button(button_label, use_container_width=True):
                update_probability(i, j)
    
    if st.button("🔄 새로운 지도 생성 (리셋)", type="primary"):
        reset_game()
        st.rerun()

    st.write("---")
    st.write("**최근 활동 기록:**")
    for log in st.session_state.history[-5:]: # 최근 5개 기록만 표시
        st.write(f"- {log}")

with col2:
    st.subheader("📊 실시간 확률 분포 및 구역 ID")
    
    # 표에 표시할 텍스트 배열 생성 (구역 ID + 확률 %)
    # 예: "A1\n12.5%"
    display_labels = []
    for i in range(4):
        row_labels = []
        for j in range(4):
            prob = st.session_state.prior[i, j] * 100
            label = f"{rows[i]}{j+1}\n{prob:.1f}%"
            row_labels.append(label)
        display_labels.append(row_labels)
    
    # 시각화 (Heatmap)
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        st.session_state.prior * 100, 
        annot=np.array(display_labels), # ID와 확률을 동시에 표시
        fmt="",                         # 문자열 포맷 그대로 사용
        cmap="YlOrRd", 
        cbar=True,
        ax=ax,
        annot_kws={"size": 12, "weight": "bold"} # 글자 크기 및 굵기 조절
    )
    plt.xlabel("열 (1-4)")
    plt.ylabel("행 (A-D)")
    st.pyplot(fig)

# 하단 도움말
with st.expander("💡 베이지안 탐색 원리 보기"):
    st.write("""
    1. **사전 확률(Prior):** 게임 시작 시 각 구역에 보물이 있을 것이라 믿는 초기 확률입니다. (랜덤 생성됨)
    2. **우도(Likelihood):** 각 구역의 지형적 특성(탐색 성공률)입니다.
    3. **업데이트:** 특정 구역을 수색해서 보물이 나오지 않으면, 그 구역의 확률은 줄어들고 **나머지 모든 구역의 확률이 비례해서 상승**합니다.
    """)
