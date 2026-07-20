# -*- coding: utf-8 -*-
"""
Health Simulation Module using Counterfactual Explanation
Analyzes how changes in lifestyle habits (exercise, sleep, weight), blood pressure,
and smoking cessation impact the 10-year CVD risk percentage, highlighting the top N recommendations.
"""

'''
[중요 - 모델 한계 명시]
아래 계수(체중→콜레스테롤/혈압, 운동→HDL/혈압, 수면→혈압 영향) 중 
체중→혈압 관계는 AHA/ACC 2025 가이드라인 및 관련 메타분석에서 확인된 
수치를 보수적으로 반영하였다. 나머지 계수(체중→콜레스테롤, 운동→HDL, 
수면→혈압)는 방향성과 대략적인 크기는 문헌에서 확인되나, 본 모델에서 
사용한 "주당/1kg당 선형 비례" 형태의 정확한 수치를 직접 제시하는 
단일 문헌은 확인하지 못했다. 이는 개념 실증(proof-of-concept) 목적의 
근사 모델이며, 정밀한 의학적 예측치로 해석되어서는 안 된다.
'''

import itertools
import logging
from framingham import calculate_multiple_risks
from constants import NO_EXERCISE, NO_TIME_FOR_SLEEP, DIET_ONLY, VALID_CONSTRAINTS

# 로거 설정
logger = logging.getLogger("health_twin_ai.simulation")

def _evaluate_single_combination(
    user_data: dict,
    base_risk_pct: float,
    exec_val: int,
    sleep_val: int,
    weight_chg: int,
    sbp_chg: int,
    smoker_val: bool,
    orig_exercise: int,
    orig_sleep: int,
    orig_tc: float,
    orig_hdl: float,
    orig_sbp: float,
    orig_smoker: bool
) -> dict:
    """
    개별 생활습관 조합에 대한 가상 환자 정보 업데이트 및 위험도 개선율을 평가합니다.
    """
    # A. 체중 변화가 콜레스테롤과 혈압에 미치는 영향
    tc_impact_weight = weight_chg * 1.5   # 근거: 체중감량과 콜레스테롤 개선의 전반적 연관성은 다수 문헌에서 확인되나(예: 5-10% 체중감량 시 개선), 1kg당 정량적 수치를 제시하는 문헌은 확인하지 못함. 임상적으로 알려진 일반 경향에 기반한 근사치 (특정 논문 수치 아님).
    sbp_impact_weight = weight_chg * 0.5  # 근거: AHA/ACC 2025 고혈압 가이드라인 및 Neter et al. (Hypertension, 2003) 메타분석은 체중 1kg 감량당 약 1.0mmHg의 수축기혈압 감소를 보고함. 본 모델은 보수적 추정을 위해 0.5mmHg로 설정함 (원 문헌 수치의 약 절반).
    
    # B. 운동 횟수 변화가 HDL 및 혈압에 미치는 영향
    exec_diff = exec_val - orig_exercise
    hdl_impact_exec = exec_diff * 1.0     # 근거: AHA(2021) 신체활동 권고 발표는 신체활동 증가 시 HDL +1~2mg/dL, 수축기혈압 -3~4mmHg의 전반적 효과를 보고함. 본 모델은 이를 주당 운동 횟수에 비례하는 선형 근사로 단순화하였으며, 원 문헌은 '주당 1회 증가'를 직접 규정하지 않음에 유의.
    sbp_impact_exec = exec_diff * -0.8    # 근거: AHA(2021) 신체활동 권고 발표는 신체활동 증가 시 HDL +1~2mg/dL, 수축기혈압 -3~4mmHg의 전반적 효과를 보고함. 본 모델은 이를 주당 운동 횟수에 비례하는 선형 근사로 단순화하였으며, 원 문헌은 '주당 1회 증가'를 직접 규정하지 않음에 유의.
    
    # C. 수면 시간 변화가 혈압에 미치는 영향
    sleep_diff = sleep_val - orig_sleep
    sbp_impact_sleep = sleep_diff * -0.5  # 근거: 수면시간과 혈압의 연관성은 다수 문헌에서 확인되나 (예: 수면 1시간 증가당 고혈압 위험 감소 경향), 연구 간 수치 편차가 커서 단일 확정 수치를 제시하기 어려움. 임상적으로 알려진 일반 경향에 기반한 근사치.
    
    # 생리학적 하한선 적용
    new_tc = max(100.0, orig_tc + tc_impact_weight)
    new_hdl = max(15.0, orig_hdl + hdl_impact_exec)
    
    total_sbp_change = sbp_impact_weight + sbp_impact_exec + sbp_impact_sleep + sbp_chg
    new_sbp = max(80.0, orig_sbp + total_sbp_change)
    
    sim_user_data = user_data.copy()
    sim_user_data["total_cholesterol"] = new_tc
    sim_user_data["hdl"] = new_hdl
    sim_user_data["systolic_bp"] = new_sbp
    sim_user_data["exercise_per_week"] = exec_val
    sim_user_data["sleep_hours"] = sleep_val
    sim_user_data["smoker"] = smoker_val
    
    new_risks = calculate_multiple_risks(sim_user_data)
    new_risk_pct = new_risks["cardiovascular_10y"]["risk_percent"]
    improvement = base_risk_pct - new_risk_pct
    
    # 요약 메시지 생성
    summary_parts = []
    
    # 흡연 변화 요약 (금연 시나리오)
    if orig_smoker and not smoker_val:
        summary_parts.append("금연")

    if weight_chg < 0:
        summary_parts.append(f"체중 {abs(weight_chg)}kg 감량")
    elif weight_chg > 0:
        summary_parts.append(f"체중 {weight_chg}kg 증가")
        
    if exec_diff > 0:
        summary_parts.append(f"주당 운동 횟수를 {exec_val}회로 조정")
    elif exec_diff < 0:
        summary_parts.append(f"주당 운동 횟수를 {exec_val}회로 조정")
        
    if sleep_diff > 0:
        summary_parts.append(f"수면 시간을 하루 {sleep_val}시간으로 조절")
    elif sleep_diff < 0:
        summary_parts.append(f"수면 시간을 하루 {sleep_val}시간으로 조절")
        
    if sbp_chg < 0:
        summary_parts.append(f"수축기 혈압 조절치 {abs(sbp_chg)}mmHg 감축")
        
    if not summary_parts:
        summary_str = "현재 생활습관 유지"
    else:
        summary_str = f"{', '.join(summary_parts)} 조합안"
        
    return {
        "changes": {
            "exercise_per_week": exec_val,
            "sleep_hours": sleep_val,
            "weight_change_kg": weight_chg,
            "systolic_bp_change": sbp_chg,
            "smoker": smoker_val
        },
        "new_risks": new_risks,
        "improvement_percent": round(improvement, 1),
        "improvement_summary": summary_str
    }

def _are_recommendations_similar(c1: dict, c2: dict) -> bool:
    """
    추천 다양성 판단 함수:
    두 추천 조합(c1, c2)의 5개 핵심 변수(체중, 혈압, 운동, 수면, 금연)를 비교하여,
    미세 수치만 동일한 유사/중복 추천인지를 엄격하게 판정합니다.
    """
    ch1 = c1.get("changes", {})
    ch2 = c2.get("changes", {})
    
    t1 = c1.get("recommendation_type")
    t2 = c2.get("recommendation_type")
    
    # 단일 레버(single_lever)끼리의 비교인 경우:
    # 변경된 타겟 변수가 다르면(예: 하나는 혈압만 -20, 하나는 체중만 -10) 서로 다른 주 전략이므로 유사하지 않음.
    if t1 == "single_lever" and t2 == "single_lever":
        keys1 = {k for k, v in ch1.items() if (k == "weight_change_kg" and v != 0) or (k == "systolic_bp_change" and v != 0) or (k == "exercise_per_week" and v != c1.get("_orig_exercise")) or (k == "sleep_hours" and v != c1.get("_orig_sleep")) or (k == "smoker" and v is False)}
        keys2 = {k for k, v in ch2.items() if (k == "weight_change_kg" and v != 0) or (k == "systolic_bp_change" and v != 0) or (k == "exercise_per_week" and v != c2.get("_orig_exercise")) or (k == "sleep_hours" and v != c2.get("_orig_sleep")) or (k == "smoker" and v is False)}
        if keys1 and keys2 and keys1 != keys2:
            return False

    # 1. 체중 변화 차이 (2kg 이내 미세 차이면 유사)
    w1, w2 = ch1.get("weight_change_kg", 0), ch2.get("weight_change_kg", 0)
    w_same = abs(w1 - w2) <= 2
    
    # 2. 혈압 변화 차이 (5mmHg 이내 미세 차이면 유사)
    sbp1, sbp2 = ch1.get("systolic_bp_change", 0), ch2.get("systolic_bp_change", 0)
    sbp_same = abs(sbp1 - sbp2) <= 5
    
    # 3. 운동 횟수 차이
    ex1, ex2 = ch1.get("exercise_per_week"), ch2.get("exercise_per_week")
    ex_same = (ex1 == ex2)
    
    # 4. 수면 시간 차이
    sl1, sl2 = ch1.get("sleep_hours"), ch2.get("sleep_hours")
    sl_same = (sl1 == sl2)
    
    # 5. 금연 여부
    sm1, sm2 = ch1.get("smoker"), ch2.get("smoker")
    sm_same = (sm1 == sm2)
    
    same_count = sum([w_same, sbp_same, ex_same, sl_same, sm_same])
    
    # 5개 변수 중 4개 이상이 거의 동일하여 미세한 수치 차이에 불과한 경우 유사 추천으로 정화
    return same_count >= 4

def generate_counterfactuals(user_data: dict, top_n: int = 3, user_constraint: str = None) -> list:
    """
    사용자의 건강 지표 및 생활습관 가상 시뮬레이션을 수행하여
    다양성 로직(단일 레버 2개 + 복합 개선안 1개, 변수 2개 이상 차이 필수)을 바탕으로 상위 N개 추천을 반환합니다.
    """
    
    # 1. 제약 조건 입력 유효성 검사 및 정비
    if user_constraint is not None and user_constraint not in VALID_CONSTRAINTS:
        logger.warning("Invalid constraint, ignoring: %s", user_constraint)
        user_constraint = None
        
    # 기본 임상값 추출
    orig_exercise = user_data.get("exercise_per_week", 2)
    orig_sleep = user_data.get("sleep_hours", 6)
    orig_tc = user_data.get("total_cholesterol", 200.0)
    orig_hdl = user_data.get("hdl", 50.0)
    orig_sbp = user_data.get("systolic_bp", 120.0)
    orig_smoker = bool(user_data.get("smoker", False))
    
    # 기본 위험도 계산
    base_risks = calculate_multiple_risks(user_data)
    base_risk_pct = base_risks["cardiovascular_10y"]["risk_percent"]
    
    # 탐색 변수 기본값 범위
    exercise_options = range(1, 6)            # 1~5회
    sleep_options = range(5, 9)               # 5~8시간
    weight_change_options = range(-10, 4, 1)  # -10kg ~ +3kg
    sbp_change_options = range(-20, 1, 5)     # -20 ~ 0 mmHg
    smoker_options = [True, False] if orig_smoker else [False]  # 흡연자인 경우 금연 시나리오 포함
    
    # 제약 사항에 따른 탐색 범위 조정
    if user_constraint == NO_EXERCISE:
        exercise_options = [orig_exercise]
    elif user_constraint == NO_TIME_FOR_SLEEP:
        sleep_options = [orig_sleep]
    elif user_constraint == DIET_ONLY:
        weight_change_options = range(-5, 4, 1)  # 체중감량의 하한을 -5kg로 제한
        
    # --- 1단계: 단일 레버(Single Lever) 추천 계산 ---
    single_lever_candidates = []
    
    # (1) 운동만 변화
    if user_constraint != NO_EXERCISE:
        local_best = None
        for exec_val in exercise_options:
            if exec_val == orig_exercise:
                continue
            res = _evaluate_single_combination(
                user_data, base_risk_pct, exec_val, orig_sleep, 0, 0, orig_smoker,
                orig_exercise, orig_sleep, orig_tc, orig_hdl, orig_sbp, orig_smoker
            )
            if local_best is None or res["improvement_percent"] > local_best["improvement_percent"]:
                local_best = res
        if local_best:
            local_best["recommendation_type"] = "single_lever"
            local_best["_orig_exercise"] = orig_exercise
            local_best["_orig_sleep"] = orig_sleep
            single_lever_candidates.append(local_best)
            
    # (2) 체중만 변화
    local_best = None
    for weight_chg in weight_change_options:
        if weight_chg == 0:
            continue
        res = _evaluate_single_combination(
            user_data, base_risk_pct, orig_exercise, orig_sleep, weight_chg, 0, orig_smoker,
            orig_exercise, orig_sleep, orig_tc, orig_hdl, orig_sbp, orig_smoker
        )
        if local_best is None or res["improvement_percent"] > local_best["improvement_percent"]:
            local_best = res
    if local_best:
        local_best["recommendation_type"] = "single_lever"
        local_best["_orig_exercise"] = orig_exercise
        local_best["_orig_sleep"] = orig_sleep
        single_lever_candidates.append(local_best)
        
    # (3) 수면만 변화
    if user_constraint != NO_TIME_FOR_SLEEP:
        local_best = None
        for sleep_val in sleep_options:
            if sleep_val == orig_sleep:
                continue
            res = _evaluate_single_combination(
                user_data, base_risk_pct, orig_exercise, sleep_val, 0, 0, orig_smoker,
                orig_exercise, orig_sleep, orig_tc, orig_hdl, orig_sbp, orig_smoker
            )
            if local_best is None or res["improvement_percent"] > local_best["improvement_percent"]:
                local_best = res
        if local_best:
            local_best["recommendation_type"] = "single_lever"
            local_best["_orig_exercise"] = orig_exercise
            local_best["_orig_sleep"] = orig_sleep
            single_lever_candidates.append(local_best)
            
    # (4) 혈압관리만 변화
    local_best = None
    for sbp_chg in sbp_change_options:
        if sbp_chg == 0:
            continue
        res = _evaluate_single_combination(
            user_data, base_risk_pct, orig_exercise, orig_sleep, 0, sbp_chg, orig_smoker,
            orig_exercise, orig_sleep, orig_tc, orig_hdl, orig_sbp, orig_smoker
        )
        if local_best is None or res["improvement_percent"] > local_best["improvement_percent"]:
            local_best = res
    if local_best:
        local_best["recommendation_type"] = "single_lever"
        local_best["_orig_exercise"] = orig_exercise
        local_best["_orig_sleep"] = orig_sleep
        single_lever_candidates.append(local_best)

    # (5) 금연만 변화 (사용자가 흡연자인 경우)
    if orig_smoker:
        res_quit = _evaluate_single_combination(
            user_data, base_risk_pct, orig_exercise, orig_sleep, 0, 0, False,
            orig_exercise, orig_sleep, orig_tc, orig_hdl, orig_sbp, orig_smoker
        )
        res_quit["recommendation_type"] = "single_lever"
        res_quit["_orig_exercise"] = orig_exercise
        res_quit["_orig_sleep"] = orig_sleep
        single_lever_candidates.append(res_quit)
        
    # 단일 레버 후보군 정렬 (개선율 내림차순)
    single_lever_candidates.sort(key=lambda x: x["improvement_percent"], reverse=True)
    
    # --- 2단계: 복합 개선안(Combined) 계산 ---
    all_combined_candidates = []
    positive_combined_candidates = []
    
    for exec_val, sleep_val, weight_chg, sbp_chg, smoker_val in itertools.product(
        exercise_options, sleep_options, weight_change_options, sbp_change_options, smoker_options
    ):
        # 모든 변수가 원래 값인 케이스 제외
        if (exec_val == orig_exercise and sleep_val == orig_sleep and 
            weight_chg == 0 and sbp_chg == 0 and smoker_val == orig_smoker):
            continue
            
        res = _evaluate_single_combination(
            user_data, base_risk_pct, exec_val, sleep_val, weight_chg, sbp_chg, smoker_val,
            orig_exercise, orig_sleep, orig_tc, orig_hdl, orig_sbp, orig_smoker
        )
        res["recommendation_type"] = "combined"
        res["_orig_exercise"] = orig_exercise
        res["_orig_sleep"] = orig_sleep
        all_combined_candidates.append(res)
        if res["improvement_percent"] > 0:
            positive_combined_candidates.append(res)
            
    # 정렬
    all_combined_candidates.sort(key=lambda x: x["improvement_percent"], reverse=True)
    positive_combined_candidates.sort(key=lambda x: x["improvement_percent"], reverse=True)
    
    # --- 3단계: 다양성 판단 규칙 기반 Top 3 추출 (단일 레버 2개 + 복합 개선 1개) ---
    positive_single_levers = [c for c in single_lever_candidates if c["improvement_percent"] > 0]
    
    final_recommendations = []
    
    def _is_similar_to_any(candidate, selected_list):
        for s in selected_list:
            if _are_recommendations_similar(candidate, s):
                return True
        return False

    # (1) 단일 레버 상위 2개 선정 (서로 다른 독립 전략 2개 선택)
    for cand in positive_single_levers:
        if len([c for c in final_recommendations if c.get("recommendation_type") == "single_lever"]) >= 2:
            break
        if not _is_similar_to_any(cand, final_recommendations):
            final_recommendations.append(cand)
            
    # (2) 복합 개선 최적 1개 선정 (단일 레버들과 4개 이상 변수가 겹치지 않고 90% 이상 동일하지 않은 최적 1개)
    for cand in positive_combined_candidates:
        if len([c for c in final_recommendations if c.get("recommendation_type") == "combined"]) >= 1:
            break
        if not _is_similar_to_any(cand, final_recommendations):
            final_recommendations.append(cand)
            
    # (3) 부족분 보충 (유사도 필터링을 지키며 보충)
    all_positive = positive_single_levers + positive_combined_candidates
    all_positive.sort(key=lambda x: x["improvement_percent"], reverse=True)
    
    for cand in all_positive:
        if len(final_recommendations) >= top_n:
            break
        if not _is_similar_to_any(cand, final_recommendations):
            final_recommendations.append(cand)
            
    # --- 4단계: 극단적 고위험군 안전장치 ---
    if len(final_recommendations) < top_n:
        all_candidates = single_lever_candidates + all_combined_candidates
        all_candidates.sort(key=lambda x: x["improvement_percent"], reverse=True)
        
        for cand in all_candidates:
            if len(final_recommendations) >= top_n:
                break
            if not _is_similar_to_any(cand, final_recommendations):
                if cand["improvement_percent"] <= 0:
                    cand["note"] = "이미 위험 요인이 높아 추가 개선 효과가 제한적일 수 있습니다"
                final_recommendations.append(cand)
                
    # 반환 객체에서 임시 키 제거
    for r in final_recommendations:
        r.pop("_orig_exercise", None)
        r.pop("_orig_sleep", None)
        
    return final_recommendations[:top_n]
