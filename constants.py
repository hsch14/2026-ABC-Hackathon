# -*- coding: utf-8 -*-
"""
Constants for Health Twin AI Explainer Module
Centralizes constraint keys and LLM/API configuration parameters.
"""

# 제약사항 (Constraints) 정의
NO_EXERCISE = "no_exercise"
NO_TIME_FOR_SLEEP = "no_time_for_sleep"
DIET_ONLY = "diet_only"

# 유효한 제약사항 세트
VALID_CONSTRAINTS = {NO_EXERCISE, NO_TIME_FOR_SLEEP, DIET_ONLY}

# Groq API 및 LLM 매개변수 설정
MODEL_NAME = "llama-3.3-70b-versatile"
FALLBACK_MODEL_NAME = "fallback-template"
TEMPERATURE = 0.3
TOP_P = 0.9
MAX_TOKENS = 500
TIMEOUT_SECONDS = 15

# 자유 대화형 챗봇의 자연스러운 응답 생성을 위해 기존 구조화 모델(500) 대비 여유 있게 설정
CHAT_MAX_TOKENS = 800

