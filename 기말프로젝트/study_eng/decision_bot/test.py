import google.generativeai as genai

# Google Generative AI 설정
def configure_genai():
    GOOGLE_API_KEY = "AIzaSyAsTk4zj6gmewYEdZnOBhjChDW2dkb6dwk"  # 여기에 API 키 입력
    genai.configure(api_key=GOOGLE_API_KEY)

# 프롬프트를 통해 답변 받기
def get_genai_response(prompt):
    """
    Google Generative AI에 프롬프트를 입력하고 답변을 반환합니다.
    :param prompt: 사용자가 입력한 프롬프트 문자열
    :return: 생성된 텍스트 응답
    """
    try:
        response = genai.generate_text(prompt=prompt)
        # response.result에 생성된 텍스트가 있음
        return response.result
    except Exception as e:
        return f"오류가 발생했습니다: {e}"

# 메인 함수
if __name__ == "__main__":
    # 설정 초기화
    configure_genai()

    # 사용자 입력 프롬프트
    user_prompt = input("프롬프트를 입력하세요: ")

    # Google Generative AI로부터 답변 가져오기
    response = get_genai_response(user_prompt)

    # 출력
    print("\nGoogle Generative AI의 응답:")
    print(response)
