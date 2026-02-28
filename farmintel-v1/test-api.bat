@echo off
REM Test FarmIntel V1 APIs

set API_URL=https://aj59v1wf4j.execute-api.ap-south-1.amazonaws.com/Prod

echo Testing Price API for Wheat...
curl "%API_URL%/api/prices/wheat"
echo.
echo.

echo Testing Price API for Tomato...
curl "%API_URL%/api/prices/tomato"
echo.
echo.

echo Testing Insights API for Wheat...
curl "%API_URL%/api/insights/wheat"
echo.
echo.

pause
