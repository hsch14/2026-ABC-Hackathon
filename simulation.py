# -*- coding: utf-8 -*-
"""
Health Simulation Module using Counterfactual Explanation
Analyzes how changes in lifestyle habits (exercise, sleep, weight) and blood pressure
impact the 10-year CVD risk percentage, highlighting the top N recommendations.
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
    orig_exercise: int,
    orig_sleep: int,
    orig_tc: float,
    orig_hdl: float,
    orig_sbp: float
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
    
    new_risks = calculate_multiple_risks(sim_user_data)
    new_risk_pct = new_risks["cardiovascular_10y"]["risk_percent"]
    improvement = base_risk_pct - new_risk_pct
    
    # 요약 메시지 생성
    summary_parts = []
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
            "systolic_bp_change": sbp_chg
        },
        "new_risks": new_risks,
        "improvement_percent": round(improvement, 1),
        "improvement_summary": summary_str
    }

def generate_counterfactuals(user_data: dict, top_n: int = 3, user_constraint: str = None) -> list:
    """
    사용자의 건강 지표 및 생활습관 가상 시뮬레이션을 수행하여
    다양성 로직(단일 레버와 종합 개선안 비례 조합)을 바탕으로 상위 N개 추천을 반환합니다.
    
    Parameters:
        user_data (dict): 사용자 임상 및 생활습관 정보
        top_n (int): 추천할 상위 조합 개수 (기본값: 3)
        user_constraint (str): 상황별 제약조건 조건 명칭
        
    Returns:
        list[dict]: 상위 N개 추천 결과 리스트
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
    
    # 기본 위험도 계산
    base_risks = calculate_multiple_risks(user_data)
    base_risk_pct = base_risks["cardiovascular_10y"]["risk_percent"]
    
    # 탐색 변수 기본값 범위
    exercise_options = range(1, 6)            # 1~5회
    sleep_options = range(5, 9)               # 5~8시간
    weight_change_options = range(-10, 4, 1)  # -10kg ~ +3kg
    sbp_change_options = range(-20, 1, 5)     # -20 ~ 0 mmHg
    
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
                user_data, base_risk_pct, exec_val, orig_sleep, 0, 0,
                orig_exercise, orig_sleep, orig_tc, orig_hdl, orig_sbp
            )
            if local_best is None or res["improvement_percent"] > local_best["improvement_percent"]:
                local_best = res
        if local_best and local_best["improvement_percent"] > 0:
            local_best["recommendation_type"] = "single_lever"
            single_lever_candidates.append(local_best)
            
    # (2) 체중만 변화
    local_best = None
    for weight_chg in weight_change_options:
        if weight_chg == 0:
            continue
        res = _evaluate_single_combination(
            user_data, base_risk_pct, orig_exercise, orig_sleep, weight_chg, 0,
            orig_exercise, orig_sleep, orig_tc, orig_hdl, orig_sbp
        )
        if local_best is None or res["improvement_percent"] > local_best["improvement_percent"]:
            local_best = res
    if local_best and local_best["improvement_percent"] > 0:
        local_best["recommendation_type"] = "single_lever"
        single_lever_candidates.append(local_best)
        
    # (3) 수면만 변화
    if user_constraint != NO_TIME_FOR_SLEEP:
        local_best = None
        for sleep_val in sleep_options:
            if sleep_val == orig_sleep:
                continue
            res = _evaluate_single_combination(
                user_data, base_risk_pct, orig_exercise, sleep_val, 0, 0,
                orig_exercise, orig_sleep, orig_tc, orig_hdl, orig_sbp
            )
            if local_best is None or res["improvement_percent"] > local_best["improvement_percent"]:
                local_best = res
        if local_best and local_best["improvement_percent"] > 0:
            local_best["recommendation_type"] = "single_lever"
            single_lever_candidates.append(local_best)
            
    # (4) 혈압관리만 변화
    local_best = None
    for sbp_chg in sbp_change_options:
        if sbp_chg == 0:
            continue
        res = _evaluate_single_combination(
            user_data, base_risk_pct, orig_exercise, orig_sleep, 0, sbp_chg,
            orig_exercise, orig_sleep, orig_tc, orig_hdl, orig_sbp
        )
        if local_best is None or res["improvement_percent"] > local_best["improvement_percent"]:
            local_best = res
    if local_best and local_best["improvement_percent"] > 0:
        local_best["recommendation_type"] = "single_lever"
        single_lever_candidates.append(local_best)
        
    # 단일 레버 후보군 정렬 (개선율 내림차순)
    single_lever_candidates.sort(key=lambda x: x["improvement_percent"], reverse=True)
    
    # --- 2단계: 종합 개선안(Combined) 계산 ---
    # 전체 조합을 탐색하되, 속도가 느리다고 체감될 경우 functools.lru_cache 등의 캐싱을 호출부에 적용하는 것을 설계 고려 가능함.
    combined_candidates = []
    for exec_val, sleep_val, weight_chg, sbp_chg in itertools.product(
        exercise_options, sleep_options, weight_change_options, sbp_change_options
    ):
        # 모든 변수가 원래 값인 케이스 제외
        if exec_val == orig_exercise and sleep_val == orig_sleep and weight_chg == 0 and sbp_chg == 0:
            continue
            
        res = _evaluate_single_combination(
            user_data, base_risk_pct, exec_val, sleep_val, weight_chg, sbp_chg,
            orig_exercise, orig_sleep, orig_tc, orig_hdl, orig_sbp
        )
        if res["improvement_percent"] > 0:
            res["recommendation_type"] = "combined"
            combined_candidates.append(res)
            
    # 개선율 내림차순 정렬
    combined_candidates.sort(key=lambda x: x["improvement_percent"], reverse=True)
    
    # --- 3단계: 최종 병합 및 다양성 기반 추출 ---
    # 비례 산출 (단일 레버 대 종합 대안 비율 ≈ 2:1)
    n_single = round(top_n * 2 / 3)
    n_combined = top_n - n_single
    
    final_recommendations = []
    used_changes = []
    
    def _is_duplicate(changes, used_list):
        for u in used_list:
            if u == changes:
                return True
        return False
        
    # (1) 단일 레버 추천 확보
    single_added = 0
    for cand in single_lever_candidates:
        if single_added >= n_single:
            break
        if not _is_duplicate(cand["changes"], used_changes):
            final_recommendations.append(cand)
            used_changes.append(cand["changes"])
            single_added += 1
            
    # (2) 종합 개선안 추천 확보
    combined_added = 0
    for cand in combined_candidates:
        if combined_added >= n_combined:
            break
        if not _is_duplicate(cand["changes"], used_changes):
            final_recommendations.append(cand)
            used_changes.append(cand["changes"])
            combined_added += 1
            
    # (3) 중복 제거 등으로 인해 개수가 모자란 경우 후순위 보충
    # 먼저 단일 레버에서 보충
    for cand in single_lever_candidates:
        if len(final_recommendations) >= top_n:
            break
        if not _is_duplicate(cand["changes"], used_changes):
            final_recommendations.append(cand)
            used_changes.append(cand["changes"])
            
    # 그 다음 종합 개선안에서 보충
    for cand in combined_candidates:
        if len(final_recommendations) >= top_n:
            break
        if not _is_duplicate(cand["changes"], used_changes):
            final_recommendations.append(cand)
            used_changes.append(cand["changes"])
            
    return final_recommendations[:top_n]
