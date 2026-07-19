# -*- coding: utf-8 -*-
"""
Framingham 10-Year General Cardiovascular Disease (CVD) Risk Score Calculator
Based on: D'Agostino et al. (2008) "General cardiovascular risk profile for use in primary care: 
the Framingham Heart Study" (Circulation. 2008;117(6):743-753)

Official Source: https://www.framinghamheartstudy.org/fhs-risk-functions/cardiovascular-disease-10-year-risk/
"""

def calculate_framingham(
    age: int,
    gender: str,
    total_cholesterol: float,
    hdl: float,
    systolic_bp: float,
    treated_bp: bool,
    smoker: bool,
    diabetes: bool
) -> dict:
    """
    D'Agostino et al. (2008) 포인트 시스템 기반 10년 심혈관질환 위험도를 계산합니다.
    
    Parameters:
        age (int): 나이 (30 ~ 74세 범위 내)
        gender (str): 성별 ('male', 'm', 'female', 'f' 대소문자 무관)
        total_cholesterol (float): 총콜레스테롤 (mg/dL)
        hdl (float): HDL 콜레스테롤 (mg/dL)
        systolic_bp (float): 수축기 혈압 (mmHg)
        treated_bp (bool): 고혈압 치료 약물 복용 여부
        smoker (bool): 현재 흡연 여부
        diabetes (bool): 당뇨병 여부
        
    Returns:
        dict: {"points": int, "risk_percent": float, "risk_level": "low/medium/high", "source": "출처 URL"}
    """
    
    # 1. 입력값 검증
    # 나이 유효성 검사 (공식 논문 코호트 연령 범위 30~74세)
    if not (30 <= age <= 74):
        raise ValueError("나이는 30~74세 범위여야 합니다 (D'Agostino 2008 원논문 검증 범위)")

        
    # 성별 정형화
    gender_norm = gender.lower().strip()
    if gender_norm in ('male', 'm'):
        gender_key = 'male'
    elif gender_norm in ('female', 'f'):
        gender_key = 'female'
    else:
        raise ValueError("성별(gender)은 'male'('m') 또는 'female'('f') 이어야 합니다.")
        
    # 수치 유효성 검사
    if total_cholesterol <= 0 or hdl <= 0 or systolic_bp <= 0:
        raise ValueError("콜레스테롤 수치 및 혈압은 0보다 큰 양수여야 합니다.")

    points = 0
    
    # 2. 성별에 따른 포인트 계산
    if gender_key == 'female':
        # (1) 나이 포인트
        if 30 <= age < 35:
            points += 0
        elif 35 <= age < 40:
            points += 2
        elif 40 <= age < 45:
            points += 4
        elif 45 <= age < 50:
            points += 5
        elif 50 <= age < 55:
            points += 7
        elif 55 <= age < 60:
            points += 8
        elif 60 <= age < 65:
            points += 9
        elif 65 <= age < 70:
            points += 10
        elif 70 <= age <= 74:
            points += 11
            
        # (2) HDL 콜레스테롤 포인트
        if hdl >= 60:
            points += -2
        elif 50 <= hdl < 60:
            points += -1
        elif 45 <= hdl < 50:
            points += 0
        elif 35 <= hdl < 45:
            points += 1
        else:  # hdl < 35
            points += 2
            
        # (3) 총콜레스테롤 포인트
        if total_cholesterol < 160:
            points += 0
        elif 160 <= total_cholesterol < 200:
            points += 1
        elif 200 <= total_cholesterol < 240:
            points += 2
        elif 240 <= total_cholesterol < 280:
            points += 3
        else:  # total_cholesterol >= 280
            points += 4
            
        # (4) 수축기 혈압 포인트 (치료 여부에 따른 구분)
        if treated_bp:
            if systolic_bp < 120:
                points += 0
            elif 120 <= systolic_bp < 130:
                points += 3
            elif 130 <= systolic_bp < 140:
                points += 4
            elif 140 <= systolic_bp < 150:
                points += 5
            elif 150 <= systolic_bp < 160:
                points += 6
            else:  # systolic_bp >= 160
                points += 6
        else:  # untreated
            if systolic_bp < 120:
                points += -3
            elif 120 <= systolic_bp < 130:
                points += 0
            elif 130 <= systolic_bp < 140:
                points += 1
            elif 140 <= systolic_bp < 150:
                points += 2
            elif 150 <= systolic_bp < 160:
                points += 3
            else:  # systolic_bp >= 160
                points += 4
                
        # (5) 흡연 포인트
        if smoker:
            points += 9
            
        # (6) 당뇨 포인트
        if diabetes:
            points += 3
            
    else:  # male
        # (1) 나이 포인트
        if 30 <= age < 35:
            points += 0
        elif 35 <= age < 40:
            points += 2
        elif 40 <= age < 45:
            points += 5
        elif 45 <= age < 50:
            points += 7
        elif 50 <= age < 55:
            points += 8
        elif 55 <= age < 60:
            points += 10
        elif 60 <= age < 65:
            points += 11
        elif 65 <= age < 70:
            points += 12
        elif 70 <= age <= 74:
            points += 14
            
        # (2) HDL 콜레스테롤 포인트
        if hdl >= 60:
            points += -2
        elif 50 <= hdl < 60:
            points += -1
        elif 45 <= hdl < 50:
            points += 0
        elif 35 <= hdl < 45:
            points += 1
        else:  # hdl < 35
            points += 2
            
        # (3) 총콜레스테롤 포인트
        if total_cholesterol < 160:
            points += 0
        elif 160 <= total_cholesterol < 200:
            points += 1
        elif 200 <= total_cholesterol < 240:
            points += 2
        elif 240 <= total_cholesterol < 280:
            points += 3
        else:  # total_cholesterol >= 280
            points += 4
            
        # (4) 수축기 혈압 포인트 (치료 여부에 따른 구분)
        if treated_bp:
            if systolic_bp < 120:
                points += 0
            elif 120 <= systolic_bp < 130:
                points += 1
            elif 130 <= systolic_bp < 140:
                points += 2
            elif 140 <= systolic_bp < 160:
                points += 3
            else:  # systolic_bp >= 160
                points += 3
        else:  # untreated
            if systolic_bp < 120:
                points += -2
            elif 120 <= systolic_bp < 130:
                points += 0
            elif 130 <= systolic_bp < 140:
                points += 1
            elif 140 <= systolic_bp < 160:
                points += 2
            else:  # systolic_bp >= 160
                points += 3
                
        # (5) 흡연 포인트
        if smoker:
            points += 8
            
        # (6) 당뇨 포인트
        if diabetes:
            points += 2

    # 3. 포인트 -> 10년 위험도(%) 환산
    risk_percent = 0.0
    if gender_key == 'female':
        # 여성용 위험도 매핑 (Table 6 기반)
        if points <= -3:
            risk_percent = 0.5
        elif points == -2:
            risk_percent = 0.5
        elif points == -1:
            risk_percent = 1.0
        elif points == 0:
            risk_percent = 1.2
        elif points == 1:
            risk_percent = 1.5
        elif points == 2:
            risk_percent = 1.7
        elif points == 3:
            risk_percent = 2.0
        elif points == 4:
            risk_percent = 2.4
        elif points == 5:
            risk_percent = 2.8
        elif points == 6:
            risk_percent = 3.3
        elif points == 7:
            risk_percent = 3.9
        elif points == 8:
            risk_percent = 4.5
        elif points == 9:
            risk_percent = 5.3
        elif points == 10:
            risk_percent = 6.3
        elif points == 11:
            risk_percent = 7.3
        elif points == 12:
            risk_percent = 8.6
        elif points == 13:
            risk_percent = 10.0
        elif points == 14:
            risk_percent = 11.7
        elif points == 15:
            risk_percent = 13.7
        elif points == 16:
            risk_percent = 15.9
        elif points == 17:
            risk_percent = 18.5
        elif points == 18:
            risk_percent = 21.5
        elif points == 19:
            risk_percent = 24.8
        elif points == 20:
            risk_percent = 27.5
        else:  # points >= 21
            risk_percent = 32.0
    else:  # male
        # 남성용 위험도 매핑 (Table 8 기반)
        if points <= -3:
            risk_percent = 0.5
        elif points == -2:
            risk_percent = 1.1
        elif points == -1:
            risk_percent = 1.4
        elif points == 0:
            risk_percent = 1.6
        elif points == 1:
            risk_percent = 1.9
        elif points == 2:
            risk_percent = 2.3
        elif points == 3:
            risk_percent = 2.8
        elif points == 4:
            risk_percent = 3.3
        elif points == 5:
            risk_percent = 3.9
        elif points == 6:
            risk_percent = 4.7
        elif points == 7:
            risk_percent = 5.6
        elif points == 8:
            risk_percent = 6.7
        elif points == 9:
            risk_percent = 7.9
        elif points == 10:
            risk_percent = 9.4
        elif points == 11:
            risk_percent = 11.2
        elif points == 12:
            risk_percent = 13.3
        elif points == 13:
            risk_percent = 15.6
        elif points == 14:
            risk_percent = 18.4
        elif points == 15:
            risk_percent = 21.6
        elif points == 16:
            risk_percent = 25.3
        elif points == 17:
            risk_percent = 29.3
        else:  # points >= 18
            risk_percent = 32.0

    # 4. 임상 가이드라인(CCS 등)에 기반한 위험도 등급(Risk Level) 결정
    # Low: < 10%, Medium: 10% ~ 19.9%, High: >= 20%
    if risk_percent < 10.0:
        risk_level = "low"
    elif risk_percent < 20.0:
        risk_level = "medium"
    else:
        risk_level = "high"

    return {
        "points": points,
        "risk_percent": risk_percent,
        "risk_level": risk_level,
        "source": "https://www.framinghamheartstudy.org/fhs-risk-functions/cardiovascular-disease-10-year-risk/"
    }

def calculate_multiple_risks(user_data: dict) -> dict:
    """
    유저 데이터를 딕셔너리 형태로 받아 10년 심혈관질환 위험도를 포함한 
    여러 건강 위험도를 통합 계산하는 인터페이스 함수입니다.
    
    Parameters:
        user_data (dict): 임상 정보를 포함하는 딕셔너리
        
    Returns:
        dict: {"cardiovascular_10y": calculate_framingham 결과}
    """
    # 누락된 키가 있으면 임상적 표준 기본값으로 적절히 설정
    age = user_data.get("age", 40)
    gender = user_data.get("gender", "female")
    total_cholesterol = user_data.get("total_cholesterol", 200.0)
    hdl = user_data.get("hdl", 50.0)
    systolic_bp = user_data.get("systolic_bp", 120.0)
    treated_bp = user_data.get("treated_bp", False)
    smoker = user_data.get("smoker", False)
    diabetes = user_data.get("diabetes", False)
    
    cvd_risk = calculate_framingham(
        age=age,
        gender=gender,
        total_cholesterol=total_cholesterol,
        hdl=hdl,
        systolic_bp=systolic_bp,
        treated_bp=treated_bp,
        smoker=smoker,
        diabetes=diabetes
    )
    
    return {
        "cardiovascular_10y": cvd_risk
    }

