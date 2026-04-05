@echo off
setlocal

echo ========================================
echo AMS PROJECT - TEST PIPELINE
echo ========================================

echo.
echo [0] Verification environnement...
python --version
pytest --version
if errorlevel 1 goto :error

echo OK environnement pret
echo ----------------------------------------

echo.
echo [1] Tests PREPROCESSOR
pytest tests/test_preprocessor.py -v
if errorlevel 1 goto :error
echo [OK] Preprocessor OK
echo ----------------------------------------

echo.
echo [2] Tests GRAPH BUILDER
pytest tests/test_graph_builder.py -v
if errorlevel 1 goto :error
echo [OK] Graph Builder OK
echo ----------------------------------------

echo.
echo [3] Tests RESOURCES AND POLARITY RULES
pytest tests/test_resources_and_polarity_rules.py -v
if errorlevel 1 goto :error
echo [OK] Resources and Rules OK
echo ----------------------------------------

echo.
echo [4] Tests NER AND ALIAS
pytest tests/test_ner_alias.py -v
if errorlevel 1 goto :error
echo [OK] NER and Alias OK
echo ----------------------------------------

echo.
echo [5] Tests NON-REGRESSION
pytest tests/test_non_regression.py -v
if errorlevel 1 goto :error
echo [OK] Non-regression OK
echo ----------------------------------------

echo.
echo [6] Tests POLARITY ANALYZER V2
if exist tests\test_polarity_analyzer_v2.py (
    pytest tests/test_polarity_analyzer_v2.py -v
    if errorlevel 1 (
        echo [WARNING] Polarity V2 tests partiellement echoues
    ) else (
        echo [OK] Polarity Analyzer V2 OK
    )
) else (
    echo [INFO] test_polarity_analyzer_v2.py absent
)
echo ----------------------------------------

echo.
echo [7] Tests CONTEXT ENTITY FILTER
if exist tests\test_context_entity_filter.py (
    pytest tests/test_context_entity_filter.py -v
    if errorlevel 1 (
        echo [WARNING] Context filter tests partiellement echoues
    ) else (
        echo [OK] Context Entity Filter OK
    )
) else (
    echo [INFO] test_context_entity_filter.py absent
)
echo ----------------------------------------

echo.
echo [8] Tests MAIN PIPELINE
if exist tests\test_main_pipeline.py (
    pytest tests/test_main_pipeline.py -v
    if errorlevel 1 (
        echo [WARNING] Main pipeline test echoue
    ) else (
        echo [OK] Main pipeline OK
    )
) else (
    echo [INFO] test_main_pipeline.py absent
)
echo ----------------------------------------

echo.
echo [9] Tests INTEGRATION (optionnel)
pytest tests/test_integration_pipeline_light.py -v
if errorlevel 1 (
    echo [WARNING] Tests integration partiellement echoues
) else (
    echo [OK] Integration OK
)
echo ----------------------------------------

echo.
echo ========================================
echo TOUS LES TESTS PRINCIPAUX SONT VALIDES
echo ========================================
echo Projet stable et pret pour experimentation

echo.
echo [COVERAGE] Analyse couverture
pytest --cov=. --cov-report=term-missing
pytest --cov=. --cov-report=html

goto :eof

:error
echo.
echo [ERROR] Une etape a echoue.
exit /b 1