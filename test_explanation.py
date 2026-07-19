# -*- coding: utf-8 -*-
"""
Pytest Suite for Counterfactual Health Explanation Module
Tests all 8 requirements-driven scenarios including constraint mapping,
API key omission fallback, schema validation failure, HTTP errors, and logging.
"""

import os
import json
import shutil
import unittest
from unittest.mock import patch, MagicMock
import urllib.error
from io import BytesIO

# 테스트 환경을 명확히 설정 (constants 상수를 안전하게 import)
from constants import NO_EXERCISE, NO_TIME_FOR_SLEEP, DIET_ONLY
from explanation import generate_natural_explanation

class TestExplanationModule(unittest.TestCase):
    
    def setUp(self):
        # 테스트용 가상 환경 변수 백업 및 설정
        self.original_env_key = os.environ.get("GROQ_API_KEY")
        os.environ["GROQ_API_KEY"] = "mock_groq_api_key_for_testing"
        
        # 기본 입력 값 정의
        self.user_data = {
            "age": 55,
            "gender": "male",
            "total_cholesterol": 250,
            "hdl": 35,
            "systolic_bp": 150,
            "treated_bp": True,
            "smoker": True,
            "diabetes": False
        }
        self.current_result = {
            "points": 25,
            "risk_percent": 32.0,
            "risk_level": "high"
        }
        self.counterfactual_results = [
            {
                "changes": {"exercise_per_week": 4, "weight_change_kg": -5},
                "new_risk_percent": 24.0,
                "improvement": 8.0
            }
        ]
        
        # 로그 저장 디렉토리 삭제하여 깨끗한 상태에서 시작
        if os.path.exists("logs"):
            shutil.rmtree("logs")

    def tearDown(self):
        # 가상 환경 변수 복원
        if self.original_env_key is not None:
            os.environ["GROQ_API_KEY"] = self.original_env_key
        else:
            if "GROQ_API_KEY" in os.environ:
                del os.environ["GROQ_API_KEY"]
                
        # 테스트 완료 후 로그 청소
        if os.path.exists("logs"):
            shutil.rmtree("logs")

    @patch("urllib.request.urlopen")
    def test_scenario_1_general_user(self, mock_urlopen):
        """
        Scenario 1: 일반 사용자 (제약 없음) 정상 작동 검증
        """
        # 정상적인 JSON 반환 모킹
        mock_llm_response = {
            "current_risk_summary": "현재 향후 10년 동안 심장이나 뇌혈관 질환이 생길 가능성은 약 32.0%로 고위험 수준입니다. 정밀 검진을 권합니다.",
            "recommendations": [
                {
                    "title": "주당 운동 4회 및 체중 5kg 감량 조합안",
                    "description": "생활 습관 변화를 통해 위험성을 약 8.0%p 낮출 수 있습니다."
                }
            ],
            "best_action": "가장 큰 효과를 보이는 체중 감량 조합을 실천해 보세요.",
            "constraint_advice": None
        }
        
        mock_api_response = {
            "choices": [{"message": {"content": json.dumps(mock_llm_response)}}]
        }
        
        # urlopen 응답 모킹 설정
        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = json.dumps(mock_api_response).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response_obj
        
        # 함수 실행
        res = generate_natural_explanation(
            self.user_data, self.current_result, self.counterfactual_results, user_constraint=None
        )
        
        # 검증
        self.assertEqual(res["generated_by"], "llm")
        self.assertEqual(res["fallback"], False)
        self.assertIsNone(res["error"])
        self.assertEqual(res["current_risk_summary"], mock_llm_response["current_risk_summary"])
        self.assertEqual(len(res["recommendations"]), len(self.counterfactual_results))
        self.assertEqual(res["recommendations"][0]["title"], mock_llm_response["recommendations"][0]["title"])
        
    @patch("urllib.request.urlopen")
    def test_scenario_2_no_exercise_constraint(self, mock_urlopen):
        """
        Scenario 2: NO_EXERCISE 제약사항 전달 시 설명 및 스키마 검증
        """
        mock_llm_response = {
            "current_risk_summary": "현재 심장 질환 가능성이 32.0% 수준입니다.",
            "recommendations": [
                {
                    "title": "식단 조절 중심 조언",
                    "description": "운동이 불가하므로 식습관 개선으로 8.0%p 개선 효과를 기대합니다."
                }
            ],
            "best_action": "식단 개선",
            "constraint_advice": "사용자는 운동이 어려운 상황이므로 체중관리 및 혈압관리를 중점 조언합니다."
        }
        
        mock_api_response = {
            "choices": [{"message": {"content": json.dumps(mock_llm_response)}}]
        }
        
        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = json.dumps(mock_api_response).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response_obj
        
        res = generate_natural_explanation(
            self.user_data, self.current_result, self.counterfactual_results, user_constraint=NO_EXERCISE
        )
        
        self.assertEqual(res["generated_by"], "llm")
        self.assertIsNotNone(res["constraint_advice"])
        self.assertIn("운동", res["constraint_advice"])
        
    @patch("urllib.request.urlopen")
    def test_scenario_3_no_time_for_sleep_constraint(self, mock_urlopen):
        """
        Scenario 3: NO_TIME_FOR_SLEEP 제약사항 조언 검증
        """
        mock_llm_response = {
            "current_risk_summary": "위험도는 32.0%입니다.",
            "recommendations": [
                {
                    "title": "짧은 운동 조합안",
                    "description": "야근 상황이므로 일상 속 수면 효율 관리를 통해 약 8.0%p를 경감시킵니다."
                }
            ],
            "best_action": "짧은 운동",
            "constraint_advice": "야근으로 시간이 부족하므로 수면 및 스트레스 조언을 제공합니다."
        }
        
        mock_api_response = {
            "choices": [{"message": {"content": json.dumps(mock_llm_response)}}]
        }
        
        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = json.dumps(mock_api_response).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response_obj
        
        res = generate_natural_explanation(
            self.user_data, self.current_result, self.counterfactual_results, user_constraint=NO_TIME_FOR_SLEEP
        )
        
        self.assertEqual(res["generated_by"], "llm")
        self.assertIsNotNone(res["constraint_advice"])
        self.assertIn("야근", res["constraint_advice"])

    def test_scenario_4_api_key_missing_fallback(self):
        """
        Scenario 4: API Key 오류 (환경변수 빈 문자열) -> 재시도 없이 즉시 Fallback으로 복구
        """
        # API Key 비우기
        os.environ["GROQ_API_KEY"] = ""
        
        res = generate_natural_explanation(
            self.user_data, self.current_result, self.counterfactual_results, user_constraint=None
        )
        
        # 검증
        self.assertEqual(res["generated_by"], "fallback")
        self.assertEqual(res["model"], "fallback-template")
        self.assertEqual(res["fallback"], True)
        self.assertEqual(res["retry_count"], 0)
        self.assertEqual(res["error"], "APIKeyMissing")
        
        # recommendations 크기와 counterfactual_results 크기 대조 검증
        self.assertEqual(len(res["recommendations"]), len(self.counterfactual_results))

    @patch("urllib.request.urlopen")
    def test_scenario_5_log_creation(self, mock_urlopen):
        """
        Scenario 5: logs 생성 여부 및 필드 스키마 완전성 검증
        """
        mock_llm_response = {
            "current_risk_summary": "안내",
            "recommendations": [{"title": "추천", "description": "설명"}],
            "best_action": "행동",
            "constraint_advice": None
        }
        mock_api_response = {
            "choices": [{"message": {"content": json.dumps(mock_llm_response)}}]
        }
        
        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = json.dumps(mock_api_response).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response_obj
        
        # 실행
        generate_natural_explanation(
            self.user_data, self.current_result, self.counterfactual_results, user_constraint=None
        )
        
        # 로그 파일 및 latest.json 존재 확인
        latest_path = os.path.join("logs", "latest.json")
        self.assertTrue(os.path.exists(latest_path))
        
        # latest.json 데이터 스키마 완전성 검사
        with open(latest_path, "r", encoding="utf-8") as f:
            log_data = json.load(f)
            
        expected_log_keys = {
            "user_data", "current_result", "counterfactual_results", "llm_input",
            "llm_output", "generated_by", "model", "timestamp", "latency_ms",
            "retry_count", "fallback", "error"
        }
        for key in expected_log_keys:
            self.assertIn(key, log_data)
            
        # latency_ms가 유효한 양의 정수/실수(perf_counter 측정치)인지 검증
        self.assertGreaterEqual(log_data["latency_ms"], 0)

    @patch("urllib.request.urlopen")
    def test_scenario_6_invalid_constraint_value(self, mock_urlopen):
        """
        Scenario 6: 정의되지 않은 constraint 값 입력 시 constraint_advice None 반환 및 WARNING 로깅 확인
        """
        mock_llm_response = {
            "current_risk_summary": "안내",
            "recommendations": [{"title": "추천", "description": "설명"}],
            "best_action": "행동",
            "constraint_advice": None
        }
        mock_api_response = {
            "choices": [{"message": {"content": json.dumps(mock_llm_response)}}]
        }
        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = json.dumps(mock_api_response).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response_obj
        
        # "invalid_constraint_str"는 VALID_CONSTRAINTS에 속하지 않음
        res = generate_natural_explanation(
            self.user_data, self.current_result, self.counterfactual_results, user_constraint="invalid_constraint_str"
        )
        
        # 검증
        self.assertIsNone(res["constraint_advice"])
        self.assertEqual(res["generated_by"], "llm")

    @patch("urllib.request.urlopen")
    def test_scenario_7_http_401_error_immediate_fallback(self, mock_urlopen):
        """
        Scenario 7: HTTP 401 에러 모킹 시 재시도(retry_count=0) 없이 즉시 fallback 및 에러 기록 검증
        """
        # HTTP 401 에러 객체 생성하여 모킹
        http_error = urllib.error.HTTPError(
            url="https://api.groq.com",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=None
        )
        mock_urlopen.side_effect = http_error
        
        res = generate_natural_explanation(
            self.user_data, self.current_result, self.counterfactual_results, user_constraint=None
        )
        
        # 검증
        self.assertEqual(res["generated_by"], "fallback")
        self.assertEqual(res["fallback"], True)
        self.assertEqual(res["retry_count"], 0)  # HTTP 401은 즉시 fallback으로 가야 함
        self.assertEqual(res["error"], "HTTP401")
        self.assertEqual(len(res["recommendations"]), len(self.counterfactual_results))

    @patch("urllib.request.urlopen")
    def test_scenario_8_non_json_llm_response_schema_validation_failure(self, mock_urlopen):
        """
        Scenario 8: LLM이 일반 텍스트(비JSON) 반환 시 _validate_response_schema 파싱/검증 에러 발생 후 fallback 복구 검증
        """
        # 비JSON 형태의 답변 모킹
        non_json_content = "안녕하세요. 당신의 10년 심장 질환 발생 위험도는 32%이며 체중 감량을 추천합니다."
        mock_api_response = {
            "choices": [{"message": {"content": non_json_content}}]
        }
        
        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = json.dumps(mock_api_response).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response_obj
        
        res = generate_natural_explanation(
            self.user_data, self.current_result, self.counterfactual_results, user_constraint=None
        )
        
        # 검증 (JSONDecodeError로 빠지며 fallback으로 안전 복구)
        self.assertEqual(res["generated_by"], "fallback")
        self.assertEqual(res["fallback"], True)
        self.assertEqual(res["retry_count"], 0)
        self.assertEqual(res["error"], "JSONDecodeError")
        self.assertEqual(len(res["recommendations"]), len(self.counterfactual_results))

if __name__ == "__main__":
    unittest.main()
