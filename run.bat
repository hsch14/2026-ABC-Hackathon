@echo off
chcp 65001 > nul
:menu
cls
echo ============================================================
echo   [Health Twin AI] 일괄 데모 실행 및 단위 테스트 제어기
echo ============================================================
echo.
echo  [1] 통합 데모 파이프라인 (run_demo.py) 실행
echo  [2] 실시간 대시보드 웹 애플리케이션 (dashboard.py) 실행
echo  [3] 전체 단위 테스트 (test_framingham, test_simulation, test_explanation) 실행
echo  [4] 종료
echo.
echo ============================================================
set /p choice="실행할 번호를 입력하고 Enter를 누르세요 (1-4): "

if "%choice%"=="1" (
    echo.
    echo ------------------------------------------------------------
    echo 통합 데모 파이프라인 실행 중...
    python run_demo.py
    pause
    goto menu
)
if "%choice%"=="2" (
    echo.
    echo ------------------------------------------------------------
    echo 실시간 대시보드 웹앱 구동 중 (브라우저가 자동으로 열립니다)...
    streamlit run dashboard.py
    pause
    goto menu
)
if "%choice%"=="3" (
    echo.
    echo ------------------------------------------------------------
    echo 전체 단위 테스트 일괄 실행 중...
    echo.
    echo [테스트 1] Framingham 계산기 테스트 실행...
    python test_framingham.py
    echo.
    echo [테스트 2] Counterfactual 시뮬레이터 테스트 실행...
    python test_simulation.py
    echo.
    echo [테스트 3] 자연어 설명 엔진 테스트 실행...
    python test_explanation.py
    pause
    goto menu
)
if "%choice%"=="4" (
    exit
)

echo 잘못된 입력입니다. 다시 입력해 주세요.
pause
goto menu
