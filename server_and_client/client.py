# client.py
# 실행하려면 아래 명령어를 터미널에 입력
# streamlit run client.py

import streamlit as st
import requests
from PIL import Image
from io import BytesIO

# 페이지 제목
st.title("미로 이미지 생성기")

# 버튼 영역
if st.button("생성하기"):
    with st.spinner("이미지를 생성 중입니다..."):
        try:
            # Flask 서버에 GET 요청 보내기
            response = requests.get("http://localhost:5000/generate")
            response.raise_for_status()

            # 이미지 수신 및 PIL로 디코딩
            image = Image.open(BytesIO(response.content))

            # 이미지 표시
            st.image(image, caption="생성된 이미지", use_container_width=True)

        except requests.exceptions.RequestException as e:
            st.error(f"요청 중 오류 발생: {e}")
        except Exception as e:
            st.error(f"이미지 처리 중 오류 발생: {e}")



