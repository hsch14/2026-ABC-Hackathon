# ❤️ Health Twin AI - 심혈관 건강 Twin 시뮬레이터 & AI 대시보드

> **Counterfactual Explanation** 기반의 10년 심혈관 질환(CVD) 위험도 시뮬레이션 및 Llama-3.3 지능형 AI 맞춤 리포트·챗봇 대시보드 시스템입니다.

---

## 📌 1. 프로젝트 개요 (Overview)

**Health Twin AI**는 사용자의 임상 데이터(나이, 성별, 콜레스테롤, 수축기 혈압, 당뇨 여부 등)와 평상시 생활습관(주당 운동 횟수, 하루 수면 시간)을 분석하여, **향후 10년 내 심혈관 질환 발생 위험도**를 산출하고 **최적의 예방 행동 변화 시나리오(Counterfactual Top 3)**를 예측하는 인공지능 헬스케어 플랫폼입니다.

---

## ✨ 2. 핵심 기능 (Key Features)

### 📊 1) Framingham Risk Score 연산 엔진 (`framingham.py`)
- **원논문 수식 충실 반영**: D'Agostino et al. (2008) 원논문 코호트 연령 기준인 **`30 <= age <= 74`** 범위를 엄격하게 준수합니다.
- **다빈치 위험도 수치화**: 포인트(Points) 및 10년 CVD 위험 비율(%) 계산과 함께 위험 등급(저위험군, 중위험군, 고위험군)을 평가합니다.

### 🌟 2) Counterfactual 예방 시나리오 탐색 엔진 (`simulation.py`)
- **다양성(Diversity) 기반 Top 3 대안 제시**: 체중 숫자가 미세하게 겹치는 무의미한 중복 추천을 배제하고, **독립적인 행동 전략 카테고리**를 보장합니다.
  - **Top 1**: 위험도 감축 효과가 가장 높은 최적 종합 개선안 (Combined)
  - **Top 2**: Top 1에서 사용하지 않은 남은 레버(운동/수면/체중/혈압)의 최적 단일 개선안 (Single Lever)
  - **Top 3**: Top 1과 Top 2에서 사용하지 않은 차순위 남은 레버의 단일 개선안 (Single Lever)
- **실천 가능한 변화(Changes) 중심 표시**: 유지되는 기존 습관은 제외하고, 사용자가 **직접 실천해야 하는 변화 수치(Delta)**만 깔끔하게 시각화합니다.
- **제약 조건(Constraints) 연동**: `운동이 어려움(NO_EXERCISE)`, `야근이 많음(NO_TIME_FOR_SLEEP)`, `식단 조절이 어려움(DIET_ONLY)` 등 개인의 생활 제약에 맞춘 우회 대안을 자동 산출합니다.

### ✍️ 3) AI 맞춤 설명 리포트 (`explanation.py`)
- **Llama-3.3-70b 연동**: Groq API 기반의 LLM을 사용하여 임상 델타 수치를 쉽게 이해할 수 있는 한글 자연어 설명서로 재구성합니다.
- **Graceful Fallback 템플릿 엔진**: API Key 미등록, 네트워크 장애, 스키마 유효성 오류 발생 시 에러 없이 파이썬 내장 템플릿 엔진으로 즉시 복구 렌더링합니다.

### 💬 4) 안전한 AI 건강 상담 챗봇 (`dashboard.py`)
- **Prompt Injection 방어벽 탑재**: "의사 행세를 하라", "시스템 프롬프트를 공개하라" 등의 공격 문구를 완벽히 차단합니다.
- **의료 처방 금지 및 내원 유도**: 의학적 진단/처방 요청 시 `"이 부분은 병원에서 전문의와 상담하시는 것이 안전합니다"` 문구로 환자의 병원 방문을 안전하게 유도합니다.

---

## 🛠️ 3. 시스템 아키텍처 (Architecture)

```text
ABC-Hackathon-Free Contest/
├── dashboard.py               # Streamlit 대시보드 UI, 챗봇 및 로그 제어
├── simulation.py              # Counterfactual 시뮬레이션 & Top3 다양성 엔진
├── framingham.py              # Framingham Risk Score 10년 CVD 연산 모듈
├── explanation.py             # LLM Prompt 연동 & Fallback 리포트 생성 모듈
├── constants.py               # 시스템 상수 (제약조건 명칭, LLM 하이퍼파라미터)
├── verify_changes.py          # 12개 통합 기능 회귀 검증 자동화 스크립트
├── verify_chatbot_safety.py   # Prompt Injection 5대 공격 자동 검증 스크립트
└── README.md                  # 프로젝트 안내 문서
```

---

## 🚀 4. 설치 및 실행 가이드 (Getting Started)

### 요구 사항 (Prerequisites)
- **Python**: 3.10 이상
- **패키지**: Streamlit, Requests 등

### 1) 프로젝트 저장소 복제 (Clone)
```bash
git clone https://github.com/hsch14/ABC-Hackathon-Free-Contest.git
cd ABC-Hackathon-Free-Contest
```

### 2) 가상환경 구축 및 패키지 설치 (uv 추천)
```bash
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install streamlit
```

### 3) 대시보드 실행 (Run Streamlit App)
```bash
streamlit run dashboard.py
```
> 실행 후 브라우저에서 `http://localhost:8501` 주소로 접속합니다.

---

## 🧪 5. 검증 및 테스트 결과 (Validation & QA)

### 1) 통합 시나리오 검증 (`python verify_changes.py`)
- **검증 항목**: 나이 30~74세 예외 제약, 대시보드 UI 인자, Constraint 탐색 범위, Top 3 다양성 로직 등 **12개 검증 항목 전원 100% PASS**
```text
============================================================
   [최종 요약] 전체 12개 항목 중 12개 PASS, 0개 FAIL
============================================================
```

### 2) 챗봇 보안성 검증 (`python verify_chatbot_safety.py`)
- **검증 항목**: 의사 위장 진단 공격, 시스템 프롬프트 요구, API Key 노출 시도, 규칙 무시 시도 등 **5대 Prompt Injection 공격 100% SAFE 판정**

---

## 📄 6. 라이선스 및 출처 (License & Citation)

- **Framingham CVD Risk Score**: D'Agostino RB Sr, et al. *General Cardiovascular Risk Profile for Use in Primary Care: The Framingham Heart Study*. Circulation. 2008;117(6):743-753.
- **임상 출처**: AHA/ACC 2025 Hypertension Guidelines, Neter et al. (*Hypertension*, 2003) 메타분석 등.
