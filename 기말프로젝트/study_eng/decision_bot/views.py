from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import google.generativeai as genai
import re

# Google Generative AI 설정
def configure_genai():
    GOOGLE_API_KEY = "AIzaSyAsTk4zj6gmewYEdZnOBhjChDW2dkb6dwk"
    genai.configure(api_key=GOOGLE_API_KEY)

# 분석 텍스트를 섹션별로 파싱하는 함수
def parse_and_format_analysis(analysis_text):
    sections = {
        "오류 내용 출력": "",
        "영어 문장에서 사용된 문법 규칙": "",
        "의미와 스타일 개선을 위한 제안": "",
        "수정된 한국어 번역": "",
    }

    analysis_text = re.sub(r"[^a-zA-Z가-힣0-9\s:()\*\'\".,]+", "", analysis_text)
    section_pattern = re.compile(r"\*\*(.+?):\*\*")

    current_section = None
    for line in analysis_text.split("\n"):
        line = line.strip()

        match = section_pattern.match(line)
        if match:
            section_title = match.group(1).strip()
            content = line[match.end():].strip()
            if section_title in sections:
                current_section = section_title
                sections[current_section] = content
            else:
                current_section = None
        elif current_section:
            sections[current_section] += " " + line.strip()

    for section in sections:
        sections[section] = re.sub(r'["]', '', sections[section]).strip()

    # Formatting the "영어 문장에서 사용된 문법 규칙" section for better readability
    if sections["영어 문장에서 사용된 문법 규칙"]:
        grammar_rules = re.findall(r"([^:]+): ([^()]+) \(([^)]+)\)", sections["영어 문장에서 사용된 문법 규칙"])
        formatted_rules = "<ul>"
        for term, description, details in grammar_rules:
            formatted_rules += f"<li><strong>{term.strip()}</strong>: {description.strip()} ({details.strip()})</li>"
        formatted_rules += "</ul>"
        sections["영어 문장에서 사용된 문법 규칙"] = formatted_rules

    return sections

# 추가: 문법 설명 세부 정보 생성 함수
def generate_grammar_details(grammar_rules):
    detailed_explanations = {
        "the": "The is a definite article used to refer to a specific noun that is already known to the listener or reader.",
        "cat": "Cat is a noun that represents a type of animal, commonly domesticated.",
        "sat": "Sat is the past tense of the verb sit, indicating a past action of resting on a surface.",
        "on": "On is a preposition used to indicate a position above or in contact with a surface.",
        "mat": "Mat is a noun referring to a piece of material placed on the floor for various purposes, such as comfort or cleanliness."
    }

    explanations = "<ul>"
    for rule in grammar_rules:
        term = rule[0].strip()
        explanation = detailed_explanations.get(term.lower(), "No detailed explanation available.")
        explanations += f"<li><strong>{term}:</strong> {explanation}</li>"
    explanations += "</ul>"

    return explanations

@csrf_exempt
def analyze_translation(request):
    if request.method == 'GET':
        try:
            # Generative AI 초기화
            configure_genai()
            model = genai.GenerativeModel('gemini-pro')

            # 영어 문장 생성
            google_prompt = "Please make an English sentence."
            google_response = model.generate_content(google_prompt)

            if google_response and hasattr(google_response, 'text'):
                english_sentence = google_response.text

                # 세션에 영어 문장 저장
                request.session['english_sentence'] = english_sentence

                return render(request, 'decision_bot/index.html', {'english_sentence': english_sentence})
            else:
                return render(request, 'decision_bot/index.html', {'error': '영어 문장을 생성할 수 없습니다.'})

        except Exception as e:
            return render(request, 'decision_bot/index.html', {'error': str(e)})

    elif request.method == 'POST':
        try:
            # 클라이언트에서 받은 데이터 파싱
            data = json.loads(request.body)
            korean_translation = data.get('korean_translation', '')

            if not korean_translation:
                return JsonResponse({'error': '한국어 번역을 제공해야 합니다.'}, status=400)

            # 세션에서 영어 문장 가져오기
            english_sentence = request.session.get('english_sentence', None)
            if not english_sentence:
                return JsonResponse({'error': '생성된 영어 문장이 없습니다. 먼저 GET 요청을 수행하세요.'}, status=400)

            # 프롬프트 생성
            translated_prompt = f"""
            이 문장을 한국어로 번역하고 분석하세요:
            영어: {english_sentence}
            한국어: {korean_translation}

            아래 양식에 맞추어 영어 문장을 상세히 분석하고 아래 양식과 철저히 똑같이 출력하세요.:
            - 오류 내용 출력(번역된 문장에 오류가 있다면 [의미 오류, 구문 오류, 단어 선택 오류, 어순 오류 ,문화적 오류]중 선택하고 오류 내용 출력, ex **오류 내용 출력 :** 구문 오류 "뜀"은 동작을 나타내는 명사이지만, 영어 문장에서는 동작을 나타내는 동사 "jumps"가 사용되었습니다.) : 
            - 영어 문장에서 사용된 문법 규칙(ex **영어 문장에서 사용된 문법 규칙 :** "the" : 특정 명사를 가리킴 (정관사), "fox" and "dog" : 명사 (사물이나 생물을 나타냄), "jumped" : 과거형 동사 (과거의 동작이나 상태를 나타냄), "over" : 전치사 (위치 관계를 표현함).):
            - 의미와 스타일 개선을 위한 제안(더 명확하거나 자연스러운 표현이 있다면 그 표현에 대해서만 써줘). : 
            - 수정된 한국어 번역(있으면 주고 없으면 없다고 표기) : 
            """

            # Generative AI 요청
            configure_genai()
            model = genai.GenerativeModel('gemini-pro')
            translated_response = model.generate_content(translated_prompt)

            if translated_response and hasattr(translated_response, 'text'):
                analysis_text = translated_response.text
                formatted_analysis = parse_and_format_analysis(analysis_text)

                # 추가: 상세 문법 설명 생성
                grammar_rules = re.findall(r"([^:]+): ([^()]+) \(([^)]+)\)", formatted_analysis["영어 문장에서 사용된 문법 규칙"])
                detailed_explanation = generate_grammar_details(grammar_rules)

                return JsonResponse({
                    'english_sentence': english_sentence,
                    'korean_translation': korean_translation,
                    'analysis': formatted_analysis,
                    'grammar_details': detailed_explanation
                })
            else:
                return JsonResponse({'error': 'AI 응답을 생성할 수 없습니다.'}, status=500)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        try:
            # 세션 데이터 초기화
            if 'english_sentence' in request.session:
                del request.session['english_sentence']

            return JsonResponse({'message': 'Session data has been reset.'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)