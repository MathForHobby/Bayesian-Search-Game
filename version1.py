import streamlit as st
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 1. 환경 설정 및 구역 이름 정의
st.set_page_config(page_title="베이지안 보물찾기", layout="wide")
st.title("🔍 실시간 베이지안 보물찾기 지도")

# 구역 이름 정의 (4x4)
regions = ["숲(A)", "바다(B)", "도심(C)", "산악(D)"]
cell_names = [[f"{r}-{i+1}" for i in range(4)] for r in regions]
flat_names = [name for sublist in cell_names for name in sublist]

# 세션 상태 초기화
if 'prior' not in st.session_state:
    st.session_state.prior = np.full((4, 4), 1/16)
    # 구역별로 다른 탐색 성공률 설정 (예: 바다는 찾기 어렵고, 도심은 쉬움)
    # A: 0.7, B: 0.3, C: 0.9, D: 0.5
    st.session_state.detection = np.array([
        [0.7, 0.7, 0.7, 0.7], # 숲
        [0.3, 0.3, 0.3, 0.3], # 바다
        [0.9, 0.9, 0.9, 0.9], # 도심
        [0.5, 0.5, 0.5, 0.5]  # 산악
    ])

# 2. 업데이트 로직
def update_probability(r, c):
    p = st.session_state.prior
    d = st.session_state.detection
    
    total_fail_prob = 1 - (p[r, c] * d[r, c])
    
    new_p = np.copy(p)
    for i in range(4):
        for j in range(4):
            if i == r and j == c:
                new_p[i, j] = (p[i, j] * (1 - d[i, j])) / total_fail_prob
            else:
                new_p[i, j] = p[i, j] / total_fail_prob
    st.session_state.prior = new_p

# 3. UI 레이아웃
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📍 수색 지역 선택")
    st.write("각 칸을 클릭하면 수색을 시도합니다. (실패 가정)")
    
    for i in range(4):
        cols = st.columns(4)
        for j in range(4):
            # 버튼에 '숲-1' 등의 이름을 표시
            if cols[j].button(cell_names[i][j], use_container_width=True):
                update_probability(i, j)

with col2:
    st.subheader("📊 구역별 보물 존재 확률 (%)")
    # 히트맵 데이터프레임 생성 (인덱스와 컬럼명 설정)
    df = pd.DataFrame(
        st.session_state.prior * 100, # 백분율 표시
        index=regions, 
        columns=["1", "2", "3", "4"]
    )
    
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(df, annot=True, fmt=".1f", cmap="YlOrRd", ax=ax, cbar=True)
    plt.xlabel("세부 구역")
    plt.ylabel("대구역")
    st.pyplot(fig)

# 하단 정보 표시
st.info(f"현재 가장 확률이 높은 곳: **{flat_names[np.argmax(st.session_state.prior)]}**")
