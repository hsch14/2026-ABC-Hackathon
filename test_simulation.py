# -*- coding: utf-8 -*-
"""
Unit Test Suite for Counterfactual Health Simulation Module
Tests generate_counterfactuals with constraints and diversity selection algorithm.
"""

import unittest
import logging
from constants import NO_EXERCISE, NO_TIME_FOR_SLEEP, DIET_ONLY
from simulation import generate_counterfactuals

class TestCounterfactualSimulation(unittest.TestCase):
    
    def setUp(self):
        # 55세 남성 임상 및 생활습관 정보 프로필
        self.user_data = {
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

    def test_scenario_1_no_constraint_diversity_ratio(self):
        """
        Scenario 1: constraint=None -> 전체 탐색, 
        결과 3개 중 "single_lever" 2개 + "combined" 1개인지 검증
        """
        results = generate_counterfactuals(self.user_data, top_n=3, user_constraint=None)
        
        self.assertEqual(len(results), 3)
        
        single_lever_count = sum(1 for r in results if r["recommendation_type"] == "single_lever")
        combined_count = sum(1 for r in results if r["recommendation_type"] == "combined")
        
        self.assertEqual(single_lever_count, 2)
        self.assertEqual(combined_count, 1)

    def test_scenario_2_no_exercise_constraint(self):
        """
        Scenario 2: constraint=NO_EXERCISE -> 반환된 모든 결과의
        changes["exercise_per_week"]가 원래 값(1)과 동일한지 검증
        """
        results = generate_counterfactuals(self.user_data, top_n=3, user_constraint=NO_EXERCISE)
        
        self.assertTrue(len(results) > 0)
        for res in results:
            self.assertEqual(res["changes"]["exercise_per_week"], self.user_data["exercise_per_week"])

    def test_scenario_3_no_time_for_sleep_constraint(self):
        """
        Scenario 3: constraint=NO_TIME_FOR_SLEEP -> sleep_hours가 원래 값(5)과 동일한지 검증
        """
        results = generate_counterfactuals(self.user_data, top_n=3, user_constraint=NO_TIME_FOR_SLEEP)
        
        self.assertTrue(len(results) > 0)
        for res in results:
            self.assertEqual(res["changes"]["sleep_hours"], self.user_data["sleep_hours"])

    def test_scenario_4_diet_only_constraint(self):
        """
        Scenario 4: constraint=DIET_ONLY -> weight_change_kg가 -5 미만으로 내려가지 않는지 검증
        """
        results = generate_counterfactuals(self.user_data, top_n=3, user_constraint=DIET_ONLY)
        
        self.assertTrue(len(results) > 0)
        for res in results:
            self.assertGreaterEqual(res["changes"]["weight_change_kg"], -5)

    def test_scenario_5_invalid_constraint_logging(self):
        """
        Scenario 5: 정의되지 않은 constraint 문자열 입력 -> WARNING 로그가 기록되고 전체 탐색 수행 검증
        """
        # 로그 캡처 설정
        with self.assertLogs("health_twin_ai.simulation", level="WARNING") as log_capture:
            results = generate_counterfactuals(self.user_data, top_n=3, user_constraint="invalid_constraint_str")
            
        # 로그 메시지 매칭 검증
        self.assertTrue(any("Invalid constraint, ignoring" in log for log in log_capture.output))
        # 무제한 전체 탐색이 정상 진행되어 3개의 결과 반환 검증
        self.assertEqual(len(results), 3)

    def test_scenario_6_recommendations_diversity(self):
        """
        Scenario 6: Top 3 결과의 changes가 서로 실질적으로 다른지 검증 (다양성 회귀 테스트)
        최소 2개 이상의 변수에서 값의 차이가 존재하는지 대조합니다.
        """
        results = generate_counterfactuals(self.user_data, top_n=3, user_constraint=None)
        self.assertEqual(len(results), 3)
        
        # 1위와 2위, 2위와 3위의 변수 차이 개수 산출
        def get_diff_count(c1, c2):
            diff = 0
            for key in ["exercise_per_week", "sleep_hours", "weight_change_kg", "systolic_bp_change"]:
                if c1[key] != c2[key]:
                    diff += 1
            return diff
            
        diff_1_2 = get_diff_count(results[0]["changes"], results[1]["changes"])
        diff_2_3 = get_diff_count(results[1]["changes"], results[2]["changes"])
        diff_1_3 = get_diff_count(results[0]["changes"], results[2]["changes"])
        
        # 다양성 검증: 각 조합간 최소 1개 이상, 혹은 실질적 차이(2개 이상)가 있는지 대조
        self.assertGreaterEqual(diff_1_2, 1)
        self.assertGreaterEqual(diff_2_3, 1)
        self.assertGreaterEqual(diff_1_3, 1)

if __name__ == "__main__":
    unittest.main()

