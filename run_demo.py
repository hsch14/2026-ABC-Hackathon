# -*- coding: utf-8 -*-
"""
Health Twin AI - Unified Execution Demo Script
Runs the entire health twin pipeline:
1. Calculates Base CVD Risk (framingham.py)
2. Runs Counterfactual Simulator (simulation.py)
3. Generates Natural Language Explanation (explanation.py)
4. Saves Execution Logs (logs/)
"""

import os
import json
from framingham import calculate_multiple_risks
from simulation import generate_counterfactuals
from explanation import generate_natural_explanation
from constants import NO_EXERCISE, NO_TIME_FOR_SLEEP

def main():
    print("=" * 60)
    print("   [Health Twin AI] 통합 파이프라인 데모 실행을 시작합니다.")
    print("=" * 60)
    
    # 1. 시뮬레이션용 사용자 건강 정보 프로필 정의 (55세 남성 고위험군 예시)
    user_profile = {
        "age": 55,
        "gender": "male",
        "total_cholesterol": 210.0,
        "hdl": 36.0,
        "systolic_bp": 145.0,
        "treated_bp": True,
        "smoker": False,
        "diabetes": True,
        "exercise_per_week": 1,
        "sleep_hours": 5
    }
    print(f"\n[Step 1] 사용자 기초 건강 프로필 입력:")
    print(json.dumps(user_profile, indent=2))
    
    # 2. 기존(Base) 심혈관 위험도 산출 (framingham.py)
    print("\n[Step 2] 기본 10년 심혈관 질환(CVD) 위험도 산출 중...")
    base_results = calculate_multiple_risks(user_profile)
    base_risk = base_results["cardiovascular_10y"]
    print(f"  - 계산 결과 점수: {base_risk['points']}점")
    print(f"  - 10년 내 질환 가능성: {base_risk['risk_percent']}%")
    print(f"  - 위험군 분류: {base_risk['risk_level'].upper()}")
    
    # 3. Counterfactual 시뮬레이션 실행 (simulation.py)
    # 1,400개 조합 분석을 통한 상위 3개 조합 추천 생성
    print("\n[Step 3] Counterfactual 시뮬레이션 가동 (생활습관 개선안 탐색)...")
    sim_results = generate_counterfactuals(user_profile, top_n=3)
    
    print("  - 최적의 개선 제안 Top 3:")
    for idx, rec in enumerate(sim_results, 1):
        print(f"    [{idx}위 추천] 개선율: {rec['improvement_percent']}%p 감소")
        print(f"      * 내용: {rec['improvement_summary']}")
        print(f"      * 목표: {rec['changes']}")
        print(f"      * 변경 후 위험 가능성: {rec['new_risks']['cardiovascular_10y']['risk_percent']}%")
        
    # 4. 자연어 설명 및 조언 생성 (explanation.py)
    # API 키 상태 체크 (API 키 유무에 따라 LLM 모드 또는 Fallback 템플릿 모드로 동작)
    api_key_status = "설정됨 (LLM 모드 작동)" if os.environ.get("GROQ_API_KEY") else "미설정 (안전 템플릿 Fallback 모드 작동)"
    print(f"\n[Step 4] 자연어 설명서 생성 가동 (API Key 상태: {api_key_status})...")
    
    # 운동 불가 제약 조건(NO_EXERCISE)을 상황 제약으로 전달
    explanation = generate_natural_explanation(
        user_data=user_profile,
        current_result=base_risk,
        counterfactual_results=sim_results,
        user_constraint=NO_EXERCISE
    )
    
    print("\n" + "-" * 50)
    print("   [사용자 대상 건강 정보 자연어 설명 리포트]")
    print("-" * 50)
    print(f"■ 기존 건강 상태 요약:\n{explanation['current_risk_summary']}\n")
    print("■ 최적 생활습관 추천 개선안:")
    for idx, rec_desc in enumerate(explanation["recommendations"], 1):
        print(f"  {idx}. {rec_desc['title']}")
        print(f"     -> {rec_desc['description']}")
    print(f"\n■ 최선의 행동 제안:\n{explanation['best_action']}\n")
    print(f"■ 상황별 제약조건(운동 부족) 맞춤 조언:\n{explanation['constraint_advice']}")
    print("-" * 50)
    
    # 5. 실행 결과 메타데이터 확인
    print(f"\n[Step 5] 시뮬레이션 실행 메타데이터:")
    print(f"  - 데이터 생성 방식: {explanation['generated_by'].upper()}")
    print(f"  - 사용 모델: {explanation['model']}")
    print(f"  - 전체 소요 시간: {explanation['latency_ms']} ms")
    print(f"  - API 재시도 횟수: {explanation['retry_count']}")
    print(f"  - Fallback 가동 여부: {explanation['fallback']}")
    print(f"  - 발생 오류 로그: {explanation['error']}")
    print(f"  - 최신 로그 파일 저장 완료: logs/latest.json")
    print("=" * 60)
    print("   데모 실행이 완료되었습니다.")
    print("=" * 60)

if __name__ == "__main__":
    main()
