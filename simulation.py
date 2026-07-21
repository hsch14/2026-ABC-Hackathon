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
    (smoker는 환자 입력 고정 변수이므로 탐색 변수에서 완전 제외)
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

def _category_overlap_score(new_categories: set, used_categories_list: list) -> int:
    """
    new_categories와 이미 사용된 카테고리 집합들 중 가장 많이 겹치는 
    정도를 반환한다. 0이면 완전히 다름(가장 좋음), 값이 클수록 
    겹치는 카테고리가 많음(다양성 낮음).
    """
    if not used_categories_list:
        return 0
    return min(len(new_categories & used) for used in used_categories_list)

def generate_counterfactuals(user_data: dict, top_n: int = 3, user_constraint: str = None) -> list:
    """
    Counterfactual 추천 알고리즘:
    - Top1: 전체 탐색 조합 중 위험도 감소가 가장 큰 최적 종합 개선안
    - Top2: Top1에서 사용하지 않은 미사용 레버 단일 추천 중 가장 효과가 큰 항목
    - Top3: Top1과 Top2에서 모두 사용하지 않은 남은 레버 단일 추천 중 가장 효과가 큰 항목
    (smoker는 탐색 변수에서 전면 제외되며 changes에는 오직 4개 키만 존재)
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
    
    # 탐색 변수 기본값 범위 (운동, 수면, 체중, 혈압 4개뿐!)
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
        
    CATEGORIES = ["exercise", "weight", "sleep", "sbp"]
    
    # --- 1. 각 카테고리별 최고의 단일 레버(Single Lever) 탐색 ---
    single_lever_dict = {}
    
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
            if local_best is None or res["improvement_percent"] > local_best["improvement_percent"] or (res["improvement_percent"] == local_best["improvement_percent"] and exec_val > local_best["changes"]["exercise_per_week"]):
                local_best = res
        if local_best:
            local_best["recommendation_type"] = "single_lever"
            local_best["category"] = "exercise"
            single_lever_dict["exercise"] = local_best

    # (2) 체중만 변화
    local_best = None
    for weight_chg in weight_change_options:
        if weight_chg == 0:
            continue
        res = _evaluate_single_combination(
            user_data, base_risk_pct, orig_exercise, orig_sleep, weight_chg, 0,
            orig_exercise, orig_sleep, orig_tc, orig_hdl, orig_sbp
        )
        if local_best is None or res["improvement_percent"] > local_best["improvement_percent"] or (res["improvement_percent"] == local_best["improvement_percent"] and weight_chg < local_best["changes"]["weight_change_kg"]):
            local_best = res
    if local_best:
        local_best["recommendation_type"] = "single_lever"
        local_best["category"] = "weight"
        single_lever_dict["weight"] = local_best

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
            if local_best is None or res["improvement_percent"] > local_best["improvement_percent"] or (res["improvement_percent"] == local_best["improvement_percent"] and sleep_val > local_best["changes"]["sleep_hours"]):
                local_best = res
        if local_best:
            local_best["recommendation_type"] = "single_lever"
            local_best["category"] = "sleep"
            single_lever_dict["sleep"] = local_best

    # (4) 혈압관리만 변화
    local_best = None
    for sbp_chg in sbp_change_options:
        if sbp_chg == 0:
            continue
        res = _evaluate_single_combination(
            user_data, base_risk_pct, orig_exercise, orig_sleep, 0, sbp_chg,
            orig_exercise, orig_sleep, orig_tc, orig_hdl, orig_sbp
        )
        if local_best is None or res["improvement_percent"] > local_best["improvement_percent"] or (res["improvement_percent"] == local_best["improvement_percent"] and sbp_chg < local_best["changes"]["systolic_bp_change"]):
            local_best = res
    if local_best:
        local_best["recommendation_type"] = "single_lever"
        local_best["category"] = "sbp"
        single_lever_dict["sbp"] = local_best

    def _get_active_categories(ch):
        cats = set()
        if ch.get("weight_change_kg", 0) != 0:
            cats.add("weight")
        if ch.get("systolic_bp_change", 0) != 0:
            cats.add("sbp")
        if ch.get("exercise_per_week") != orig_exercise:
            cats.add("exercise")
        if ch.get("sleep_hours") != orig_sleep:
            cats.add("sleep")
        return cats

    # --- 2. 전체 조합(복합 포함) 탐색 및 정렬 ---
    all_positive_candidates = []
    all_candidates_raw = []
    
    for exec_val, sleep_val, weight_chg, sbp_chg in itertools.product(
        exercise_options, sleep_options, weight_change_options, sbp_change_options
    ):
        if (exec_val == orig_exercise and sleep_val == orig_sleep and weight_chg == 0 and sbp_chg == 0):
            continue
        res = _evaluate_single_combination(
            user_data, base_risk_pct, exec_val, sleep_val, weight_chg, sbp_chg,
            orig_exercise, orig_sleep, orig_tc, orig_hdl, orig_sbp
        )
        # 단일 레버 여부 분류
        changed_count = sum([
            exec_val != orig_exercise,
            sleep_val != orig_sleep,
            weight_chg != 0,
            sbp_chg != 0
        ])
        res["recommendation_type"] = "single_lever" if changed_count == 1 else "combined"
        all_candidates_raw.append(res)
        if res["improvement_percent"] > 0:
            all_positive_candidates.append(res)
            
    # 개선율 우대 + 동일/유사 개선 구간 내 레버 개수가 적은(간결한) 조합 우선 정렬!
    all_positive_candidates.sort(
        key=lambda x: (
            round(x["improvement_percent"], 0),
            -len(_get_active_categories(x["changes"])),
            x["improvement_percent"]
        ),
        reverse=True
    )
    all_candidates_raw.sort(
        key=lambda x: (
            round(x["improvement_percent"], 0),
            -len(_get_active_categories(x["changes"])),
            x["improvement_percent"]
        ),
        reverse=True
    )

    # --- 3. Top1, Top2, Top3 단계별 추출 로직 ---
    final_recommendations = []
    used_categories = set()
    used_changes = []

    def _is_duplicate_change(ch, used_list):
        return ch in used_list

    # [Top 1]: 전체 조합 중 가장 위험도 감소가 큰 간결한 최적 조합
    candidate_pool_for_top1 = all_positive_candidates if all_positive_candidates else all_candidates_raw
    if candidate_pool_for_top1:
        top1 = candidate_pool_for_top1[0]
        final_recommendations.append(top1)
        used_changes.append(top1["changes"])
        used_categories.update(_get_active_categories(top1["changes"]))

    # [Top 2]: Top1에서 사용하지 않은 남은 레버 단일 추천 중 가장 효과가 높은 것
    rem_cats_top2 = [c for c in CATEGORIES if c not in used_categories]
    top2_candidates = [single_lever_dict[c] for c in rem_cats_top2 if c in single_lever_dict and not _is_duplicate_change(single_lever_dict[c]["changes"], used_changes)]
    top2_candidates.sort(key=lambda x: x["improvement_percent"], reverse=True)
    
    if top2_candidates:
        top2 = top2_candidates[0]
        final_recommendations.append(top2)
        used_changes.append(top2["changes"])
        used_categories.update(_get_active_categories(top2["changes"]))

    # [Top 3]: Top1과 Top2에서 사용하지 않은 남은 레버 단일 추천 중 가장 효과가 높은 것
    rem_cats_top3 = [c for c in CATEGORIES if c not in used_categories]
    top3_candidates = [single_lever_dict[c] for c in rem_cats_top3 if c in single_lever_dict and not _is_duplicate_change(single_lever_dict[c]["changes"], used_changes)]
    top3_candidates.sort(key=lambda x: x["improvement_percent"], reverse=True)
    
    if top3_candidates:
        top3 = top3_candidates[0]
        final_recommendations.append(top3)
        used_changes.append(top3["changes"])
        used_categories.update(_get_active_categories(top3["changes"]))

    # --- 4. 부족분 보충 (미사용 레버 단일 추천이 모자라 3개가 안 채워진 경우 폴백) ---
    if len(final_recommendations) < top_n:
        search_pool = all_positive_candidates + all_candidates_raw
        
        while len(final_recommendations) < top_n:
            used_cats_list = [_get_active_categories(r["changes"]) for r in final_recommendations]
            
            unselected_candidates = []
            for cand in search_pool:
                if not _is_duplicate_change(cand["changes"], used_changes):
                    cand_cats = _get_active_categories(cand["changes"])
                    overlap_score = _category_overlap_score(cand_cats, used_cats_list)
                    unselected_candidates.append((overlap_score, cand))
                    
            if not unselected_candidates:
                break
                
            # (overlap_score 오름차순, improvement_percent 내림차순) 정렬
            unselected_candidates.sort(key=lambda x: (x[0], -x[1]["improvement_percent"]))
            
            best_overlap, best_cand = unselected_candidates[0]
            
            if best_overlap > 0:
                best_cand["note"] = "유사한 개선 전략이 반복되어 표시됩니다. 더 다양한 대안을 찾지 못했습니다"
            elif best_cand["improvement_percent"] <= 0:
                best_cand["note"] = "이미 위험 요인이 높아 추가 개선 효과가 제한적일 수 있습니다"
                
            final_recommendations.append(best_cand)
            used_changes.append(best_cand["changes"])
            used_categories.update(_get_active_categories(best_cand["changes"]))

    # 내부 정리용 임시 category 키 제거
    for r in final_recommendations:
        r.pop("category", None)

    return final_recommendations[:top_n]
